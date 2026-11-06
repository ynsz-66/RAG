from qdrant_client import QdrantClient
from src.chunking import create_chunk
from src.validators import Chunk
from typing import List

def run_indexing(
    raw_path: str,
    max_chunk_size: int = 2000,
) -> List[Chunk]:
    print("Create chunks...")
    chunks = create_chunk(raw_path, max_chunk_size=max_chunk_size)
    if not chunks:
        return []
    client = QdrantClient(url="http://localhost:6333")
    # lancer l'embedding sur tout les chunks
    # save dans client (base vectorielle)
    # return les chunks
    return chunks
