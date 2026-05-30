"""Compact text formatters. Designed to print short summaries to stdout
so the agent's context isn't blown up by full paper bodies."""
from __future__ import annotations

from typing import Any, Iterable


def _truncate(text: str, n: int) -> str:
    text = (text or "").strip().replace("\n", " ")
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def _join(values: Iterable[Any] | None, sep: str = ", ", limit: int = 6) -> str:
    if not values:
        return ""
    items = [str(v) for v in values][:limit]
    return sep.join(items)


def split_paragraphs(body: str) -> list[str]:
    """Split a section body into paragraphs by blank lines."""
    if not body:
        return []
    parts = [p.strip() for p in body.replace("\r\n", "\n").split("\n\n")]
    return [p for p in parts if p]


def fmt_search_row(rank: int, paper: dict[str, Any]) -> str:
    pid = paper.get("paper_id") or "?"
    score = paper.get("score")
    score_s = f"{score:.3f}" if isinstance(score, (int, float)) else "    -"
    title = _truncate(paper.get("title", ""), 110)
    return f"[{rank:>3}] {pid:<14} {score_s}  {title}"


def fmt_search_list(papers: list[dict[str, Any]], with_tldr: bool = False) -> str:
    out: list[str] = []
    for i, paper in enumerate(papers, start=1):
        out.append(fmt_search_row(i, paper))
        if with_tldr:
            tldr = _truncate(paper.get("tldr") or paper.get("abstract", ""), 200)
            if tldr:
                out.append(f"        {tldr}")
    return "\n".join(out)


def fmt_brief(paper: dict[str, Any]) -> str:
    pid = paper.get("paper_id", "?")
    title = paper.get("title", "(no title)")
    tldr = paper.get("tldr") or paper.get("abstract", "")
    keywords = _join(paper.get("keywords"), limit=10)
    cats = _join(paper.get("categories"), limit=6)
    authors = _join(
        [a.get("name") if isinstance(a, dict) else a for a in (paper.get("authors") or [])],
        limit=6,
    )
    citations = paper.get("citation_count")
    code_url = paper.get("code_url") or ""
    pdf_url = paper.get("pdf_url") or ""
    url = paper.get("url") or ""
    date = paper.get("date", "")
    source = paper.get("source", "")

    lines = [
        f"# {title}",
        f"paper_id : {pid}",
    ]
    if source:
        lines.append(f"source   : {source}")
    if date:
        lines.append(f"date     : {date}")
    if authors:
        lines.append(f"authors  : {authors}")
    if cats:
        lines.append(f"categories: {cats}")
    if citations is not None:
        lines.append(f"citations: {citations}")
    if pdf_url:
        lines.append(f"pdf      : {pdf_url}")
    if code_url:
        lines.append(f"code     : {code_url}")
    if url:
        lines.append(f"url      : {url}")
    if keywords:
        lines.append(f"keywords : {keywords}")
    if tldr:
        lines.append("")
        lines.append("TLDR:")
        lines.append(_truncate(tldr, 1200))
    return "\n".join(lines)


def fmt_head(paper: dict[str, Any], with_paragraph_counts: bool = False) -> str:
    """Print structure (sections + sizes) without dumping section bodies."""
    pid = paper.get("paper_id", "?")
    title = paper.get("title", "(no title)")
    abstract = paper.get("abstract", "")
    head = paper.get("head") or {}
    head_sections = head.get("sections") if isinstance(head, dict) else None
    cached_sections = paper.get("sections") or {}

    lines = [
        f"# {title}",
        f"paper_id : {pid}",
    ]
    if abstract:
        lines.append("")
        lines.append("Abstract:")
        lines.append(_truncate(abstract, 1500))

    rows: list[tuple[str, Any]] = []
    if head_sections:
        for s in head_sections:
            if isinstance(s, dict):
                name = s.get("name") or s.get("title") or "?"
                length = s.get("length") or s.get("char_count") or s.get("tokens") or "?"
                rows.append((name, length))
            else:
                rows.append((str(s), "?"))
    else:
        for name, body in cached_sections.items():
            rows.append((name, len(body or "")))

    if rows:
        lines.append("")
        lines.append("Sections:")
        for name, length in rows:
            extra = ""
            if with_paragraph_counts:
                body = cached_sections.get(name)
                if body is not None:
                    extra = f", {len(split_paragraphs(body))} paragraphs"
                else:
                    extra = ", paragraphs=?"
            lines.append(f"  - {name}  ({length} chars{extra})")
    return "\n".join(lines)


def fmt_read(paper: dict[str, Any], section: str, paragraphs: list[tuple[int, str]]) -> str:
    pid = paper.get("paper_id", "?")
    out = [f"# {pid} :: {section}", ""]
    if not paragraphs:
        out.append("(no paragraphs matched)")
        return "\n".join(out)
    for idx, body in paragraphs:
        out.append(f"[#{idx}]")
        out.append(body.strip())
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def fmt_topic_summary(meta: dict[str, Any], paper_count: int) -> str:
    lines = [
        f"# {meta.get('title', meta.get('slug'))}",
        f"slug       : {meta.get('slug')}",
        f"created_at : {meta.get('created_at', '?')}",
        f"updated_at : {meta.get('updated_at', '?')}",
        f"papers     : {paper_count}",
    ]
    desc = meta.get("description") or ""
    if desc:
        lines += ["", "Description:", desc]
    queries = meta.get("queries") or []
    if queries:
        lines += ["", f"Queries ({len(queries)}):"]
        for q in queries[-10:]:
            lines.append(f"  - [{q.get('at','?')}] ({q.get('count', '?')}) {q.get('query','')}")
    return "\n".join(lines)
