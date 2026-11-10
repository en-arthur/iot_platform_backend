import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.models.audit import AuditLogEntry


class AuditRepository:
    """Manages system audit logging across security and governance events:
    SPEC_CONFIRM, CODE_GENERATE, VERIFICATION_RUN, DEVICE_PROVISION,
    DEVICE_COMMAND, and PROJECT_DEPLOY.
    """

    def __init__(self):
        self._logs: List[AuditLogEntry] = []

    def record_action(
        self,
        action: str,
        user_id: str,
        project_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            id=f"aud-{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            project_id=project_id,
            action=action,
            payload=payload or {},
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._logs.append(entry)
        return entry

    def list_logs_for_project(
        self, project_id: str, limit: int = 100
    ) -> List[AuditLogEntry]:
        matched = [log for log in self._logs if log.project_id == project_id]
        return matched[-limit:]

    def list_all_logs(self, limit: int = 100) -> List[AuditLogEntry]:
        return self._logs[-limit:]


audit_repo = AuditRepository()
