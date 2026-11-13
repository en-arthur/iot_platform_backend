import copy
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.db import supabase_store
from app.models.project import Project, ProjectConfirmResponse, ProjectCreate
from app.models.spec import FieldPatchItem, SpecDiff, SpecVersionSummary
from app.models.validation import ValidationIssue
from app.services.spec_engine import SpecEngine
from app.validation.engine import validation_engine


class ProjectRepository:
    """Manages Project lifecycle, 12-section specs, versions, and confirmation gating."""

    def __init__(self):
        # In-memory storage for test suites and rapid development
        self._projects: Dict[str, Project] = {}
        self._specs: Dict[str, Dict[str, Any]] = {}
        self._versions: Dict[str, List[Dict[str, Any]]] = {}

        # Prepopulate demo project ONLY in development/test mode
        if getattr(settings, "ENVIRONMENT", "development") in ("development", "test"):
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

        # A deployment date supplied by the wizard satisfies the one mandatory
        # field that otherwise blocks the first confirmation.
        if getattr(payload, "target_deployment_date", None):
            fields = initial_spec.setdefault("metadata", {}).setdefault("fields", {})
            field = fields.get("target_deployment_date")
            if field is None:
                fields["target_deployment_date"] = {
                    "value": payload.target_deployment_date,
                    "state": "confirmed",
                    "source": "user",
                }
            else:
                field["value"] = payload.target_deployment_date
                field["state"] = "confirmed"
                field["source"] = "user"

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

        # Mirror to Supabase so the project survives redeploys.
        supabase_store.save_project(project, current_spec=initial_spec)
        supabase_store.save_spec_version(
            project_id=project_id,
            version_number=1,
            spec=initial_spec,
            author="Hardware Engineer",
            summary="Initial synthesized spec baseline (v1.0).",
        )
        return project

    def list_projects(self, user_id: str) -> List[Project]:
        """Lists projects owned by user. Never leaks demo projects in production."""
        is_dev = getattr(settings, "ENVIRONMENT", "development") in ("development", "test")
        return [
            p
            for p in self._projects.values()
            if p.user_id == user_id or (is_dev and p.user_id == "default-user")
        ]

    def get_project(self, project_id: str, user_id: str) -> Project:
        project = self._projects.get(project_id)
        if not project:
            raise NotFoundError(f"Project '{project_id}' not found")
        is_dev = getattr(settings, "ENVIRONMENT", "development") in ("development", "test")
        if project.user_id != user_id and not (is_dev and project.user_id == "default-user"):
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
        supabase_store.save_project(project, current_spec=current_spec)
        return current_spec, sorted(list(set(all_affected)))

    def validate_spec(self, project_id: str, user_id: str) -> List[ValidationIssue]:
        project = self.get_project(project_id, user_id)
        spec = self.get_spec(project_id, user_id)
        val_res = validation_engine.validate_spec(spec)

        # Update lifecycle to validated if no errors, or draft if errors exist
        lifecycle_before = project.lifecycle
        if val_res.can_confirm and project.lifecycle == "draft":
            project.lifecycle = "validated"
        elif not val_res.can_confirm and project.lifecycle == "validated":
            project.lifecycle = "draft"

        if project.lifecycle != lifecycle_before:
            supabase_store.save_project(project, current_spec=spec)

        return val_res.issues

    def confirm_spec(self, project_id: str, user_id: str) -> ProjectConfirmResponse:
        """Enforces SERVER-SIDE confirmation gate: rejected (409 Conflict) if any open field or error issue exists."""
        project = self.get_project(project_id, user_id)
        spec = self.get_spec(project_id, user_id)

        # 1. Run 5-layer validation
        val_res = validation_engine.validate_spec(spec)
        blocking_errors = [i for i in val_res.issues if i.severity == "error"]

        # 2. Check for open blocking fields
        open_fields = SpecEngine.get_open_blocking_fields(spec)
        for f in open_fields:
            if not any(i.field_path == f for i in blocking_errors):
                blocking_errors.append(
                    ValidationIssue(
                        id=f"comp-open-{f}",
                        layer="completeness",
                        severity="error",
                        field_path=f,
                        message=f"Field '{f}' is open and must be completed before confirmation.",
                    )
                )

        if blocking_errors:
            raise ConflictError(
                detail=f"Cannot confirm spec: {len(blocking_errors)} error-level issue(s) require resolution",
                reasons=[f"[{i.layer.upper()}] {i.field_path}: {i.message}" for i in blocking_errors],
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

        supabase_store.save_project(project, current_spec=spec)
        supabase_store.save_spec_version(
            project_id=project_id,
            version_number=new_version_num,
            spec=spec,
            author="Hardware Engineer",
            summary=f"Confirmed specification sign-off (v{new_version_num}.0).",
            diff=diff.model_dump(),
        )

        # Audit log entry
        from app.db.repositories.audit_repo import audit_repo
        audit_repo.record_action(
            action="SPEC_CONFIRM",
            user_id=user_id,
            project_id=project_id,
            payload={"version": new_version_num, "status": "confirmed"},
        )

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

    def delete_project(self, project_id: str, user_id: str) -> None:
        """Permanently delete a project and all associated specs, versions, and data."""
        project = self.get_project(project_id, user_id)
        # Prevent deleting demo projects via the API
        if project.user_id == "default-user":
            raise ForbiddenError("Cannot delete demo projects")
        self._projects.pop(project_id, None)
        self._specs.pop(project_id, None)
        self._versions.pop(project_id, None)
        supabase_store.delete_project(project_id)


project_repo = ProjectRepository()
