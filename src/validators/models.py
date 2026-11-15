import uuid
from typing import List, Union

from pydantic import BaseModel, Field


class MinimalSource(BaseModel):
    """A minimal source of information in the indexed knowledge base."""

    file_path: str
    content: str = ""  # ground-truth sources in the datasets carry no content
    first_character_index: int
    last_character_index: int


class UnansweredQuestion(BaseModel):
    """A question with no ground-truth answer (used as input)."""

    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):

    """A question enriched with ground-truth sources and a reference answer."""

    sources: List[MinimalSource]
    answer: str


class RagDataset(BaseModel):
    """A dataset of RAG questions, either answered or unanswered."""

    rag_questions: List[Union[AnsweredQuestion, UnansweredQuestion]]


class MinimalSearchResults(BaseModel):
    """Search results for a single question: the retrieved sources only."""

    question_id: str
    question_str: str
    retrieved_sources: List[MinimalSource]


class MinimalAnswer(MinimalSearchResults):
    """Search results enriched with a generated answer."""

    answer: str


class StudentSearchResults(BaseModel):
    """Top-level output of the `search_dataset` command."""

    search_results: List[MinimalSearchResults]
    k: int


class StudentSearchResultsAndAnswer(StudentSearchResults):
    """Top-level output of the `answer_dataset` command."""

    search_results: List[MinimalAnswer]  # type: ignore[assignment]
