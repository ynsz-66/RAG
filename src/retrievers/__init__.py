from typing import Callable, List

from src.retrievers.bm25.indexing import run_indexing as bm25_index
from src.retrievers.bm25.retrieve import retrieve as bm25_retrieve
from src.validators import Chunk, MinimalSource

METHODS = ("bm25", "embedding", "hybrid")


def check_method(method: str) -> None:
    """Reject unknown or not-yet-implemented retrieval methods."""
    if method not in METHODS:
        raise ValueError(f"--method must be one of {METHODS}, got {method!r}")
    if method != "bm25":
        raise NotImplementedError(f"--method {method} is not implemented yet")


def get_indexer(method: str) -> Callable[[str, int], List[Chunk]]:
    check_method(method)
    return bm25_index


def get_retriever(method: str) -> Callable[[str, int], List[MinimalSource]]:
    check_method(method)
    return bm25_retrieve
