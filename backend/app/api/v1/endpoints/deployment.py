from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.db.repositories.deployment_repo import deployment_repo
from app.models.auth import AuthUser
from app.models.devices import DeploymentResponse

router = APIRouter(tags=["Deployment"])


@router.post(
    "/projects/{project_id}/deploy",
    response_model=DeploymentResponse,
)
def deploy_project(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> DeploymentResponse:
    """Deploy project infrastructure, register cloud service tenant, and transition lifecycle to 'deployed'."""
    return deployment_repo.deploy_project(project_id, current_user.id)


@router.get(
    "/projects/{project_id}/deployment",
    response_model=DeploymentResponse,
)
def get_deployment_status(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> DeploymentResponse:
    """Get status of active deployment for a project."""
    return deployment_repo.get_deployment(project_id, current_user.id)
