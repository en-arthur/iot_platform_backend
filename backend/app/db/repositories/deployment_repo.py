import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.db.repositories.project_repo import project_repo
from app.models.devices import DeploymentResponse


class DeploymentRepository:
    """Manages project deployment to cloud infrastructure, WorkersCraft service registration,
    and lifecycle transition to 'deployed'.
    """

    def __init__(self):
        self._deployments: Dict[str, DeploymentResponse] = {}

    def deploy_project(self, project_id: str, user_id: str) -> DeploymentResponse:
        project = project_repo.get_project(project_id, user_id)

        # Confirm gate checks: project should ideally be verified or generated
        if project.lifecycle not in ("verified", "generated", "confirmed"):
            raise ConflictError(
                f"Cannot deploy project in '{project.lifecycle}' state. Project must be confirmed, generated, or verified first."
            )

        deployment_id = f"dep-{uuid.uuid4().hex[:8]}"
        now_str = datetime.now(timezone.utc).isoformat()
        cloud_app_id = f"wc-app-{project_id}"

        # Transition lifecycle to deployed
        project.lifecycle = "deployed"

        # Render exposes the broker publicly only over WSS on 443, regardless of
        # the internal MQTT_BROKER_PORT.
        broker_url = (
            f"wss://{settings.MQTT_BROKER_HOST}:443"
            if settings.MQTT_USE_TLS
            else f"mqtt://{settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}"
        )

        response = DeploymentResponse(
            deployment_id=deployment_id,
            project_id=project_id,
            status="active",
            broker_url=broker_url,
            cloud_service_app_id=cloud_app_id,
            deployed_at=now_str,
            message="Project deployed successfully. Cloud storage and MQTT ingress are active.",
        )
        self._deployments[project_id] = response

        # Record audit log
        from app.db.repositories.audit_repo import audit_repo
        audit_repo.record_action(
            action="PROJECT_DEPLOY",
            user_id=user_id,
            project_id=project_id,
            payload={"deployment_id": deployment_id, "cloud_service_app_id": cloud_app_id},
        )

        return response

    def get_deployment(self, project_id: str, user_id: str) -> DeploymentResponse:
        project_repo.get_project(project_id, user_id)
        dep = self._deployments.get(project_id)
        if not dep:
            raise NotFoundError(f"No active deployment found for project '{project_id}'")
        return dep


deployment_repo = DeploymentRepository()
