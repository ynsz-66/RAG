import time
from typing import List

from qdrant_client import QdrantClient, models

from src.retrievers.embedding.indexing import embed
from src.retrievers.hybrid.indexing import TEXT_FIELD
from src.validators import MinimalSource
from src.var import QDRANT_HYBRID_COLLECTION, QDRANT_URL

PREFETCH_LIMIT = 100


def retrieve(query: str, k: int = 10) -> List[MinimalSource]:
    """Fuse dense and BM25 results from Qdrant with RRF, return top-``k``."""
    start_time = time.time()
    client = QdrantClient(url=QDRANT_URL)
    if not client.collection_exists(QDRANT_HYBRID_COLLECTION):
        raise FileNotFoundError(
            "Qdrant hybrid collection not found: index the corpus first"
        )

    hits = client.query_points(
        QDRANT_HYBRID_COLLECTION,
        prefetch=[
            models.Prefetch(
                query=embed([query])[0], limit=max(k, PREFETCH_LIMIT)
            ),
            models.Prefetch(
                query=models.TextQuery(text=query),
                using=TEXT_FIELD,
                limit=max(k, PREFETCH_LIMIT),
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=k,
    ).points

    print(f"time = {time.time() - start_time:.2f} seconds")
    return [
        MinimalSource(**{
            key: hit.payload[key] for key in MinimalSource.model_fields
        })
        for hit in hits
        if hit.payload is not None
    ]
