from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Chunk(BaseModel):
    """An indexed text chunk with its source path and character offsets.

    Offsets are ``[first, last)`` positions in the source file text, so
    ``file_text[first:last]`` is the chunk body (without any added header).
    """

    file_path: str = Field(...)
    content: str = Field(...)
    type: Literal[".py", ".md", ".pdf", ".txt", ".json"] = Field(...)
    first_character_index: int = Field(..., ge=0)
    last_character_index: int = Field(..., ge=0)
    char: int = 0

    @model_validator(mode="after")
    def validator(self) -> "Chunk":
        """Auto-fill ``char`` and validate offsets."""
        if self.char == 0:
            self.char = len(self.content)
        if self.first_character_index > self.last_character_index:
            raise ValueError(
                "first_character_index must be <= last_character_index"
            )
        return self
