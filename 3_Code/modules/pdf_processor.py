"""PDF Processing Module for AUTOSAR HLD documents using PyMuPDF (fitz)."""
from pathlib import Path
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF
import re

from config.settings import CHUNK_SIZE, CHUNK_OVERLAP
from models.schemas import DocumentChunk
from utils.helpers import clean_text

class PDFProcessor:
    """Extracts text, headings, tables, and creates structured chunks from AUTOSAR HLD PDFs."""

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_pdf(self, filepath: str, doc_id: str, filename: str) -> Tuple[List[DocumentChunk], Dict[str, Any]]:
        """
        Extracts structured page-wise content, detects headings/tables, and chunks text.
        Returns (chunks, metadata_dict).
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found at: {filepath}")

        doc = fitz.open(str(path))
        total_pages = len(doc)
        total_text_length = 0
        pages_content = []

        current_heading = "System Overview"

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]

            # 1. Extract text and detect headings based on font size / block structure
            blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_SEARCH).get("blocks", [])
            page_text_pieces = []

            for block in blocks:
                if block.get("type") == 0:  # Text block
                    block_text = ""
                    max_size = 0.0
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            txt = span.get("text", "")
                            block_text += txt + " "
                            max_size = max(max_size, span.get("size", 10.0))

                    block_text = clean_text(block_text)
                    if not block_text:
                        continue

                    # Heuristic for section heading: Larger font or explicit Section/Chapter regex
                    if max_size >= 13.0 or re.match(r"^(Section|\d+\.|\d+\.\d+|Chapter)\s+[A-Z]", block_text):
                        if len(block_text) < 100:  # headings are generally short
                            current_heading = block_text

                    page_text_pieces.append(block_text)

            # 2. Extract tables where supported (fitz page.find_tables())
            table_texts = []
            try:
                tables = page.find_tables()
                for table in tables:
                    df = table.extract()
                    if df:
                        # Format table into readable markdown text
                        row_strs = [" | ".join(str(cell or "").strip() for cell in row) for row in df if any(row)]
                        if row_strs:
                            table_md = "\n[TABLE DATA]\n" + "\n".join(row_strs) + "\n[/TABLE DATA]\n"
                            table_texts.append(table_md)
            except Exception:
                # If table extraction is not supported in this PyMuPDF version or fails, fallback safely
                pass

            combined_page_text = clean_text("\n\n".join(page_text_pieces + table_texts))
            total_text_length += len(combined_page_text)

            pages_content.append({
                "page_num": page_num,
                "heading": current_heading,
                "text": combined_page_text
            })

        doc.close()

        # Check if PDF contains little or no extractable text (scanned or image-only)
        avg_chars_per_page = total_text_length / max(1, total_pages)
        is_scanned_or_empty = (total_text_length < 100) or (avg_chars_per_page < 30)

        # 3. Create context-aware overlapping chunks
        chunks: List[DocumentChunk] = []
        chunk_idx = 0

        for page_data in pages_content:
            p_num = page_data["page_num"]
            heading = page_data["heading"]
            p_text = page_data["text"]

            if not p_text:
                continue

            # Split into paragraphs/sentences preserving signal definitions
            paragraphs = p_text.split("\n\n")
            current_chunk_words: List[str] = []
            current_heading_ref = heading

            for para in paragraphs:
                para_words = para.split()
                if not para_words:
                    continue

                if len(current_chunk_words) + len(para_words) > self.chunk_size:
                    # Flush chunk
                    chunk_text = " ".join(current_chunk_words)
                    chunk_id = f"{doc_id}_p{p_num}_c{chunk_idx}"
                    chunks.append(DocumentChunk(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        filename=filename,
                        page_number=p_num,
                        section_heading=current_heading_ref,
                        text=chunk_text,
                        char_length=len(chunk_text)
                    ))
                    chunk_idx += 1

                    # Retain overlap from end of current chunk
                    if self.chunk_overlap > 0 and len(current_chunk_words) > self.chunk_overlap:
                        current_chunk_words = current_chunk_words[-self.chunk_overlap:] + para_words
                    else:
                        current_chunk_words = para_words
                else:
                    current_chunk_words.extend(para_words)

            # Flush any remaining words on the page
            if current_chunk_words:
                chunk_text = " ".join(current_chunk_words)
                chunk_id = f"{doc_id}_p{p_num}_c{chunk_idx}"
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    filename=filename,
                    page_number=p_num,
                    section_heading=current_heading_ref,
                    text=chunk_text,
                    char_length=len(chunk_text)
                ))
                chunk_idx += 1

        metadata_dict = {
            "total_pages": total_pages,
            "total_text_length": total_text_length,
            "is_scanned_or_empty": is_scanned_or_empty,
            "chunk_count": len(chunks)
        }

        return chunks, metadata_dict
