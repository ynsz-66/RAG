import json
import os
from functools import partial
from typing import Callable, List, Optional

import bm25s  # type: ignore
import bm25s.utils.corpus as saving_progress_bar  # type: ignore
from src.chunking import create_chunk
from src.validators import Chunk

from .var import CHUNKS_DIR, CHUNKS_PATH, INDEX_DIR

saving_progress_bar.find_newline_positions = partial(
    saving_progress_bar.find_newline_positions, show_progress=False
)


def run_indexing(
    raw_path: str,
    lang: str,
    max_chunk_size: int = 2000,
    on_step: Optional[Callable[[str], None]] = None,
) -> List[Chunk]:
    """Chunk, tokenize, build and save the BM25 index; return the chunks.

    ``on_step`` is called with a description at each step (progress).
    """
    if on_step:
        on_step("Chunking files...")
    chunks = create_chunk(raw_path, max_chunk_size=max_chunk_size)
    if not chunks:
        return []

    texts = [c.content for c in chunks]

    if on_step:
        on_step("Tokenizing chunks...")
    texts_tokens = bm25s.tokenize(
        texts, stopwords=lang, show_progress=False
    )

    if on_step:
        on_step("Building BM25 index...")
    retriever = bm25s.BM25()
    retriever.index(texts_tokens, show_progress=False)

    if on_step:
        on_step("Saving index/chunks...")

    os.makedirs(CHUNKS_DIR, exist_ok=True)

    with open(CHUNKS_PATH, "w") as f:
        for c in chunks:
            f.write(json.dumps({
                "file_path": c.file_path,
                "content": c.content,
                "type": c.type,
            }) + "\n")

    retriever.save(INDEX_DIR)

    return chunks
