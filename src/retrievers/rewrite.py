from src.ollama_llm import OllamaLLM
from src.var import REWRITE_SYSTEM


def rewrite_query(query: str) -> str:
    """Rewrite ``query`` into a search query with the local LLM."""
    rewritten = OllamaLLM(think=False).chat(REWRITE_SYSTEM, query).strip()
    return rewritten or query
