import copy
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.project import Project, ProjectConfirmResponse, ProjectCreate
from app.models.spec import FieldPatchItem, SpecDiff, SpecVersionSummary
from app.services.spec_engine import SpecEngine


class ProjectRepository:
    """Manages Project lifecycle, 12-section specs, versions, and confirmation gating."""

    def __init__(self):
        # In-memory storage for test suites and rapid development
        self._projects: Dict[str, Project] = {}
        self._specs: Dict[str, Dict[str, Any]] = {}
        self._versions: Dict[str, List[Dict[str, Any]]] = {}

        # Prepopulate demo project for immediate testing/parity with frontend
        demo_id = "proj-greenhouse-01"
        demo_proj = Project(
            id=demo_id,
            user_id="default-user",
            name="Solar LoRaWAN Soil Moisture Array",
            description="Long-range ultra low-power moisture sensing array with capacitive probes, deep sleep cycles, and LoRaWAN/MQTT telemetry.",
            board_id="esp32-s3-devkitc-1",
            interface_type="dashboard",
            lifecycle="draft",
            version=1,
            deployed_version="v1.0",
        )
        self._projects[demo_id] = demo_proj
        demo_spec = SpecEngine.create_default_spec(
            ProjectCreate(
                name=demo_proj.name,
                description=demo_proj.description,
                board_id=demo_proj.board_id,
                interface_type=demo_proj.interface_type,
            )
        )
        self._specs[demo_id] = demo_spec
        self._versions[demo_id] = [
            {
                "version_number": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "author": "Hardware Engineer",
                "summary": "Initial synthesized baseline specification (v1.0).",
                "lifecycle": "draft",
                "spec": copy.deepcopy(demo_spec),
            }
        ]

    def create_project(self, user_id: str, payload: ProjectCreate) -> Project:
        project_id = f"proj-{uuid.uuid4().hex[:8]}"
        project = Project(
            id=project_id,
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            board_id=payload.board_id,
            interface_type=payload.interface_type,
            lifecycle="draft",
            version=1,
            deployed_version="v1.0",
        )
        self._projects[project_id] = project

        # Synthesize initial 12-section spec
        initial_spec = SpecEngine.create_default_spec(payload)
        self._specs[project_id] = initial_spec

        # Create version 1 baseline
        self._versions[project_id] = [
            {
                "version_number": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "author": "Hardware Engineer",
                "summary": "Initial synthesized spec baseline (v1.0).",
                "lifecycle": "draft",
                "spec": copy.deepcopy(initial_spec),
            }
        ]
        return project

    def list_projects(self, user_id: str) -> List[Project]:
        """Lists projects owned by user, plus demo projects in dev mode."""
        return [
            p
            for p in self._projects.values()
            if p.user_id == user_id or p.user_id == "default-user"
        ]

    def get_project(self, project_id: str, user_id: str) -> Project:
        project = self._projects.get(project_id)
        if not project:
            raise NotFoundError(f"Project '{project_id}' not found")
        if project.user_id != user_id and project.user_id != "default-user":
            raise ForbiddenError("You do not have access to this project")
        return project

    def get_spec(self, project_id: str, user_id: str) -> Dict[str, Any]:
        self.get_project(project_id, user_id)
        spec = self._specs.get(project_id)
        if not spec:
            raise NotFoundError(f"Spec for project '{project_id}' not found")
        return spec

    def patch_spec_fields(
        self, project_id: str, user_id: str, patches: List[FieldPatchItem]
    ) -> Tuple[Dict[str, Any], List[str]]:
        project = self.get_project(project_id, user_id)
        current_spec = self.get_spec(project_id, user_id)

        all_affected: List[str] = []
        for patch in patches:
            current_spec, affected = SpecEngine.patch_field(
                current_spec,
                path=patch.path,
                value=patch.value,
                state=patch.state,
                override_reason=patch.override_reason,
            )
            all_affected.extend(affected)

        # Edits to a project always return it to draft lifecycle
        project.lifecycle = "draft"
        project.updated_at = datetime.now(timezone.utc).isoformat()
        return current_spec, sorted(list(set(all_affected)))

    def confirm_spec(self, project_id: str, user_id: str) -> ProjectConfirmResponse:
        """Enforces SERVER-SIDE confirmation gate: rejected (409 Conflict) if any open field exists."""
        project = self.get_project(project_id, user_id)
        spec = self.get_spec(project_id, user_id)

        # Check for open blocking fields
        open_fields = SpecEngine.get_open_blocking_fields(spec)
        if open_fields:
            raise ConflictError(
                detail=f"Cannot confirm spec: {len(open_fields)} open blocking field(s) require resolution",
                reasons=[f"Field '{f}' is open and must be completed" for f in open_fields],
            )

        # Successful confirmation: transition lifecycle and mint new immutable version
        new_version_num = project.version + 1
        project.version = new_version_num
        project.lifecycle = "confirmed"
        project.updated_at = datetime.now(timezone.utc).isoformat()

        # Archive confirmed version
        previous_spec = self._versions[project_id][-1]["spec"]
        diff = SpecEngine.compute_diff(
            previous_spec, spec, version_a=project.version - 1, version_b=new_version_num
        )

        version_record = {
            "version_number": new_version_num,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "author": "Hardware Engineer",
            "summary": f"Confirmed specification sign-off (v{new_version_num}.0).",
            "lifecycle": "confirmed",
            "spec": copy.deepcopy(spec),
            "diff": diff.model_dump(),
        }
        self._versions[project_id].append(version_record)

        return ProjectConfirmResponse(
            success=True,
            lifecycle="confirmed",
            version=new_version_num,
            message="Spec confirmed and locked for firmware generation.",
        )

    def list_versions(self, project_id: str, user_id: str) -> List[SpecVersionSummary]:
        self.get_project(project_id, user_id)
        records = self._versions.get(project_id, [])
        return [
            SpecVersionSummary(
                version_number=r["version_number"],
                created_at=r["created_at"],
                author=r["author"],
                summary=r["summary"],
                lifecycle=r.get("lifecycle", "confirmed"),
            )
            for r in reversed(records)
        ]

    def get_version(self, project_id: str, version_n: int, user_id: str) -> Dict[str, Any]:
        self.get_project(project_id, user_id)
        records = self._versions.get(project_id, [])
        for r in records:
            if r["version_number"] == version_n:
                return r
        raise NotFoundError(f"Version '{version_n}' not found for project '{project_id}'")

    def get_diff(self, project_id: str, version_a: int, version_b: int, user_id: str) -> SpecDiff:
        rec_a = self.get_version(project_id, version_a, user_id)
        rec_b = self.get_version(project_id, version_b, user_id)
        return SpecEngine.compute_diff(
            rec_a["spec"], rec_b["spec"], version_a=version_a, version_b=version_b
        )


project_repo = ProjectRepository()
