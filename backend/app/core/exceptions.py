from typing import Any, List, Optional
from fastapi import HTTPException, status


class APIError(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        reasons: Optional[List[Any]] = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={"message": detail, "reasons": reasons or []} if reasons else detail,
        )


class UnauthorizedError(APIError):
    def __init__(self, detail: str = "Invalid or expired authentication token"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(APIError):
    def __init__(self, detail: str = "You do not have permission to access this resource"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundError(APIError):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(APIError):
    def __init__(self, detail: str = "Operation conflict", reasons: Optional[List[Any]] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            reasons=reasons,
        )


class SpecValidationError(APIError):
    def __init__(self, detail: str = "Spec validation failed", issues: Optional[List[Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            reasons=issues,
        )
