"""Resolve downloaded papers without exposing the rest of the filesystem."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAPER_ROOT = PROJECT_ROOT / "paper"


def resolve_paper_path(value, *, must_exist=True):
    """Accept portable paths and historical absolute paths inside paper/ only."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError("A non-empty paper path is required.")
    root = PAPER_ROOT.resolve()
    candidate = Path(value)
    candidate = (PROJECT_ROOT / candidate).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise ValueError("Paper path is outside the download directory.") from None
    if candidate == root or candidate.suffix.lower() != ".pdf":
        raise ValueError("A downloaded PDF file is required.")
    if must_exist and not candidate.is_file():
        raise FileNotFoundError("Paper file does not exist.")
    return candidate
