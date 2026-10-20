from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class Chunk(BaseModel):
    """An indexed text chunk with its source path and optional offsets."""

    file_path: str = Field(...)
    content: str = Field(...)
    type: Literal[".py", ".md", ".pdf", ".txt", ".json"] = Field(...)
    char: int = 0
    first_character_index: Optional[int] = Field(default=None, ge=0)
    last_character_index: Optional[int] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validator(self) -> "Chunk":
        """Auto-fill ``char`` and validate offsets when both are provided."""
        if self.char == 0:
            self.char = len(self.content)
        if (
            self.first_character_index is not None
            and self.last_character_index is not None
            and self.last_character_index <= self.first_character_index
        ):
            raise ValueError(
                "last_character_index must be greater than"
                " first_character_index."
            )
        return self
