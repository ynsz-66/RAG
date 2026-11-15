from functools import lru_cache
from typing import List

from fastembed.rerank.cross_encoder import TextCrossEncoder

from src.validators import MinimalSource
from src.var import RERANKER_MODEL


@lru_cache(maxsize=1)
def get_reranker() -> TextCrossEncoder:
    """Load the cross-encoder once, on first use (downloads it if missing)."""
    print(f"Loading reranker {RERANKER_MODEL}")
    return TextCrossEncoder(model_name=RERANKER_MODEL)


def rerank(
    query: str, sources: List[MinimalSource], k: int
) -> List[MinimalSource]:
    """Score (query, chunk) pairs with the cross-encoder, keep top-``k``."""
    if not sources:
        return []
    texts = [f"{s.file_path}\n{s.content}" for s in sources]
    scores = get_reranker().rerank(query, texts)
    ranked = sorted(
        zip(scores, sources), key=lambda pair: pair[0], reverse=True
    )
    return [source for _, source in ranked[:k]]
