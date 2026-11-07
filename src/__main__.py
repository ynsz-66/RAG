import fire  # type: ignore

from src.ollama_llm import OllamaLLM
from src.retrievers import get_indexer, get_retriever
from src.var import SYSTEM

MAX_TOKENS = 1024


class CLI:
    """Local RAG: index a corpus, retrieve sources, answer questions.

    --method: bm25 (default) | embedding | hybrid
    """

    def index(
        self,
        raw_path: str,
        max_chunk_size: int = 2000,
        method: str = "bm25",
    ) -> None:
        """Chunk and index a corpus."""
        chunks = get_indexer(method)(raw_path, max_chunk_size)
        print(f"{len(chunks)} chunks indexed from {raw_path}")

    def retrieve(self, query: str, k: int = 10, method: str = "bm25") -> None:
        """Print the top-k sources for a query."""
        # fire parses args as Python literals ("42" -> int), so force str
        for i, source in enumerate(get_retriever(method)(str(query), k), 1):
            print(f"--- [{i}] {source.file_path}\n{source.content}\n")

    def answer(
        self, query: str, k: int = 10, keep: int = 3, method: str = "bm25"
    ) -> None:
        """Stream an LLM answer from the top sources."""
        query = str(query)
        sources = get_retriever(method)(query, k)[:keep]
        context = "\n\n".join(source.content for source in sources)
        prompt = f"Sources:\n{context}\n\nQuestion: {query}"
        print("answering...")
        for delta in OllamaLLM().chat_stream(SYSTEM, prompt, MAX_TOKENS):
            print(delta, end="", flush=True)
        print()


def main() -> None:
    fire.Fire(CLI)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        print(f"Goodbye! (KeyboardInterrupt: {e})")
    except Exception as e:
        print(f"Error: {e}")
