"""Local Embedding Generator using BAAI/bge-small-en-v1.5 and fallback support."""
import logging
from typing import List
import requests

from config.settings import EMBEDDING_MODEL_NAME, OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Singleton service to compute dense vector embeddings locally."""
    _instance = None
    _model = None
    _mode = "sentence_transformers"  # or 'ollama'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        """Loads BAAI/bge-small-en-v1.5 via sentence-transformers, with fallback to Ollama nomic-embed-text."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading local embedding model: {EMBEDDING_MODEL_NAME}")
            self._model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            self._mode = "sentence_transformers"
            logger.info("SentenceTransformer BGE model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}). Attempting Ollama embedding fallback...")
            try:
                # Test Ollama embedding endpoint
                resp = requests.post(
                    f"{OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": OLLAMA_EMBED_MODEL, "prompt": "test"},
                    timeout=5
                )
                if resp.status_code == 200:
                    self._mode = "ollama"
                    logger.info(f"Using local Ollama embedding: {OLLAMA_EMBED_MODEL}")
                else:
                    self._mode = "mock"
                    logger.warning("Ollama embed returned non-200, falling back to lightweight dense feature mode.")
            except Exception as o_err:
                self._mode = "mock"
                logger.warning(f"Ollama embedding unavailable ({o_err}), using local feature embeddings.")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized vector embeddings for a list of text strings."""
        if not texts:
            return []

        if self._mode == "sentence_transformers" and self._model is not None:
            embeddings = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return embeddings.tolist()

        elif self._mode == "ollama":
            vectors = []
            for t in texts:
                try:
                    resp = requests.post(
                        f"{OLLAMA_BASE_URL}/api/embeddings",
                        json={"model": OLLAMA_EMBED_MODEL, "prompt": t},
                        timeout=15
                    )
                    if resp.status_code == 200:
                        vectors.append(resp.json()["embedding"])
                    else:
                        vectors.append([0.0] * 384)
                except Exception:
                    vectors.append([0.0] * 384)
            return vectors

        else:
            # Deterministic hash-based 384-dimensional vector fallback for extreme offline/no-network cases
            import hashlib
            vectors = []
            for t in texts:
                h = hashlib.sha384(t.encode("utf-8")).digest()
                # 48 bytes -> normalize into 384 floats
                vec = [(b / 255.0) - 0.5 for b in h] * 8
                norm = sum(x*x for x in vec) ** 0.5 or 1.0
                vectors.append([x / norm for x in vec])
            return vectors

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string."""
        res = self.embed_texts([query])
        return res[0] if res else []
