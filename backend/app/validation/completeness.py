import uuid
from typing import Any, Dict, List, Optional
from app.models.library import Board, Peripheral
from app.models.validation import ValidationIssue
from app.validation.base import BaseValidator


class CompletenessValidator(BaseValidator):
    """Layer 1: Completeness Validation.
    Ensures that no open blocking fields remain and all mandatory architecture parameters
    are filled before engineering sign-off.
    """

    def validate(
        self,
        spec: Dict[str, Any],
        board: Optional[Board] = None,
        peripherals: Optional[List[Peripheral]] = None,
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        for sec_key, sec in spec.items():
            if not isinstance(sec, dict) or "fields" not in sec:
                continue

            for f_key, f_data in sec["fields"].items():
                if not isinstance(f_data, dict):
                    continue

                field_path = f"{sec_key}.{f_key}"
                state = f_data.get("state")
                val = f_data.get("value")

                # 1. Open field check (Blocking Error)
                if state == "open":
                    reason = f_data.get("override_reason") or "Parameter value required"
                    issues.append(
                        ValidationIssue(
                            id=f"comp-open-{uuid.uuid4().hex[:6]}",
                            layer="completeness",
                            severity="error",
                            field_path=field_path,
                            message=f"Mandatory field '{field_path}' is open: {reason}",
                        )
                    )

                # 2. Null value on non-open field (Warning)
                elif val is None and state != "open":
                    issues.append(
                        ValidationIssue(
                            id=f"comp-null-{uuid.uuid4().hex[:6]}",
                            layer="completeness",
                            severity="warning",
                            field_path=field_path,
                            message=f"Field '{field_path}' has null value. Verify if optional.",
                        )
                    )

        return issues
