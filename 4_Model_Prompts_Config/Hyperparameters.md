# System Hyperparameters & Runtime Configurations

This document details all tunable hyperparameters used across the PDF chunking, embedding, vector retrieval, and LLM inference pipelines.

---

## 1. Document Ingestion & Chunking Parameters

| Parameter | Default Value | Rationale |
|---|---|---|
| `CHUNK_SIZE` | 500 tokens (~2000 chars) | Balances context richness with embedding granularity; fits AUTOSAR component sections |
| `CHUNK_OVERLAP` | 75 tokens (~300 chars) | Prevents boundary severance across signal tables and port interfaces |
| `MIN_CHUNK_LENGTH` | 40 characters | Discards trivial page headers, footers, and blank pages |
| `PRESERVE_TABLES` | True | Extracts tabular signal definitions intact via PyMuPDF table heuristics |
| `HEADING_DETECTION_THRESHOLD` | 13.0 pt | Identifies AUTOSAR section headers by text block font size |

---

## 2. Embedding & Vector Search Parameters

| Parameter | Default Value | Rationale |
|---|---|---|
| `EMBEDDING_DIMENSION` | 384 (BGE) / 768 (nomic) | Standard normalized dense vector dimension |
| `DISTANCE_METRIC` | Cosine Similarity | Optimal for semantic relevance ranking in dense text retrieval |
| `TOP_K_RETRIEVAL` | 5 chunks | Delivers adequate supporting context (~2500 tokens) without context bloat |
| `SIMILARITY_THRESHOLD` | 0.45 | Cosine distance cutoff to identify weak retrieval or absent facts |
| `REINDEX_ON_MODIFICATION` | True | Uses SHA-256 hash checks to prevent redundant vector operations |

---

## 3. LLM Generation Hyperparameters

| Parameter | Default Value | Rationale |
|---|---|---|
| `TEMPERATURE` | 0.1 | Low temperature enforces strict factual adherence and minimal hallucination |
| `TOP_P` | 0.9 | Nucleus sampling cutoff to maintain coherent technical vocabulary |
| `TOP_K` | 40 | Limits token vocabulary selection to high-probability tokens |
| `REPEAT_PENALTY` | 1.15 | Discourages repetitive looping on technical port names |
| `MAX_OUTPUT_TOKENS` | 1,500 tokens | Accommodates detailed architecture tables and full summaries |
| `CONTEXT_WINDOW` | 8,192 tokens | Leaves sufficient headroom for multi-chunk context and conversation history |
