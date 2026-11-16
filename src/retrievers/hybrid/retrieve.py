import time
from typing import List

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException

from src.retrievers.embedding.indexing import embed
from src.retrievers.hybrid.indexing import TEXT_FIELD
from src.retrievers.rerank import rerank
from src.retrievers.rewrite import keywords_query
from src.retrievers.rewrite import reformulated_query
from src.validators import MinimalSource
from src.var import (
    EMBED_HOST, EMBED_MODEL, QDRANT_HYBRID_COLLECTION, QDRANT_URL,
    RERANK_CANDIDATES,
)

PREFETCH_LIMIT = 100


def retrieve(
    query: str, k: int = 10, reranker: bool = False, rewrite: bool = False
) -> List[MinimalSource]:
    """Fuse dense and BM25 with RRF, return top-``k``, reranked if asked."""
    start_time = time.time()
    client = QdrantClient(url=QDRANT_URL)
    try:
        exists = client.collection_exists(QDRANT_HYBRID_COLLECTION)
    except ResponseHandlingException:
        raise ConnectionError(
            f"Qdrant unreachable at {QDRANT_URL}: run `make up` first"
        ) from None
    if not exists:
        raise FileNotFoundError(
            "Qdrant hybrid collection not found: index the corpus first"
        )

    dense_query, text_query = query, query
    if rewrite:
        dense_query = reformulated_query(query)
        text_query = keywords_query(query)
        print(f"rewrite (dense): {dense_query}")
        print(f"rewrite (bm25): {text_query}")

    candidates = max(k, RERANK_CANDIDATES) if reranker else k
    print(f"embedding: calling {EMBED_MODEL} on {EMBED_HOST}")
    vector = embed([dense_query])[0]
    print(f"qdrant: hybrid search (dense + BM25, RRF) on {QDRANT_URL} "
          f"(collection {QDRANT_HYBRID_COLLECTION}, limit {candidates})")
    hits = client.query_points(
        QDRANT_HYBRID_COLLECTION,
        prefetch=[
            models.Prefetch(
                query=vector,
                limit=max(candidates, PREFETCH_LIMIT),
            ),
            models.Prefetch(
                query=models.TextQuery(text=text_query),
                using=TEXT_FIELD,
                limit=max(candidates, PREFETCH_LIMIT),
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=candidates,
    ).points

    sources = [
        MinimalSource(**{
            key: hit.payload[key] for key in MinimalSource.model_fields
        })
        for hit in hits
        if hit.payload is not None
    ]
    top = rerank(query, sources, k) if reranker else sources
    print(f"time = {time.time() - start_time:.2f} seconds")
    return top
