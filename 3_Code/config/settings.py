"""Configuration settings for the AUTOSAR HLD Analysis Assistant."""
from pathlib import Path
import os

# Base Directories
CODE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = CODE_DIR.parent
DATA_DIR = CODE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma_db"
REPORT_DIR = DATA_DIR / "reports"
METADATA_FILE = DATA_DIR / "document_metadata.json"

for d in [DATA_DIR, UPLOAD_DIR, CHROMA_DIR, REPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# LLM Configuration (Ollama)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_LLM_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
FALLBACK_LLM_MODELS = ["qwen2.5:3b", "qwen2.5-coder:3b", "qwen3.5:9b", "qwen2.5:7b", "llama3.1:8b", "mistral:latest"]

# Embedding Configuration
# Primary: BAAI/bge-small-en-v1.5
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
OLLAMA_EMBED_MODEL = "nomic-embed-text:latest"

# ChromaDB Configuration
CHROMA_COLLECTION_NAME = "autosar_hld_kb"
CHUNK_SIZE = 500  # Words / token approximation
CHUNK_OVERLAP = 60
SIMILARITY_TOP_K = 5
SIMILARITY_CUTOFF = 0.85  # Max cosine distance for valid relevance

# UI Configuration
PAGE_TITLE = "AUTOSAR HLD Analysis Assistant"
PAGE_ICON = "🚗"
LAYOUT = "wide"
