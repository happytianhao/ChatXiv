"""PDF downloader for cached papers.

Downloads each paper's PDF into a flat directory, named `<paper_id>__<title>.pdf`.
Local-first and idempotent: existing files are skipped unless `overwrite=True`,
so re-running simply fills in whatever is missing.
"""
from __future__ import annotations

import logging
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WHITESPACE = re.compile(r"\s+")
_MAX_TITLE_LEN = 150  # leave headroom under the 255-byte filename limit
_USER_AGENT = "ChatXiv/1.0 (+https://github.com/DeepXiv)"


@dataclass(frozen=True)
class DownloadResult:
    """Outcome of a single PDF download attempt."""

    paper_id: str
    status: str  # "downloaded" | "skipped" | "no_url" | "error"
    path: Optional[Path] = None
    detail: str = ""


def _sanitize_title(title: str) -> str:
    """Turn a paper title into a filesystem-safe filename fragment."""
    cleaned = _UNSAFE.sub(" ", title or "")
    cleaned = _WHITESPACE.sub(" ", cleaned).strip()
    cleaned = cleaned.strip(". ")  # avoid trailing dots/spaces (Windows-hostile)
    if len(cleaned) > _MAX_TITLE_LEN:
        cleaned = cleaned[:_MAX_TITLE_LEN].rstrip()
    return cleaned or "untitled"


def pdf_filename(paper_id: str, title: str) -> str:
    """Build the `<paper_id> - <title>.pdf` filename for a paper."""
    pid = _sanitize_title(paper_id)
    return f"{pid} - {_sanitize_title(title)}.pdf"


def download_pdf(
    url: str,
    dest: Path,
    *,
    timeout: int = 60,
    overwrite: bool = False,
) -> DownloadResult:
    """Download a single PDF to `dest`. Writes atomically via a temp file."""
    paper_stem = dest.stem
    if dest.is_file() and dest.stat().st_size > 0 and not overwrite:
        return DownloadResult(paper_stem, "skipped", dest, "already exists")

    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        if not data:
            return DownloadResult(paper_stem, "error", None, "empty response")
        tmp.write_bytes(data)
        tmp.replace(dest)
        return DownloadResult(paper_stem, "downloaded", dest, f"{len(data)} bytes")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as e:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        logger.warning("Failed to download %s: %s", url, e)
        return DownloadResult(paper_stem, "error", None, str(e))


def throttle(seconds: float) -> None:
    """Polite delay between network requests."""
    if seconds > 0:
        time.sleep(seconds)
