from typing import Any, Dict, List, Optional
from app.db.repositories.library_repo import library_repo
from app.models.library import Board, Peripheral
from app.models.validation import ValidationIssue, ValidationResponse
from app.validation.completeness import CompletenessValidator
from app.validation.electrical import ElectricalValidator
from app.validation.logical import LogicalValidator
from app.validation.resource import ResourceValidator
from app.validation.security import SecurityValidator


class ValidationEngine:
    """Orchestrates 5-layer spec validation:
    1. completeness
    2. electrical
    3. logical
    4. resource
    5. security
    """

    def __init__(self):
        self.validators = [
            CompletenessValidator(),
            ElectricalValidator(),
            LogicalValidator(),
            ResourceValidator(),
            SecurityValidator(),
        ]

    def validate_spec(
        self,
        spec: Dict[str, Any],
        board: Optional[Board] = None,
        peripherals: Optional[List[Peripheral]] = None,
    ) -> ValidationResponse:
        # Auto-resolve board from spec if not explicitly provided
        if not board:
            board_id = spec.get("hardware", {}).get("fields", {}).get("board_id", {}).get("value")
            if board_id:
                board = library_repo.get_board(str(board_id))

        all_issues: List[ValidationIssue] = []
        for validator in self.validators:
            issues = validator.validate(spec=spec, board=board, peripherals=peripherals)
            all_issues.extend(issues)

        error_count = sum(1 for i in all_issues if i.severity == "error")
        warning_count = sum(1 for i in all_issues if i.severity == "warning")
        info_count = sum(1 for i in all_issues if i.severity == "info")

        can_confirm = error_count == 0

        return ValidationResponse(
            issues=all_issues,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            can_confirm=can_confirm,
        )


validation_engine = ValidationEngine()
