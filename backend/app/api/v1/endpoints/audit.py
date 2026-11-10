from typing import List
from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user
from app.db.repositories.audit_repo import audit_repo
from app.db.repositories.project_repo import project_repo
from app.models.audit import AuditLogEntry, AuditLogListResponse
from app.models.auth import AuthUser

router = APIRouter(tags=["Audit & Governance"])


@router.get(
    "/projects/{project_id}/audit-logs",
    response_model=AuditLogListResponse,
)
def get_project_audit_logs(
    project_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: AuthUser = Depends(get_current_user),
) -> AuditLogListResponse:
    """Retrieve immutable audit logs for security, lifecycle confirmations, commands, and deployments."""
    # Verify access to project
    project_repo.get_project(project_id, current_user.id)
    items = audit_repo.list_logs_for_project(project_id, limit=limit)
    return AuditLogListResponse(total=len(items), items=items)
