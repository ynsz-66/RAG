import os
from typing import List, Union

from src.validators import Chunk

from .md_chunks import get_md_chunks
from .py_chunks import get_python_chunks
from .pdf_chunks import get_pdf_chunks
from .txt_chunks import get_txt_chunks

EXTENSIONS = {".md", ".py", ".pdf", ".txt"}


def dispatch(
    file_path: str,
    content: Union[str, bytes],
    ext: str,
    max_chunk_size: int,
    chunks: List[Chunk],
    md: bool = True,
    py: bool = True,
    pdf: bool = True,
    txt: bool = True,
) -> None:
    """Route loaded content to the chunker matching ``ext``."""
    if ext == ".md" and md and isinstance(content, str):
        get_md_chunks(file_path, content, max_chunk_size, chunks)
    elif ext == ".py" and py and isinstance(content, str):
        get_python_chunks(file_path, content, max_chunk_size, chunks)
    elif ext == ".pdf" and pdf and isinstance(content, bytes):
        get_pdf_chunks(file_path, content, max_chunk_size, chunks)
    elif ext == ".txt" and txt and isinstance(content, str):
        get_txt_chunks(file_path, content, max_chunk_size, chunks)


def create_chunk(
    what_to_read: str = "data/raw/",
    max_chunk_size: int = 2000,
    md: bool = True,
    py: bool = True,
    pdf: bool = True,
    txt: bool = True,
) -> List[Chunk]:
    """Walk ``what_to_read`` and return chunks of enabled file types."""
    chunks: List[Chunk] = []

    for directory, _, files in os.walk(what_to_read):
        for name in files:
            file_path = os.path.join(directory, name)
            ext = os.path.splitext(name)[1].lower()
            if ext not in EXTENSIONS:
                continue

            content: Union[str, bytes]
            if ext == ".pdf":
                with open(file_path, "rb") as fb:
                    content = fb.read()
            else:
                with open(file_path, "r") as ft:
                    content = ft.read()

            dispatch(
                file_path, content, ext, max_chunk_size, chunks,
                md=md, py=py, pdf=pdf, txt=txt,
            )

    return chunks
