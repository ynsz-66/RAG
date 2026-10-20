import ast
from typing import List, Optional

from src.validators import Chunk


def make_header(
    class_name: Optional[str] = None,
    func_name: Optional[str] = None,
) -> str:
    """Build a class/function context header, or an empty string."""
    lines = []
    if class_name:
        lines.append(f"# Class: {class_name}")
    if func_name:
        lines.append(f"# Function: {func_name}")
    if not lines:
        return ""
    return "\n".join(lines) + "\n\n"


def flush(
    chunks: List[Chunk],
    file_path: str,
    buf: str,
    header: str = "",
) -> None:
    """Append ``header + buf`` as a chunk if ``buf`` is not empty."""
    if not buf:
        return
    chunks.append(Chunk(
        file_path=file_path,
        content=header + buf,
        type=".py",
    ))


def append_split(
    chunks: List[Chunk],
    file_path: str,
    content: str,
    max_chunk_size: int,
    header: str = "",
) -> None:
    """Append ``content`` as size-bounded chunks prefixed by ``header``."""
    effective_max = max(1, max_chunk_size - len(header))

    if len(content) <= effective_max:
        if content:
            chunks.append(Chunk(
                file_path=file_path,
                content=header + content,
                type=".py",
            ))
        return

    lines = content.splitlines(keepends=True)
    buf = ""
    for line in lines:
        if len(line) > effective_max:
            flush(chunks, file_path, buf, header)
            buf = ""
            for i in range(0, len(line), effective_max):
                piece = line[i:i + effective_max]
                flush(chunks, file_path, piece, header)
        elif len(buf) + len(line) <= effective_max:
            buf += line
        else:
            flush(chunks, file_path, buf, header)
            buf = line
    flush(chunks, file_path, buf, header)


def get_python_chunks(
    file_path: str,
    content: str,
    max_chunk_size: int,
    chunks: List[Chunk],
) -> None:
    """Chunk Python source on top-level function/class boundaries."""
    lines = content.splitlines()

    line_offsets: List[int] = [0]
    for line in lines:
        line_offsets.append(line_offsets[-1] + len(line) + 1)

    tree = ast.parse(content)

    nodes = [
        n for n in ast.iter_child_nodes(tree)
        if isinstance(n, (ast.FunctionDef, ast.ClassDef))
    ]

    nodes = sorted(nodes, key=lambda n: n.lineno)

    cursor = 0

    for node in nodes:
        start_line = node.lineno - 1
        end_line = node.end_lineno if node.end_lineno is not None else 0

        if start_line > cursor:
            header_text = content[
                line_offsets[cursor]:line_offsets[start_line]
            ]
            append_split(
                chunks,
                file_path,
                header_text,
                max_chunk_size,
            )

        if isinstance(node, ast.ClassDef):
            node_header = make_header(class_name=node.name)
        else:
            node_header = make_header(func_name=node.name)

        text = content[line_offsets[start_line]:line_offsets[end_line]]
        append_split(
            chunks,
            file_path,
            text,
            max_chunk_size,
            node_header,
        )

        cursor = end_line

    if line_offsets[cursor] < len(content):
        final_text = content[line_offsets[cursor]:]
        append_split(
            chunks,
            file_path,
            final_text,
            max_chunk_size,
        )
