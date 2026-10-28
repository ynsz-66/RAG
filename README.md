<div align="center">

# 🔎 RAG — Keyword Search over Your Docs

**A simple, 100% local RAG: BM25 keyword retrieval + an Ollama LLM.**
Point it at a folder, ask a question, get an answer grounded in your files.

![Python](https://img.shields.io/badge/python-≥3.10-3776AB?logo=python&logoColor=white)
![Ollama](https://img.shields.io/badge/LLM-Ollama-000000?logo=ollama&logoColor=white)
![Retrieval](https://img.shields.io/badge/retrieval-BM25-orange)
![Local](https://img.shields.io/badge/100%25-local-success)
![License](https://img.shields.io/github/license/ynsz-66/RAG)

</div>

---

## ✨ Features

- 🔒 **Fully local**: no API key, nothing sent to the cloud
- 📂 **Multi-format**: `.md`, `.py`, `.pdf`, `.txt`
- ✂️ **Format-aware chunking**: Markdown by headings, Python by AST, PDF by page, text by lines
- ⚡ **Lightweight**: no GPU needed for retrieval, the index is just files on disk
- 🌍 **Answers in your language**, even when the sources are in another
- 💬 **Terminal UI** ([Textual](https://textual.textualize.io/)) with streamed Markdown answers and saved conversation history

## ⚙️ How it works

```
                 ┌──────────────┐     ┌─────────────┐
 docs folder ──▶ │   chunking   │ ──▶ │ BM25 index  │   (keywords, on disk)
                 └──────────────┘     └──────┬──────┘
                                             │ top-k chunks
 question ───────────── tokenize ───────────▶│
                                             ▼
                                      ┌─────────────┐
                                      │ Ollama LLM  │ ──▶ answer
                                      └─────────────┘
```

1. **Index**: files are split into chunks, tokenized (with stopwords removed)
   and stored as a BM25 index in `data/processed/`.
2. **Retrieve**: your question is tokenized the same way; the top-k chunks
   that share the most relevant keywords are selected.
3. **Generate**: those chunks are sent as context to a local Ollama model,
   which answers **only** from the sources (or says *"Not found in the sources."*).

## 🚀 Quick start

### 1. Install

Requirements: Python ≥ 3.10, [`uv`](https://docs.astral.sh/uv/) and [Ollama](https://ollama.com).

```bash
git clone git@github.com:ynsz-66/RAG.git rag && cd rag
make install        # uv sync
```

### 2. Start Ollama

```bash
ollama serve                # API on http://localhost:11434
ollama pull qwen3:8b        # ~5 GB, good quality/RAM trade-off
```

### 3. Configure *(optional)*

```bash
cp .env.example .env
```

| Variable       | Default                  | Description                                         |
|----------------|--------------------------|-----------------------------------------------------|
| `OLLAMA_HOST`  | `http://localhost:11434` | Ollama server URL                                   |
| `OLLAMA_MODEL` | `qwen3:8b`               | Any model installed locally                         |
| `BM25_LANG`    | `fr`                     | Stopwords language: set `en` for an English corpus  |

### 4. Run

```bash
make app
```

In the UI, select the folder to index, then ask your questions.

## 🛠️ Commands

| Command            | Description                                             |
|--------------------|---------------------------------------------------------|
| `make install`     | Install dependencies (`uv sync`)                        |
| `make app`         | Launch the Textual interface                            |
| `make lint`        | Run flake8 + mypy                                       |
| `make lint-strict` | Strict lint                                             |
| `make clean`       | Remove venv, caches and `data/processed/`               |

## 🧱 Stack

[`bm25s`](https://github.com/xhluca/bm25s) · `httpx` (→ Ollama) · `python-dotenv` · `pypdf` · `pydantic` · `textual`

## 📄 License

See [LICENSE](LICENSE).
