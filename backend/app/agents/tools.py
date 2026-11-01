import json
from typing import Any, Dict, List
from app.db.repositories.library_repo import library_repo
from app.db.repositories.project_repo import project_repo
from app.validation.engine import validation_engine


class ReadOnlyAgentTools:
    """Read-only tools for AI agents.
    HARD RULE: Agents never write directly to the spec.
    They only read specs, query the hardware library, and run validation.
    """

    @staticmethod
    def library_lookup(query: str, component_type: str = "peripheral") -> Dict[str, Any]:
        """Look up verified boards or peripherals from the hardware library.
        Facts (pins, voltages, addresses) must come ONLY from this library.
        """
        if component_type == "board":
            boards = library_repo.list_boards(include_all=True)
            matched = [b.model_dump() for b in boards if query.lower() in b.name.lower() or query.lower() in b.id]
            return {"boards": matched}
        else:
            peripherals = library_repo.list_peripherals(query=query)
            return {"peripherals": [p.model_dump() for p in peripherals]}

    @staticmethod
    def get_spec(project_id: str) -> Dict[str, Any]:
        """Read current 12-section project specification."""
        try:
            return project_repo.get_spec(project_id=project_id, user_id="default-user")
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def validate_spec(project_id: str) -> Dict[str, Any]:
        """Run 5-layer verification on project spec and return current issues."""
        try:
            spec = project_repo.get_spec(project_id=project_id, user_id="default-user")
            res = validation_engine.validate_spec(spec)
            return res.model_dump()
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def list_versions(project_id: str) -> List[Dict[str, Any]]:
        """List historical spec versions for context."""
        try:
            versions = project_repo.list_versions(project_id=project_id, user_id="default-user")
            return [v.model_dump() for v in versions]
        except Exception as e:
            return [{"error": str(e)}]

    @staticmethod
    def read_run_logs(run_id: str) -> str:
        """Read compiler or verification test logs for debugging."""
        return f"Mock build logs for verification run '{run_id}': No compilation faults detected."
