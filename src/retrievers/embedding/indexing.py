import logging
import time
from functools import lru_cache
from typing import List

import httpx
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from tqdm import tqdm  # type: ignore

from src.chunking import create_chunk
from src.validators import Chunk
from src.var import (
    EMBED_HOST, EMBED_MODEL, EMBED_QUERY_INSTRUCT, QDRANT_COLLECTION,
    QDRANT_URL, VLLM_API_KEY, VLLM_EMBED_MODEL, VLLM_EMBED_URL, llm_backend,
)

BATCH_SIZE = 32

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def embed_client() -> OpenAI:
    return OpenAI(base_url=VLLM_EMBED_URL, api_key=VLLM_API_KEY, timeout=300)


def embed_target() -> str:
    """'<model> on <host>' for the current backend (logs)."""
    if llm_backend() == "vllm":
        return f"{VLLM_EMBED_MODEL} on {VLLM_EMBED_URL}"
    return f"{EMBED_MODEL} on {EMBED_HOST}"


def embed(texts: List[str]) -> List[List[float]]:
    """Embed texts: vLLM /v1/embeddings, or Ollama's native /api/embed."""
    if llm_backend() == "vllm":
        result = embed_client().embeddings.create(
            model=VLLM_EMBED_MODEL, input=texts
        )
        return [item.embedding for item in result.data]
    response = httpx.post(
        f"{EMBED_HOST}/api/embed",
        json={"model": EMBED_MODEL, "input": texts},
        timeout=300,
    )
    response.raise_for_status()
    embeddings: List[List[float]] = response.json()["embeddings"]
    return embeddings


def embed_query(query: str) -> List[float]:
    """Embed a search query, prefixed with the model's instruction if set
    (documents are embedded raw by ``embed``)."""
    if EMBED_QUERY_INSTRUCT:
        query = f"Instruct: {EMBED_QUERY_INSTRUCT}\nQuery: {query}"
    return embed([query])[0]


def run_indexing(
    raw_path: str,
    max_chunk_size: int = 2000,
    collection: str = QDRANT_COLLECTION,
) -> List[Chunk]:
    start_time = time.time()
    log.info("Create chunks...")
    chunks = create_chunk(raw_path, max_chunk_size=max_chunk_size)
    if not chunks:
        return []

    log.info(f"Embedding {len(chunks)} chunks with {embed_target()}...")
    vectors: List[List[float]] = []
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), unit="batch"):
        batch = chunks[i:i + BATCH_SIZE]
        vectors.extend(embed([c.content for c in batch]))

    log.info(f"Saving to Qdrant at {QDRANT_URL} (collection {collection})...")
    client = QdrantClient(url=QDRANT_URL, timeout=60)
    # full re-index: drop stale chunks from a previous run
    if client.collection_exists(collection):
        client.delete_collection(collection)
    client.create_collection(
        collection,
        vectors_config=VectorParams(
            size=len(vectors[0]), distance=Distance.COSINE
        ),
    )
    client.upload_points(
        collection,
        points=[
            PointStruct(id=i, vector=v, payload=c.model_dump())
            for i, (c, v) in enumerate(zip(chunks, vectors))
        ],
        batch_size=256,
    )
    log.info(f"time = {time.time() - start_time:.2f} seconds")
    return chunks
