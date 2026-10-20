# RAG

Small **100% local** RAG: **BM25** indexing + generation via **Ollama**.
Index any folder of `.md` / `.py` / `.pdf` / `.txt` files, then ask
questions in natural language. No API key, no data sent to the cloud.

```
corpus  ─┐
         ├─ chunking ─▶ BM25 index ─▶ retrieve top-k ─▶ LLM (Ollama) ─▶ answer
query  ──┘
```

## 1. Installation

Requirements: Python ≥ 3.10, [`uv`](https://docs.astral.sh/uv/) and
[Ollama](https://ollama.com).

```bash
git clone git@github.com:ynsz-66/RAG.git rag && cd rag
make install        # uv sync
```

## 2. Start Ollama

```bash
ollama serve                # exposes the API on http://localhost:11434
ollama pull qwen3:8b        # ~5 GB, good quality/RAM trade-off
```

Optional configuration:

```bash
cp .env.example .env
```

```env
OLLAMA_HOST="http://localhost:11434"
OLLAMA_MODEL="qwen3:8b"       # or any locally installed model
```

## 3. Prepare the corpus and launch the app

Put the files to index in a folder, then launch the interface:

```bash
make app
```

Indexing is driven from the UI (select the sources folder):
- chunking by type (`.md` → headings, `.py` → AST, `.pdf` → page, `.txt` → lines)
- BM25 tokenization, index saved to `data/processed/bm25_index/`
  and chunks to `data/processed/chunks/chunks.json`.

## 4. Query the RAG

Ask questions directly in the Textual interface: the top-k sources are
retrieved via BM25 and sent to the Ollama model, and the answer is streamed
as Markdown. The model answers in the language of your question.
Conversations are saved and can be reloaded from the history panel.

## 5. Going further

- **Change model**: `ollama pull <model>` then edit `OLLAMA_MODEL`
  in `.env`.
- **English corpus**: set `BM25_LANG="en"` (BM25 stopwords).
- **Lint**: `make lint` (flake8 + mypy) or `make lint-strict`.
- **Full reset**: `make clean` (removes venv, caches, `data/processed/`).

## Stack

`bm25s` · `httpx` (→ Ollama) · `python-dotenv` · `pypdf` · `pydantic` · `textual`
