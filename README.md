# Tata-tech-project-Pranali-123B1B221

# AUTOSAR High-Level Design (HLD) Analysis Assistant

An enterprise-grade, **100% offline and privacy-preserving AI assistant** designed for automotive systems engineers and software architects to analyze, audit, and extract entities from AUTOSAR High-Level Design (HLD) documents.

---

## 🚗 Project Overview

High-Level Design (HLD) documents in automotive systems engineering span hundreds of pages and specify complex software component architectures, sender-receiver interfaces, client-server operations, and timing configurations. Manually auditing these specifications is tedious, error-prone, and slow.

This assistant runs **100% locally with zero cloud egress**, guaranteeing complete protection of proprietary automotive intellectual property without needing third-party cloud API keys.

---

## 🌟 Key Application Features

1. **Executive Dashboard:** High-level metrics showing indexed documents, pages, software components (SWCs), interfaces, signals, and dependencies.
2. **Upload & Ingestion Pipeline:** Automatic text extraction, table parsing, semantic chunking, and local vector indexing in ChromaDB with SHA-256 deduplication.
3. **Grounded AI Technical Assistant:** RAG-powered chat assistant strictly grounded on document context, offering exact page citations and anti-hallucination guardrails.
4. **Architecture Entity Extraction:** Hybrid rule-based and LLM-assisted extraction of SWCs, Port Interfaces, Signals, and Candidate Dependencies.
5. **Interactive Dependency Visualization:** NetworkX and Plotly directed relationship graph illustrating provider-to-consumer software component architectures.
6. **Consistency Audit Engine:** Deterministic verification catching interface mismatches, publication timing conflicts, and signal range contradictions.
7. **Engineering Report Export:** Instant one-click exports of comprehensive analysis results in standardized JSON and tabular CSV formats.

---

## 🛠️ Technology Stack

* **Large Language Model (LLM):** Local [Ollama](https://ollama.com/) running `qwen2.5:3b`
* **Embedding Model:** Local `SentenceTransformers` (`BAAI/bge-small-en-v1.5`, 384 dimensions)
* **Vector Store:** Local Persistent [ChromaDB](https://www.trychroma.com/)
* **Frontend UI:** [Streamlit](https://streamlit.io/) (Enterprise Automotive Dashboard)
* **Graph Modeling:** NetworkX & Plotly Interactive Visualization
* **Document Processing:** PyMuPDF (fitz) & pdfplumber with table structure recognition

---

## 📂 Repository Structure

```text
├── 1_Synopsis/               # Project synopsis and initial documentation
├── 2_Input_Data/             # Input reference specifications and datasets
├── 3_Code/                   # Application source code
│   ├── config/               # Settings and hyperparameters
│   ├── data/                 # Local uploads, ChromaDB storage, and metadata
│   ├── models/               # Pydantic data schemas
│   ├── modules/              # Core modules (RAG, extractor, consistency, etc.)
│   ├── sample_data/          # Synthetic test datasets and generation scripts
│   ├── tests/                # Automated pytest unit test suite
│   ├── utils/                # Utility and helper functions
│   └── app.py                # Streamlit main dashboard application
├── 4_Model_Prompts_Config/   # LLM system prompts and hyperparameter configs
├── 5_Evaluation_Results/     # Evaluation metrics, test cases, and screenshots
├── 6_Documentation/          # System architecture and workflow diagrams
├── 7_Video/                  # Pre-recorded demonstration video
├── 8_Declarations/           # AI usage and originality declarations
└── build_all_artifacts.py    # Automation script to rebuild project artifacts
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* Python 3.10 to 3.13
* Local [Ollama](https://ollama.com/) installed and running:
  ```bash
  ollama run qwen2.5:3b
  ```

### 2. Installation
```bash
cd 3_Code
pip install -r requirements.txt
```

### 3. Run the Application
```bash
streamlit run app.py
```
Open your browser at **`http://localhost:8501`**.

---

## 🧪 Testing

Run automated unit tests:
```bash
python -m pytest 3_Code/tests
```
