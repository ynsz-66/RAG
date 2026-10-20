import io
from typing import List, Union

from pypdf import PdfReader

from src.validators import Chunk


def extract_text_from_pdf(source: Union[str, bytes]) -> List[str]:
    """Return non-empty PDF page texts; empty list on error."""
    try:
        if isinstance(source, bytes):
            reader = PdfReader(io.BytesIO(source))
        else:
            reader = PdfReader(source)
        pages: List[str] = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
        return pages
    except Exception as e:
        print(f"Error while reading PDF: {e}")
        return []


def get_pdf_chunks(
    file_path: str,
    content: bytes,
    max_chunk_size: int,
    chunks: List[Chunk],
) -> None:
    """Chunk raw PDF bytes page by page."""
    pages = extract_text_from_pdf(content)

    for page in pages:
        if len(page) <= max_chunk_size:
            chunks.append(Chunk(
                file_path=file_path,
                content=page,
                type=".pdf",
            ))
            continue

        page_lines = page.split("\n")
        buf = ""
        for line in page_lines:
            piece = line + "\n"
            if len(buf) + len(piece) <= max_chunk_size:
                buf += piece
            else:
                if buf:
                    chunks.append(Chunk(
                        file_path=file_path,
                        content=buf,
                        type=".pdf",
                    ))
                if len(piece) > max_chunk_size:
                    for i in range(0, len(piece), max_chunk_size):
                        chunks.append(Chunk(
                            file_path=file_path,
                            content=piece[i:i + max_chunk_size],
                            type=".pdf",
                        ))
                    buf = ""
                else:
                    buf = piece
        if buf:
            chunks.append(Chunk(
                file_path=file_path,
                content=buf,
                type=".pdf",
            ))
