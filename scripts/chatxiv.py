#!/usr/bin/env python3
"""ChatXiv CLI — local-first, progressive-disclosure paper research tool.

Usage:
    python scripts/chatxiv.py search "world models for autonomous driving" --limit 100
    python scripts/chatxiv.py brief 2409.05591
    python scripts/chatxiv.py head 2409.05591
    python scripts/chatxiv.py read 2409.05591 "Method" --grep "diffusion"
    python scripts/chatxiv.py topic create "World Models for AD"
    python scripts/chatxiv.py topic list
    python scripts/chatxiv.py local-find "world model"
    python scripts/chatxiv.py status 2409.05591
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.config import Paths, load_env
from lib.store import PaperStore
from lib.topics import TopicStore, slugify
from lib import format as fmt

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client():
    from lib.deepxiv_client import DeepXivClient
    return DeepXivClient()


def _normalize_paper(raw: dict, default_source: str = "arxiv") -> dict:
    """Fold DeepXiv response shape into the canonical local schema."""
    p = dict(raw)
    pid = (
        p.pop("arxiv_id", None)
        or p.pop("biorxiv_id", None)
        or p.pop("medrxiv_id", None)
        or p.get("paper_id")
        or p.get("id")
    )
    if pid:
        p["paper_id"] = pid
        p.pop("id", None)
    p.setdefault("source", default_source)
    if "github_url" in p and not p.get("code_url"):
        p["code_url"] = p.pop("github_url")
    else:
        p.pop("github_url", None)
    if pid and not p.get("pdf_url") and p.get("source") == "arxiv":
        p["pdf_url"] = f"https://arxiv.org/pdf/{pid}.pdf"
    return p


def _paper_summary(record: dict) -> dict:
    """Project a paper record down to lightweight fields for display."""
    return {
        k: record[k]
        for k in (
            "paper_id", "source", "title", "score", "date", "citation_count",
            "categories", "tldr", "abstract", "pdf_url", "code_url",
        )
        if k in record
    }


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_search(args: argparse.Namespace) -> int:
    paths = Paths.detect()
    load_env(paths)
    store = PaperStore(paths.papers)
    topic_store = TopicStore(paths.topics)

    query = args.query
    limit = args.limit
    offset = args.offset

    local_hits = store.find(query, limit=limit) if not args.remote_only else []

    if len(local_hits) >= limit and not args.remote_only:
        print(f"[local] {len(local_hits)} cached papers match. Use --remote-only to also query DeepXiv.\n")
        print(fmt.fmt_search_list(local_hits, with_tldr=args.with_tldr))
        return 0

    remote_papers: list[dict] = []
    try:
        client = _get_client()
        kwargs: dict = dict(
            size=min(limit, 100),
            offset=offset,
            source=args.source,
            use_fine_rerank=args.rerank,
        )
        if args.categories:
            kwargs["categories"] = args.categories.split(",")
        if args.authors:
            kwargs["authors"] = args.authors.split(",")
        if args.date_from:
            kwargs["date_from"] = args.date_from
        if args.date_to:
            kwargs["date_to"] = args.date_to
        if args.min_citations:
            kwargs["min_citation"] = args.min_citations

        resp = client.search(query, **kwargs)
        remote_papers = resp.get("result") or []
        print(f"[deepxiv] returned {len(remote_papers)} papers.\n")
    except Exception as e:
        if not local_hits:
            print(f"[error] DeepXiv search failed: {e}", file=sys.stderr)
            return 1
        print(f"[warn] DeepXiv unavailable ({e}); showing local results only.\n")

    seen: set[str] = set()
    merged: list[dict] = []
    for raw in remote_papers:
        p = _normalize_paper(raw, default_source=args.source)
        pid = p.get("paper_id")
        if not pid or pid in seen:
            continue
        seen.add(pid)
        store.upsert(pid, p)
        merged.append(store.load(pid) or p)
    for p in local_hits:
        pid = p.get("paper_id", "")
        if pid and pid not in seen:
            seen.add(pid)
            merged.append(p)

    merged = merged[:limit]

    if args.topic:
        slug = slugify(args.topic)
        if not topic_store.exists(slug):
            topic_store.create(slug, args.topic, description=f"Research on: {query}")
        topic_store.append_query(slug, query, len(merged))
        topic_store.append_papers(slug, [_paper_summary(p) for p in merged])
        print(f"[topic] saved to topics/{slug}/\n")

    print(fmt.fmt_search_list(merged, with_tldr=args.with_tldr))
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    paths = Paths.detect()
    load_env(paths)
    store = PaperStore(paths.papers)
    paper_id = args.paper_id

    record = store.load(paper_id) or {"paper_id": paper_id}
    has_complete_brief = record.get("tldr") and record.get("keywords")

    if not has_complete_brief and not args.local_only:
        try:
            client = _get_client()
            resp = client.brief(paper_id)
            data = resp if isinstance(resp, dict) else (json.loads(resp) if isinstance(resp, str) else {})
            if data:
                normalized = _normalize_paper({**data, "paper_id": paper_id}, default_source=record.get("source", "arxiv"))
                for k in ("title", "tldr", "keywords", "abstract", "citation_count",
                          "code_url", "pdf_url", "url", "authors", "categories", "date", "source"):
                    if normalized.get(k) is not None:
                        record[k] = normalized[k]
                store.upsert(paper_id, record)
                record = store.load(paper_id) or record
        except Exception as e:
            if not has_complete_brief:
                print(f"[error] Cannot fetch brief for {paper_id}: {e}", file=sys.stderr)
                return 1
            print(f"[warn] DeepXiv unavailable ({e}); showing cached data.\n")

    print(fmt.fmt_brief(record))
    return 0


def cmd_batch_brief(args: argparse.Namespace) -> int:
    """Fetch briefs for multiple papers at once."""
    paths = Paths.detect()
    load_env(paths)
    store = PaperStore(paths.papers)
    paper_ids = args.paper_ids

    client = None
    if not args.local_only:
        try:
            client = _get_client()
        except Exception as e:
            print(f"[warn] DeepXiv unavailable ({e}); using local cache only.\n")

    results = []
    for paper_id in paper_ids:
        record = store.load(paper_id) or {"paper_id": paper_id}
        has_complete_brief = record.get("tldr") and record.get("keywords")

        if not has_complete_brief and client and not args.local_only:
            try:
                resp = client.brief(paper_id)
                data = resp if isinstance(resp, dict) else (json.loads(resp) if isinstance(resp, str) else {})
                if data:
                    normalized = _normalize_paper({**data, "paper_id": paper_id}, default_source=record.get("source", "arxiv"))
                    for k in ("title", "tldr", "keywords", "abstract", "citation_count",
                              "code_url", "pdf_url", "url", "authors", "categories", "date", "source"):
                        if normalized.get(k) is not None:
                            record[k] = normalized[k]
                    store.upsert(paper_id, record)
                    record = store.load(paper_id) or record
            except Exception as e:
                print(f"[warn] Cannot fetch brief for {paper_id}: {e}", file=sys.stderr)

        results.append(record)

    print(f"[batch] fetched briefs for {len(results)} papers\n")
    for record in results:
        print(fmt.fmt_brief(record))
        print()
    return 0


def cmd_head(args: argparse.Namespace) -> int:
    paths = Paths.detect()
    load_env(paths)
    store = PaperStore(paths.papers)
    paper_id = args.paper_id

    record = store.load(paper_id) or {"paper_id": paper_id}
    has_head = record.get("head") or record.get("sections")

    if not has_head and not args.local_only:
        try:
            client = _get_client()
            resp = client.head(paper_id)
            data = resp if isinstance(resp, dict) else {}
            if data:
                store.merge_field(paper_id, "head", data)
                record = store.load(paper_id) or record
        except Exception as e:
            if not has_head:
                print(f"[error] Cannot fetch head for {paper_id}: {e}", file=sys.stderr)
                return 1
            print(f"[warn] DeepXiv unavailable ({e}); showing cached data.\n")

    print(fmt.fmt_head(record, with_paragraph_counts=args.with_paragraph_counts))
    return 0


def _parse_range(spec: str) -> tuple[int, int]:
    if ":" not in spec:
        raise ValueError("--range expects N:M (0-indexed, end-exclusive)")
    a, b = spec.split(":", 1)
    return int(a or "0"), int(b) if b else -1


def cmd_read(args: argparse.Namespace) -> int:
    paths = Paths.detect()
    load_env(paths)
    store = PaperStore(paths.papers)
    paper_id = args.paper_id
    section_name = args.section

    record = store.load(paper_id) or {"paper_id": paper_id}
    body = (record.get("sections") or {}).get(section_name)

    if body is None:
        if args.local_only:
            print(f"[error] Section '{section_name}' not cached for {paper_id}.", file=sys.stderr)
            return 1
        try:
            client = _get_client()
            resp = client.section(paper_id, section_name)
            body = resp if isinstance(resp, str) else (resp.get("content") or resp.get("text") or str(resp))
            store.merge_section(paper_id, section_name, body)
            record = store.load(paper_id) or record
        except Exception as e:
            print(f"[error] Cannot fetch section '{section_name}' for {paper_id}: {e}", file=sys.stderr)
            return 1

    paragraphs = fmt.split_paragraphs(body)
    indexed = list(enumerate(paragraphs))

    if args.grep:
        needle = args.grep.lower()
        indexed = [(i, p) for i, p in indexed if needle in p.lower()]
    if args.range:
        try:
            start, end = _parse_range(args.range)
        except ValueError as e:
            print(f"[error] {e}", file=sys.stderr)
            return 1
        end = len(indexed) if end < 0 else end
        indexed = indexed[start:end]
    if args.paragraphs is not None:
        indexed = indexed[: args.paragraphs]

    print(fmt.fmt_read(record, section_name, indexed))
    return 0


def cmd_local_find(args: argparse.Namespace) -> int:
    paths = Paths.detect()
    store = PaperStore(paths.papers)
    results = store.find(args.query, limit=args.limit)
    if not results:
        print(f"No local papers match '{args.query}'.")
        return 0
    print(f"[local] {len(results)} papers match.\n")
    print(fmt.fmt_search_list(results, with_tldr=args.with_tldr))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    paths = Paths.detect()
    store = PaperStore(paths.papers)
    paper_id = args.paper_id

    record = store.load(paper_id)
    if not record:
        print(f"Paper {paper_id} not in local cache.")
        return 1

    fetched = record.get("fetched_at") or {}
    sections = record.get("sections") or {}
    lines = [
        f"paper_id : {paper_id}",
        f"source   : {record.get('source', '?')}",
        f"title    : {record.get('title', '?')}",
        f"has_brief: {'yes' if record.get('tldr') else 'no'}",
        f"has_head : {'yes' if record.get('head') else 'no'}",
        f"sections : {list(sections.keys()) if sections else '[]'}",
        f"fetched_at: {json.dumps(fetched, indent=2) if fetched else '{}'}",
    ]
    print("\n".join(lines))
    return 0


def cmd_topic(args: argparse.Namespace) -> int:
    paths = Paths.detect()
    topic_store = TopicStore(paths.topics)

    if args.topic_cmd == "create":
        slug = slugify(args.name)
        topic_store.create(slug, args.name, description=args.desc or "")
        print(f"Created topic: topics/{slug}/")
        return 0

    if args.topic_cmd == "list":
        slugs = topic_store.list_slugs()
        if not slugs:
            print("No topics yet. Create one with: chatxiv.py topic create \"My Topic\"")
            return 0
        for s in slugs:
            meta = topic_store.load_meta(s) or {}
            count = len(topic_store.list_papers(s))
            print(f"  {s:<30} ({count} papers)  {meta.get('title', '')}")
        return 0

    if args.topic_cmd == "show":
        slug = slugify(args.name)
        meta = topic_store.load_meta(slug)
        if not meta:
            print(f"Topic '{slug}' not found.", file=sys.stderr)
            return 1
        count = len(topic_store.list_papers(slug))
        print(fmt.fmt_topic_summary(meta, count))
        return 0

    if args.topic_cmd == "papers":
        slug = slugify(args.name)
        papers = topic_store.list_papers(slug)
        if not papers:
            print(f"No papers in topic '{slug}'.")
            return 0
        print(f"[topic:{slug}] {len(papers)} papers\n")
        print(fmt.fmt_search_list(papers, with_tldr=args.with_tldr))
        return 0

    print("Unknown topic subcommand.", file=sys.stderr)
    return 1


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="chatxiv", description="Local-first paper research CLI.")
    sub = p.add_subparsers(dest="command")

    sp = sub.add_parser("search", help="Search papers (local-first, then DeepXiv)")
    sp.add_argument("query", help="Search query")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--offset", type=int, default=0)
    sp.add_argument("--topic", help="Attach results to a topic")
    sp.add_argument("--source", default="arxiv", choices=["arxiv", "biorxiv", "medrxiv"])
    sp.add_argument("--categories", help="Comma-separated category filter")
    sp.add_argument("--authors", help="Comma-separated author filter")
    sp.add_argument("--date-from", dest="date_from")
    sp.add_argument("--date-to", dest="date_to")
    sp.add_argument("--min-citations", dest="min_citations", type=int)
    sp.add_argument("--rerank", action="store_true", help="Enable fine reranking")
    sp.add_argument("--remote-only", dest="remote_only", action="store_true")
    sp.add_argument("--with-tldr", dest="with_tldr", action="store_true")

    sp = sub.add_parser("brief", help="Show paper brief (title, TLDR, keywords)")
    sp.add_argument("paper_id")
    sp.add_argument("--local-only", dest="local_only", action="store_true")

    sp = sub.add_parser("batch-brief", help="Fetch briefs for multiple papers")
    sp.add_argument("paper_ids", nargs="+", help="Paper IDs (space-separated)")
    sp.add_argument("--local-only", dest="local_only", action="store_true")

    sp = sub.add_parser("head", help="Show paper structure (sections + sizes)")
    sp.add_argument("paper_id")
    sp.add_argument("--local-only", dest="local_only", action="store_true")
    sp.add_argument("--with-paragraph-counts", dest="with_paragraph_counts", action="store_true",
                    help="Also show paragraph count per cached section")

    sp = sub.add_parser("read", help="Read a section of a paper, optionally zooming into paragraphs")
    sp.add_argument("paper_id")
    sp.add_argument("section", help="Section name, e.g. Introduction, Method")
    sp.add_argument("--grep", help="Only print paragraphs containing this substring (case-insensitive)")
    sp.add_argument("--range", help="Paragraph slice N:M (0-indexed, end-exclusive)")
    sp.add_argument("--paragraphs", type=int, help="Print at most this many paragraphs (after grep/range)")
    sp.add_argument("--local-only", dest="local_only", action="store_true")

    sp = sub.add_parser("local-find", help="Search local cache only (no API calls)")
    sp.add_argument("query")
    sp.add_argument("--limit", type=int, default=30)
    sp.add_argument("--with-tldr", dest="with_tldr", action="store_true")

    sp = sub.add_parser("status", help="Show cache status for a paper")
    sp.add_argument("paper_id")

    tp = sub.add_parser("topic", help="Manage research topics")
    tsub = tp.add_subparsers(dest="topic_cmd")
    tc = tsub.add_parser("create", help="Create a new topic")
    tc.add_argument("name", help="Topic title")
    tc.add_argument("--desc", default="", help="Description")
    tsub.add_parser("list", help="List all topics")
    ts = tsub.add_parser("show", help="Show topic details")
    ts.add_argument("name")
    tps = tsub.add_parser("papers", help="List papers in a topic")
    tps.add_argument("name")
    tps.add_argument("--with-tldr", dest="with_tldr", action="store_true")

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    dispatch = {
        "search": cmd_search,
        "brief": cmd_brief,
        "batch-brief": cmd_batch_brief,
        "head": cmd_head,
        "read": cmd_read,
        "local-find": cmd_local_find,
        "status": cmd_status,
        "topic": cmd_topic,
    }
    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
