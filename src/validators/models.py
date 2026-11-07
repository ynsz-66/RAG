
from pydantic import BaseModel


class MinimalSource(BaseModel):
    """A minimal source of information in the indexed knowledge base."""

    file_path: str
    content: str
