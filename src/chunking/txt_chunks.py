from typing import List

from src.validators import Chunk


def get_txt_chunks(
    file_path: str,
    content: str,
    max_chunk_size: int,
    chunks: List[Chunk],
) -> None:
    """Chunk plain text line by line and append to ``chunks``."""
    lines = content.splitlines(keepends=True)

    def add(text: str, start: int) -> None:
        chunks.append(Chunk(
            file_path=file_path,
            content=text,
            type=".txt",
            first_character_index=start,
            last_character_index=start + len(text),
        ))

    buf = ""
    buf_start = 0
    pos = 0
    for line in lines:
        if len(buf) + len(line) <= max_chunk_size:
            if not buf:
                buf_start = pos
            buf += line
        else:
            if buf:
                add(buf, buf_start)
            if len(line) > max_chunk_size:
                for i in range(0, len(line), max_chunk_size):
                    add(line[i:i + max_chunk_size], pos + i)
                buf = ""
            else:
                buf = line
                buf_start = pos
        pos += len(line)
    if buf:
        add(buf, buf_start)
