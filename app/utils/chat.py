from collections.abc import Iterator
from datetime import datetime

from app.utils.persistence import ConversationRecord, Exchange
from src.ollama_llm import OllamaLLM
from src.retrieve import retrieve
from src.var import SYSTEM, TITLE_SYSTEM

TITLE_MAX_LENGTH = 40
MAX_TOKENS = 1024


class Conversation:
    """Numbered history of question/answer exchanges."""

    def __init__(self) -> None:
        """Start with an empty history."""
        self.reset()

    def add(self, query: str, response: str) -> None:
        """Append an exchange to the history."""
        self.count += 1
        self.history += f"{self.count}. {query} -> {response}\n"
        self.record.exchanges.append(Exchange(query=query, response=response))

    def reset(self) -> None:
        """Clear the history and start a new record."""
        self.history = ""
        self.count = 0
        self.record = ConversationRecord(
            created_at=datetime.now().strftime("%Y%m%d_%H%M%S")
        )

    def restore(self, record: ConversationRecord) -> None:
        """Rebuild the history from a saved conversation."""
        self.history = ""
        self.count = 0
        self.record = record
        for exchange in record.exchanges:
            self.count += 1
            self.history += (
                f"{self.count}. {exchange.query} -> {exchange.response}\n"
            )

    def build_prompt(self, query: str, context: str) -> str:
        """Build the user message sent to the LLM."""
        if self.history:
            return (
                f"Sources:\n{context}\n\n"
                f"Conversation history:\n{self.history}\n\n"
                f"Question: {query}"
            )
        return f"Sources:\n{context}\n\nQuestion: {query}"


def fetch_context(
    query: str, lang: str, top_k: int = 10, keep: int = 3
) -> str:
    """Retrieve the top sources and join them into a context string."""
    sources = retrieve(query, lang, top_k)[:keep]
    return "\n\n".join(source.content for source in sources)


def generate_title(query: str, max_new_tokens: int = 300) -> str:
    """Summarize the first prompt into a short conversation title."""
    llm = OllamaLLM()
    raw = llm.chat(TITLE_SYSTEM, query, max_new_tokens=max_new_tokens)
    title = raw.strip().splitlines()[0] if raw.strip() else ""
    return title.strip(" \"'.:-")[:TITLE_MAX_LENGTH].strip()


def stream_answer(
    user_message: str,
    system: str = SYSTEM,
    max_new_tokens: int = MAX_TOKENS,
) -> Iterator[str]:
    """Stream the LLM answer chunk by chunk."""
    llm = OllamaLLM()
    yield from llm.chat_stream(
        system, user_message, max_new_tokens=max_new_tokens
    )
