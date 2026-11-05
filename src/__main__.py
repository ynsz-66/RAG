import fire  # type: ignore

from src.indexing import run_indexing
from src.ollama_llm import OllamaLLM
from src.retrieve import retrieve as retrieve_sources
from src.var import RAW_DIR, SYSTEM

MAX_TOKENS = 1024


class CLI:
    """Local BM25 RAG: index a corpus, retrieve sources, answer questions."""

    def index(
        self, raw_path: str = RAW_DIR, max_chunk_size: int = 2000
    ) -> None:
        """Chunk and index a corpus."""
        chunks = run_indexing(raw_path, max_chunk_size)
        print(f"{len(chunks)} chunks indexed from {raw_path}")

    def retrieve(self, query: str, k: int = 10) -> None:
        """Print the top-k sources for a query."""
        # fire parses args as Python literals ("42" -> int), so force str
        for i, source in enumerate(retrieve_sources(str(query), k), 1):
            print(f"--- [{i}] {source.file_path}\n{source.content}\n")

    def answer(self, query: str, k: int = 10, keep: int = 3) -> None:
        """Stream an LLM answer from the top sources."""
        query = str(query)
        sources = retrieve_sources(query, k)[:keep]
        context = "\n\n".join(source.content for source in sources)
        prompt = f"Sources:\n{context}\n\nQuestion: {query}"
        for delta in OllamaLLM().chat_stream(SYSTEM, prompt, MAX_TOKENS):
            print(delta, end="", flush=True)
        print()


def main() -> None:
    fire.Fire(CLI)


if __name__ == "__main__":
    main()
