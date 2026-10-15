"""AUTOSAR Architecture Entity Extractor using Hybrid Regex and LLM Structured Parsing."""
import re
import json
import logging
from typing import List, Dict, Any, Optional

from models.schemas import SoftwareComponent, Interface, Signal, Dependency, ExtractionResult
from modules.llm_service import LLMService

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are a strict AUTOSAR Architecture Parser. Analyze the given AUTOSAR HLD text excerpt and extract software components, interfaces, signals, and dependencies into valid JSON.
Never invent components or signals. If a detail is missing, set it to "Not specified". Output strictly valid JSON matching this schema:
{
  "software_components": [
    {"name": "...", "description": "...", "responsibilities": ["..."], "associated_interfaces": ["..."], "page_number": 1}
  ],
  "interfaces": [
    {"name": "...", "interface_type": "Sender-Receiver|Client-Server|Parameter|Trigger", "associated_components": ["..."], "direction": "Provided|Required|Both", "page_number": 1}
  ],
  "signals": [
    {"name": "...", "sender": "...", "receiver": "...", "data_type": "...", "page_number": 1}
  ],
  "dependencies": [
    {"source_component": "...", "target_component": "...", "dependency_type": "Functional|Data Flow|Service Call|Diagnostic", "description": "...", "evidence": "...", "status": "Candidate"}
  ]
}"""

class EntityExtractor:
    """Extracts AUTOSAR SWCs, interfaces, signals, and dependencies using rule-based + LLM parsing."""

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or LLMService()

    def extract_from_chunks(
        self,
        chunks: List[Dict[str, Any]],
        use_llm: bool = True
    ) -> ExtractionResult:
        """
        Runs hybrid extraction across chunks.
        Combines deterministic regex and table extraction with LLM JSON extraction for high recall and precision.
        """
        components_map: Dict[str, SoftwareComponent] = {}
        interfaces_map: Dict[str, Interface] = {}
        signals_map: Dict[str, Signal] = {}
        dependencies_list: List[Dependency] = []

        def _get_chunk_info(c):
            if isinstance(c, dict):
                return c.get("text", ""), c.get("metadata", {}).get("page_number", 1), c.get("metadata", {}).get("filename", "Unknown")
            return getattr(c, "text", ""), getattr(c, "page_number", 1), getattr(c, "filename", "Unknown")

        # First pass: collect table-defined interfaces across all chunks
        table_interfaces_found = False
        for chunk in chunks:
            text, page, filename = _get_chunk_info(chunk)
            iface_table_rows = re.findall(
                r"((?:IF|If)_[a-zA-Z0-9_]+)\s*\|\s*([a-zA-Z\-]+)\s*\|\s*(.*?)(?=(?:(?:IF|If)_[a-zA-Z0-9_]+\s*\|)|(?:\[/TABLE DATA\])|$)",
                text
            )
            for if_name, if_type, elements in iface_table_rows:
                table_interfaces_found = True
                if if_name not in interfaces_map:
                    interfaces_map[if_name] = Interface(
                        name=if_name,
                        interface_type=if_type.strip(),
                        associated_components=[],
                        direction="Provided/Required",
                        source_document=filename,
                        source_page=page,
                        status="Candidate"
                    )

        # 1. Deterministic Rule-Based & Table Extraction across all chunks
        for chunk in chunks:
            text, page, filename = _get_chunk_info(chunk)

            # A. Rule-based SWC detection
            swc_matches = set(re.findall(r"\b([A-Z][a-zA-Z0-9]+(?:SWC|Component|Manager))\b", text))
            for swc in swc_matches:
                if len(swc) > 3 and swc not in ["Component", "Manager", "SWC", "AUTOSAR", "Software"]:
                    if swc not in components_map:
                        desc = "Not specified"
                        for sent in text.split("."):
                            if swc in sent and len(sent.strip()) > 10:
                                desc = sent.strip()
                                break
                        components_map[swc] = SoftwareComponent(
                            name=swc,
                            description=desc[:250],
                            responsibilities=[],
                            associated_interfaces=[],
                            source_document=filename,
                            source_page=page,
                            status="Candidate"
                        )

            # B. Parse Table Data: Component Ports (Section 5)
            comp_port_rows = re.findall(
                r"([A-Z][a-zA-Z0-9]+SWC)\s*\|\s*([^|]+)\s*\|\s*([^|\[\n]+)",
                text
            )
            for swc_name, prov_ports, req_ports in comp_port_rows:
                if swc_name in components_map:
                    swc = components_map[swc_name]
                    # Extract interface names from ports (e.g., IF_*)
                    linked_ifs = re.findall(r"(?:IF|If)_[a-zA-Z0-9_]+", f"{prov_ports} {req_ports}")
                    for lif in linked_ifs:
                        if lif not in swc.associated_interfaces:
                            swc.associated_interfaces.append(lif)
                        if not table_interfaces_found and lif not in interfaces_map:
                            interfaces_map[lif] = Interface(
                                name=lif,
                                interface_type="Sender-Receiver",
                                associated_components=[swc_name],
                                direction="Provided/Required",
                                source_document=filename,
                                source_page=page,
                                status="Candidate"
                            )

            # Fallback Rule-based Interface detection ONLY if no formal table interfaces exist in document
            if not table_interfaces_found:
                if_matches = set(re.findall(r"\b((?:IF|If|Port|Interface|Pi)_[a-zA-Z0-9_]+)\b", text))
                for if_name in if_matches:
                    if if_name not in interfaces_map:
                        if_type = "Client-Server" if any(w in text.lower() for w in ["client", "server", "call", "service"]) else "Sender-Receiver"
                        interfaces_map[if_name] = Interface(
                            name=if_name,
                            interface_type=if_type,
                            associated_components=[],
                            direction="Provided/Required",
                            source_document=filename,
                            source_page=page,
                            status="Candidate"
                        )

            # D. Parse Table Data: Signal Ownership & Consumption (Section 7)
            sig_table_rows = re.findall(
                r"([a-zA-Z0-9_]+)\s*\|\s*([a-zA-Z0-9_]+SWC)\s*\|\s*([^|]+)\s*\|\s*([0-9]+\s*ms)",
                text
            )
            for sig_name, prod, cons_str, period in sig_table_rows:
                if sig_name not in signals_map and sig_name != "Signal":
                    signals_map[sig_name] = Signal(
                        name=sig_name,
                        sender=prod.strip(),
                        receiver=cons_str.strip()[:100],
                        data_type="Not specified",
                        source_document=filename,
                        source_page=page,
                        status="Candidate"
                    )

            # Rule-based Signal detection from typed data elements: SignalName (type)
            typed_sig_matches = re.finditer(r"\b([A-Z][a-zA-Z0-9_]+)\s*\((float32|uint8|uint16|uint32|boolean|bool|int32)\)", text)
            for m in typed_sig_matches:
                s_name, s_type = m.group(1), m.group(2)
                if s_name not in signals_map:
                    signals_map[s_name] = Signal(
                        name=s_name,
                        sender="Not specified",
                        receiver="Not specified",
                        data_type=s_type,
                        source_document=filename,
                        source_page=page,
                        status="Candidate"
                    )
                else:
                    signals_map[s_name].data_type = s_type

            # Rule-based Signal detection for Sig_* names
            sig_matches = set(re.findall(r"\b((?:Sig|Signal)_[a-zA-Z0-9_]+)\b", text))
            for sig_name in sig_matches:
                if sig_name not in signals_map:
                    signals_map[sig_name] = Signal(
                        name=sig_name,
                        sender="Not specified",
                        receiver="Not specified",
                        data_type="Not specified",
                        source_document=filename,
                        source_page=page,
                        status="Candidate"
                    )

            # E. Parse Table Data: Explicit Component Dependency List (Section 9)
            dep_table_rows = re.findall(
                r"([A-Z][a-zA-Z0-9]+SWC)\s*\|\s*([A-Z][a-zA-Z0-9]+SWC)\s*\|\s*(.*?)(?=(?:[A-Z][a-zA-Z0-9]+SWC\s*\|)|(?:\[/TABLE DATA\])|$)",
                text
            )
            for src, tgt, reason in dep_table_rows:
                if src != tgt:
                    dependencies_list.append(Dependency(
                        source_component=src.strip(),
                        target_component=tgt.strip(),
                        dependency_type="Functional",
                        description=reason.strip()[:150],
                        evidence=f"Explicit dependency table row: {src} -> {tgt} ({reason.strip()[:80]})",
                        source_document=filename,
                        source_page=page,
                        status="Candidate"
                    ))

            # Rule-based Dependency detection from text patterns
            dep_patterns = [
                r"([A-Z][a-zA-Z0-9]+SWC)\s+(?:depends on|requires|receives data from|transmits to|interacts with|calls)\s+([A-Z][a-zA-Z0-9]+SWC)",
                r"([A-Z][a-zA-Z0-9]+SWC)\s+(?:sends|provides)\s+[a-zA-Z0-9_\s]+\s+to\s+([A-Z][a-zA-Z0-9]+SWC)"
            ]
            for pat in dep_patterns:
                for match in re.finditer(pat, text, re.IGNORECASE):
                    src, tgt = match.group(1), match.group(2)
                    if src != tgt:
                        dependencies_list.append(Dependency(
                            source_component=src,
                            target_component=tgt,
                            dependency_type="Data Flow",
                            description=f"Identified dependency: {match.group(0).strip()}",
                            evidence=match.group(0).strip(),
                            source_document=filename,
                            source_page=page,
                            status="Candidate"
                        ))

        # Associate SWCs with Interfaces based on Port usage and Signal tables
        for c_name, c in components_map.items():
            for if_name, iface in interfaces_map.items():
                if if_name in c.associated_interfaces:
                    if c_name not in iface.associated_components:
                        iface.associated_components.append(c_name)

        # 2. LLM-assisted extraction for rich semantic entities (if enabled and chunks available)
        if use_llm and chunks:
            # Select key chunks with highest entity density
            sorted_chunks = sorted(
                chunks,
                key=lambda c: len(re.findall(r"SWC|Interface|Signal|Port|Component", _get_chunk_info(c)[0])),
                reverse=True
            )[:4]

            for chunk in sorted_chunks:
                chunk_text, page, filename = _get_chunk_info(chunk)

                prompt = f"""Document: {filename} (Page {page})
Text:
{chunk_text}

Task: Extract all AUTOSAR software components, interfaces, signals, and dependencies found strictly in this text into the requested JSON schema."""

                llm_response = self.llm_service.generate(
                    prompt=prompt,
                    system_prompt=EXTRACTION_SYSTEM_PROMPT,
                    temperature=0.0,
                    max_tokens=1500
                )

                parsed = self._safe_parse_json(llm_response)
                if parsed:
                    self._merge_llm_entities(parsed, components_map, interfaces_map, signals_map, dependencies_list, filename, page)

        # Deduplicate dependencies
        unique_deps: List[Dependency] = []
        dep_keys = set()
        for d in dependencies_list:
            key = (d.source_component, d.target_component)
            if key not in dep_keys and d.source_component != d.target_component:
                dep_keys.add(key)
                unique_deps.append(d)

        return ExtractionResult(
            components=list(components_map.values()),
            interfaces=list(interfaces_map.values()),
            signals=list(signals_map.values()),
            dependencies=unique_deps
        )

    def _safe_parse_json(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON block from LLM output."""
        try:
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            bracket_match = re.search(r"(\{.*\})", response_text, re.DOTALL)
            if bracket_match:
                return json.loads(bracket_match.group(1))
            return json.loads(response_text)
        except Exception:
            return None

    def _merge_llm_entities(
        self,
        parsed_data: Dict[str, Any],
        components_map: Dict[str, SoftwareComponent],
        interfaces_map: Dict[str, Interface],
        signals_map: Dict[str, Signal],
        dependencies_list: List[Dependency],
        filename: str,
        page: int
    ):
        """Merges parsed LLM JSON entities into global catalog with validation."""
        for c in parsed_data.get("software_components", []):
            name = c.get("name", "").strip()
            if name and name not in ["Not specified", ""]:
                if name not in components_map:
                    components_map[name] = SoftwareComponent(
                        name=name,
                        description=c.get("description", "Not specified"),
                        responsibilities=c.get("responsibilities", []),
                        associated_interfaces=c.get("associated_interfaces", []),
                        source_document=filename,
                        source_page=page,
                        status="Candidate"
                    )
                else:
                    existing = components_map[name]
                    if existing.description in ["Not specified", ""] and c.get("description"):
                        existing.description = c.get("description")
                    if c.get("responsibilities"):
                        existing.responsibilities = list(set(existing.responsibilities + c.get("responsibilities", [])))
                    if c.get("associated_interfaces"):
                        existing.associated_interfaces = list(set(existing.associated_interfaces + c.get("associated_interfaces", [])))

        for iface in parsed_data.get("interfaces", []):
            name = iface.get("name", "").strip()
            if name and name not in ["Not specified", ""]:
                if name not in interfaces_map:
                    interfaces_map[name] = Interface(
                        name=name,
                        interface_type=iface.get("interface_type", "Sender-Receiver"),
                        associated_components=iface.get("associated_components", []),
                        direction=iface.get("direction", "Provided/Required"),
                        source_document=filename,
                        source_page=page,
                        status="Candidate"
                    )

        for sig in parsed_data.get("signals", []):
            name = sig.get("name", "").strip()
            if name and name not in ["Not specified", ""]:
                if name not in signals_map:
                    signals_map[name] = Signal(
                        name=name,
                        sender=sig.get("sender", "Not specified"),
                        receiver=sig.get("receiver", "Not specified"),
                        data_type=sig.get("data_type", "Not specified"),
                        source_document=filename,
                        source_page=page,
                        status="Candidate"
                    )

        for dep in parsed_data.get("dependencies", []):
            src = dep.get("source_component", "").strip()
            tgt = dep.get("target_component", "").strip()
            if src and tgt and src != tgt and src != "Not specified" and tgt != "Not specified":
                dependencies_list.append(Dependency(
                    source_component=src,
                    target_component=tgt,
                    dependency_type=dep.get("dependency_type", "Functional"),
                    description=dep.get("description", "Not specified"),
                    evidence=dep.get("evidence", "Identified in architecture section"),
                    source_document=filename,
                    source_page=page,
                    status="Candidate"
                ))
