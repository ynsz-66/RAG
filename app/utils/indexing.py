import shutil
import threading
from pathlib import Path

from tqdm import tqdm  # type: ignore[import-untyped]

tqdm.set_lock(threading.RLock())

from src.indexing import run_indexing  # noqa: E402
from src.var import CHUNKS_DIR, INDEX_DIR  # noqa: E402


def index_directory(path: Path, lang: str) -> int:
    """Build the BM25 index for the directory and return the chunk count."""
    return len(run_indexing(str(path), lang))


def has_files(path: Path) -> bool:
    """Return True if the directory exists and contains at least one file."""
    if not path.is_dir():
        return False
    return any(entry.is_file() for entry in path.rglob("*"))


def clear_index() -> None:
    """Delete the index and chunks stored on disk."""
    for directory in (INDEX_DIR, CHUNKS_DIR):
        shutil.rmtree(directory, ignore_errors=True)
