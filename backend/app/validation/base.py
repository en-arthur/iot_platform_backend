from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.models.library import Board, Peripheral
from app.models.validation import ValidationIssue


class BaseValidator(ABC):
    """Abstract base validator for all 5 spec verification layers."""

    @abstractmethod
    def validate(
        self,
        spec: Dict[str, Any],
        board: Optional[Board] = None,
        peripherals: Optional[List[Peripheral]] = None,
    ) -> List[ValidationIssue]:
        """Performs validation checks and returns issues found in this layer."""
        pass
