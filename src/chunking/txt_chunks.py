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

    buf = ""
    for line in lines:
        if len(buf) + len(line) <= max_chunk_size:
            buf += line
        else:
            if buf:
                chunks.append(Chunk(
                    file_path=file_path,
                    content=buf,
                    type=".txt",
                ))
            if len(line) > max_chunk_size:
                for i in range(0, len(line), max_chunk_size):
                    chunks.append(Chunk(
                        file_path=file_path,
                        content=line[i:i + max_chunk_size],
                        type=".txt",
                    ))
                buf = ""
            else:
                buf = line
    if buf:
        chunks.append(Chunk(
            file_path=file_path,
            content=buf,
            type=".txt",
        ))
