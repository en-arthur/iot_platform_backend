from typing import List
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.db.repositories.proposal_repo import proposal_repo
from app.models.auth import AuthUser
from app.models.proposals import ProposalResolutionResponse, SpecProposal

router = APIRouter(prefix="/projects/{project_id}/proposals", tags=["Proposals"])


@router.get("", response_model=List[SpecProposal])
async def list_project_proposals(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> List[SpecProposal]:
    """Retrieve all pending and resolved AI proposals for a project."""
    return proposal_repo.list_proposals(project_id=project_id)


@router.post("/{proposal_id}/approve", response_model=ProposalResolutionResponse)
async def approve_proposal(
    project_id: str,
    proposal_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> ProposalResolutionResponse:
    """Approve AI proposal: applies changes to the spec as the user and mints a new version."""
    return proposal_repo.approve_proposal(
        project_id=project_id, proposal_id=proposal_id, user_id=current_user.id
    )


@router.post("/{proposal_id}/reject", response_model=ProposalResolutionResponse)
async def reject_proposal(
    project_id: str,
    proposal_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> ProposalResolutionResponse:
    """Reject AI proposal: dismisses without modifying the specification."""
    return proposal_repo.reject_proposal(
        project_id=project_id, proposal_id=proposal_id, user_id=current_user.id
    )
