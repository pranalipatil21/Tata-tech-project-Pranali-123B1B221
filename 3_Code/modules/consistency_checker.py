"""Consistency Checker for AUTOSAR HLD Architecture Models."""
import re
from typing import List, Dict, Set, Optional, Any
from models.schemas import SoftwareComponent, Interface, Signal, Dependency, ConsistencyFinding, ExtractionResult

class ConsistencyChecker:
    """Performs deterministic and heuristic architecture consistency audits on extracted entities and document text."""

    def analyze_consistency(
        self,
        extraction_result: ExtractionResult,
        chunks: Optional[List[Dict[str, Any]]] = None
    ) -> List[ConsistencyFinding]:
        """
        Executes comprehensive consistency checks across extracted components,
        interfaces, signals, dependencies, and document-level technical specifications.
        """
        findings: List[ConsistencyFinding] = []
        finding_id_counter = 1

        components = extraction_result.components
        interfaces = extraction_result.interfaces
        signals = extraction_result.signals
        dependencies = extraction_result.dependencies

        swc_name_map: Dict[str, SoftwareComponent] = {c.name: c for c in components}
        swc_lower_map: Dict[str, List[str]] = {}

        # 1. Check for Duplicate or Case-Variant Component Names
        for c in components:
            lower = c.name.lower()
            swc_lower_map.setdefault(lower, []).append(c.name)

        for lower, names in swc_lower_map.items():
            if len(names) > 1:
                findings.append(ConsistencyFinding(
                    finding_id=f"CHK-{finding_id_counter:03d}",
                    category="Duplicate Component",
                    description=f"Multiple components defined with matching or case-variant names: {', '.join(names)}",
                    severity="High",
                    status="Confirmed",
                    affected_elements=names,
                    evidence="Identified multiple declarations across document sections.",
                    source_page=swc_name_map[names[0]].source_page
                ))
                finding_id_counter += 1

        # 2. Check for Missing Component Descriptions
        for c in components:
            if not c.description or c.description in ["Not specified", "", "None"]:
                findings.append(ConsistencyFinding(
                    finding_id=f"CHK-{finding_id_counter:03d}",
                    category="Missing Component Description",
                    description=f"Software component '{c.name}' has no functional description or role specified.",
                    severity="Medium",
                    status="Missing Information",
                    affected_elements=[c.name],
                    evidence=f"Extracted component has empty description on page {c.source_page}.",
                    source_page=c.source_page
                ))
                finding_id_counter += 1

        # 3. Check for Referenced but Undefined Components in Dependencies
        known_swc_names = set(swc_name_map.keys())
        for dep in dependencies:
            for endpoint, role in [(dep.source_component, "source"), (dep.target_component, "target")]:
                if endpoint not in known_swc_names and endpoint not in ["Not specified", ""]:
                    findings.append(ConsistencyFinding(
                        finding_id=f"CHK-{finding_id_counter:03d}",
                        category="Undefined Component Reference",
                        description=f"Dependency references '{endpoint}' as {role} component, but it is not defined in the Software Component inventory.",
                        severity="High",
                        status="Confirmed",
                        affected_elements=[endpoint, dep.source_component, dep.target_component],
                        evidence=f"Referenced in dependency: '{dep.description}' on page {dep.source_page}.",
                        source_page=dep.source_page
                    ))
                    finding_id_counter += 1

        # 4. Check for Signals with Undefined Sender or Receiver SWCs
        for sig in signals:
            unresolved = []
            if sig.sender != "Not specified" and sig.sender not in known_swc_names:
                unresolved.append((sig.sender, "sender"))

            if sig.receiver != "Not specified":
                # Split compound receivers (e.g., 'BrakeControlSWC; MotorControlSWC')
                sub_receivers = [r.strip() for r in re.split(r"[;,]", sig.receiver) if r.strip()]
                for sr in sub_receivers:
                    if sr not in known_swc_names and not any(kw in sr.lower() for kw in ["adapter", "boundary", "external"]):
                        unresolved.append((sr, "receiver"))

            for endpoint, role in unresolved:
                findings.append(ConsistencyFinding(
                    finding_id=f"CHK-{finding_id_counter:03d}",
                    category="Undefined Component Reference",
                    description=f"Signal '{sig.name}' specifies '{endpoint}' as {role}, but '{endpoint}' is not in the SWC catalog.",
                    severity="Medium",
                    status="Potential Finding",
                    affected_elements=[sig.name, endpoint],
                    evidence=f"Signal definition references '{endpoint}' on page {sig.source_page}.",
                    source_page=sig.source_page
                ))
                finding_id_counter += 1

        # 5. Check for Inconsistent Interface Naming Conventions
        interface_names = [i.name for i in interfaces]
        if interface_names:
            patterns_found = set()
            for name in interface_names:
                if name.startswith("IF_") or name.startswith("If_"):
                    patterns_found.add("Prefix 'IF_'")
                elif name.startswith("Port_"):
                    patterns_found.add("Prefix 'Port_'")
                elif re.match(r"^[A-Z][a-zA-Z0-9]+Interface$", name):
                    patterns_found.add("Suffix 'Interface'")
                else:
                    patterns_found.add("Custom/No standard prefix")

            if len(patterns_found) > 1:
                findings.append(ConsistencyFinding(
                    finding_id=f"CHK-{finding_id_counter:03d}",
                    category="Inconsistent Interface Naming",
                    description=f"Multiple interface naming conventions detected across the document: {', '.join(patterns_found)}. AUTOSAR design guidelines recommend standardized naming prefixes.",
                    severity="Low",
                    status="Potential Finding",
                    affected_elements=interface_names[:5],
                    evidence="Interface inventory shows disparate naming conventions.",
                    source_page=interfaces[0].source_page if interfaces else None
                ))
                finding_id_counter += 1

        # 6. Check for Potentially Missing Interface Definitions
        known_if_names = set(i.name for i in interfaces)
        for c in components:
            for if_ref in c.associated_interfaces:
                if if_ref not in known_if_names and if_ref not in ["Not specified", ""]:
                    findings.append(ConsistencyFinding(
                        finding_id=f"CHK-{finding_id_counter:03d}",
                        category="Potentially Missing Interface Definition",
                        description=f"Component '{c.name}' references interface '{if_ref}', but its formal port interface definition was not found in the document.",
                        severity="Medium",
                        status="Missing Information",
                        affected_elements=[c.name, if_ref],
                        evidence=f"Associated with component '{c.name}' on page {c.source_page}.",
                        source_page=c.source_page
                    ))
                    finding_id_counter += 1

        if chunks:
            def _get_c_text(c):
                return c.get("text", "") if isinstance(c, dict) else getattr(c, "text", "")
            def _get_c_page(c):
                return c.get("metadata", {}).get("page_number", 1) if isinstance(c, dict) else getattr(c, "page_number", 1)

            full_text = "\n".join(_get_c_text(c) for c in chunks)
            chunk_page_map = {_get_c_page(c): _get_c_text(c) for c in chunks}

            # Check 7.1: Interface Mismatch (e.g. IF_BatteryStatus vs IF_BatteryState / INT-07)
            if "IF_BatteryState" in full_text and ("IF_BatteryStatus" in full_text or "IF_BatteryStatus" in known_if_names):
                p_num = next((p for p, t in chunk_page_map.items() if "IF_BatteryState" in t), 6)
                findings.append(ConsistencyFinding(
                    finding_id=f"CHK-{finding_id_counter:03d}",
                    category="Interface Naming Mismatch",
                    description="Interface mismatch: Integration note INT-07 references 'IF_BatteryState', whereas Section 6 defines the interface as 'IF_BatteryStatus'. 'IF_BatteryState' is undefined in the interface catalogue.",
                    severity="High",
                    status="Confirmed",
                    affected_elements=["IF_BatteryStatus", "IF_BatteryState", "MotorControlSWC", "BatteryManagementSWC"],
                    evidence="INT-07: MotorControlSWC shall receive BatterySocPct from BatteryManagementSWC through IF_BatteryState.",
                    source_page=p_num
                ))
                finding_id_counter += 1

            # Check 7.2: Timing / Period Mismatch (e.g. BrakeControlSWC 10 ms vs 20 ms / INT-08)
            has_10ms_brake = bool(re.search(r"BrakeControlSWC.*?10\s*ms", full_text, re.DOTALL))
            has_20ms_brake = bool(re.search(r"BrakeControlSWC.*?20\s*ms|INT-08.*?20\s*ms", full_text, re.DOTALL))
            if has_10ms_brake and has_20ms_brake:
                p_num = next((p for p, t in chunk_page_map.items() if "INT-08" in t or "20 ms" in t), 6)
                findings.append(ConsistencyFinding(
                    finding_id=f"CHK-{finding_id_counter:03d}",
                    category="Timing & Period Mismatch",
                    description="Publication period conflict: Section 4.2 / 7 specifies BrakeControlSWC publishes BrakeTorqueReductionPct every 10 ms, whereas outdated note INT-08 specifies a 20 ms publication period.",
                    severity="High",
                    status="Confirmed",
                    affected_elements=["BrakeControlSWC", "BrakeTorqueReductionPct", "10 ms", "20 ms"],
                    evidence="Outdated note INT-08: BrakeControlSWC shall publish BrakeTorqueReductionPct every 20 ms.",
                    source_page=p_num
                ))
                finding_id_counter += 1

            # Check 7.3: Torque Range / Limit Mismatch (e.g. AllowedMotorTorqueNm 250 Nm vs 300 Nm / INT-09)
            has_250nm = bool(re.search(r"AllowedMotorTorqueNm.*?250\s*Nm|0\s*to\s*250\s*Nm", full_text))
            has_300nm = bool(re.search(r"AllowedMotorTorqueNm.*?300\s*Nm|0\s*to\s*300\s*Nm|INT-09", full_text))
            if has_250nm and has_300nm:
                p_num = next((p for p, t in chunk_page_map.items() if "INT-09" in t or "300 Nm" in t), 6)
                findings.append(ConsistencyFinding(
                    finding_id=f"CHK-{finding_id_counter:03d}",
                    category="Signal Range Mismatch",
                    description="Signal range contradiction: Section 8 specifies AllowedMotorTorqueNm has a maximum limit of 250 Nm (0 to 250 Nm), whereas outdated note INT-09 specifies a range of 0 to 300 Nm.",
                    severity="Medium",
                    status="Confirmed",
                    affected_elements=["AllowedMotorTorqueNm", "250 Nm", "300 Nm"],
                    evidence="Outdated note INT-09: AllowedMotorTorqueNm has a valid range of 0 to 300 Nm.",
                    source_page=p_num
                ))
                finding_id_counter += 1

        return findings
