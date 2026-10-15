"""Synthetic AUTOSAR HLD Document Generator for Technical Evaluation."""
from pathlib import Path
import sys

SAMPLE_HLD_TEXT = [
    {
        "page": 1,
        "title": "AUTOSAR High-Level Design Specification",
        "section": "1. Document Metadata & System Overview",
        "content": """AUTOSAR HIGH-LEVEL DESIGN (HLD) SPECIFICATION
DOCUMENT CLASSIFICATION: SYNTHETIC DEMONSTRATION DATA FOR TECHNICAL EVALUATION ONLY.
NOTICE: This document is an illustrative, synthetic engineering benchmark designed for technical evaluation of automated analysis systems. It is NOT an OEM-approved production architecture.

1.1 System Architecture Scope
The Powertrain and Chassis Domain Controller (PCDC) coordinates electric traction, friction braking, energy recuperation, and high-voltage power distribution for a dual-motor electric vehicle. The architecture conforms to the AUTOSAR Classic Platform Release 4.4.0 standards.

1.2 System Level Goals
- Coordinate brake blending between friction braking and electric regenerative braking.
- Maintain vehicle lateral and longitudinal stability under emergency deceleration.
- Manage high-voltage battery state of charge (SoC) and cell temperature derating.
- Comply with ISO 26262 ASIL-D functional safety requirements across braking and torque intervention loops."""
    },
    {
        "page": 2,
        "title": "Software Architecture Overview",
        "section": "2. AUTOSAR Software Layering & Virtual Functional Bus",
        "content": """2.1 Virtual Functional Bus (VFB) Representation
The PCDC application layer resides above the AUTOSAR Run-Time Environment (RTE). All inter-component interactions are mediated via well-defined Port Interfaces according to AUTOSAR Virtual Functional Bus specifications.

2.2 Software Component (SWC) Inventory
The system architecture defines five primary application and service software components:
1. VehicleSpeedSWC: Sensor abstraction and vehicle velocity calculation component.
2. BrakeControlSWC: Core anti-lock braking (ABS), electronic stability program (ESP), and brake arbitration component.
3. MotorControlSWC: Electric traction inverter torque command generator and regenerative power manager.
4. BatteryManagementSWC: High-voltage battery pack state estimation, thermal protection, and current derating monitor.
5. DiagnosticManagerSWC: On-board diagnostics (OBD-II / UDS ISO 14229) service component, fault code storage, and fail-safe coordinator."""
    },
    {
        "page": 3,
        "title": "Software Component: VehicleSpeedSWC",
        "section": "3. Software Component Specification: VehicleSpeedSWC",
        "content": """3.1 Component Identification
- Component Name: VehicleSpeedSWC
- Category: Sensor Actuator Software Component (SensorSWC)
- Safety Integrity Level: ASIL-B
- Execution Periodicity: 10ms cyclic runnable (Runnable_CalculateSpeed)

3.2 Functional Description & Responsibilities
VehicleSpeedSWC interfaces with four wheel speed pulse counters via Complex Device Drivers (CDD). It is responsible for:
- Reading raw wheel rotation pulse rates from front-left, front-right, rear-left, and rear-right sensors.
- Filtering high-frequency wheel slip noise using a recursive Kalman filter.
- Calculating reference vehicle linear speed in kilometers per hour (kph).
- Detecting wheel speed sensor plausibility faults and reporting diagnostic events.

3.3 Associated Interfaces
- Provided Interface: If_VehicleSpeed (Sender-Receiver)
- Required Interface: If_WheelPulseCDD (Client-Server)
- Required Interface: If_DiagnosticService (Client-Server)"""
    },
    {
        "page": 4,
        "title": "Software Component: BrakeControlSWC",
        "section": "4. Software Component Specification: BrakeControlSWC",
        "content": """4.1 Component Identification
- Component Name: BrakeControlSWC
- Category: Application Software Component (ApplicationSWC)
- Safety Integrity Level: ASIL-D
- Execution Periodicity: 10ms cyclic runnable (Runnable_BrakeArbitration)

4.2 Functional Description & Responsibilities
BrakeControlSWC is the primary deceleration authority in the chassis domain. Its core duties include:
- Acquiring driver brake pedal travel percentage and hydraulic line pressure.
- Computing total target vehicle braking deceleration torque.
- Determining brake blending ratio: allocating maximum feasible regenerative braking to MotorControlSWC while applying remainder via electro-hydraulic friction brakes.
- Triggering Anti-Lock Braking (ABS) modulation when individual wheel slip exceeds 15 percent.

4.3 Associated Interfaces & Dependencies
- BrakeControlSWC depends on VehicleSpeedSWC for vehicle velocity and individual wheel speeds.
- Provided Interface: If_BrakeCommand (Sender-Receiver)
- Provided Interface: If_BrakeTorqueCommand (Sender-Receiver)
- Required Interface: If_VehicleSpeed (Sender-Receiver)
- Required Interface: If_DiagnosticService (Client-Server)"""
    },
    {
        "page": 5,
        "title": "Software Component: MotorControlSWC",
        "section": "5. Software Component Specification: MotorControlSWC",
        "content": """5.1 Component Identification
- Component Name: MotorControlSWC
- Category: Application Software Component (ApplicationSWC)
- Safety Integrity Level: ASIL-D
- Execution Periodicity: 5ms cyclic runnable (Runnable_MotorTorqueControl)

5.2 Functional Description & Responsibilities
MotorControlSWC translates acceleration pedal inputs and brake blending requests into front and rear inverter torque commands.
- Coordinates electric motor traction torque delivery up to 450 Nm peak torque.
- Executes regenerative braking deceleration torque requests requested by BrakeControlSWC.
- Limits instantaneous torque output based on maximum allowable discharge and charge current limits from BatteryManagementSWC.
- MotorControlSWC depends on BatteryManagementSWC for high-voltage battery state of charge and thermal power limits.

5.3 Associated Interfaces
- Provided Interface: If_MotorTorque (Sender-Receiver)
- Required Interface: If_BrakeTorqueCommand (Sender-Receiver)
- Required Interface: If_BatteryState (Sender-Receiver)
- Required Interface: If_PowerDerateRequest (Client-Server)"""
    },
    {
        "page": 6,
        "title": "Software Component: BatteryManagementSWC",
        "section": "6. Software Component Specification: BatteryManagementSWC",
        "content": """6.1 Component Identification
- Component Name: BatteryManagementSWC
- Category: Application Software Component (ApplicationSWC)
- Safety Integrity Level: ASIL-C
- Execution Periodicity: 50ms cyclic runnable (Runnable_BatteryMonitor)

6.2 Functional Description & Responsibilities
BatteryManagementSWC oversees the 800V lithium-ion traction battery pack:
- Computes state of charge (SoC), state of health (SoH), and internal cell resistance.
- Monitors cell voltages (minimum 3.0V, maximum 4.2V) and multi-point pack temperature probes.
- Issues power derating warnings to MotorControlSWC when pack temperature exceeds 55 degrees Celsius.
- Controls main high-voltage pyrotechnic and electromechanical contactor isolation in emergency cutoff scenarios.

6.3 Associated Interfaces
- Provided Interface: If_BatteryState (Sender-Receiver)
- Provided Interface: If_PowerDerateRequest (Client-Server)
- Required Interface: If_DiagnosticService (Client-Server)"""
    },
    {
        "page": 7,
        "title": "Software Component: DiagnosticManagerSWC",
        "section": "7. Software Component Specification: DiagnosticManagerSWC",
        "content": """7.1 Component Identification
- Component Name: DiagnosticManagerSWC
- Category: Service Component / Complex Driver (ServiceSWC)
- Safety Integrity Level: ASIL-B
- Execution Periodicity: 100ms background runnable (Runnable_DiagnosticService)

7.2 Functional Description & Responsibilities
DiagnosticManagerSWC provides centralized diagnostic event logging, fault debouncing, and UDS ISO 14229 compliance:
- Collects diagnostic trouble codes (DTCs) from BrakeControlSWC, MotorControlSWC, and BatteryManagementSWC.
- Implements Client-Server interface If_DiagnosticService with operations SetDTCStatus(), GetFaultReport(), and ClearDTC().
- Freezes environmental freeze-frame telemetry upon detection of confirmed safety faults.
- Manages vehicle limp-home and fail-safe transitions when critical sensor loss occurs.

7.3 Associated Interfaces
- Provided Interface: If_DiagnosticService (Client-Server)
- Required Interface: If_VehicleSpeed (Sender-Receiver)"""
    },
    {
        "page": 8,
        "title": "Port Interfaces Specification",
        "section": "8. Detailed Port Interfaces & Communication Matrix",
        "content": """8.1 Sender-Receiver Port Interfaces
The following Sender-Receiver interfaces provide asynchronous data communication across the AUTOSAR RTE:

Interface: If_VehicleSpeed
- Interface Type: Sender-Receiver
- Direction: Provided by VehicleSpeedSWC, Required by BrakeControlSWC and DiagnosticManagerSWC
- Data Elements:
  * Sig_VehicleSpeed_kph (float32, 0.0 to 300.0 kph)
  * Sig_WheelSpeed_FL_rpm (uint16, 0 to 4000 rpm)
  * Sig_WheelSpeed_FR_rpm (uint16, 0 to 4000 rpm)

Interface: If_BrakeTorqueCommand
- Interface Type: Sender-Receiver
- Direction: Provided by BrakeControlSWC, Required by MotorControlSWC
- Data Elements:
  * Sig_TargetBrakeTorque_Nm (float32, -2000.0 to 0.0 Nm)
  * Sig_BrakePedalPosition_pct (uint8, 0 to 100 %)

Interface: If_MotorTorque
- Interface Type: Sender-Receiver
- Direction: Provided by MotorControlSWC, Required by BrakeControlSWC
- Data Elements:
  * Sig_ActualMotorTorque_Nm (float32, -2000.0 to +2000.0 Nm)
  * Sig_MotorTemp_degC (int16, -40 to +180 degC)

Interface: If_BatteryState
- Interface Type: Sender-Receiver
- Direction: Provided by BatteryManagementSWC, Required by MotorControlSWC
- Data Elements:
  * Sig_BatterySoC_pct (uint8, 0 to 100 %)
  * Sig_BatteryCurrent_A (float32, -600.0 to +600.0 A)
  * Sig_BatteryVoltage_V (float32, 500.0 to 900.0 V)"""
    },
    {
        "page": 9,
        "title": "Client-Server Interfaces Specification",
        "section": "9. Client-Server Operations & Service Interfaces",
        "content": """9.1 Client-Server Interfaces
Synchronous and client-server request-response operations are modeled via dedicated Client-Server interfaces:

Interface: If_DiagnosticService
- Interface Type: Client-Server
- Direction: Provided by DiagnosticManagerSWC, Required by BrakeControlSWC, MotorControlSWC, and BatteryManagementSWC
- Operations:
  * SetDTCStatus(in uint32 DTCNumber, in uint8 FaultStatus) -> uint8 ReturnCode
  * GetFaultReport(in uint32 DTCNumber, out FaultRecordStructure FaultRecord) -> uint8 ReturnCode
  * ClearDTC(in uint32 DTCGroup) -> uint8 ReturnCode

Interface: If_PowerDerateRequest
- Interface Type: Client-Server
- Direction: Provided by BatteryManagementSWC, Required by MotorControlSWC
- Operations:
  * RequestTorqueLimit(in float32 MaxAllowableTorque_Nm, in uint8 ReasonCode) -> boolean Acknowledged
  * GetCurrentDeratingStatus(out uint8 DerateState) -> void"""
    },
    {
        "page": 10,
        "title": "Signals and Data Elements Catalog",
        "section": "10. Signals and Data Dictionary",
        "content": """10.1 Global Signal Data Dictionary
The table below documents all active signals exchanged across the RTE:

Signal Name | Sender SWC | Receiver SWC | Data Type | Units | Range
Sig_VehicleSpeed_kph | VehicleSpeedSWC | BrakeControlSWC | float32 | kph | 0.0 - 300.0
Sig_WheelSpeed_FL_rpm | VehicleSpeedSWC | BrakeControlSWC | uint16 | rpm | 0 - 4000
Sig_WheelSpeed_FR_rpm | VehicleSpeedSWC | BrakeControlSWC | uint16 | rpm | 0 - 4000
Sig_TargetBrakeTorque_Nm | BrakeControlSWC | MotorControlSWC | float32 | Nm | -2000.0 - 0.0
Sig_BrakePedalPosition_pct | BrakeControlSWC | MotorControlSWC | uint8 | % | 0 - 100
Sig_ActualMotorTorque_Nm | MotorControlSWC | BrakeControlSWC | float32 | Nm | -2000.0 - 2000.0
Sig_MotorTemp_degC | MotorControlSWC | DiagnosticManagerSWC | int16 | degC | -40 - 180
Sig_BatterySoC_pct | BatteryManagementSWC | MotorControlSWC | uint8 | % | 0 - 100
Sig_BatteryCurrent_A | BatteryManagementSWC | MotorControlSWC | float32 | A | -600.0 - 600.0
Sig_BatteryVoltage_V | BatteryManagementSWC | MotorControlSWC | float32 | V | 500.0 - 900.0"""
    },
    {
        "page": 11,
        "title": "Architectural Dependencies & Functional Flows",
        "section": "11. Component Dependencies and Run-Time Interactions",
        "content": """11.1 Component Architectural Dependencies
The verified dependencies across software components are summarized below:
- BrakeControlSWC depends on VehicleSpeedSWC for accurate ground speed reference and anti-lock slip control.
- MotorControlSWC depends on BrakeControlSWC for regenerative braking torque setpoint coordination.
- MotorControlSWC depends on BatteryManagementSWC for maximum battery charge current and thermal derating limits.
- BrakeControlSWC calls DiagnosticManagerSWC to report ABS solenoid faults and pressure plausibility errors.
- BatteryManagementSWC calls DiagnosticManagerSWC to register cell over-voltage, thermal runaway, and insulation breakdown events.
- MotorControlSWC calls DiagnosticManagerSWC to report inverter over-temperature and phase short-circuit events.

11.2 Regenerative Braking Coordination Functional Flow
1. Driver depresses brake pedal. BrakeControlSWC samples pedal stroke via 10ms runnable.
2. BrakeControlSWC queries VehicleSpeedSWC to check if vehicle speed exceeds 5 kph.
3. BrakeControlSWC queries MotorControlSWC for available regen torque capacity.
4. If BatteryManagementSWC allows charging (SoC < 98% and pack temp < 50C), BrakeControlSWC commands negative regenerative torque to MotorControlSWC via If_BrakeTorqueCommand.
5. Remaining deceleration demand is fulfilled by the friction braking calipers."""
    },
    {
        "page": 12,
        "title": "System Integration & Safety Requirements",
        "section": "12. Integration, RTE Mapping, and ISO 26262 Requirements",
        "content": """12.1 RTE Task Scheduling & Task Allocation
- 5ms Periodic Task (OS_Task_5ms, Priority 30): Hosts MotorControlSWC Runnable_MotorTorqueControl.
- 10ms Periodic Task (OS_Task_10ms, Priority 25): Hosts VehicleSpeedSWC Runnable_CalculateSpeed and BrakeControlSWC Runnable_BrakeArbitration.
- 50ms Periodic Task (OS_Task_50ms, Priority 15): Hosts BatteryManagementSWC Runnable_BatteryMonitor.
- 100ms Periodic Task (OS_Task_100ms, Priority 10): Hosts DiagnosticManagerSWC Runnable_DiagnosticService.

12.2 Functional Safety & ISO 26262 Compliance
- BrakeControlSWC and MotorControlSWC are classified as ASIL-D safety items. Freedom from interference (FFI) is enforced via hardware Memory Protection Unit (MPU) partitioning.
- BatteryManagementSWC is classified as ASIL-C.
- VehicleSpeedSWC and DiagnosticManagerSWC are classified as ASIL-B.
- Watchdog Manager (WdgM) performs alive supervision on 5ms and 10ms tasks with a maximum fault reaction tolerance time (FRTT) of 20 milliseconds."""
    }
]

def generate_pdf(output_path: str):
    """Generates the synthetic AUTOSAR HLD document using reportlab or PyMuPDF."""
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(str(out_p), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#1E3A8A'))
        section_style = ParagraphStyle('DocSec', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#2563EB'))
        body_style = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#1F2937'))

        story = []
        for i, item in enumerate(SAMPLE_HLD_TEXT):
            story.append(Paragraph(item["title"], title_style))
            story.append(Spacer(1, 4))
            story.append(Paragraph(item["section"], section_style))
            story.append(Spacer(1, 8))

            # Split paragraphs
            paras = item["content"].split("\n\n")
            for p in paras:
                # Check for pseudo-table
                if "|" in p and "\n" in p:
                    rows = [r.split("|") for r in p.strip().split("\n")]
                    table_data = [[Paragraph(cell.strip(), body_style) for cell in row] for row in rows]
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                    ]))
                    story.append(t)
                else:
                    clean_p = p.replace("\n", "<br/>")
                    story.append(Paragraph(clean_p, body_style))
                story.append(Spacer(1, 6))

            if i < len(SAMPLE_HLD_TEXT) - 1:
                story.append(PageBreak())

        doc.build(story)
        print(f"Generated sample AUTOSAR HLD via ReportLab at: {out_p}")
        return True

    except Exception as e:
        print(f"ReportLab generation failed or not installed ({e}). Trying PyMuPDF...")
        try:
            import fitz
            doc = fitz.open()
            for item in SAMPLE_HLD_TEXT:
                page = doc.new_page(width=612, height=792)  # Letter
                # Insert title
                page.insert_text((40, 50), item["title"], fontsize=15, color=(0.1, 0.2, 0.5))
                page.insert_text((40, 75), item["section"], fontsize=11, color=(0.15, 0.4, 0.8))
                
                # Insert body
                rect = fitz.Rect(40, 95, 572, 750)
                page.insert_textbox(rect, item["content"], fontsize=9, color=(0.15, 0.15, 0.15))
            doc.save(str(out_p))
            doc.close()
            print(f"Generated sample AUTOSAR HLD via PyMuPDF at: {out_p}")
            return True
        except Exception as p_err:
            print(f"PyMuPDF generation failed ({p_err}).")
            return False

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "Sample_AUTOSAR_HLD.pdf"
    generate_pdf(out_file)
