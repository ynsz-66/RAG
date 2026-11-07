import time
from typing import List

from qdrant_client import QdrantClient
from tqdm import tqdm  # type: ignore

from src.retrievers.embedding.indexing import embed
from src.validators import MinimalSource
from src.var import QDRANT_COLLECTION, QDRANT_URL


def retrieve(query: str, k: int = 10) -> List[MinimalSource]:
    """Embed ``query`` and return the top-``k`` chunks from Qdrant."""
    start_time = time.time()
    client = QdrantClient(url=QDRANT_URL)
    if not client.collection_exists(QDRANT_COLLECTION):
        raise FileNotFoundError(
            "Qdrant collection not found: index the corpus first"
        )

    with tqdm(total=2, unit="step") as bar:
        bar.set_description("embed query")
        vector = embed([query])[0]
        bar.update()
        bar.set_description("search qdrant")
        hits = client.query_points(
            QDRANT_COLLECTION, query=vector, limit=k
        ).points
        bar.update()

    print(f"time = {time.time() - start_time:.2f} seconds")
    return [
        MinimalSource(
            file_path=hit.payload["file_path"],
            content=hit.payload["content"],
        )
        for hit in hits
        if hit.payload is not None
    ]
