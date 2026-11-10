import hashlib
from typing import Dict, List, Optional
from app.codegen.engine import codegen_engine
from app.core.exceptions import NotFoundError
from app.db.repositories.project_repo import project_repo
from app.models.files import GeneratedFile


class FilesRepository:
    """Manages synthesized code artifacts, manual developer edits, and storage persistence."""

    def __init__(self):
        # In-memory storage for test suites & session cache
        self._files: Dict[str, Dict[str, GeneratedFile]] = {}

    def list_files(self, project_id: str) -> List[GeneratedFile]:
        return list(self._files.get(project_id, {}).values())

    def get_file(self, project_id: str, path: str) -> Optional[GeneratedFile]:
        return self._files.get(project_id, {}).get(path)

    def save_file(self, project_id: str, file_obj: GeneratedFile):
        self._files.setdefault(project_id, {})[file_obj.path] = file_obj

    def update_file_content(self, project_id: str, path: str, new_content: str) -> GeneratedFile:
        file_obj = self.get_file(project_id, path)
        if not file_obj:
            raise NotFoundError(f"File '{path}' not found in project '{project_id}'")

        file_obj.content = new_content
        file_obj.is_protected = True
        file_obj.checksum = hashlib.sha256(new_content.encode("utf-8")).hexdigest()
        return file_obj

    def generate_project_code(
        self, project_id: str, user_id: str, scope: Optional[List[str]] = None
    ) -> List[GeneratedFile]:
        project = project_repo.get_project(project_id, user_id)
        spec = project_repo.get_spec(project_id, user_id)

        # Collect existing files to preserve protected user regions
        existing_map = {f.path: f.content for f in self.list_files(project_id)}

        generated = codegen_engine.generate_all(
            project_id=project_id,
            version=project.version,
            spec=spec,
            existing_files=existing_map,
            scope=scope,
        )

        for f in generated:
            self.save_file(project_id, f)

        # Update lifecycle to 'generated'
        project.lifecycle = "generated"

        # Record audit log
        from app.db.repositories.audit_repo import audit_repo
        audit_repo.record_action(
            action="CODE_GENERATE",
            user_id=user_id,
            project_id=project_id,
            payload={"files_count": len(generated), "scope": scope or ["firmware", "cloud", "interface"]},
        )

        return generated


files_repo = FilesRepository()
