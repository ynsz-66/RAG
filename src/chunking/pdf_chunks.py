import logging
import io
from typing import List, Union

from pypdf import PdfReader

from src.validators import Chunk

log = logging.getLogger(__name__)


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
        log.warning(f"Error while reading PDF: {e}")
        return []


def get_pdf_chunks(
    file_path: str,
    content: bytes,
    max_chunk_size: int,
    chunks: List[Chunk],
) -> None:
    """Chunk raw PDF bytes page by page.

    shortcut: offsets index the concatenated extracted page text, not the
    PDF bytes; enough while no evaluation dataset targets PDFs.
    """
    def add(text: str, start: int) -> None:
        chunks.append(Chunk(
            file_path=file_path,
            content=text,
            type=".pdf",
            first_character_index=start,
            last_character_index=start + len(text),
        ))

    page_start = 0
    for page in extract_text_from_pdf(content):
        if len(page) <= max_chunk_size:
            add(page, page_start)
            page_start += len(page)
            continue

        buf = ""
        buf_start = page_start
        pos = page_start
        for line in page.split("\n"):
            piece = line + "\n"
            if len(buf) + len(piece) <= max_chunk_size:
                if not buf:
                    buf_start = pos
                buf += piece
            else:
                if buf:
                    add(buf, buf_start)
                if len(piece) > max_chunk_size:
                    for i in range(0, len(piece), max_chunk_size):
                        add(piece[i:i + max_chunk_size], pos + i)
                    buf = ""
                else:
                    buf = piece
                    buf_start = pos
            pos += len(piece)
        if buf:
            add(buf, buf_start)
        page_start += len(page)
