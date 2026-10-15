"""Persistent ChromaDB vector store integration for AUTOSAR HLD chunks with automatic dimension healing."""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings

from config.settings import CHROMA_DIR, CHROMA_COLLECTION_NAME, SIMILARITY_TOP_K
from models.schemas import DocumentChunk
from modules.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

class VectorStore:
    """Manages persistent ChromaDB vector storage and semantic querying with automatic dimension healing."""

    def __init__(self, persist_dir: Path = CHROMA_DIR, collection_name: str = CHROMA_COLLECTION_NAME):
        self.persist_dir = persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embed_service = EmbeddingService()

        # Initialize persistent Chroma client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        self._ensure_compatible_collection()

    @property
    def collection(self):
        """Always resolves the current active collection handle to avoid stale UUID errors."""
        try:
            return self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "AUTOSAR HLD Chunks Knowledge Base"}
            )
        except Exception:
            return self.client.get_collection(self.collection_name)

    def _ensure_compatible_collection(self):
        """Verifies Chroma collection dimension and recreates if incompatible."""
        probe_vec = self.embed_service.embed_query("dimension_check")
        expected_dim = len(probe_vec) if probe_vec else 384

        try:
            coll = self.collection
            if coll.count() > 0:
                coll.query(query_embeddings=[probe_vec], n_results=1)
        except Exception as e:
            logger.warning(f"ChromaDB collection reset triggered due to incompatibility or stale ID ({e}).")
            try:
                self.client.delete_collection(name=self.collection_name)
            except Exception:
                pass
            self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "AUTOSAR HLD Chunks Knowledge Base", "dimension": expected_dim}
            )

    def add_chunks(self, chunks: List[DocumentChunk]):
        """Embeds and upserts document chunks into ChromaDB."""
        if not chunks:
            return

        texts = [c.text for c in chunks]
        embeddings = self.embed_service.embed_texts(texts)
        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {
                "doc_id": c.doc_id,
                "filename": c.filename,
                "page_number": c.page_number,
                "section_heading": c.section_heading or "General",
                "char_length": c.char_length
            }
            for c in chunks
        ]

        batch_size = 200
        for i in range(0, len(chunks), batch_size):
            end_idx = i + batch_size
            try:
                self.collection.upsert(
                    ids=ids[i:end_idx],
                    embeddings=embeddings[i:end_idx],
                    documents=texts[i:end_idx],
                    metadatas=metadatas[i:end_idx]
                )
            except Exception as e:
                err_msg = str(e).lower()
                if "dimension" in err_msg or "does not exist" in err_msg:
                    logger.warning(f"Chroma upsert error ({e}). Resetting collection and retrying...")
                    self._ensure_compatible_collection()
                    self.collection.upsert(
                        ids=ids[i:end_idx],
                        embeddings=embeddings[i:end_idx],
                        documents=texts[i:end_idx],
                        metadatas=metadatas[i:end_idx]
                    )
                else:
                    raise e
        logger.info(f"Upserted {len(chunks)} chunks into ChromaDB collection '{self.collection_name}'.")

    def query(self, query_text: str, top_k: int = SIMILARITY_TOP_K, doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Executes semantic search against ChromaDB.
        Returns list of matched chunks with metadata, text, and cosine distance score.
        """
        query_embedding = self.embed_service.embed_query(query_text)
        where_filter = {"doc_id": doc_id} if doc_id and doc_id != "all" else None

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            err_msg = str(e).lower()
            if "dimension" in err_msg or "does not exist" in err_msg:
                logger.warning(f"Chroma query error ({e}). Re-initializing collection.")
                self._ensure_compatible_collection()
                return []
            raise e

        matches = []
        if results and "ids" in results and results["ids"] and results["ids"][0]:
            count = len(results["ids"][0])
            for i in range(count):
                chunk_id = results["ids"][0][i]
                doc_text = results["documents"][0][i] if results["documents"] else ""
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0

                matches.append({
                    "chunk_id": chunk_id,
                    "text": doc_text,
                    "metadata": meta,
                    "distance": distance
                })

        return matches

    def get_document_chunks(self, doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all chunks for a specific document or all documents without distance filtering.
        Ensures 100% architectural entity recall across all document pages.
        """
        where_filter = {"doc_id": doc_id} if doc_id and doc_id != "all" else None
        try:
            results = self.collection.get(
                where=where_filter,
                include=["documents", "metadatas"]
            )
            matches = []
            if results and "ids" in results and results["ids"]:
                for i in range(len(results["ids"])):
                    chunk_id = results["ids"][i]
                    doc_text = results["documents"][i] if results.get("documents") else ""
                    meta = results["metadatas"][i] if results.get("metadatas") else {}
                    matches.append({
                        "chunk_id": chunk_id,
                        "text": doc_text,
                        "metadata": meta,
                        "distance": 0.0
                    })
                # Sort chunks chronologically by page number
                matches.sort(key=lambda x: x.get("metadata", {}).get("page_number", 0))
            return matches
        except Exception as e:
            logger.warning(f"Error retrieving document chunks: {e}")
            return []

    def delete_document_chunks(self, doc_id: str):
        """Deletes all chunks belonging to a specific document."""
        try:
            self.collection.delete(where={"doc_id": doc_id})
            logger.info(f"Removed chunks for doc_id {doc_id} from vector store.")
        except Exception as e:
            logger.warning(f"Error removing chunks for doc_id {doc_id}: {e}")

    def get_chunk_count(self) -> int:
        """Returns total number of chunks indexed in the collection."""
        try:
            return self.collection.count()
        except Exception:
            return 0
