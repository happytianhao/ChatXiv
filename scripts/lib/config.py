"""Paths, env loading, and shared configuration."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


def _detect_root() -> Path:
    override = os.environ.get("CHATXIV_ROOT")
    if override:
        return Path(override).resolve()
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "papers").is_dir() and (parent / "topics").is_dir():
            return parent
    return Path.cwd()


@dataclass(frozen=True)
class Paths:
    root: Path
    papers: Path
    pdfs: Path
    topics: Path
    env_file: Path

    @classmethod
    def detect(cls) -> "Paths":
        root = _detect_root()
        return cls(
            root=root,
            papers=root / "papers",
            pdfs=root / "pdfs",
            topics=root / "topics",
            env_file=root / ".env",
        )


def load_env(paths: Paths | None = None) -> None:
    """Load DEEPXIV_TOKEN from .env if present (manual fallback without python-dotenv)."""
    paths = paths or Paths.detect()
    for env_path in [paths.env_file, Path.home() / ".env"]:
        if not env_path.is_file():
            continue
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and val and key not in os.environ:
                        os.environ[key] = val
        except Exception as e:
            logger.warning("Failed to load %s: %s", env_path, e)


def get_token() -> str | None:
    return os.environ.get("DEEPXIV_TOKEN") or None


def get_report_language() -> str:
    """Report language code from REPORT_LANGUAGE env (defaults to 'en')."""
    return (os.environ.get("REPORT_LANGUAGE") or "en").strip().lower()


def report_filename(lang: str | None = None) -> str:
    """Report filename for a language: 'report.md' for en, 'report_<lang>.md' otherwise."""
    lang = (lang or get_report_language()).strip().lower()
    return "report.md" if lang in ("", "en") else f"report_{lang}.md"
