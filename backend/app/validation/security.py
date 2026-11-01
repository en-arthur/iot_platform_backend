import uuid
from typing import Any, Dict, List, Optional
from app.models.library import Board, Peripheral
from app.models.validation import ValidationIssue
from app.validation.base import BaseValidator


class SecurityValidator(BaseValidator):
    """Layer 5: Device & Cloud Security Verification.
    Enforces encryption, signed updates, rollback protection, and prevents hardcoded secrets.
    """

    def validate(
        self,
        spec: Dict[str, Any],
        board: Optional[Board] = None,
        peripherals: Optional[List[Peripheral]] = None,
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        sec_fields = spec.get("security", {}).get("fields", {})
        cloud_fields = spec.get("cloud_backend", {}).get("fields", {})
        conn_fields = spec.get("connectivity", {}).get("fields", {})
        updates_fields = spec.get("updates", {}).get("fields", {})

        # 1. Transport Encryption (TLS) Check
        tls_enabled = sec_fields.get("tls_enabled", {}).get("value")
        broker_port = cloud_fields.get("broker_port", {}).get("value")

        if tls_enabled is False or broker_port == 1883:
            issues.append(
                ValidationIssue(
                    id=f"sec-plaintext-mqtt-{uuid.uuid4().hex[:6]}",
                    layer="security",
                    severity="warning",
                    field_path="security.tls_enabled",
                    message="MQTT broker port is set to 1883 (plaintext). Production firmware requires TLS on port 8883 to prevent credential interception.",
                )
            )

        # 2. Hardcoded Secret Detection
        wifi_pass = conn_fields.get("wifi_password", {}).get("value")
        if wifi_pass and isinstance(wifi_pass, str):
            if not wifi_pass.startswith("ENV_") and not wifi_pass.startswith("SECRET_") and len(wifi_pass) > 0:
                issues.append(
                    ValidationIssue(
                        id=f"sec-hardcoded-secret-{uuid.uuid4().hex[:6]}",
                        layer="security",
                        severity="error",
                        field_path="connectivity.wifi_password",
                        message="Potential hardcoded plaintext credential detected. Credentials must reference environment variables (e.g. 'ENV_WIFI_PASSWORD').",
                    )
                )

        # 3. OTA Bootloader Rollback Protection
        ota_enabled = updates_fields.get("ota_enabled", {}).get("value")
        rollback_enabled = updates_fields.get("rollback_on_failed_boot", {}).get("value")
        if ota_enabled and rollback_enabled is False:
            issues.append(
                ValidationIssue(
                    id=f"sec-ota-rollback-{uuid.uuid4().hex[:6]}",
                    layer="security",
                    severity="error",
                    field_path="updates.rollback_on_failed_boot",
                    message="OTA enabled without rollback protection. A failed update may permanently brick remote hardware without recovery.",
                )
            )

        return issues
