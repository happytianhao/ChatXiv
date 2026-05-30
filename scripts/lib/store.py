"""Local paper cache. Each paper is a JSON file named <paper_id>.json."""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ID_SAFE = re.compile(r"[^A-Za-z0-9._\-]")

_FIELD_ORDER: tuple[str, ...] = (
    "paper_id",
    "source",
    "title",
    "date",
    "authors",
    "categories",
    "citation_count",
    "score",
    "tldr",
    "abstract",
    "keywords",
    "url",
    "pdf_url",
    "code_url",
    "head",
    "sections",
    "fetched_at",
)


def _slug_id(paper_id: str) -> str:
    return _ID_SAFE.sub("_", paper_id.strip())


def _ordered(paper: dict[str, Any]) -> dict[str, Any]:
    """Return paper dict with canonical key order: identity → bibliographic → content → structure → meta."""
    ordered: dict[str, Any] = {k: paper[k] for k in _FIELD_ORDER if k in paper}
    extras = sorted(k for k in paper if k not in ordered)
    for k in extras:
        ordered[k] = paper[k]
    return ordered


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class PaperStore:
    """Local-first paper JSON store."""

    def __init__(self, papers_dir: Path) -> None:
        self.dir = papers_dir
        self.dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, paper_id: str) -> Path:
        return self.dir / f"{_slug_id(paper_id)}.json"

    def exists(self, paper_id: str) -> bool:
        return self.path_for(paper_id).is_file()

    def load(self, paper_id: str) -> dict[str, Any] | None:
        path = self.path_for(paper_id)
        if not path.is_file():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Corrupt paper file %s: %s", path, e)
            return None

    def save(self, paper: dict[str, Any]) -> Path:
        paper_id = paper.get("paper_id")
        if not paper_id:
            raise ValueError("Paper record requires paper_id")
        path = self.path_for(paper_id)
        with path.open("w", encoding="utf-8") as f:
            json.dump(_ordered(paper), f, ensure_ascii=False, indent=2)
        return path

    def upsert(self, paper_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        record = self.load(paper_id) or {"paper_id": paper_id, "fetched_at": {}}
        for k, v in patch.items():
            if v is not None:
                record[k] = v
        record["paper_id"] = paper_id
        self.save(record)
        return record

    def merge_field(self, paper_id: str, field: str, value: Any) -> dict[str, Any]:
        record = self.load(paper_id) or {"paper_id": paper_id, "fetched_at": {}}
        record[field] = value
        record.setdefault("fetched_at", {})[field] = now_iso()
        self.save(record)
        return record

    def merge_section(self, paper_id: str, section: str, content: str) -> dict[str, Any]:
        record = self.load(paper_id) or {"paper_id": paper_id, "fetched_at": {}}
        sections = record.setdefault("sections", {})
        sections[section] = content
        fetched = record.setdefault("fetched_at", {}).setdefault("sections", {})
        fetched[section] = now_iso()
        self.save(record)
        return record

    def list_ids(self) -> list[str]:
        return sorted(p.stem for p in self.dir.glob("*.json"))

    def find(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Substring search over title/abstract/tldr/keywords. Cheap and offline."""
        q = query.lower().strip()
        if not q:
            return []
        results: list[tuple[float, dict[str, Any]]] = []
        for path in self.dir.glob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    rec = json.load(f)
            except json.JSONDecodeError:
                continue
            haystack_parts = [str(rec.get(k, "")) for k in ("title", "abstract", "tldr")]
            haystack_parts.append(" ".join(rec.get("keywords") or []))
            haystack = " ".join(haystack_parts).lower()
            if q in haystack:
                score = 0.0
                if q in str(rec.get("title", "")).lower():
                    score += 2.0
                score += haystack.count(q) * 0.1
                results.append((score, rec))
        results.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in results[:limit]]
