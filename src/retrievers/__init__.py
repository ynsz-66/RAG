from typing import Callable, Dict, List, Tuple

from src.retrievers.embedding.indexing import run_indexing as embedding_index
from src.retrievers.embedding.retrieve import retrieve as embedding_retrieve
from src.retrievers.bm25.indexing import run_indexing as bm25_index
from src.retrievers.bm25.retrieve import retrieve as bm25_retrieve
from src.validators import Chunk, MinimalSource

METHODS_NAME = ("bm25", "embedding", "hybrid")

Indexer = Callable[[str, int], List[Chunk]]
Retriever = Callable[[str, int], List[MinimalSource]]

METHODS: Dict[int, Tuple[Indexer, Retriever]] = {
    1: (bm25_index, bm25_retrieve),
    2: (embedding_index, embedding_retrieve),
}


def check_method(method: str) -> int:
    """Reject unknown or not-yet-implemented retrieval methods."""
    if method not in METHODS_NAME:
        raise ValueError(
            f"--method must be one of {METHODS_NAME}, got {method!r}"
        )
    elif method == "bm25":
        return 1
    elif method == "embedding":
        return 2
    raise NotImplementedError("Hybrid retrieval is not yet implemented.")


def get_indexer(method: str) -> Indexer:
    return METHODS[check_method(method)][0]


def get_retriever(method: str) -> Retriever:
    return METHODS[check_method(method)][1]
