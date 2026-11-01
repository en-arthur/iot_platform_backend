from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from app.core.auth import get_current_user
from app.db.repositories.project_repo import project_repo
from app.models.auth import AuthUser
from app.models.project import Project, ProjectConfirmResponse, ProjectCreate
from app.models.spec import FieldPatchItem, SpecDiff, SpecVersionSummary

router = APIRouter(prefix="/projects", tags=["Projects & Spec Engine"])


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: AuthUser = Depends(get_current_user),
) -> Project:
    """Create a new IoT project and synthesize initial 12-section spec."""
    return project_repo.create_project(user_id=current_user.id, payload=payload)


@router.get("", response_model=List[Project])
async def list_projects(
    current_user: AuthUser = Depends(get_current_user),
) -> List[Project]:
    """Retrieve all projects belonging to the authenticated user."""
    return project_repo.list_projects(user_id=current_user.id)


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> Project:
    """Retrieve metadata and lifecycle for a specific project."""
    return project_repo.get_project(project_id=project_id, user_id=current_user.id)


@router.get("/{project_id}/spec", response_model=Dict[str, Any])
async def get_project_spec(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve the full 12-section specification single source of truth."""
    return project_repo.get_spec(project_id=project_id, user_id=current_user.id)


@router.patch("/{project_id}/spec/fields", response_model=Dict[str, Any])
async def patch_spec_fields(
    project_id: str,
    patches: List[FieldPatchItem],
    current_user: AuthUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Optimistically patch one or more specification fields and evaluate cross-section dependencies."""
    updated_spec, affected_sections = project_repo.patch_spec_fields(
        project_id=project_id, user_id=current_user.id, patches=patches
    )
    return {
        "spec": updated_spec,
        "affected_sections": affected_sections,
    }


@router.post("/{project_id}/spec/confirm", response_model=ProjectConfirmResponse)
async def confirm_spec(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> ProjectConfirmResponse:
    """Server-enforced confirmation gate: locks spec and creates new immutable version.
    Returns 409 Conflict if blocking open fields or errors remain.
    """
    return project_repo.confirm_spec(project_id=project_id, user_id=current_user.id)


@router.get("/{project_id}/versions", response_model=List[SpecVersionSummary])
async def list_spec_versions(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> List[SpecVersionSummary]:
    """List historical immutable versions for this project."""
    return project_repo.list_versions(project_id=project_id, user_id=current_user.id)


@router.get("/{project_id}/versions/{version_num}", response_model=Dict[str, Any])
async def get_spec_version(
    project_id: str,
    version_num: int,
    current_user: AuthUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve exact snapshot of specification at version N."""
    return project_repo.get_version(
        project_id=project_id, version_n=version_num, user_id=current_user.id
    )


@router.get("/{project_id}/versions/{version_a}/diff/{version_b}", response_model=SpecDiff)
async def get_spec_diff(
    project_id: str,
    version_a: int,
    version_b: int,
    current_user: AuthUser = Depends(get_current_user),
) -> SpecDiff:
    """Compute structured field-by-field diff between two spec versions."""
    return project_repo.get_diff(
        project_id=project_id,
        version_a=version_a,
        version_b=version_b,
        user_id=current_user.id,
    )
