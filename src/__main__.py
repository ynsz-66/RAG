import fire  # type: ignore

from src.openai_llm import get_llm
import json
import os
from functools import partial
from typing import List

from src.retrievers import get_indexer, get_retriever
from src.retrievers.bm25.retrieve import load_index, query_index
from src.var import SYSTEM, llm_backend
from src.validators import (
    AnsweredQuestion,
    MinimalAnswer,
    MinimalSearchResults,
    MinimalSource,
    RagDataset,
    StudentSearchResults,
    StudentSearchResultsAndAnswer,
)
from src.recall import recall_at

MAX_TOKENS = 1024


class CLI:
    """Local RAG: index a corpus, retrieve sources, answer questions.

    --method: bm25 (default) | embedding | hybrid
    --llm: vllm (default, env LLM_BACKEND) | ollama — backend for the
        rewrite/answer LLM, the embeddings and the reranker
    """

    def __init__(self, llm: str | None = None) -> None:
        if llm is not None:
            os.environ["LLM_BACKEND"] = str(llm)
        print(f"backend: {llm_backend()}")

    def index(
        self,
        raw_path: str,
        max_chunk_size: int = 2000,
        method: str = "bm25",
    ) -> None:
        """Chunk and index a corpus."""
        chunks = get_indexer(method)(raw_path, max_chunk_size)
        print(f"{len(chunks)} chunks indexed from {raw_path}")

    def retrieve(
        self,
        query: str,
        k: int = 10,
        method: str = "bm25",
        reranker: bool = False,
        rewrite: bool = False,
    ) -> None:
        """Print the top-k sources for a query."""
        sources = get_retriever(method)(str(query), k, reranker, rewrite)
        for i, source in enumerate(sources, 1):
            print(f"--- [{i}] {source.file_path}\n{source.content}\n")

    def answer(
        self, query: str,
        k: int = 10,
        keep: int = 3,
        method: str = "bm25",
        reranker: bool = False,
        rewrite: bool = False,
    ) -> None:
        """Stream an LLM answer from the top sources."""
        query = str(query)
        sources = get_retriever(method)(query, k, reranker, rewrite)[:keep]
        context = "\n\n".join(source.content for source in sources)
        prompt = f"Sources:\n{context}\n\nQuestion: {query}"
        print("answering...")
        for delta in get_llm().chat_stream(SYSTEM, prompt, MAX_TOKENS):
            print(delta, end="", flush=True)
        print()

    def answer_dataset(
        self,
        student_search_results_path: str,
        save_directory: str,
        keep: int = 3,
    ) -> None:
        """Generate answers from pre-computed search results.

        Args:
            student_search_results_path: Path to a ``StudentSearchResults``
                JSON file produced by ``search_dataset``.
            save_directory: Directory in which the enriched results will
                be written.
            keep: Number of top sources passed to the LLM as context.
        """
        try:
            with open(student_search_results_path) as f:
                searched = StudentSearchResults(**json.load(f))
        except FileNotFoundError:
            raise FileNotFoundError(
                f"{student_search_results_path} not found: "
                "run `search_dataset` first."
            )
        llm = get_llm()
        answers: List[MinimalAnswer] = []
        for i, res in enumerate(searched.search_results, 1):
            print(f"[{i}/{len(searched.search_results)}] {res.question_str}")
            context = "\n\n".join(
                s.content for s in res.retrieved_sources[:keep]
            )
            prompt = f"Sources:\n{context}\n\nQuestion: {res.question_str}"
            answers.append(MinimalAnswer(
                **res.model_dump(),
                answer=llm.chat(SYSTEM, prompt, MAX_TOKENS),
            ))
        save_json(
            StudentSearchResultsAndAnswer(
                search_results=answers, k=searched.k
            ).model_dump_json(indent=2),
            save_directory,
            student_search_results_path,
        )

    def search_dataset(
        self,
        dataset_path: str,
        save_directory: str,
        k: int = 10,
        method: str = "bm25",
        reranker: bool = False,
        rewrite: bool = False,
    ) -> None:
        """Batch-search a dataset of questions.

        Args:
            dataset_path: Path to the input JSON dataset.
            save_directory: Directory in which results will be written.
            k: Number of results to retrieve per question.
            method: Retrieval method (bm25 | embedding | hybrid).
            reranker: Rerank candidates with the cross-encoder.
            rewrite: Rewrite each question per engine (BM25 keywords,
                dense reformulation); rerank keeps the original.
        """
        with open(dataset_path) as f:
            dataset = RagDataset(**json.load(f))
        retrieve = (
            partial(query_index, *load_index())
            if method == "bm25" else get_retriever(method)
        )
        results: List[MinimalSearchResults] = []
        total = len(dataset.rag_questions)
        for i, q in enumerate(dataset.rag_questions, 1):
            print(f"[{i}/{total}] {q.question}")
            results.append(MinimalSearchResults(
                question_id=q.question_id,
                question_str=q.question,
                retrieved_sources=retrieve(q.question, k, reranker, rewrite),
            ))
            print("-----------")
        save_json(
            StudentSearchResults(
                search_results=results, k=k
            ).model_dump_json(indent=2),
            save_directory,
            dataset_path,
        )

    def evaluate(
        self,
        student_answer_path: str, dataset_path: str, k: int = 10,
    ) -> None:
        """Compute Recall@1, @3, @5, @k against the ground truth."""

        try:
            try:
                with open(student_answer_path) as f:
                    student = StudentSearchResults(**json.load(f))
            except Exception as e:
                print(f"[ERROR] Student data is not valid: {e}")
                print()
                return
            with open(dataset_path) as f:
                truth = RagDataset(**json.loads(f.read()))

            gt: dict[str, List[MinimalSource]] = {
                q.question_id: q.sources
                for q in truth.rag_questions
                if isinstance(q, AnsweredQuestion)
            }

            print(
                f"Questions evaluated: {len(student.search_results)}"
            )
            for c in (1, 3, 5, k):
                print(f"Recall@{c}: {recall_at(gt, student, c):.3f}")
            print()

        except Exception as e:
            print(f"[ERROR] ({e.__class__.__name__}) {e}")
            print()


def save_json(data: str, save_directory: str, input_path: str) -> None:
    """Write ``data`` to ``save_directory`` under the input file's name."""
    os.makedirs(save_directory, exist_ok=True)
    path = os.path.join(save_directory, os.path.basename(input_path))
    with open(path, "w") as f:
        f.write(data)
    print(f"Saved to {path}")


def main() -> None:
    fire.Fire(CLI)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        print(f"Goodbye! (KeyboardInterrupt: {e})")
    except Exception as e:
        print(f"Error: {e}")
