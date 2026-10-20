import json
from typing import Any, Dict, List, Tuple

import bm25s  # type: ignore[import-untyped]
from src.validators import MinimalSource
from .var import INDEX_DIR, CHUNKS_PATH


def load_index() -> Tuple[bm25s.BM25, List[Dict[str, Any]]]:
    """Load the BM25 retriever and chunk metadata from disk."""
    try:
        retriever = bm25s.BM25.load(INDEX_DIR)
    except FileNotFoundError:
        raise FileNotFoundError("BM25 index not found: index the corpus first")

    with open(CHUNKS_PATH) as f:
        chunks_meta = [json.loads(line) for line in f]

    return retriever, chunks_meta


def query_index(
    retriever: bm25s.BM25,
    lang: str,
    chunks_meta: List[Dict[str, Any]],
    query: str,
    k: int = 10,
) -> List[MinimalSource]:
    """Return the top-``k`` sources for ``query`` from a loaded index."""
    query_tokens = bm25s.tokenize(query, stopwords=lang, show_progress=False)
    results, _ = retriever.retrieve(
        query_tokens, k=k, show_progress=False
    )
    return [
        MinimalSource(
            file_path=chunks_meta[int(doc_id)]["file_path"],
            content=chunks_meta[int(doc_id)]["content"],
        )
        for doc_id in results[0]
    ]


def retrieve(query: str, lang: str, k: int = 10) -> List[MinimalSource]:
    """Load the index from disk and return the top-``k`` sources."""
    retriever, chunks_meta = load_index()
    return query_index(retriever, lang, chunks_meta, query, k)
