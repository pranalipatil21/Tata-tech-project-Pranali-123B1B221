"""Pydantic data models for AUTOSAR HLD Analysis Assistant."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    doc_id: str
    filename: str
    filepath: str
    file_hash: str
    total_pages: int
    file_size_kb: float
    upload_timestamp: str
    chunk_count: int = 0
    is_scanned_or_empty: bool = False
    status: str = "indexed"

class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    page_number: int
    section_heading: Optional[str] = "General"
    text: str
    char_length: int = 0

class SoftwareComponent(BaseModel):
    name: str
    description: Optional[str] = "Not specified"
    responsibilities: List[str] = Field(default_factory=list)
    associated_interfaces: List[str] = Field(default_factory=list)
    source_document: Optional[str] = "Not specified"
    source_page: Optional[int] = None
    status: str = "Candidate"

class Interface(BaseModel):
    name: str
    interface_type: str = "Sender-Receiver"  # Sender-Receiver, Client-Server, Parameter, Trigger
    associated_components: List[str] = Field(default_factory=list)
    direction: str = "Provided/Required"
    source_document: Optional[str] = "Not specified"
    source_page: Optional[int] = None
    status: str = "Candidate"

class Signal(BaseModel):
    name: str
    sender: str = "Not specified"
    receiver: str = "Not specified"
    data_type: Optional[str] = "Not specified"
    source_document: Optional[str] = "Not specified"
    source_page: Optional[int] = None
    status: str = "Candidate"

class Dependency(BaseModel):
    source_component: str
    target_component: str
    dependency_type: str = "Functional"  # Functional, Data Flow, Service Call, Diagnostic
    description: str = "Not specified"
    evidence: str = "Not specified"
    source_document: Optional[str] = "Not specified"
    source_page: Optional[int] = None
    status: str = "Candidate"  # Candidate vs Reviewed

class ConsistencyFinding(BaseModel):
    finding_id: str
    category: str  # Duplicate Component, Inconsistent Interface Naming, Missing Description, Undefined Component Reference, etc.
    description: str
    severity: str = "Medium"  # High, Medium, Low, Info
    status: str = "Potential Finding"  # Confirmed, Potential Finding, Missing Information, Insufficient Evidence
    affected_elements: List[str] = Field(default_factory=list)
    evidence: Optional[str] = "Not specified"
    source_page: Optional[int] = None

class ExtractionResult(BaseModel):
    components: List[SoftwareComponent] = Field(default_factory=list)
    interfaces: List[Interface] = Field(default_factory=list)
    signals: List[Signal] = Field(default_factory=list)
    dependencies: List[Dependency] = Field(default_factory=list)

class QAResponse(BaseModel):
    question: str
    answer: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    retrieval_confidence: str = "High"  # High, Medium, Low, Insufficient Evidence
    warning: Optional[str] = None
