from typing import List

from qdrant_client import QdrantClient, models

from src.retrievers.embedding.indexing import run_indexing as embed_index
from src.validators import Chunk
from src.var import (
    QDRANT_HYBRID_COLLECTION, QDRANT_URL, STEMMER_LANG, STOPWORDS_EN_FR
)

TEXT_FIELD = "content"


def run_indexing(
    raw_path: str,
    max_chunk_size: int = 2000,
) -> List[Chunk]:
    """Store dense vectors in Qdrant, then BM25-index the chunk text."""
    chunks = embed_index(
        raw_path, max_chunk_size, collection=QDRANT_HYBRID_COLLECTION
    )
    if not chunks:
        return []

    print("Building Qdrant BM25 text index...")
    QdrantClient(url=QDRANT_URL, timeout=60).create_payload_index(
        QDRANT_HYBRID_COLLECTION,
        field_name=TEXT_FIELD,
        field_schema=models.TextIndexParams(
            type=models.TextIndexType.TEXT,
            stemmer=models.SnowballParams(
                type=models.Snowball.SNOWBALL,
                language=models.SnowballLanguage(STEMMER_LANG),
            ),
            stopwords=models.StopwordsSet(custom=list(STOPWORDS_EN_FR)),
            scoring=True,
        ),
        wait=True,
    )
    return chunks
