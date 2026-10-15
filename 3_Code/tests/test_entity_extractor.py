"""Unit tests for Entity Extractor module."""
import pytest
from modules.entity_extractor import EntityExtractor
from models.schemas import ExtractionResult

def test_rule_based_entity_extraction():
    extractor = EntityExtractor()

    sample_chunks = [
        {
            "text": """BrakeControlSWC is an Application SWC responsible for ABS arbitration.
                       BrakeControlSWC depends on VehicleSpeedSWC for vehicle ground speed calculations.
                       It transmits Sig_TargetBrakeTorque_Nm via If_BrakeTorqueCommand to MotorControlSWC.""",
            "metadata": {"page_number": 4, "filename": "sample_hld.pdf"}
        },
        {
            "text": """MotorControlSWC manages inverter torque.
                       BatteryManagementSWC oversees battery state of charge.
                       DiagnosticManagerSWC provides UDS services.""",
            "metadata": {"page_number": 5, "filename": "sample_hld.pdf"}
        }
    ]

    result: ExtractionResult = extractor.extract_from_chunks(sample_chunks, use_llm=False)

    # Verify SWCs extracted
    swc_names = [c.name for c in result.components]
    assert "BrakeControlSWC" in swc_names
    assert "VehicleSpeedSWC" in swc_names
    assert "MotorControlSWC" in swc_names
    assert "BatteryManagementSWC" in swc_names
    assert "DiagnosticManagerSWC" in swc_names

    # Verify Interfaces extracted
    if_names = [i.name for i in result.interfaces]
    assert "If_BrakeTorqueCommand" in if_names

    # Verify Signals extracted
    sig_names = [s.name for s in result.signals]
    assert "Sig_TargetBrakeTorque_Nm" in sig_names

    # Verify Dependencies
    assert len(result.dependencies) > 0
    dep = result.dependencies[0]
    assert dep.source_component == "BrakeControlSWC"
    assert dep.target_component == "VehicleSpeedSWC"
