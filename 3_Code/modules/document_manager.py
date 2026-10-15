"""Document Manager for managing uploaded AUTOSAR HLD files, metadata, and deduplication."""
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from config.settings import UPLOAD_DIR, METADATA_FILE
from models.schemas import DocumentMetadata
from utils.helpers import compute_file_hash, sanitize_filename, get_iso_timestamp

class DocumentManager:
    """Handles PDF file storage, SHA-256 deduplication, and JSON metadata catalog."""

    def __init__(self, metadata_path: Path = METADATA_FILE, upload_dir: Path = UPLOAD_DIR):
        self.metadata_path = metadata_path
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_metadata_file()

    def _ensure_metadata_file(self):
        if not self.metadata_path.exists():
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)

    def load_all_metadata(self) -> Dict[str, DocumentMetadata]:
        """Load all document metadata from disk."""
        self._ensure_metadata_file()
        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {doc_id: DocumentMetadata(**meta) for doc_id, meta in data.items()}
        except Exception:
            return {}

    def save_all_metadata(self, catalog: Dict[str, DocumentMetadata]):
        """Persist metadata catalog to disk."""
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            serializable = {doc_id: meta.model_dump() for doc_id, meta in catalog.items()}
            json.dump(serializable, f, indent=2)

    def find_by_hash(self, file_hash: str) -> Optional[DocumentMetadata]:
        """Check if a file with this hash was already processed."""
        catalog = self.load_all_metadata()
        for meta in catalog.values():
            if meta.file_hash == file_hash:
                return meta
        return None

    def save_uploaded_file(self, filename: str, file_bytes: bytes) -> tuple[DocumentMetadata, bool]:
        """
        Saves uploaded file bytes to disk after deduplication check.
        Returns (DocumentMetadata, is_new).
        """
        file_hash = compute_file_hash(file_bytes)
        existing = self.find_by_hash(file_hash)
        if existing:
            return existing, False

        clean_name = sanitize_filename(filename)
        # Avoid overwriting files with the same name but different content
        target_path = self.upload_dir / clean_name
        base_stem = target_path.stem
        suffix = target_path.suffix
        counter = 1
        while target_path.exists():
            target_path = self.upload_dir / f"{base_stem}_{counter}{suffix}"
            counter += 1

        with open(target_path, "wb") as f:
            f.write(file_bytes)

        file_size_kb = round(len(file_bytes) / 1024.0, 2)
        doc_id = file_hash[:16]

        meta = DocumentMetadata(
            doc_id=doc_id,
            filename=target_path.name,
            filepath=str(target_path.resolve()),
            file_hash=file_hash,
            total_pages=0,
            file_size_kb=file_size_kb,
            upload_timestamp=get_iso_timestamp(),
            chunk_count=0,
            is_scanned_or_empty=False,
            status="uploaded"
        )

        catalog = self.load_all_metadata()
        catalog[doc_id] = meta
        self.save_all_metadata(catalog)
        return meta, True

    def update_document_metadata(self, doc_id: str, **kwargs) -> Optional[DocumentMetadata]:
        """Update fields for a specific document."""
        catalog = self.load_all_metadata()
        if doc_id in catalog:
            meta_dict = catalog[doc_id].model_dump()
            meta_dict.update(kwargs)
            updated = DocumentMetadata(**meta_dict)
            catalog[doc_id] = updated
            self.save_all_metadata(catalog)
            return updated
        return None

    def remove_document(self, doc_id: str) -> bool:
        """Removes a document from disk and metadata index."""
        catalog = self.load_all_metadata()
        if doc_id in catalog:
            meta = catalog[doc_id]
            file_p = Path(meta.filepath)
            if file_p.exists():
                try:
                    file_p.unlink()
                except OSError:
                    pass
            del catalog[doc_id]
            self.save_all_metadata(catalog)
            return True
        return False
