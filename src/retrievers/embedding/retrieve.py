import time
from typing import List

from qdrant_client import QdrantClient
from tqdm import tqdm  # type: ignore
from qdrant_client.http.exceptions import ResponseHandlingException

from src.retrievers.embedding.indexing import embed
from src.retrievers.rerank import rerank
from src.validators import MinimalSource
from src.var import QDRANT_COLLECTION, QDRANT_URL, RERANK_CANDIDATES


def retrieve(
    query: str, k: int = 10, reranker: bool = False
) -> List[MinimalSource]:
    """Embed ``query``, return the top-``k`` chunks, reranked if asked."""
    start_time = time.time()
    client = QdrantClient(url=QDRANT_URL)
    try:
        exists = client.collection_exists(QDRANT_COLLECTION)
    except ResponseHandlingException:
        raise ConnectionError(
            f"Qdrant unreachable at {QDRANT_URL}: run `make up` first"
        ) from None
    if not exists:
        raise FileNotFoundError(
            "Qdrant collection not found: index the corpus first"
        )

    with tqdm(total=2, unit="step") as bar:
        bar.set_description("embed query")
        vector = embed([query])[0]
        bar.update()
        bar.set_description("search qdrant")
        hits = client.query_points(
            QDRANT_COLLECTION, query=vector,
            limit=max(k, RERANK_CANDIDATES) if reranker else k,
        ).points
        bar.update()

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
