import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.db import supabase_store
from app.db.repositories.project_repo import project_repo
from app.models.proposals import ProposalResolutionResponse, SpecChangeItem, SpecProposal
from app.models.spec import FieldPatchItem


class ProposalRepository:
    """Manages AI-generated spec proposals and human engineer approval / rejection."""

    def __init__(self):
        # In-memory storage for test suites & session cache
        self._proposals: Dict[str, Dict[str, SpecProposal]] = {}

        # Seed pre-existing demo proposal for 'proj-greenhouse-01' ONLY in development/test
        if getattr(settings, "ENVIRONMENT", "development") in ("development", "test"):
            demo_proj = "proj-greenhouse-01"
            self._proposals[demo_proj] = {
                "prop-fix-pin-conflict": SpecProposal(
                    proposal_id="prop-fix-pin-conflict",
                    project_id=demo_proj,
                    summary="Remap manual override button from GPIO4 to GPIO10 to eliminate I2C bus collision.",
                    changes=[
                        SpecChangeItem(
                            path="peripherals.button_pin",
                            old="GPIO4",
                            new="GPIO10",
                            reason="Resolve pin multiplexing conflict with BME280 I2C SDA on GPIO4.",
                        ),
                        SpecChangeItem(
                            path="metadata.target_deployment_date",
                            old=None,
                            new="2026-12-01",
                            reason="Resolve open blocking deployment date parameter.",
                        ),
                    ],
                    status="pending",
                )
            }

    def create_proposal(
        self,
        project_id: str,
        summary: str,
        changes: List[SpecChangeItem],
    ) -> SpecProposal:
        proposal_id = f"prop-{uuid.uuid4().hex[:8]}"
        proposal = SpecProposal(
            proposal_id=proposal_id,
            project_id=project_id,
            summary=summary,
            changes=changes,
            status="pending",
        )
        self._proposals.setdefault(project_id, {})[proposal_id] = proposal
        return proposal

    def list_proposals(self, project_id: str) -> List[SpecProposal]:
        return list(self._proposals.get(project_id, {}).values())

    def get_proposal(self, project_id: str, proposal_id: str) -> Optional[SpecProposal]:
        return self._proposals.get(project_id, {}).get(proposal_id)

    def approve_proposal(
        self, project_id: str, proposal_id: str, user_id: str
    ) -> ProposalResolutionResponse:
        """Approves proposal, applies proposed field mutations as the user, and creates a new version."""
        proposal = self.get_proposal(project_id, proposal_id)
        if not proposal:
            raise NotFoundError(f"Proposal '{proposal_id}' not found for project '{project_id}'")

        if proposal.status != "pending":
            return ProposalResolutionResponse(
                success=False,
                proposal_id=proposal_id,
                status=proposal.status,
                message=f"Proposal is already {proposal.status}.",
            )

        # 1. Transform proposal changes into FieldPatchItems
        patches = [
            FieldPatchItem(
                path=ch.path,
                value=ch.new,
                state="confirmed",
                override_reason=ch.reason,
            )
            for ch in proposal.changes
        ]

        # 2. Apply patches to spec via ProjectRepository
        project_repo.patch_spec_fields(project_id=project_id, user_id=user_id, patches=patches)

        # 3. Mark proposal as approved
        proposal.status = "approved"
        proposal.resolved_at = datetime.now(timezone.utc).isoformat()

        # 4. Mint a new version reflecting approved AI proposal
        project = project_repo.get_project(project_id, user_id)
        new_version = project.version + 1
        project.version = new_version
        project.updated_at = datetime.now(timezone.utc).isoformat()

        # Archive version record
        spec = project_repo.get_spec(project_id, user_id)
        summary = f"Applied proposal {proposal_id}: {proposal.summary}"
        author = "AI Assistant (Approved by Engineer)"
        project_repo._versions[project_id].append(
            {
                "version_number": new_version,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "author": author,
                "summary": summary,
                "lifecycle": project.lifecycle,
                "spec": spec,
            }
        )

        # Mirror the approval to Supabase so the new version and the bumped
        # project version survive a redeploy.
        supabase_store.save_project(project, current_spec=spec)
        supabase_store.save_spec_version(
            project_id=project_id,
            version_number=new_version,
            spec=spec,
            author=author,
            summary=summary,
        )

        return ProposalResolutionResponse(
            success=True,
            proposal_id=proposal_id,
            status="approved",
            new_version=new_version,
            message="Proposal approved and applied to specification.",
        )

    def reject_proposal(
        self, project_id: str, proposal_id: str, user_id: str
    ) -> ProposalResolutionResponse:
        proposal = self.get_proposal(project_id, proposal_id)
        if not proposal:
            raise NotFoundError(f"Proposal '{proposal_id}' not found for project '{project_id}'")

        proposal.status = "rejected"
        proposal.resolved_at = datetime.now(timezone.utc).isoformat()

        return ProposalResolutionResponse(
            success=True,
            proposal_id=proposal_id,
            status="rejected",
            message="Proposal rejected. No changes made to specification.",
        )


proposal_repo = ProposalRepository()
