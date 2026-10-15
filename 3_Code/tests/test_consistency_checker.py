"""Unit tests for Consistency Checker module."""
import pytest
from modules.consistency_checker import ConsistencyChecker
from models.schemas import ExtractionResult, SoftwareComponent, Interface, Signal, Dependency

def test_consistency_checks_detection():
    checker = ConsistencyChecker()

    # Create dummy extraction with deliberate inconsistencies:
    # 1. Duplicate component name ('MotorControlSWC' and 'motorcontrolswc')
    # 2. Undefined target component ('SteeringControlSWC' referenced in dependency but not in SWC list)
    # 3. Missing description for 'BatteryManagementSWC'
    # 4. Inconsistent interface naming ('If_Speed' vs 'Port_Torque')

    components = [
        SoftwareComponent(name="MotorControlSWC", description="Handles inverter motor drive", source_page=2),
        SoftwareComponent(name="motorcontrolswc", description="Duplicate motor entry", source_page=5),
        SoftwareComponent(name="BatteryManagementSWC", description="Not specified", source_page=6),
    ]

    dependencies = [
        Dependency(source_component="MotorControlSWC", target_component="SteeringControlSWC", source_page=3)
    ]

    interfaces = [
        Interface(name="If_Speed", source_page=2),
        Interface(name="Port_Torque", source_page=3)
    ]

    extraction = ExtractionResult(
        components=components,
        interfaces=interfaces,
        signals=[],
        dependencies=dependencies
    )

    findings = checker.analyze_consistency(extraction)
    assert len(findings) >= 3

    categories = [f.category for f in findings]
    assert "Duplicate Component" in categories
    assert "Undefined Component Reference" in categories
    assert "Missing Component Description" in categories
