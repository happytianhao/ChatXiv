"""Topic folders — each research topic lives under topics/<slug>/."""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import report_filename

logger = logging.getLogger(__name__)

_SLUG_BAD = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    s = _SLUG_BAD.sub("-", text.lower()).strip("-")
    return s or "topic"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TopicStore:
    def __init__(self, topics_dir: Path) -> None:
        self.dir = topics_dir
        self.dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, slug: str) -> Path:
        return self.dir / slug

    def exists(self, slug: str) -> bool:
        return self.path_for(slug).is_dir()

    def list_slugs(self) -> list[str]:
        return sorted(
            p.name for p in self.dir.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        )

    def create(self, slug: str, title: str, description: str = "") -> Path:
        path = self.path_for(slug)
        path.mkdir(parents=True, exist_ok=True)
        meta_path = path / "topic.json"
        if not meta_path.exists():
            meta = {
                "slug": slug,
                "title": title,
                "description": description,
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "queries": [],
            }
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        papers_file = path / "papers.jsonl"
        papers_file.touch(exist_ok=True)
        report = path / report_filename()
        if not report.exists():
            report.write_text(
                f"# {title}\n\n"
                f"_Created {now_iso()}_\n\n"
                "## Scope\n\n"
                f"{description or '_(fill in)_'}\n\n"
                "## Method\n\n"
                "_Search queries, sources, filters used._\n\n"
                "## Landscape\n\n"
                "_Major sub-areas and their representative papers._\n\n"
                "## Selected papers\n\n"
                "_5–20 papers with one-paragraph summaries._\n\n"
                "## Open questions\n\n"
                "## References\n\n"
                "_See `papers.jsonl` for the full ranked list._\n",
                encoding="utf-8",
            )
        return path

    def load_meta(self, slug: str) -> dict[str, Any] | None:
        meta = self.path_for(slug) / "topic.json"
        if not meta.is_file():
            return None
        return json.loads(meta.read_text(encoding="utf-8"))

    def save_meta(self, slug: str, meta: dict[str, Any]) -> None:
        meta["updated_at"] = now_iso()
        path = self.path_for(slug) / "topic.json"
        path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def append_query(self, slug: str, query: str, count: int) -> None:
        meta = self.load_meta(slug) or {"slug": slug, "queries": []}
        meta.setdefault("queries", []).append(
            {"query": query, "count": count, "at": now_iso()}
        )
        self.save_meta(slug, meta)

    def append_papers(self, slug: str, papers: list[dict[str, Any]]) -> Path:
        path = self.path_for(slug) / "papers.jsonl"
        existing_ids: set[str] = set()
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    existing_ids.add(json.loads(line).get("paper_id", ""))
                except json.JSONDecodeError:
                    continue
        with path.open("a", encoding="utf-8") as f:
            for p in papers:
                pid = p.get("paper_id")
                if not pid or pid in existing_ids:
                    continue
                existing_ids.add(pid)
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
        return path

    def list_papers(self, slug: str) -> list[dict[str, Any]]:
        path = self.path_for(slug) / "papers.jsonl"
        if not path.is_file():
            return []
        out: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out
