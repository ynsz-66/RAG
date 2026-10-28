# RAG

100% local RAG: format-aware chunking → BM25 retrieval (`bm25s`) → Ollama LLM, with a Textual terminal UI.

## Commands
- `make install`: `uv sync`
- `make app`: launch the Textual UI (`main_visu.py`)
- `make lint` / `make lint-strict`: flake8 + mypy (strict must pass)
- `make clean`: removes venv, caches, index and chat history

## Layout
- `src/chunking/`: per-format chunkers (`.md` by headings, `.py` by AST, `.pdf` by page, `.txt` by lines)
- `src/indexing.py`: `run_indexing` builds the BM25 index and writes `chunks.json`
- `src/retrieve.py`: `load_index`, `query_index`, `retrieve`
- `src/ollama_llm.py`: `OllamaLLM`, an httpx client for Ollama's native `/api/chat`
- `src/var.py`: prompts and paths, all overridable via `.env`
- `app/`: Textual UI (`ui/`) and helpers (`utils/`: indexing, chat, persistence)

## Conventions
- No private functions or attributes (no `_name`).
- Type hints everywhere; code must pass `mypy --strict`.
- Ollama is called with plain `httpx` (no LangChain or SDK).

## Branches
- `main`: stable, BM25-only retrieval.
- `embedding`: work in progress on **hybrid retrieval**, adding a vector search next to BM25:
  - Embeddings: Ollama `qwen3-embedding:0.6b` (1024 dims) via `/api/embed`, batched. Queries get the Qwen3 `Instruct: ...\nQuery: ...` prefix; documents don't.
  - Vector store: Qdrant in local mode (`QdrantClient(path=...)`), no server. Point id = the chunk's index in `chunks.json`, shared with BM25.
  - Fusion: Reciprocal Rank Fusion in Python (`1 / (60 + rank)`), on top of the BM25 and dense top-k.
  - To touch: `run_indexing`, `load_index` / `query_index`, `clear_index` (app/utils), `var.py` (`EMBED_MODEL`, `QDRANT_PATH`), `pyproject.toml` (`qdrant-client`).
  - Measure with a small eval set (question → expected file, recall@k) comparing bm25 / dense / hybrid.
- Planned next: a BM25 stemmer (`bm25s.tokenize(..., stemmer=...)` with PyStemmer, applied at both indexing and query time).
