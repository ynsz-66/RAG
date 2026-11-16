import re
from typing import List

from src.ollama_llm import OllamaLLM
from src.var import (
    REWRITE_KEYWORDS_SYSTEM,
    REWRITE_MODEL,
    REWRITE_QUERY_SYSTEM,
)

MAX_REWRITE_WORDS = 8


def first_line(text: str) -> str:
    """First non-empty line, without <think>, prefix or quotes."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    line = re.sub(r"^(search )?(query|keywords|question)\s*:\s*", "",
                  lines[0], flags=re.IGNORECASE)
    return line.strip("\"'` ")


def clean_keywords(text: str) -> str:
    """First line, deduplicated, capped at MAX_REWRITE_WORDS."""
    words: List[str] = []
    for word in first_line(text).split():
        if word.lower() not in (w.lower() for w in words):
            words.append(word)
    return " ".join(words[:MAX_REWRITE_WORDS])


def rewrite_llm() -> OllamaLLM:
    print(f"rewrite: calling {REWRITE_MODEL}")
    # repeat_penalty: small models loop at temperature 0
    return OllamaLLM(
        model=REWRITE_MODEL, think=False, temperature=0, repeat_penalty=1.3
    )


def keywords_query(query: str) -> str:
    """BM25 query: ``query`` + LLM keywords (original kept first)."""
    keywords = clean_keywords(
        rewrite_llm().chat(REWRITE_KEYWORDS_SYSTEM, query, 48)
    )
    # Appended, not replaced: a small model may drop exact identifiers.
    return f"{query} {keywords}" if keywords else query


def reformulated_query(query: str) -> str:
    """Dense query: ``query`` + one LLM-reformulated technical sentence."""
    sentence = first_line(rewrite_llm().chat(REWRITE_QUERY_SYSTEM, query, 64))
    return f"{query} {sentence}" if sentence else query
