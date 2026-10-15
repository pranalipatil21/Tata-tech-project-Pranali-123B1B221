"""AI-Powered AUTOSAR High-Level Design (HLD) Document Analysis Assistant.
Streamlit Engineering Dashboard and Interactive Analysis Interface.
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import json

from config.settings import PAGE_TITLE, PAGE_ICON, LAYOUT
from modules.document_manager import DocumentManager
from modules.pdf_processor import PDFProcessor
from modules.vector_store import VectorStore
from modules.llm_service import LLMService
from modules.rag_pipeline import RAGPipeline
from modules.entity_extractor import EntityExtractor
from modules.consistency_checker import ConsistencyChecker
from modules.dependency_graph import DependencyGraphBuilder
from modules.report_generator import ReportGenerator
from models.schemas import ExtractionResult

# Set Streamlit Page Config
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom Enterprise CSS
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 4px;
    }
    .sub-header {
        font-size: 14px;
        color: #475569;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #1E40AF;
    }
    .metric-label {
        font-size: 12px;
        color: #64748B;
        text-transform: uppercase;
    }
    .source-box {
        background-color: #F1F5F9;
        border-left: 4px solid #2563EB;
        padding: 10px 14px;
        margin: 8px 0;
        font-size: 13px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "extraction_result" not in st.session_state:
    st.session_state.extraction_result = ExtractionResult()
if "consistency_findings" not in st.session_state:
    st.session_state.consistency_findings = []
if "document_summary" not in st.session_state:
    st.session_state.document_summary = ""
if "selected_doc_id" not in st.session_state:
    st.session_state.selected_doc_id = "all"

# Initialize Backend Singletons
@st.cache_resource
def get_services():
    doc_mgr = DocumentManager()
    pdf_proc = PDFProcessor()
    vec_store = VectorStore()
    llm_svc = LLMService()
    rag_pipe = RAGPipeline(vector_store=vec_store, llm_service=llm_svc)
    extractor = EntityExtractor(llm_service=llm_svc)
    checker = ConsistencyChecker()
    graph_builder = DependencyGraphBuilder()
    reporter = ReportGenerator()
    return doc_mgr, pdf_proc, vec_store, llm_svc, rag_pipe, extractor, checker, graph_builder, reporter

doc_mgr, pdf_proc, vec_store, llm_svc, rag_pipe, extractor, checker, graph_builder, reporter = get_services()

# Sidebar Navigation
st.sidebar.markdown(f"### {PAGE_ICON} AUTOSAR Assistant")
st.sidebar.caption("Automotive Engineering HLD Analysis System")

# LLM Status Indicator
llm_status = llm_svc.check_health()
if llm_status["is_running"]:
    st.sidebar.success(f"🟢 LLM Active: {llm_status['active_model']}")
else:
    st.sidebar.error(f"🔴 Local LLM Offline: {llm_status['error'] or 'Check Ollama'}")

nav_choice = st.sidebar.radio(
    "Navigation",
    [
        "1. Dashboard",
        "2. Upload Documents",
        "3. AI Document Assistant",
        "4. Architecture Analysis",
        "5. Dependency Visualization",
        "6. Consistency Checks",
        "7. Export Reports"
    ]
)

# Active Document Selector in Sidebar
catalog = doc_mgr.load_all_metadata()
doc_options = {"all": "All Documents (Consolidated)"}
for doc_id, meta in catalog.items():
    doc_options[doc_id] = f"{meta.filename} ({meta.total_pages} pp)"

selected_doc = st.sidebar.selectbox(
    "Active Document Context",
    options=list(doc_options.keys()),
    format_func=lambda x: doc_options[x]
)

def ensure_extracted_state():
    """Ensures architecture entities and consistency findings are populated for the active document."""
    target_doc = None if st.session_state.selected_doc_id == "all" else st.session_state.selected_doc_id
    chunks = vec_store.get_document_chunks(target_doc)
    if chunks and not st.session_state.extraction_result.components:
        ext_res = extractor.extract_from_chunks(chunks, use_llm=False)
        st.session_state.extraction_result = ext_res
        st.session_state.consistency_findings = checker.analyze_consistency(ext_res, chunks=chunks)

# Detect if selected document changed
if st.session_state.get("prev_selected_doc") != selected_doc:
    st.session_state.prev_selected_doc = selected_doc
    st.session_state.selected_doc_id = selected_doc
    target_doc = None if selected_doc == "all" else selected_doc
    chunks = vec_store.get_document_chunks(target_doc)
    if chunks:
        ext_res = extractor.extract_from_chunks(chunks, use_llm=False)
        st.session_state.extraction_result = ext_res
        st.session_state.consistency_findings = checker.analyze_consistency(ext_res, chunks=chunks)
    else:
        st.session_state.extraction_result = ExtractionResult()
        st.session_state.consistency_findings = []

ensure_extracted_state()

st.sidebar.markdown("---")
st.sidebar.caption("System Environment: Local Offline execution | Zero Cloud Egress")

# -------------------------------------------------------------
# 1. DASHBOARD
# -------------------------------------------------------------
if nav_choice == "1. Dashboard":
    st.markdown('<div class="main-header">AUTOSAR HLD Analysis Executive Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Overview of indexed engineering specifications and extracted software architecture entities.</div>', unsafe_allow_html=True)

    # Compute high-level metrics
    total_docs = len(catalog)
    total_pages = sum(m.total_pages for m in catalog.values())
    ext = st.session_state.extraction_result

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.markdown(f'<div class="metric-card"><div class="metric-value">{total_docs}</div><div class="metric-label">Documents</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-value">{total_pages}</div><div class="metric-label">Indexed Pages</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-value">{len(ext.components)}</div><div class="metric-label">Software Components</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-value">{len(ext.interfaces)}</div><div class="metric-label">Interfaces</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-card"><div class="metric-value">{len(ext.signals)}</div><div class="metric-label">Signals</div></div>', unsafe_allow_html=True)
    m6.markdown(f'<div class="metric-card"><div class="metric-value">{len(ext.dependencies)}</div><div class="metric-label">Dependencies</div></div>', unsafe_allow_html=True)

    st.markdown("### Document Catalog")
    if catalog:
        cat_data = []
        for m in catalog.values():
            cat_data.append({
                "Document ID": m.doc_id,
                "Filename": m.filename,
                "Pages": m.total_pages,
                "Size (KB)": m.file_size_kb,
                "Upload Timestamp": m.upload_timestamp,
                "Chunks": m.chunk_count,
                "Status": "Indexed" if not m.is_scanned_or_empty else "Scanned/Empty Warning"
            })
        st.dataframe(pd.DataFrame(cat_data), use_container_width=True)
    else:
        st.info("No AUTOSAR HLD documents uploaded yet. Go to **Upload Documents** to begin.")

    st.markdown("### Architecture Summary")
    if st.session_state.document_summary:
        st.markdown(st.session_state.document_summary)
    else:
        st.caption("No architectural summary generated yet. Run analysis or request a summary in the AI Assistant.")

# -------------------------------------------------------------
# 2. UPLOAD DOCUMENTS
# -------------------------------------------------------------
elif nav_choice == "2. Upload Documents":
    st.markdown('<div class="main-header">Upload & Process AUTOSAR HLD Documents</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload PDF specifications for text extraction, semantic chunking, and local ChromaDB vector indexing.</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Select AUTOSAR High-Level Design PDF documents",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        for uf in uploaded_files:
            file_bytes = uf.read()
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📄 **{uf.name}** ({round(len(file_bytes)/1024, 1)} KB)")

            meta, is_new = doc_mgr.save_uploaded_file(uf.name, file_bytes)
            if not is_new and meta.chunk_count > 0 and meta.status == "indexed":
                st.warning(f"File **{uf.name}** is already indexed (SHA-256 match: `{meta.file_hash[:12]}...`). Skipping duplicate ingestion.")
                continue

            with st.spinner(f"Extracting and indexing {uf.name}..."):
                try:
                    chunks, p_meta = pdf_proc.process_pdf(meta.filepath, meta.doc_id, meta.filename)

                    if p_meta["is_scanned_or_empty"]:
                        st.error(f"⚠️ Document **{uf.name}** contains little or no extractable text. It may be scanned or image-based. Text-based PDF required for semantic analysis.")
                        doc_mgr.update_document_metadata(
                            meta.doc_id,
                            total_pages=p_meta["total_pages"],
                            chunk_count=0,
                            is_scanned_or_empty=True,
                            status="scanned_warning"
                        )
                        continue

                    # Upsert to Vector Store
                    vec_store.add_chunks(chunks)

                    # Update metadata catalog
                    doc_mgr.update_document_metadata(
                        meta.doc_id,
                        total_pages=p_meta["total_pages"],
                        chunk_count=len(chunks),
                        is_scanned_or_empty=False,
                        status="indexed"
                    )
                    st.success(f"Successfully processed and indexed **{uf.name}** ({p_meta['total_pages']} pages, {len(chunks)} chunks).")
                except Exception as e:
                    st.error(f"Error processing {uf.name}: {str(e)}")

    st.markdown("---")
    c_hdr, c_reindex = st.columns([3, 1])
    with c_hdr:
        st.markdown("### Manage Uploaded Documents")
    with c_reindex:
        if st.button("🔄 Re-index Library", use_container_width=True):
            with st.spinner("Re-indexing all uploaded documents..."):
                catalog = doc_mgr.load_all_metadata()
                reindexed_count = 0
                for d_id, m in catalog.items():
                    try:
                        p_chunks, p_m = pdf_proc.process_pdf(m.filepath, m.doc_id, m.filename)
                        if p_chunks:
                            vec_store.add_chunks(p_chunks)
                            doc_mgr.update_document_metadata(
                                m.doc_id,
                                total_pages=p_m["total_pages"],
                                chunk_count=len(p_chunks),
                                is_scanned_or_empty=False,
                                status="indexed"
                            )
                            reindexed_count += 1
                    except Exception as re_err:
                        st.error(f"Failed re-indexing {m.filename}: {re_err}")
                st.success(f"Re-indexed {reindexed_count} documents successfully.")
                st.rerun()
    catalog = doc_mgr.load_all_metadata()
    if catalog:
        for doc_id, meta in list(catalog.items()):
            col_info, col_del = st.columns([4, 1])
            with col_info:
                st.markdown(f"**{meta.filename}** | Pages: {meta.total_pages} | Chunks: {meta.chunk_count} | SHA-256: `{meta.file_hash[:16]}...`")
            with col_del:
                if st.button("Delete Document", key=f"del_{doc_id}"):
                    vec_store.delete_document_chunks(doc_id)
                    doc_mgr.remove_document(doc_id)
                    st.success(f"Removed {meta.filename}")
                    st.rerun()
    else:
        st.info("No documents currently in library.")

# -------------------------------------------------------------
# 3. AI DOCUMENT ASSISTANT
# -------------------------------------------------------------
elif nav_choice == "3. AI Document Assistant":
    st.markdown('<div class="main-header">Grounded AI Technical Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask technical questions regarding AUTOSAR software components, interfaces, signals, and functional flows.</div>', unsafe_allow_html=True)

    c_top1, c_top2 = st.columns([3, 1])
    with c_top1:
        st.caption(f"Active Query Context: **{doc_options.get(st.session_state.selected_doc_id, 'All')}**")
    with c_top2:
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    # Pre-canned technical prompt chips
    st.markdown("**Sample Automotive Engineering Inquiries:**")
    prompt_cols = st.columns(4)
    q1 = "What are the major software components?"
    q2 = "Which interfaces are used by BrakeControlSWC?"
    q3 = "What are the dependencies of MotorControlSWC?"
    q4 = "Explain the regenerative braking functional flow."

    user_query = None
    if prompt_cols[0].button("Major SWCs", use_container_width=True):
        user_query = q1
    if prompt_cols[1].button("BrakeControl Interfaces", use_container_width=True):
        user_query = q2
    if prompt_cols[2].button("MotorControl Dependencies", use_container_width=True):
        user_query = q3
    if prompt_cols[3].button("Regen Braking Flow", use_container_width=True):
        user_query = q4

    # Render previous conversation
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "citations" in msg and msg["citations"]:
                with st.expander("View Source Citations & References"):
                    for cit in msg["citations"]:
                        st.markdown(f"""
                        <div class="source-box">
                            <b>Document:</b> {cit['filename']} | <b>Page:</b> {cit['page']} | <b>Section:</b> {cit['section']}<br>
                            <i>"{cit['snippet']}"</i>
                        </div>
                        """, unsafe_allow_html=True)

    # Chat input
    chat_input = st.chat_input("Enter technical query regarding AUTOSAR HLD...")
    prompt_to_run = user_query or chat_input

    if prompt_to_run:
        # User message
        st.session_state.chat_history.append({"role": "user", "content": prompt_to_run})
        with st.chat_message("user"):
            st.markdown(prompt_to_run)

        # Assistant response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing document knowledge base..."):
                target_doc = None if st.session_state.selected_doc_id == "all" else st.session_state.selected_doc_id
                response = rag_pipe.answer_question(
                    question=prompt_to_run,
                    doc_id=target_doc,
                    chat_history=st.session_state.chat_history
                )

                if response.warning:
                    st.warning(response.warning)

                st.markdown(response.answer)

                if response.citations:
                    with st.expander("Supporting Document Citations"):
                        for cit in response.citations:
                            st.markdown(f"""
                            <div class="source-box">
                                <b>Document:</b> {cit['filename']} | <b>Page:</b> {cit['page']} | <b>Section:</b> {cit['section']}<br>
                                <i>"{cit['snippet']}"</i>
                            </div>
                            """, unsafe_allow_html=True)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response.answer,
                    "citations": response.citations
                })

# -------------------------------------------------------------
# 4. ARCHITECTURE ANALYSIS
# -------------------------------------------------------------
elif nav_choice == "4. Architecture Analysis":
    st.markdown('<div class="main-header">AUTOSAR Architecture Entity Extraction</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Structured catalog of Software Components (SWCs), Port Interfaces, Signals, and Candidate Dependencies.</div>', unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns([2, 2])
    with col_btn1:
        if st.button("🚀 Run Architecture Entity Extraction", type="primary", use_container_width=True):
            with st.spinner("Executing rule-based and LLM-assisted entity extraction..."):
                target_doc = None if st.session_state.selected_doc_id == "all" else st.session_state.selected_doc_id
                chunks = vec_store.get_document_chunks(target_doc)
                if not chunks:
                    chunks = vec_store.query("software component interface signal dependency", top_k=15, doc_id=target_doc)
                ext_res = extractor.extract_from_chunks(chunks, use_llm=llm_status["is_running"])
                st.session_state.extraction_result = ext_res

                # Run consistency checker with document chunks
                st.session_state.consistency_findings = checker.analyze_consistency(ext_res, chunks=chunks)
                st.success(f"Extracted {len(ext_res.components)} SWCs, {len(ext_res.interfaces)} Interfaces, {len(ext_res.signals)} Signals, {len(ext_res.dependencies)} Dependencies.")

    with col_btn2:
        if st.button("📝 Generate Technical Summary", use_container_width=True):
            with st.spinner("Synthesizing comprehensive architecture summary..."):
                target_doc = None if st.session_state.selected_doc_id == "all" else st.session_state.selected_doc_id
                summary = rag_pipe.generate_summary(doc_id=target_doc, summary_type="Detailed")
                st.session_state.document_summary = summary
                st.success("Generated technical architecture summary.")

    ext = st.session_state.extraction_result

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        f"Software Components ({len(ext.components)})",
        f"Interfaces ({len(ext.interfaces)})",
        f"Signals ({len(ext.signals)})",
        f"Dependencies ({len(ext.dependencies)})",
        "Document Summary"
    ])

    with tab1:
        if ext.components:
            swc_data = []
            for c in ext.components:
                swc_data.append({
                    "Name": c.name,
                    "Description": c.description,
                    "Responsibilities": ", ".join(c.responsibilities) if c.responsibilities else "Not specified",
                    "Interfaces": ", ".join(c.associated_interfaces) if c.associated_interfaces else "Not specified",
                    "Source Doc": c.source_document,
                    "Page": c.source_page,
                    "Status": c.status
                })
            st.dataframe(pd.DataFrame(swc_data), use_container_width=True)
        else:
            st.info("No software components extracted yet. Click 'Run Architecture Entity Extraction' above.")

    with tab2:
        if ext.interfaces:
            if_data = []
            for i in ext.interfaces:
                if_data.append({
                    "Interface Name": i.name,
                    "Type": i.interface_type,
                    "Direction": i.direction,
                    "Associated SWCs": ", ".join(i.associated_components) if i.associated_components else "Not specified",
                    "Source Doc": i.source_document,
                    "Page": i.source_page,
                    "Status": i.status
                })
            st.dataframe(pd.DataFrame(if_data), use_container_width=True)
        else:
            st.info("No interfaces extracted yet.")

    with tab3:
        if ext.signals:
            sig_data = []
            for s in ext.signals:
                sig_data.append({
                    "Signal Name": s.name,
                    "Sender SWC": s.sender,
                    "Receiver SWC": s.receiver,
                    "Data Type": s.data_type,
                    "Source Doc": s.source_document,
                    "Page": s.source_page,
                    "Status": s.status
                })
            st.dataframe(pd.DataFrame(sig_data), use_container_width=True)
        else:
            st.info("No signals extracted yet.")

    with tab4:
        if ext.dependencies:
            dep_data = []
            for d in ext.dependencies:
                dep_data.append({
                    "Source Component": d.source_component,
                    "Target Component": d.target_component,
                    "Type": d.dependency_type,
                    "Description": d.description,
                    "Evidence": d.evidence,
                    "Source Doc": d.source_document,
                    "Page": d.source_page,
                    "Status": d.status
                })
            st.dataframe(pd.DataFrame(dep_data), use_container_width=True)
        else:
            st.info("No dependencies extracted yet.")

    with tab5:
        if st.session_state.document_summary:
            st.markdown(st.session_state.document_summary)
        else:
            st.info("Click 'Generate Technical Summary' above to generate an executive synthesis.")

# -------------------------------------------------------------
# 5. DEPENDENCY VISUALIZATION
# -------------------------------------------------------------
elif nav_choice == "5. Dependency Visualization":
    st.markdown('<div class="main-header">Component Dependency Graph</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Interactive NetworkX and Plotly architectural relationship graph showing confirmed and candidate dependencies.</div>', unsafe_allow_html=True)

    ext = st.session_state.extraction_result
    fig = graph_builder.build_figure(ext.components, ext.dependencies)
    st.plotly_chart(fig, use_container_width=True)

    if ext.dependencies:
        with st.expander("Review & Confirm Candidate Dependencies"):
            st.write("Engineering Review Panel:")
            for idx, dep in enumerate(ext.dependencies):
                c_lbl, c_btn = st.columns([3, 1])
                with c_lbl:
                    st.write(f"**{dep.source_component}** → **{dep.target_component}** ({dep.dependency_type}) — *Status: {dep.status}*")
                with c_btn:
                    if dep.status == "Candidate":
                        if st.button("Confirm Dependency", key=f"conf_{idx}"):
                            dep.status = "Reviewed"
                            st.rerun()

# -------------------------------------------------------------
# 6. CONSISTENCY CHECKS
# -------------------------------------------------------------
elif nav_choice == "6. Consistency Checks":
    st.markdown('<div class="main-header">Document & Architecture Consistency Audit</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Deterministic evidence-based verification of interface naming, component definitions, and referenced symbols.</div>', unsafe_allow_html=True)

    if st.button("Run Consistency Audit", type="primary"):
        ext = st.session_state.extraction_result
        target_doc = None if st.session_state.selected_doc_id == "all" else st.session_state.selected_doc_id
        chunks = vec_store.get_document_chunks(target_doc)
        if not chunks:
            chunks = vec_store.query("interface signal requirement consistency inconsistency", top_k=15, doc_id=target_doc)
        st.session_state.consistency_findings = checker.analyze_consistency(ext, chunks=chunks)
        st.success(f"Audit completed: {len(st.session_state.consistency_findings)} findings identified.")

    findings = st.session_state.consistency_findings

    if findings:
        for f in findings:
            badge_color = "#EF4444" if f.severity == "High" else ("#F59E0B" if f.severity == "Medium" else "#3B82F6")
            status_color = "#10B981" if f.status == "Confirmed" else "#6B7280"

            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #E2E8F0; border-left: 5px solid {badge_color}; border-radius: 6px; padding: 12px; margin-bottom: 12px; background-color: #FFFFFF;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; color: #1E293B;">[{f.finding_id}] {f.category}</span>
                        <span>
                            <span style="background-color: {badge_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">{f.severity}</span>
                            <span style="background-color: {status_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-left: 4px;">{f.status}</span>
                        </span>
                    </div>
                    <p style="margin: 6px 0; color: #334155; font-size: 13px;">{f.description}</p>
                    <div style="font-size: 12px; color: #64748B;">
                        <b>Affected Elements:</b> {', '.join(f.affected_elements) if f.affected_elements else 'N/A'} | <b>Source Page:</b> {f.source_page or 'N/A'}<br>
                        <b>Evidence:</b> <i>{f.evidence}</i>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No consistency findings identified. Either no issues were found, or Architecture Extraction has not been run yet.")

# -------------------------------------------------------------
# 7. EXPORT REPORTS
# -------------------------------------------------------------
elif nav_choice == "7. Export Reports":
    st.markdown('<div class="main-header">Export Engineering Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Download comprehensive architectural findings, component inventories, and audit results in JSON and CSV formats.</div>', unsafe_allow_html=True)

    ext = st.session_state.extraction_result
    findings = st.session_state.consistency_findings
    summary = st.session_state.document_summary or "No summary generated."
    doc_name = doc_options.get(st.session_state.selected_doc_id, "Consolidated_AUTOSAR_HLD")

    st.markdown("### 1. Complete Architecture Analysis JSON")
    json_report = reporter.generate_full_json_report(doc_name, summary, ext, findings)
    st.download_button(
        label="📥 Download Complete Report (JSON)",
        data=json_report,
        file_name=f"{doc_name.replace(' ', '_')}_Analysis_Report.json",
        mime="application/json",
        use_container_width=True
    )

    st.markdown("### 2. Tabular Domain Reports (CSV)")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            label="📊 Export SWC Inventory (CSV)",
            data=reporter.generate_components_csv(ext),
            file_name=f"{doc_name}_Software_Components.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.download_button(
            label="📊 Export Interfaces Catalog (CSV)",
            data=reporter.generate_interfaces_csv(ext),
            file_name=f"{doc_name}_Interfaces.csv",
            mime="text/csv",
            use_container_width=True
        )

    with c2:
        st.download_button(
            label="📊 Export Signals Dictionary (CSV)",
            data=reporter.generate_signals_csv(ext),
            file_name=f"{doc_name}_Signals.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.download_button(
            label="📊 Export Dependencies (CSV)",
            data=reporter.generate_dependencies_csv(ext),
            file_name=f"{doc_name}_Dependencies.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.download_button(
        label="⚠️ Export Consistency Audit Findings (CSV)",
        data=reporter.generate_consistency_findings_csv(findings),
        file_name=f"{doc_name}_Consistency_Findings.csv",
        mime="text/csv",
        use_container_width=True
    )
