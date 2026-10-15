# Model Configuration & Architecture Specification

## 1. Local LLM Architecture

- **Model Engine**: Ollama (Local Daemon)
- **Primary LLM**: `qwen3.5:9b` (Qwen 3.5 9-Billion Parameter Model) / `qwen2.5:7b` compatible
- **Architecture**: Causal Decoder-Only Transformer with Grouped-Query Attention (GQA)
- **Quantization**: 4-bit / 8-bit Q4_K_M (Ollama default)
- **Context Window**: 32,768 tokens (configured for 8,192 operational window in RAG)
- **Local API Endpoint**: `http://localhost:11434/api/generate` and `http://localhost:11434/api/chat`
- **Inference Mode**: Fully offline, on-premise execution (zero egress for automotive IP protection)

## 2. Embedding Model

- **Model Identifier**: `BAAI/bge-small-en-v1.5` (Local HuggingFace / Sentence-Transformers)
- **Alternative/Fallback**: `nomic-embed-text` (via Ollama local embed endpoint)
- **Dimension**: 384 dimensions (for BGE-small-en-v1.5) / 768 dimensions (for nomic-embed-text)
- **Max Sequence Length**: 512 tokens
- **Distance Metric**: Cosine Similarity / Inner Product
- **Normalization**: L2-normalized embeddings for fast inner product search

## 3. Vector Database Specification

- **Engine**: ChromaDB (`chromadb.PersistentClient`)
- **Persistence Path**: `3_Code/data/chroma_db/`
- **Collection Name**: `autosar_hld_knowledge_base`
- **Metadata Indexing Fields**:
  - `doc_id`: Unique document SHA-256 hash
  - `filename`: Original PDF filename
  - `page_num`: 1-indexed document page
  - `section_heading`: Hierarchical section header extracted from PDF
  - `chunk_id`: Deterministic chunk identifier (`doc_id_p{page}_c{index}`)
  - `token_count`: Estimated chunk token length

## 4. Hardware Allocation & Resource Footprint

| Component | VRAM / RAM Target | Compute Target |
|---|---|---|
| Ollama Qwen3.5:9b | ~6.5 GB VRAM (GPU) or 8 GB RAM (CPU) | CUDA / AVX2 |
| BGE-small-en-v1.5 | ~200 MB VRAM or system RAM | CPU / PyTorch |
| ChromaDB | < 150 MB RAM | In-process embedded SQLite + HNSW |
| Streamlit UI | ~120 MB RAM | Python process |
