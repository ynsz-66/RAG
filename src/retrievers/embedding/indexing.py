from typing import List

import httpx
import time
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from tqdm import tqdm  # type: ignore

from src.chunking import create_chunk
from src.validators import Chunk
from src.var import EMBED_HOST, EMBED_MODEL, QDRANT_COLLECTION, QDRANT_URL

BATCH_SIZE = 32


def embed(texts: List[str]) -> List[List[float]]:
    """Embed texts with Ollama's native /api/embed endpoint."""
    response = httpx.post(
        f"{EMBED_HOST}/api/embed",
        json={"model": EMBED_MODEL, "input": texts},
        timeout=300,
    )
    response.raise_for_status()
    embeddings: List[List[float]] = response.json()["embeddings"]
    return embeddings


def run_indexing(
    raw_path: str,
    max_chunk_size: int = 2000,
) -> List[Chunk]:
    start_time = time.time()
    print("Create chunks...")
    chunks = create_chunk(raw_path, max_chunk_size=max_chunk_size)
    if not chunks:
        return []

    print(f"Embedding {len(chunks)} chunks with {EMBED_MODEL}...")
    vectors: List[List[float]] = []
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), unit="batch"):
        batch = chunks[i:i + BATCH_SIZE]
        vectors.extend(embed([c.content for c in batch]))

    print("Saving to Qdrant...")
    client = QdrantClient(url=QDRANT_URL)
    # full re-index: drop stale chunks from a previous run
    if client.collection_exists(QDRANT_COLLECTION):
        client.delete_collection(QDRANT_COLLECTION)
    client.create_collection(
        QDRANT_COLLECTION,
        vectors_config=VectorParams(
            size=len(vectors[0]), distance=Distance.COSINE
        ),
    )
    # batched upload: one big request would exceed Qdrant's 32 MB limit
    client.upload_points(
        QDRANT_COLLECTION,
        points=[
            PointStruct(id=i, vector=v, payload=c.model_dump())
            for i, (c, v) in enumerate(zip(chunks, vectors))
        ],
        batch_size=256,
    )
    print(f"time = {time.time() - start_time:.2f} seconds")
    return chunks
