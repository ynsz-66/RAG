import logging
import json
from typing import Any, Dict, List, Tuple

import bm25s  # type: ignore[import-untyped]
from src.retrievers.rerank import rerank
from src.retrievers.rewrite import keywords_query
from src.validators import MinimalSource
from src.var import (
    CHUNKS_PATH,
    INDEX_DIR,
    RERANK_CANDIDATES,
    STEMMER,
    STOPWORDS_EN_FR,
)

log = logging.getLogger(__name__)


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
    chunks_meta: List[Dict[str, Any]],
    query: str,
    k: int = 10,
    reranker: bool = False,
    rewrite: bool = False,
) -> List[MinimalSource]:
    """Return the top-``k`` sources for ``query``, reranked if asked."""
    search_query = query
    if rewrite:
        search_query = keywords_query(query)
        log.debug(f"rewrite (bm25): {search_query}")
    candidates = max(k, RERANK_CANDIDATES) if reranker else k
    log.debug("tokenize query...")
    query_tokens = bm25s.tokenize(
        search_query, stopwords=STOPWORDS_EN_FR, stemmer=STEMMER,
        show_progress=False,
    )
    log.debug("retrieve...")
    results, _ = retriever.retrieve(
        query_tokens, k=candidates, show_progress=False
    )
    fields = MinimalSource.model_fields
    sources = [
        MinimalSource(**{
            key: chunks_meta[int(doc_id)][key] for key in fields
        })
        for doc_id in results[0]
    ]
    return rerank(query, sources, k) if reranker else sources


def retrieve(
    query: str, k: int = 10, reranker: bool = False, rewrite: bool = False
) -> List[MinimalSource]:
    """Load the index from disk and return the top-``k`` sources."""
    retriever, chunks_meta = load_index()
    return query_index(retriever, chunks_meta, query, k, reranker, rewrite)
