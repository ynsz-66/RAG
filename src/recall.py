"""Recall@k evaluation helpers for retrieved sources."""

from typing import List
from src.validators import MinimalSource, StudentSearchResults


def found(
    r_list: List[MinimalSource], g: MinimalSource
) -> bool:
    """Return True if any retrieved source overlaps ``g`` by >= 5%.

    Args:
        r_list: Retrieved sources for a single question.
        g: Ground-truth source to match against.

    Returns:
        True when at least one retrieved source shares the same file as
        ``g`` and overlaps it by at least 5% of ``g``'s length.
    """
    gt_len = g.last_character_index - g.first_character_index
    for r in r_list:
        if r.file_path != g.file_path:
            continue
        start = max(
            r.first_character_index, g.first_character_index
        )
        end = min(
            r.last_character_index, g.last_character_index
        )
        if max(0, end - start) / gt_len >= 0.05:
            return True
    return False


def recall_at(
    gt: dict[str, List[MinimalSource]],
    student: StudentSearchResults,
    c: int
) -> float:
    """Compute Recall@``c`` over a student's search results.

    Args:
        gt: Mapping from ``question_id`` to its ground-truth sources.
        student: The student's retrieval output across all questions.
        c: Cutoff rank; only the top-``c`` retrieved sources are scored.

    Returns:
        Mean per-question recall in ``[0, 1]``.
    """
    total = 0.0
    for res in student.search_results:
        sources = gt[res.question_id]
        top = res.retrieved_sources[:c]
        total += sum(
            found(top, g) for g in sources
        ) / len(sources)
    return total / len(student.search_results)
