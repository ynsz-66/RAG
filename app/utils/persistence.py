import re
import unicodedata
from pathlib import Path

from pydantic import BaseModel

HISTORY_DIR = Path(".history")
SLUG_MAX_LENGTH = 40


class Exchange(BaseModel):
    """A single question/answer exchange."""

    query: str
    response: str


class ConversationRecord(BaseModel):
    """A full conversation identified by its creation timestamp."""

    created_at: str
    exchanges: list[Exchange] = []
    name: str = ""


def slugify(text: str) -> str:
    """Turn a title into a filename-safe fragment."""
    ascii_text = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")
    return slug[:SLUG_MAX_LENGTH].strip("_")


def conversation_path(record: ConversationRecord) -> Path:
    """Return the file path for the conversation."""
    stem = f"conversation_{record.created_at}"
    slug = slugify(record.name)
    if slug:
        stem += f"_{slug}"
    return HISTORY_DIR / f"{stem}.json"


def conversation_title(path: Path) -> str:
    """Rebuild a readable label from the filename."""
    parts = path.stem.split("_", 3)
    if len(parts) == 4 and parts[3]:
        return parts[3].replace("_", " ")
    if len(parts) >= 3:
        return f"{parts[1]} {parts[2]}"
    return path.stem


def save_conversation(record: ConversationRecord) -> Path:
    """Save the conversation to .history/ and return its path."""
    HISTORY_DIR.mkdir(exist_ok=True)
    path = conversation_path(record)
    path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    return path


def rename_conversation(record: ConversationRecord, name: str) -> None:
    """Name the conversation and rename its file if it already exists."""
    old_path = conversation_path(record)
    record.name = name
    new_path = conversation_path(record)
    if new_path != old_path and old_path.exists():
        old_path.rename(new_path)


def load_conversation(path: Path) -> ConversationRecord:
    """Load and validate a conversation from a JSON file."""
    return ConversationRecord.model_validate_json(
        path.read_text(encoding="utf-8")
    )


def list_conversations() -> list[Path]:
    """List conversation files, newest first."""
    return sorted(HISTORY_DIR.glob("conversation_*.json"), reverse=True)
