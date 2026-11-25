import os
from bm25s.stopwords import STOPWORDS_EN, STOPWORDS_FRENCH  # type: ignore
import Stemmer
from dotenv import load_dotenv

load_dotenv()

SYSTEM = (
    "You answer questions using ONLY the provided sources. "
    "Rules: "
    "(1) Always answer in the same language as the user's prompt, "
    "regardless of the language of the sources. "
    "(2) If a source is in another language, translate the explanation, "
    "but keep technical/precise terms (API names, code identifiers, "
    "established jargon, proper nouns) in their original form. "
    "(3) Be self-contained. "
    "(4) If the sources don't contain the answer, say "
    "'Not found in the sources.' (in the language of the question). "
    "(5) Don't cite sources used."
)
MAX_TOKENS = 1024


def answer_prompt(query: str, contents: list[str]) -> str:
    """User message for the answer LLM: sources, then the question."""
    context = "\n\n".join(contents)
    return f"Sources:\n{context}\n\nQuestion: {query}"


STOPWORDS_EN_FR = STOPWORDS_EN + STOPWORDS_FRENCH
STEMMER_LANG = os.environ.get("BM25_STEMMER_LANG", "english").lower()
STEMMER = Stemmer.Stemmer(STEMMER_LANG)
INDEX_DIR = os.environ.get("BM25_INDEX_DIR", "data/processed/bm25_index/")
CHUNKS_DIR = os.environ.get("CHUNKS_DIR", "data/processed/chunks/")
CHUNKS_PATH = os.path.join(CHUNKS_DIR, "chunks.json")
# --llm ollama: Ollama (chat, embeddings) + fastembed (reranker, local)
OLLAMA_LLM_URL = os.environ.get("OLLAMA_LLM_URL", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.environ.get("OLLAMA_LLM_MODEL", "qwen3:0.6b")
OLLAMA_EMBED_URL = os.environ.get(
    "OLLAMA_EMBED_URL", "http://localhost:11434"
)
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "BGE-M3")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "chunks")
QDRANT_HYBRID_COLLECTION = os.environ.get(
    "QDRANT_HYBRID_COLLECTION", "chunks_hybrid"
)
RERANK_CANDIDATES = int(os.environ.get("RERANK_CANDIDATES", 50))
FASTEMBED_RERANK_MODEL = os.environ.get(
    "FASTEMBED_RERANK_MODEL", "BAAI/bge-reranker-v2-m3"
)
# --llm vllm (default): OpenAI-compatible vLLM; ollama: Ollama + fastembed
LLM_BACKENDS = ("vllm", "ollama")
VLLM_API_KEY = os.environ.get("VLLM_API_KEY", "EMPTY")
VLLM_LLM_URL = os.environ.get("VLLM_LLM_URL", "http://localhost:8000/v1")
VLLM_LLM_MODEL = os.environ.get("VLLM_LLM_MODEL", "Qwen/Qwen3-8B-AWQ")
VLLM_EMBED_URL = os.environ.get("VLLM_EMBED_URL", "http://localhost:8001/v1")
VLLM_EMBED_MODEL = os.environ.get("VLLM_EMBED_MODEL", "BAAI/bge-m3")
# query-side instruction (e.g. Qwen3-Embedding); empty = raw query
EMBED_QUERY_INSTRUCT = os.environ.get("EMBED_QUERY_INSTRUCT", "")
VLLM_RERANK_URL = os.environ.get("VLLM_RERANK_URL", "http://localhost:8002/v1")
VLLM_RERANK_MODEL = os.environ.get(
    "VLLM_RERANK_MODEL", "BAAI/bge-reranker-v2-m3"
)


def llm_backend() -> str:
    """Current backend, read at call time (``CLI --llm`` sets the env)."""
    backend = os.environ.get("LLM_BACKEND", "vllm").lower()
    if backend not in LLM_BACKENDS:
        raise ValueError(
            f"--llm must be one of {LLM_BACKENDS}, got {backend!r}"
        )
    return backend


# None -> OllamaLLM falls back to OLLAMA_LLM_MODEL
OLLAMA_REWRITE_MODEL = os.environ.get("OLLAMA_REWRITE_MODEL")
REWRITE_KEYWORDS_SYSTEM = (
    "You turn a user question about vLLM (an LLM inference engine) into "
    "search keywords for its documentation and source code.\n"
    "Rules:\n"
    "- Output ONE line of 4 to 8 English keywords, space separated.\n"
    "- Copy exact identifiers unchanged (functions, classes, files, "
    "flags, env vars).\n"
    "- Fix typos, expand abbreviations, add close technical synonyms.\n"
    "- No sentence, no explanation, no quotes, no prefix.\n"
    "Examples:\n"
    "Q: how quantize model fp8 ?\n"
    "fp8 quantization quantize weights activations dtype "
    "quantization_config\n"
    "Q: where is LLM.generate defined\n"
    "LLM.generate class LLM entrypoints llm.py generate method "
    "definition\n"
    "Q: comment changer la taille du kv cache\n"
    "kv cache size gpu_memory_utilization num_gpu_blocks block_size "
    "memory\n"
    "Q: multi gpu serve ??\n"
    "tensor_parallel_size distributed multi-GPU serving "
    "pipeline_parallel_size vllm serve"
)
REWRITE_QUERY_SYSTEM = (
    "You rewrite a vague or sloppy user question about vLLM (an LLM "
    "inference engine) into one clear technical question for semantic "
    "search over its documentation and source code.\n"
    "Rules:\n"
    "- Output ONE English sentence, at most 30 words.\n"
    "- Use precise vLLM vocabulary; keep exact identifiers unchanged.\n"
    "- Do NOT answer the question. No explanation, no quotes, no prefix.\n"
    "Examples:\n"
    "Q: how quantize model fp8 ?\n"
    "How do I enable FP8 quantization of model weights and activations "
    "in vLLM?\n"
    "Q: where is LLM.generate defined\n"
    "Where is the LLM.generate method of the LLM class defined in the "
    "vLLM source code?\n"
    "Q: comment changer la taille du kv cache\n"
    "How do I configure the KV cache size and GPU memory utilization in "
    "vLLM?\n"
    "Q: multi gpu serve ??\n"
    "How do I serve a model across multiple GPUs with tensor or pipeline "
    "parallelism in vLLM?"
)
