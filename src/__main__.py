import argparse

from src.indexing import run_indexing
from src.ollama_llm import OllamaLLM
from src.retrieve import retrieve
from src.var import RAW_DIR, SYSTEM

MAX_TOKENS = 1024


def cmd_index(args: argparse.Namespace) -> None:
    chunks = run_indexing(args.raw_path, args.max_chunk_size)
    print(f"{len(chunks)} chunks indexed from {args.raw_path}")


def cmd_retrieve(args: argparse.Namespace) -> None:
    for i, source in enumerate(retrieve(args.query, args.k), 1):
        print(f"--- [{i}] {source.file_path}\n{source.content}\n")


def cmd_answer(args: argparse.Namespace) -> None:
    sources = retrieve(args.query, args.k)[: args.keep]
    context = "\n\n".join(source.content for source in sources)
    prompt = f"Sources:\n{context}\n\nQuestion: {args.query}"
    for delta in OllamaLLM().chat_stream(SYSTEM, prompt, MAX_TOKENS):
        print(delta, end="", flush=True)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m src")
    sub = parser.add_subparsers(required=True)

    index = sub.add_parser("index", help="chunk and index a corpus")
    index.add_argument("raw_path", nargs="?", default=RAW_DIR)
    index.add_argument("--max-chunk-size", type=int, default=2000)
    index.set_defaults(func=cmd_index)

    for name, func in (("retrieve", cmd_retrieve), ("answer", cmd_answer)):
        p = sub.add_parser(name, help=f"{name} for a query")
        p.add_argument("query")
        p.add_argument("-k", type=int, default=10)
        if name == "answer":
            p.add_argument("--keep", type=int, default=3)
        p.set_defaults(func=func)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
