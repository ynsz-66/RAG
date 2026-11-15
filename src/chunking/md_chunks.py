import os
import re
from typing import List, Literal, Tuple

from src.validators import Chunk

ChunkType = Literal[".py", ".md", ".pdf", ".txt"]


def chunk_type_of(file_path: str) -> ChunkType:
    """Return the chunk ``type`` literal for a given file path."""
    return ".md" if os.path.basename(file_path).endswith(".md") else ".py"


def get_chunks(
    sections: List[Tuple[int, str]],
    max_chunk_size: int,
    chunks: List[Chunk],
    file_path: str,
) -> None:
    """Split ``(offset, section)`` pairs into size-bounded chunks."""
    chunk_type = chunk_type_of(file_path)
    for offset, section in sections:
        if len(section) <= max_chunk_size:
            chunks.append(Chunk(
                file_path=file_path,
                content=section,
                type=chunk_type,
                first_character_index=offset,
                last_character_index=offset + len(section),
            ))
        else:
            paragraphes: List[str] = section.split("\n\n")
            for i in range(1, len(paragraphes)):
                paragraphes[i] = "\n\n" + paragraphes[i]

            while len(paragraphes) > 0:
                new_chunk, consumed = recur("", paragraphes, max_chunk_size)
                chunks.append(Chunk(
                    file_path=file_path,
                    content=new_chunk,
                    type=chunk_type,
                    first_character_index=offset,
                    last_character_index=offset + len(new_chunk),
                ))
                offset += consumed


def recur(
    new_section: str,
    paragraphes: List[str],
    max_chunk_size: int,
) -> Tuple[str, int]:
    """Greedily pack paragraphs (consumed in place) into one chunk.

    Returns the chunk and the number of source characters consumed.
    """
    consumed = 0
    while len(new_section) < max_chunk_size and len(paragraphes) > 0:
        if len(new_section) + len(paragraphes[0]) <= max_chunk_size:
            paragraph = paragraphes.pop(0)
            new_section += paragraph
            consumed += len(paragraph)
        elif len(new_section) == 0:
            # shortcut: tail of an oversized paragraph is dropped
            paragraph = paragraphes.pop(0)
            new_section = paragraph[:max_chunk_size]
            consumed += len(paragraph)
        else:
            break
    return new_section, consumed


def get_md_chunks(
    file_path: str,
    content: str,
    max_chunk_size: int,
    chunks: List[Chunk],
) -> None:
    """Chunk Markdown text on its heading boundaries."""
    pattern = re.compile(r"^#{1,6}\s", re.MULTILINE)

    starts = [m.start() for m in pattern.finditer(content)]
    if not starts or starts[0] > 0:
        starts.insert(0, 0)
    bounds = starts + [len(content)]
    sections = [
        (bounds[i], content[bounds[i]:bounds[i + 1]])
        for i in range(len(starts))
    ]

    get_chunks(sections, max_chunk_size, chunks, file_path)
