import os
import re
from typing import List, Literal

from src.validators import Chunk

ChunkType = Literal[".py", ".md", ".pdf", ".txt"]


def _chunk_type(file_path: str) -> ChunkType:
    """Return the chunk ``type`` literal for a given file path."""
    return ".md" if os.path.basename(file_path).endswith(".md") else ".py"


def get_chunks(
    sections: List[str],
    max_chunk_size: int,
    chunks: List[Chunk],
    file_path: str,
) -> None:
    """Split sections into size-bounded chunks appended to ``chunks``."""
    chunk_type = _chunk_type(file_path)
    for section in sections:
        if len(section) <= max_chunk_size:
            chunks.append(Chunk(
                file_path=file_path,
                content=section,
                type=chunk_type,
            ))
        else:
            paragraphes: List[str] = section.split("\n\n")
            for i in range(1, len(paragraphes)):
                paragraphes[i] = "\n\n" + paragraphes[i]

            while len(paragraphes) > 0:
                new_chunk = recur("", paragraphes, max_chunk_size)
                chunks.append(Chunk(
                    file_path=file_path,
                    content=new_chunk,
                    type=chunk_type,
                ))


def recur(
    new_section: str,
    paragraphes: List[str],
    max_chunk_size: int,
) -> str:
    """Greedily pack paragraphs (consumed in place) into one chunk."""
    while len(new_section) < max_chunk_size and len(paragraphes) > 0:
        if len(new_section) + len(paragraphes[0]) <= max_chunk_size:
            new_section += paragraphes.pop(0)
        elif len(new_section) == 0:
            new_section = paragraphes.pop(0)[:max_chunk_size]
        else:
            break
    return new_section


def get_md_chunks(
    file_path: str,
    content: str,
    max_chunk_size: int,
    chunks: List[Chunk],
) -> None:
    """Chunk Markdown text on its heading boundaries."""
    pattern = re.compile(r"^#{1,6}\s", re.MULTILINE)

    sections: List[str] = []

    matches = list(pattern.finditer(content))

    if len(matches) == 0:
        sections.append(content)
    else:
        if matches[0].start() > 0:
            sections.append(content[:matches[0].start()])

    last_character_index = 0
    if len(matches) == 1:
        sections.append(content[matches[0].start():])
    elif len(matches) > 1:
        for i in range(0, len(matches) - 1):
            first_character_index = matches[i].start()
            last_character_index = matches[i + 1].start()
            sections.append(
                content[first_character_index:last_character_index]
            )
    if len(matches) > 2:
        sections.append(content[last_character_index:])

    get_chunks(sections, max_chunk_size, chunks, file_path)
