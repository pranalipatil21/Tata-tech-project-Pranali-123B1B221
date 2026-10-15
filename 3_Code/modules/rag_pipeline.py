"""Grounded RAG Pipeline for AUTOSAR HLD Question Answering and Summarization."""
import logging
from typing import List, Dict, Any, Optional

from config.settings import SIMILARITY_TOP_K, SIMILARITY_CUTOFF
from models.schemas import QAResponse
from modules.vector_store import VectorStore
from modules.llm_service import LLMService

logger = logging.getLogger(__name__)

GROUNDED_SYSTEM_PROMPT = """You are an expert Automotive Software Architect specializing in AUTOSAR Classic and Adaptive Platform architecture.
Your duty is to answer technical questions regarding High-Level Design (HLD) specifications accurately, strictly adhering to the provided document context.

### MANDATORY GROUNDING RULES:
1. Grounding: Answer ONLY based on the facts provided in the Context below. Do NOT use unstated prior knowledge, make architectural assumptions, or extrapolate beyond what is documented.
2. Anti-Hallucination: If the provided Context does NOT contain the necessary facts to fully answer the question, clearly state:
   "Based on the provided AUTOSAR HLD document, there is insufficient evidence to answer this question. The document does not specify [missing element]."
   Never invent components, ports, interfaces, signals, or runnable entities.
3. Citations: Every technical assertion, component name, interface, signal, or dependency MUST cite its source page and document using the format: [Source: <filename>, Page <X>].
4. Professional Engineering Tone: Use formal automotive systems engineering terminology (e.g., SWC, VFB, RTE, Port Interfaces, Sender-Receiver, Client-Server, Runnable Entities, PDU).
5. Confidence & Weak Evidence: If the retrieved evidence is sparse or ambiguous, clearly mention this limitation."""

class RAGPipeline:
    """End-to-end grounded RAG pipeline for AUTOSAR HLD analysis."""

    def __init__(self, vector_store: Optional[VectorStore] = None, llm_service: Optional[LLMService] = None):
        self.vector_store = vector_store or VectorStore()
        self.llm_service = llm_service or LLMService()

    def answer_question(
        self,
        question: str,
        doc_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        top_k: int = SIMILARITY_TOP_K
    ) -> QAResponse:
        """
        Executes grounded QA:
        1. Retrieve top-k chunks from vector store.
        2. Evaluate retrieval distance and sufficiency.
        3. Construct prompt with citations context.
        4. Query local LLM.
        5. Return structured QAResponse.
        """
        matches = self.vector_store.query(question, top_k=top_k, doc_id=doc_id)

        if not matches:
            return QAResponse(
                question=question,
                answer="No relevant content found in the indexed document repository. Please ensure a document has been uploaded and indexed.",
                citations=[],
                retrieval_confidence="Insufficient Evidence",
                warning="No document chunks matched the query."
            )

        # Assess retrieval distance
        min_distance = min(m.get("distance", 1.0) for m in matches)
        citations = []
        context_parts = []

        for m in matches:
            meta = m.get("metadata", {})
            filename = meta.get("filename", "Unknown")
            page_num = meta.get("page_number", 1)
            heading = meta.get("section_heading", "General")
            text = m.get("text", "")

            context_parts.append(f"--- Document: {filename} | Page {page_num} | Section: {heading} ---\n{text}")
            citations.append({
                "filename": filename,
                "page": page_num,
                "section": heading,
                "snippet": text[:200] + "..." if len(text) > 200 else text,
                "distance": round(m.get("distance", 0.0), 3)
            })

        # Determine retrieval confidence and limitation warning
        warning = None
        if min_distance > SIMILARITY_CUTOFF:
            retrieval_confidence = "Low"
            warning = "⚠️ Low semantic retrieval confidence. The answers may be incomplete or absent from the uploaded document."
        elif min_distance > 0.65:
            retrieval_confidence = "Medium"
        else:
            retrieval_confidence = "High"

        # Format history string
        history_str = ""
        if chat_history:
            for msg in chat_history[-3:]:  # Last 3 turns
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_str += f"{role}: {msg.get('content', '')}\n"

        context_block = "\n\n".join(context_parts)
        prompt = f"""### RETRIEVED CONTEXT FROM AUTOSAR HLD:
{context_block}

### CONVERSATION HISTORY:
{history_str if history_str else "None"}

### USER QUESTION:
{question}

### GROUNDED TECHNICAL ANSWER (Include [Source: <filename>, Page <X>] citations):
"""

        answer = self.llm_service.generate(
            prompt=prompt,
            system_prompt=GROUNDED_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=1500
        )

        return QAResponse(
            question=question,
            answer=answer,
            citations=citations,
            retrieval_confidence=retrieval_confidence,
            warning=warning
        )

    def generate_summary(self, doc_id: Optional[str] = None, summary_type: str = "Detailed") -> str:
        """
        Generates Short or Detailed technical summary of an AUTOSAR HLD document.
        """
        # Retrieve key chunks representing overview, components, interfaces, and architecture
        queries = [
            "system overview architecture software components",
            "sender receiver client server interfaces signals",
            "component dependencies functional flow integration requirements"
        ]
        all_matches = []
        seen_chunks = set()

        for q in queries:
            matches = self.vector_store.query(q, top_k=3, doc_id=doc_id)
            for m in matches:
                cid = m.get("chunk_id")
                if cid and cid not in seen_chunks:
                    seen_chunks.add(cid)
                    all_matches.append(m)

        if not all_matches:
            return "No document content available for summarization. Please upload and index an AUTOSAR HLD PDF."

        context_parts = []
        for m in all_matches:
            meta = m.get("metadata", {})
            context_parts.append(f"[Page {meta.get('page_number', '?')} - {meta.get('section_heading', '')}]\n{m.get('text', '')}")

        context_block = "\n\n".join(context_parts)

        if summary_type == "Short":
            prompt = f"""Context:
{context_block}

Task: Provide a concise executive summary (2-3 paragraphs) of this AUTOSAR High-Level Design document.
Highlight:
1. System purpose and core SWCs
2. Inter-component communication
3. Key functional integration points
Include page citations [Page X]."""
        else:
            prompt = f"""Context:
{context_block}

Task: Provide a Detailed Technical Architecture Summary of this AUTOSAR High-Level Design document.
Structure your analysis into:
1. Executive System Overview
2. Software Component Inventory & Responsibilities
3. Interface & Communication Architecture (Sender-Receiver & Client-Server)
4. Critical Signal Flows & Data Elements
5. Component Dependencies & Run-Time Execution Order
6. Integration, Safety (ASIL), and Diagnostic Requirements
Include supporting page references [Page X] for every section."""

        return self.llm_service.generate(
            prompt=prompt,
            system_prompt=GROUNDED_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=2000
        )
