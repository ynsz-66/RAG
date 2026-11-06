# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Fully local RAG: BM25 keyword retrieval (`bm25s`) over a docs folder + a local Ollama LLM for answers. Python ≥ 3.10, managed with `uv`. The `embedding` branch is where hybrid BM25 + Qdrant/Ollama embeddings work happens; `main` stays BM25-only.

## Commands

```bash
make install                                   # uv sync (deps + dev group: flake8, mypy)
make lint                                      # flake8 + mypy (--disallow-untyped-defs)
make lint-strict                               # flake8 + mypy --strict
make clean                                     # removes .venv, data/processed/ index + chunks, .history/

uv run python -m src index [raw_path] [--max-chunk-size 2000] [--method bm25]  # default raw_path: data/raw/
uv run python -m src retrieve "question" [-k 10] [--method bm25]
uv run python -m src answer "question" [-k 10] [--keep 3] [--method bm25]  # needs `ollama serve`
```

- There is no test suite. Verify changes with `make lint` and by running `index` then `retrieve`/`answer` on `data/raw/`.
- `make app` points to `main_visu.py` (Textual UI), which is not currently in the repo.
- Re-run `index` after changing the corpus or `BM25_STEMMER_LANG`; `retrieve` reads the on-disk index only.

## Architecture

Pipeline: `src/__main__.py` (fire CLI) → `chunking` → `retrievers/<method>/indexing` → `retrievers/<method>/retrieve` → `ollama_llm`.

`--method` (`bm25` default | `embedding` | `hybrid`) is dispatched by `get_indexer()`/`get_retriever()` in `src/retrievers/__init__.py`; only `bm25` is implemented, the others raise `NotImplementedError`.

- **`src/var.py`** — single source of config: loads `.env`, defines `SYSTEM`/`TITLE_SYSTEM` prompts, the combined EN+FR stopword list, the global `STEMMER` (`BM25_STEMMER_LANG`, default `french`), and on-disk paths (`RAW_DIR`, `BM25_INDEX_DIR`, `CHUNKS_DIR`, `CHUNKS_PATH`, all env-overridable).
- **`src/chunking/`** — `create_chunk()` walks a directory and `dispatch()` routes by extension (`.md`, `.py`, `.pdf`, `.txt`) to a format-specific chunker. Every chunker has the same shape: `(file_path, content, max_chunk_size, chunks)` and **appends into the passed `chunks` list** rather than returning. Strategies: Markdown by headings then paragraphs, Python by AST (class/function header prepended to each chunk), PDF by page (pypdf), text by lines. Adding a format = new module + entry in `EXTENSIONS` and `dispatch()` + the `Chunk.type` literal.
- **`src/retrievers/bm25/indexing.py`** — tokenizes chunk contents with stopwords + stemmer, builds a `bm25s.BM25` index, saves it to `INDEX_DIR`, and writes chunk metadata as **JSON Lines** to `CHUNKS_PATH` (despite the `.json` name). The BM25 doc id is the line index in that file, so the two must always be written together.
- **`src/retrievers/bm25/retrieve.py`** — loads index + chunk metadata, tokenizes the query **with the same stopwords/stemmer as indexing** (keep them in sync), returns `MinimalSource` objects.
- **`src/ollama_llm.py`** — `OllamaLLM` uses Ollama's native `/api/chat` (not the OpenAI-compatible endpoint) because only it honors `think`; `chat()` blocking, `chat_stream()` yields deltas. Env: `OLLAMA_HOST`, `OLLAMA_MODEL` (default `qwen3:8b`).
- **`src/validators/`** — pydantic models: `Chunk` (indexed unit, auto-fills `char`, validates offsets) and `MinimalSource` (retrieval result).

## Conventions

- Fully typed code; mypy must pass (`make lint`). Untyped third-party modules (`bm25s`, `Stemmer`) are imported with `# type: ignore`.
- No private functions/attributes (no leading underscore) in Python code.
