import os
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
LANG = os.environ.get("BM25_LANG", "fr")
RAW_DIR = os.environ.get("RAW_DIR", "data/raw/")
INDEX_DIR = os.environ.get("BM25_INDEX_DIR", "data/processed/bm25_index/")
CHUNKS_DIR = os.environ.get("CHUNKS_DIR", "data/processed/chunks/")
CHUNKS_PATH = os.environ.get(
    "CHUNKS_PATH", os.path.join(CHUNKS_DIR, "chunks.json")
)
