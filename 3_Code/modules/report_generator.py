"""Report Generator for exporting AUTOSAR architectural analysis in JSON and CSV formats."""
import json
import pandas as pd
from typing import Dict, Any, List
from io import BytesIO, StringIO

from models.schemas import ExtractionResult, ConsistencyFinding
from utils.helpers import get_iso_timestamp

class ReportGenerator:
    """Generates structured JSON and CSV engineering reports."""

    def generate_full_json_report(
        self,
        doc_name: str,
        summary_text: str,
        extraction: ExtractionResult,
        findings: List[ConsistencyFinding]
    ) -> str:
        """Exports the complete analysis as formatted JSON string."""
        report = {
            "metadata": {
                "report_title": "AUTOSAR High-Level Design Architecture Analysis Report",
                "document_name": doc_name,
                "analysis_timestamp": get_iso_timestamp(),
                "tool_version": "1.0.0",
                "compliance_note": "AI findings require engineering verification before production release."
            },
            "document_summary": summary_text,
            "architecture_inventory": {
                "software_components": [c.model_dump() for c in extraction.components],
                "interfaces": [i.model_dump() for i in extraction.interfaces],
                "signals": [s.model_dump() for s in extraction.signals],
                "dependencies": [d.model_dump() for d in extraction.dependencies]
            },
            "consistency_findings": [f.model_dump() for f in findings],
            "metrics_summary": {
                "total_swcs": len(extraction.components),
                "total_interfaces": len(extraction.interfaces),
                "total_signals": len(extraction.signals),
                "total_dependencies": len(extraction.dependencies),
                "total_findings": len(findings)
            }
        }
        return json.dumps(report, indent=2)

    def generate_components_csv(self, extraction: ExtractionResult) -> str:
        """Exports software components inventory as CSV string."""
        if not extraction.components:
            return "name,description,responsibilities,associated_interfaces,source_document,source_page,status\n"
        records = []
        for c in extraction.components:
            records.append({
                "Name": c.name,
                "Description": c.description,
                "Responsibilities": "; ".join(c.responsibilities),
                "Associated Interfaces": "; ".join(c.associated_interfaces),
                "Source Document": c.source_document,
                "Source Page": c.source_page,
                "Review Status": c.status
            })
        df = pd.DataFrame(records)
        return df.to_csv(index=False)

    def generate_interfaces_csv(self, extraction: ExtractionResult) -> str:
        """Exports interfaces inventory as CSV string."""
        if not extraction.interfaces:
            return "Name,Type,Associated Components,Direction,Source Document,Source Page,Status\n"
        records = []
        for i in extraction.interfaces:
            records.append({
                "Name": i.name,
                "Type": i.interface_type,
                "Associated Components": "; ".join(i.associated_components),
                "Direction": i.direction,
                "Source Document": i.source_document,
                "Source Page": i.source_page,
                "Review Status": i.status
            })
        df = pd.DataFrame(records)
        return df.to_csv(index=False)

    def generate_signals_csv(self, extraction: ExtractionResult) -> str:
        """Exports signals inventory as CSV string."""
        if not extraction.signals:
            return "Name,Sender,Receiver,DataType,Source Document,Source Page,Status\n"
        records = []
        for s in extraction.signals:
            records.append({
                "Name": s.name,
                "Sender SWC": s.sender,
                "Receiver SWC": s.receiver,
                "Data Type": s.data_type,
                "Source Document": s.source_document,
                "Source Page": s.source_page,
                "Review Status": s.status
            })
        df = pd.DataFrame(records)
        return df.to_csv(index=False)

    def generate_dependencies_csv(self, extraction: ExtractionResult) -> str:
        """Exports component dependencies as CSV string."""
        if not extraction.dependencies:
            return "Source SWC,Target SWC,Type,Description,Evidence,Source Document,Source Page,Status\n"
        records = []
        for d in extraction.dependencies:
            records.append({
                "Source SWC": d.source_component,
                "Target SWC": d.target_component,
                "Type": d.dependency_type,
                "Description": d.description,
                "Evidence": d.evidence,
                "Source Document": d.source_document,
                "Source Page": d.source_page,
                "Status": d.status
            })
        df = pd.DataFrame(records)
        return df.to_csv(index=False)

    def generate_consistency_findings_csv(self, findings: List[ConsistencyFinding]) -> str:
        """Exports consistency findings as CSV string."""
        if not findings:
            return "Finding ID,Category,Severity,Status,Description,Affected Elements,Evidence,Source Page\n"
        records = []
        for f in findings:
            records.append({
                "Finding ID": f.finding_id,
                "Category": f.category,
                "Severity": f.severity,
                "Status": f.status,
                "Description": f.description,
                "Affected Elements": "; ".join(f.affected_elements),
                "Evidence": f.evidence,
                "Source Page": f.source_page
            })
        df = pd.DataFrame(records)
        return df.to_csv(index=False)
