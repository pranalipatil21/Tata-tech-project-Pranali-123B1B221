"""Unit tests for PDF Processor module."""
import pytest
from pathlib import Path
from modules.pdf_processor import PDFProcessor
from sample_data.generate_sample_hld import generate_pdf

@pytest.fixture(scope="module")
def sample_pdf_path(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("data")
    pdf_path = tmp_dir / "test_sample.pdf"
    generate_pdf(str(pdf_path))
    return str(pdf_path)

def test_pdf_processing_and_chunking(sample_pdf_path):
    proc = PDFProcessor(chunk_size=300, chunk_overlap=30)
    chunks, meta = proc.process_pdf(sample_pdf_path, doc_id="test_doc_1", filename="test_sample.pdf")

    assert meta["total_pages"] >= 10
    assert meta["is_scanned_or_empty"] is False
    assert len(chunks) > 0

    first_chunk = chunks[0]
    assert first_chunk.doc_id == "test_doc_1"
    assert first_chunk.filename == "test_sample.pdf"
    assert first_chunk.page_number == 1
    assert len(first_chunk.text) > 0

def test_empty_pdf_detection(tmp_path):
    empty_pdf = tmp_path / "empty.pdf"
    # Create blank pdf
    import fitz
    doc = fitz.open()
    doc.new_page()
    doc.save(str(empty_pdf))
    doc.close()

    proc = PDFProcessor()
    chunks, meta = proc.process_pdf(str(empty_pdf), doc_id="empty_doc", filename="empty.pdf")
    assert meta["is_scanned_or_empty"] is True
    assert len(chunks) == 0
