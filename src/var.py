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
TITLE_SYSTEM = (
    "Summarize the user's prompt as a title of 3 to 4 words maximum. "
    "Generalize and keep only the keywords. "
    "Always answer in the same language as the user's prompt. "
    "Reply with the title only, without quotes or final punctuation."
)
STOPWORDS_EN_FR = STOPWORDS_EN + STOPWORDS_FRENCH
# lowercased: PyStemmer and Qdrant both expect e.g. "english"
STEMMER_LANG = os.environ.get("BM25_STEMMER_LANG", "english").lower()
STEMMER = Stemmer.Stemmer(STEMMER_LANG)
INDEX_DIR = os.environ.get("BM25_INDEX_DIR", "data/processed/bm25_index/")
CHUNKS_DIR = os.environ.get("CHUNKS_DIR", "data/processed/chunks/")
CHUNKS_PATH = os.path.join(CHUNKS_DIR, "chunks.json")
EMBED_HOST = os.environ.get("EMBED_HOST", "http://localhost:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "BGE-M3")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "chunks")
QDRANT_HYBRID_COLLECTION = os.environ.get(
    "QDRANT_HYBRID_COLLECTION", "chunks_hybrid"
)
RERANK_CANDIDATES = int(os.environ.get("RERANK_CANDIDATES", 50))
RERANKER_MODEL = os.environ.get("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
REWRITE_SYSTEM = (
    "Rewrite the user's question into a short search query for a technical "
    "documentation and code corpus (vLLM). Keep exact identifiers, function, "
    "class and file names; add likely technical keywords and synonyms. "
    "Answer with the query only, in English, on one line."
)
