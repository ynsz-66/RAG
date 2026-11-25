import logging
from functools import lru_cache
from typing import List

import httpx
from fastembed.rerank.cross_encoder import TextCrossEncoder

from src.validators import MinimalSource
from src.var import (
    FASTEMBED_RERANK_MODEL, RERANK_CANDIDATES, VLLM_API_KEY,
    VLLM_RERANK_MODEL, VLLM_RERANK_URL, llm_backend,
)

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_reranker() -> TextCrossEncoder:
    """Load the cross-encoder once, on first use (downloads it if missing)."""
    log.debug(f"Loading reranker {FASTEMBED_RERANK_MODEL}")
    return TextCrossEncoder(model_name=FASTEMBED_RERANK_MODEL)


def no_jinja(text: str) -> str:
    """Break Jinja delimiters: vLLM renders rerank inputs through Jinja,
    so a chunk holding a chat template (``{%`` ... ``\\``) fails with
    ``unexpected char '\\'`` (400)."""
    for tag in ("{{", "{%", "{#", "}}", "%}", "#}"):
        text = text.replace(tag, f"{tag[0]} {tag[1]}")
    return text


def vllm_scores(query: str, texts: List[str]) -> List[float]:
    """Score ``texts`` with vLLM's ``/rerank`` (results come sorted)."""
    response = httpx.post(
        f"{VLLM_RERANK_URL.rstrip('/')}/rerank",
        headers={"Authorization": f"Bearer {VLLM_API_KEY}"},
        json={
            "model": VLLM_RERANK_MODEL,
            "query": no_jinja(query),
            "documents": [no_jinja(t) for t in texts],
        },
        timeout=300,
    )
    if response.is_error:
        # vLLM puts the reason (e.g. prompt too long) in the body
        raise RuntimeError(
            f"vLLM /rerank {response.status_code} at {response.url}: "
            f"{response.text}"
        )
    scores = [0.0] * len(texts)
    for result in response.json()["results"]:
        scores[result["index"]] = float(result["relevance_score"])
    return scores


def rerank(
    query: str, sources: List[MinimalSource], k: int
) -> List[MinimalSource]:
    """Score (query, chunk) pairs with the cross-encoder, keep top-``k``."""
    if not sources:
        return []
    vllm = llm_backend() == "vllm"
    target = (f"{VLLM_RERANK_MODEL} on {VLLM_RERANK_URL}" if vllm
              else FASTEMBED_RERANK_MODEL)
    log.debug(f"reranker: calling {target} on {len(sources)} "
              f"candidates (RERANK_CANDIDATES={RERANK_CANDIDATES}) -> top {k}")
    texts = [f"{s.file_path}\n{s.content}" for s in sources]
    scores = (vllm_scores(query, texts) if vllm
              else list(get_reranker().rerank(query, texts)))
    ranked = sorted(
        zip(scores, sources), key=lambda pair: pair[0], reverse=True
    )
    return [source for _, source in ranked[:k]]
