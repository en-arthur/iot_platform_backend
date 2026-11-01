from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

SpecFieldState = Literal["confirmed", "defaulted", "inferred", "open", "from_library"]
SpecFieldSource = Literal["user", "platform_default", "ai", "library"]


class SpecField(BaseModel):
    value: Any = None
    state: SpecFieldState = "defaulted"
    source: SpecFieldSource = "platform_default"
    override_reason: Optional[str] = None


# =============================================================================
# 12 SPEC SECTIONS MODELS
# Every field in the 12 sections is a SpecField instance.
# =============================================================================

class MetadataSection(BaseModel):
    title: str = "1. Project Metadata"
    fields: Dict[str, SpecField] = Field(default_factory=dict)


class HardwareSection(BaseModel):
    title: str = "2. Hardware Platform & Power"
    fields: Dict[str, SpecField] = Field(default_factory=dict)


class PeripheralsSection(BaseModel):
    title: str = "3. Peripherals & Pin Multiplexing"
    fields: Dict[str, SpecField] = Field(default_factory=dict)


class BehaviorSection(BaseModel):
    title: str = "4. Runtime Behavior & State Machine"
    fields: Dict[str, SpecField] = Field(default_factory=dict)


class DataModelSection(BaseModel):
    title: str = "5. Telemetry & Data Model"
    fields: Dict[str, SpecField] = Field(default_factory=dict)


class ConnectivitySection(BaseModel):
    title: str = "6. Connectivity & Protocols"
    fields: Dict[str, SpecField] = Field(default_factory=dict)


class CloudBackendSection(BaseModel):
    title: str = "7. Cloud Backend & Telemetry Ingestion"
    fields: Dict[str, SpecField] = Field(default_factory=dict)


class InterfaceSection(BaseModel):
    title: str = "8. Web/App Interface & Dashboards"
    fields: Dict[str, SpecField] = Field(default_factory=dict)


class SecuritySection(BaseModel):
    title: str = "9. Device Security & Identity"
    fields: Dict[str, SpecField] = Field(default_factory=dict)


class UpdatesSection(BaseModel):
    title: str = "10. Updates & Lifecycle (OTA)"
    fields: Dict[str, SpecField] = Field(default_factory=dict)


class VerificationSection(BaseModel):
    title: str = "11. Verification Contracts & Pinout Rules"
    fields: Dict[str, SpecField] = Field(default_factory=dict)


class ProvenanceSection(BaseModel):
    title: str = "12. Audit Provenance & Export Gate"
    fields: Dict[str, SpecField] = Field(default_factory=dict)


class ProjectSpec(BaseModel):
    metadata: MetadataSection = Field(default_factory=MetadataSection)
    hardware: HardwareSection = Field(default_factory=HardwareSection)
    peripherals: PeripheralsSection = Field(default_factory=PeripheralsSection)
    behavior: BehaviorSection = Field(default_factory=BehaviorSection)
    data_model: DataModelSection = Field(default_factory=DataModelSection)
    connectivity: ConnectivitySection = Field(default_factory=ConnectivitySection)
    cloud_backend: CloudBackendSection = Field(default_factory=CloudBackendSection)
    interface: InterfaceSection = Field(default_factory=InterfaceSection)
    security: SecuritySection = Field(default_factory=SecuritySection)
    updates: UpdatesSection = Field(default_factory=UpdatesSection)
    verification: VerificationSection = Field(default_factory=VerificationSection)
    provenance: ProvenanceSection = Field(default_factory=ProvenanceSection)


# =============================================================================
# PATCH & DIFF SCHEMAS
# =============================================================================

class FieldPatchItem(BaseModel):
    path: str  # e.g. "peripherals.bme280_sda_pin"
    value: Any
    state: SpecFieldState = "confirmed"
    override_reason: Optional[str] = None


class SpecDiffItem(BaseModel):
    path: str
    old: Any
    new: Any
    reason: Optional[str] = None


class SpecDiff(BaseModel):
    version_a: int
    version_b: int
    changes: List[SpecDiffItem] = Field(default_factory=list)


class SpecVersionSummary(BaseModel):
    version_number: int
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    author: str
    summary: str
    lifecycle: str = "confirmed"


class SpecVersionDetail(SpecVersionSummary):
    spec: Dict[str, Any]
    diff: Optional[Dict[str, Any]] = None
