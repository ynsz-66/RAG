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
| `BM25_STEMMER_LANG` | `french`            | Stemmer language: the majority language of your corpus |

BM25 applies **one** stemmer to the whole corpus, so set `BM25_STEMMER_LANG` to the language most of
your documents are written in: if 90% of the corpus is French, use `french`; if it is mostly English,
use `english`. Any [Snowball](https://snowballstem.org/) language works (`german`, `spanish`, …).
Re-run the indexing after changing it.

### 4. Run

```bash
uv run python -m src index [raw_path] [--max-chunk-size 2000]   # chunk + index (default: data/raw/)
uv run python -m src retrieve "your question" [-k 10]          # print the top-k sources
uv run python -m src answer "your question" [-k 10] [--keep 3]  # stream an answer from the top sources
```

All three commands take `--method bm25|embedding|hybrid` (default `bm25`; `embedding` and `hybrid` are not implemented yet).

Index once (and again after changing the corpus), then run `retrieve` or `answer` as many times as you want.

## 🛠️ Commands

| Command            | Description                                             |
|--------------------|---------------------------------------------------------|
| `make install`     | Install dependencies (`uv sync`)                        |
| `make app`         | Launch the Textual interface                            |
| `make lint`        | Run flake8 + mypy                                       |
| `make clean`       | Remove venv, caches and `data/processed/`               |
| `make fetch-vllm`  | Download the vLLM v0.10.1 sources used by the evaluation |

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

| Target           | Input                             | Output (same file name, in `SAVE_DIRECTORY`) |
|------------------|-----------------------------------|----------------------------------------------|
| `search-dataset` | a dataset JSON                    | top-`K` retrieved sources per question       |
| `evaluate`       | `search-dataset` output + dataset | Recall@1, @3, @5, @`K` printed to the terminal |
| `answer-dataset` | `search-dataset` output           | the same results, plus an `answer` per question |

All targets accept `K`, `KEEP` and `METHOD` (`bm25` or `embedding`; `embedding` needs `make up` for Qdrant).
Use a different `SAVE_DIRECTORY` per step or method: outputs keep the input's file name and overwrite each other.

> [!NOTE]
> `evaluate` only works with `AnsweredQuestions/` datasets, since the unanswered ones have no ground truth.

### Metric

A ground-truth source counts as **found** when a retrieved chunk from the same file
overlaps at least **5 %** of its character range.
**Recall@k** is the share of ground-truth sources found in the top-k chunks, averaged over all questions.

## 🧱 Stack

[`bm25s`](https://github.com/xhluca/bm25s) · `httpx` (→ Ollama) · `python-dotenv` · `pypdf` · `pydantic` · `textual`

## 📄 License

See [LICENSE](LICENSE).
