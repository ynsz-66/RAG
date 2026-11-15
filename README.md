<div align="center">

# 🔎 RAG — Ask Questions about Your Docs

**A 100% local RAG: BM25 or vector search + an Ollama LLM.**
Point it at a folder, ask a question, get an answer grounded in your files.

![Python](https://img.shields.io/badge/python-≥3.10-3776AB?logo=python&logoColor=white)
![Ollama](https://img.shields.io/badge/LLM-Ollama-000000?logo=ollama&logoColor=white)
![Retrieval](https://img.shields.io/badge/retrieval-BM25%20%7C%20embeddings-orange)
![Qdrant](https://img.shields.io/badge/vector%20DB-Qdrant-DC244C)
![Local](https://img.shields.io/badge/100%25-local-success)
![License](https://img.shields.io/github/license/ynsz-66/RAG)

</div>

---

## ✨ Features

- 🔒 **Fully local**: no API key, nothing sent to the cloud
- 🔀 **Pluggable retrieval**: BM25 keywords or semantic embeddings, selected with `--method`
- 📂 **Multi-format**: `.md`, `.py`, `.pdf`, `.txt`
- ✂️ **Format-aware chunking**: Markdown by headings, Python by AST, PDF by page, text by lines
- 🌍 **Answers in your language**, even when the sources are in another
- 📊 **Measured**: Recall@k evaluation on a public benchmark ([Evaluation](#-evaluation))

## ⚙️ How it works

```
                                    ┌─ bm25 ──────▶ BM25 index (files on disk)
 docs folder ──▶ chunking ──▶ index ┤
                                    ├─ embedding ─▶ Ollama embeddings ──▶ Qdrant
                                    └─ hybrid ────▶ both  (🚧 planned)
                                                         │
 question ───────────────── same method ────────────────▶│ top-k chunks
                                                         ▼
                                                   Ollama LLM ──▶ answer
```

1. **Index**: files are split into chunks, then indexed with the chosen method.
2. **Retrieve**: the question goes through the same method; the top-k chunks are selected.
3. **Generate**: the best chunks are sent as context to a local Ollama model,
   which answers **only** from the sources (or says *"Not found in the sources."*).

## 🔀 Retrieval methods

| `--method`  | How it ranks chunks                                   | Storage                         | Needs           |
|-------------|-------------------------------------------------------|---------------------------------|-----------------|
| `bm25` *(default)* | Shared keywords (stopwords removed, stemmed)   | `data/processed/` (files)       | nothing         |
| `embedding` | Cosine similarity of [BGE-M3](https://ollama.com/library/bge-m3) vectors | [Qdrant](https://qdrant.tech) collection | Ollama + Qdrant |
| `hybrid`    | 🚧 *Planned*: fuse the BM25 and embedding rankings     | both                            | Ollama + Qdrant |

- **BM25** is fast and exact on names, flags and identifiers (`/v1/load_lora_adapter`, `--max-model-len`).
- **Embeddings** match meaning, so they find a chunk even when it uses other words than the question.

Each method has its own index: run `index` once per method you want to use.

## 🚀 Quick start

### 1. Install

Requirements: Python ≥ 3.10, [`uv`](https://docs.astral.sh/uv/), [Ollama](https://ollama.com),
and [Docker](https://docs.docker.com/get-docker/) for the `embedding` method.

```bash
git clone git@github.com:ynsz-66/RAG.git rag && cd rag
make install                # uv sync
ollama pull qwen3:0.6b        # answer model, ~522 MB
ollama pull bge-m3          # embedding model (only for --method embedding)
```

### 2. Start the services

```bash
make up      # starts `ollama serve` + the Qdrant container (docker compose)
make down    # stops Qdrant
```

`bm25` only needs Ollama for `answer`; `retrieve` works with no service running.

### 3. Configure *(optional)*

```bash
cp .env.example .env
```

| Variable            | Default                  | Description                                            |
|---------------------|--------------------------|--------------------------------------------------------|
| `OLLAMA_HOST`       | `http://localhost:11434` | Ollama server URL                                      |
| `OLLAMA_MODEL`      | `qwen3:0.6b`               | Answer model, any model installed locally              |
| `BM25_STEMMER_LANG` | `french`                 | Stemmer language: the majority language of your corpus |
| `EMBED_HOST`        | `http://localhost:11434` | Ollama server used for embeddings                      |
| `EMBED_MODEL`       | `BGE-M3`                 | Embedding model                                        |
| `QDRANT_URL`        | `http://localhost:6333`  | Qdrant server URL                                      |
| `QDRANT_COLLECTION` | `chunks`                 | Qdrant collection holding the chunks                   |

BM25 applies **one** stemmer to the whole corpus: if 90% of your documents are French, use `french`;
if they are mostly English, use `english`. Any [Snowball](https://snowballstem.org/) language works.
Re-run the indexing after changing it (or after changing `EMBED_MODEL`).

### 4. Run

```bash
make index    [RAW=path/] [METHOD=bm25|embedding]          # chunk + index
make retrieve Q="your question" [K=10] [METHOD=...]       # print the top-K sources
make answer   Q="your question" [K=10] [KEEP=3] [METHOD=...]  # stream an answer from the top KEEP sources
```

Each target wraps `uv run python -m src <index|retrieve|answer> ... --method <method>`.
Index once (and again after changing the corpus), then query as many times as you want.

## 🗄️ Qdrant dashboard

With `make up` running, open **<http://localhost:6333/dashboard>**.
After `make index METHOD=embedding`, the `chunks` collection holds one point per chunk:
its BGE-M3 vector plus the chunk (file path, character range, content) as payload.
Open the collection and its **Graph** tab to explore neighbouring chunks:

<div align="center">
  <img src="assets/qdrant-dashboard.png" alt="Qdrant dashboard: graph of the chunks collection" width="800">
</div>

The data lives in `qdrant_storage/` (gitignored); `make fclean` deletes it.

## 🛠️ Commands

| Command            | Description                                                |
|--------------------|------------------------------------------------------------|
| `make help`        | List all targets and their variables                       |
| `make install`     | Install dependencies (`uv sync`)                           |
| `make up` / `down` | Start Ollama + Qdrant / stop Qdrant                        |
| `make index`       | Index `RAW` with `METHOD`                                  |
| `make retrieve`    | Top-`K` chunks for `Q`                                     |
| `make answer`      | LLM answer for `Q`                                         |
| `make fetch-vllm`  | Download the vLLM v0.10.1 sources used by the evaluation   |
| `make lint`        | Run flake8 + mypy                                          |
| `make clean`       | Stop Qdrant, remove venv and caches                        |
| `make fclean`      | `clean` + delete the Qdrant storage and the BM25 index     |

## 📊 Evaluation

Retrieval quality is measured on a public benchmark of questions about the
[vLLM](https://github.com/vllm-project/vllm) **v0.10.1** codebase and docs.

```
datasets_public/public/
├── AnsweredQuestions/     # questions + ground-truth sources + reference answer
│   ├── dataset_docs_public.json   # questions about the Markdown docs
│   └── dataset_code_public.json   # questions about the Python code
└── UnansweredQuestions/   # same questions, without ground truth
```

Each ground-truth source is a file path and a character range, e.g.
`data/raw/vllm-0.10.1/docs/features/lora.md [4695:6098]`, so the corpus must be
**exactly** vLLM v0.10.1, extracted at that path.

### Run it

```bash
make fetch-vllm      # downloads vLLM v0.10.1 into data/raw/vllm-0.10.1/
make index           # RAW defaults to data/raw/vllm-0.10.1/

DS=datasets_public/public/AnsweredQuestions/dataset_docs_public.json

# 1. Retrieve the top-K sources for every question
make search-dataset DATASET_PATH=$DS SAVE_DIRECTORY=results/search

# 2. Score them against the ground truth
make evaluate STUDENT_ANSWER_PATH=results/search/dataset_docs_public.json DATASET_PATH=$DS

# 3. (optional) Generate an LLM answer per question from its top KEEP sources (needs Ollama)
make answer-dataset STUDENT_SEARCH_RESULTS_PATH=results/search/dataset_docs_public.json \
                    SAVE_DIRECTORY=results/answers
```

| Target           | Input                             | Output (same file name, in `SAVE_DIRECTORY`)   |
|------------------|-----------------------------------|------------------------------------------------|
| `search-dataset` | a dataset JSON                    | top-`K` retrieved sources per question         |
| `evaluate`       | `search-dataset` output + dataset | Recall@1, @3, @5, @`K` printed to the terminal |
| `answer-dataset` | `search-dataset` output           | the same results, plus an `answer` per question |

All targets accept `K`, `KEEP` and `METHOD`. To compare methods, index and search once per method
(e.g. `METHOD=embedding SAVE_DIRECTORY=results/embedding`).
Use a different `SAVE_DIRECTORY` per step or method: outputs keep the input's file name and overwrite each other.

> [!NOTE]
> `evaluate` only works with `AnsweredQuestions/` datasets, since the unanswered ones have no ground truth.

### Metric

A ground-truth source counts as **found** when a retrieved chunk from the same file
overlaps at least **5 %** of its character range.
**Recall@k** is the share of ground-truth sources found in the top-k chunks, averaged over all questions.

## 🧱 Stack

[`bm25s`](https://github.com/xhluca/bm25s) · [Qdrant](https://qdrant.tech) + `qdrant-client` ·
Ollama (`httpx`) · `pydantic` · `pypdf` · `fire` · `python-dotenv`

## 📄 License

See [LICENSE](LICENSE).
