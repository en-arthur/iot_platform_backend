import uuid
from typing import Any, Dict, List, Optional
from app.models.library import Board, Peripheral
from app.models.validation import ValidationIssue
from app.validation.base import BaseValidator


class LogicalValidator(BaseValidator):
    """Layer 3: Logical & Contract Consistency Verification.
    Verifies that interface controls strictly map to declared behavior commands,
    widgets bind to valid data model fields, and thresholds maintain mathematical consistency.
    """

    def validate(
        self,
        spec: Dict[str, Any],
        board: Optional[Board] = None,
        peripherals: Optional[List[Peripheral]] = None,
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        behavior_fields = spec.get("behavior", {}).get("fields", {})
        data_model_fields = spec.get("data_model", {}).get("fields", {})
        interface_fields = spec.get("interface", {}).get("fields", {})

        # Extract declared behavior commands
        declared_commands_field = behavior_fields.get("declared_commands", {})
        declared_commands = set(declared_commands_field.get("value") or [])

        # Extract declared metrics
        metrics_field = data_model_fields.get("metrics", {})
        declared_metrics: List[Dict[str, Any]] = metrics_field.get("value") or []
        declared_metric_names = {m.get("name") for m in declared_metrics if isinstance(m, dict)}

        # 1. Interface Control Command Mapping Rule:
        # Every web app control must map to a command declared in the behavior section.
        widgets = interface_fields.get("widgets", {}).get("value") or []
        for widget in widgets:
            if not isinstance(widget, dict):
                continue

            command = widget.get("command")
            if command and command not in declared_commands:
                issues.append(
                    ValidationIssue(
                        id=f"log-undeclared-cmd-{uuid.uuid4().hex[:6]}",
                        layer="logical",
                        severity="error",
                        field_path="interface.widgets",
                        message=f"Interface widget '{widget.get('id')}' references command '{command}' which is not declared in behavior.declared_commands.",
                    )
                )

            metric = widget.get("metric")
            if metric and metric not in declared_metric_names:
                issues.append(
                    ValidationIssue(
                        id=f"log-missing-metric-{uuid.uuid4().hex[:6]}",
                        layer="logical",
                        severity="error",
                        field_path="interface.widgets",
                        message=f"Interface widget '{widget.get('id')}' references metric '{metric}' which does not exist in data_model.metrics.",
                    )
                )

        # 2. Threshold Sanity Check
        high_temp = behavior_fields.get("high_temperature_threshold_c", {}).get("value")
        urgent_temp = behavior_fields.get("urgent_alert_threshold_c", {}).get("value")
        if high_temp is not None and urgent_temp is not None:
            if float(urgent_temp) <= float(high_temp):
                issues.append(
                    ValidationIssue(
                        id=f"log-threshold-order-{uuid.uuid4().hex[:6]}",
                        layer="logical",
                        severity="warning",
                        field_path="behavior.urgent_alert_threshold_c",
                        message=f"Urgent alert threshold ({urgent_temp}°C) is less than or equal to warning threshold ({high_temp}°C).",
                    )
                )

        # 3. Sampling Rate Sanity
        sampling_hz = behavior_fields.get("telemetry_sampling_rate_hz", {}).get("value")
        if sampling_hz is not None and float(sampling_hz) > 20.0:
            issues.append(
                ValidationIssue(
                    id=f"log-sampling-rate-{uuid.uuid4().hex[:6]}",
                    layer="logical",
                    severity="warning",
                    field_path="behavior.telemetry_sampling_rate_hz",
                    message=f"Sampling frequency ({sampling_hz} Hz) is unusually high for I2C environmental sensing and may degrade power efficiency.",
                )
            )

        return issues
