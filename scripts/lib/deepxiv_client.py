"""Thin wrapper around the DeepXiv SDK Reader."""
from __future__ import annotations

import logging
import os
from typing import Any

from . import config

logger = logging.getLogger(__name__)


class DeepXivClient:
    """Lazy-initialized DeepXiv reader. Honors DEEPXIV_TOKEN from .env."""

    def __init__(self) -> None:
        config.load_env()
        token = config.get_token()
        if token:
            os.environ["DEEPXIV_TOKEN"] = token
        from deepxiv_sdk import Reader
        self._reader = Reader(token=token)

    def search(
        self,
        query: str,
        *,
        size: int = 10,
        offset: int = 0,
        source: str = "arxiv",
        categories: list[str] | None = None,
        authors: list[str] | None = None,
        orgs: list[str] | None = None,
        min_citation: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        use_fine_rerank: bool = False,
    ) -> dict[str, Any]:
        return self._reader.search(
            query,
            size=size,
            offset=offset,
            source=source,
            categories=categories,
            authors=authors,
            orgs=orgs,
            min_citation=min_citation,
            date_from=date_from,
            date_to=date_to,
            use_fine_rerank=use_fine_rerank,
        )

    def brief(self, paper_id: str) -> Any:
        return self._reader.brief(paper_id)

    def head(self, paper_id: str) -> Any:
        return self._reader.head(paper_id)

    def section(self, paper_id: str, section: str) -> Any:
        return self._reader.section(paper_id, section)

    def preview(self, paper_id: str) -> Any:
        return self._reader.preview(paper_id)
