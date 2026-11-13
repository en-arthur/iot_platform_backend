"""Supabase-backed persistence for projects, spec snapshots and generated files.

The repositories keep an in-memory cache so the API stays fast and works without
credentials, but every mutation is mirrored to Supabase when a real service-role
key is configured. On startup the cache is rehydrated from the database, so
projects survive Render restarts and appear in the Supabase tables.

Writes are best-effort: a database outage never fails an API request.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_PLACEHOLDER_VALUES = {
    "",
    "placeholder-service-role-key",
    "placeholder-anon-key",
    "https://example.supabase.co",
}


def _config() -> Optional[tuple[str, str]]:
    url = (settings.SUPABASE_URL or "").strip().rstrip("/")
    key = (settings.SUPABASE_SERVICE_ROLE_KEY or "").strip()
    if url in _PLACEHOLDER_VALUES or key in _PLACEHOLDER_VALUES:
        return None
    return url, key


def enabled() -> bool:
    """True when a usable Supabase URL + service role key are configured."""
    return _config() is not None


def _request(
    method: str,
    table: str,
    *,
    params: Optional[Dict[str, str]] = None,
    json: Any = None,
    prefer: Optional[str] = None,
) -> Any:
    cfg = _config()
    if not cfg:
        return None

    url, key = cfg
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer

    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.request(
                method,
                f"{url}/rest/v1/{table}",
                params=params,
                json=json,
                headers=headers,
            )
    except Exception as exc:  # pragma: no cover - network failure path
        logger.warning("Supabase %s %s failed: %s", method, table, exc)
        return None

    if response.status_code >= 300:
        logger.warning(
            "Supabase %s %s -> HTTP %s: %s",
            method,
            table,
            response.status_code,
            response.text[:300],
        )
        return None

    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def save_project(project: Any, current_spec: Optional[Dict[str, Any]] = None) -> None:
    """Upsert one project row (and its current spec) by id."""
    payload = {
        "id": project.id,
        "user_id": project.user_id,
        "name": project.name,
        "description": project.description,
        "board_id": project.board_id,
        "interface_type": project.interface_type,
        "lifecycle": project.lifecycle,
        "version": project.version,
        "deployed_version": project.deployed_version,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
    if current_spec is not None:
        payload["current_spec"] = current_spec

    _request(
        "POST",
        "projects",
        params={"on_conflict": "id"},
        json=payload,
        prefer="resolution=merge-duplicates,return=minimal",
    )


def delete_project(project_id: str) -> None:
    _request("DELETE", "projects", params={"id": f"eq.{project_id}"})


def save_spec_version(
    project_id: str,
    version_number: int,
    spec: Dict[str, Any],
    author: str,
    summary: str,
    diff: Optional[Dict[str, Any]] = None,
) -> None:
    payload = {
        "project_id": project_id,
        "version_number": version_number,
        "spec": spec,
        "author": author,
        "summary": summary,
    }
    if diff is not None:
        payload["diff"] = diff
    _request(
        "POST",
        "spec_versions",
        params={"on_conflict": "project_id,version_number"},
        json=payload,
        prefer="resolution=merge-duplicates,return=minimal",
    )


def replace_files(project_id: str, version_number: int, files: List[Any]) -> None:
    """Mirror the generated file set for a project (delete + insert)."""
    _request("DELETE", "generated_files", params={"project_id": f"eq.{project_id}"})
    if not files:
        return

    payload = [
        {
            "project_id": project_id,
            "version_number": version_number,
            "path": f.path,
            "content": f.content,
            "file_type": f.file_type,
            "is_protected": f.is_protected,
            "checksum": f.checksum,
        }
        for f in files
    ]
    _request("POST", "generated_files", json=payload, prefer="return=minimal")


def save_file(project_id: str, version_number: int, file_obj: Any) -> None:
    """Upsert one generated file (used for manual edits)."""
    _request(
        "POST",
        "generated_files",
        params={"on_conflict": "project_id,version_number,path"},
        json={
            "project_id": project_id,
            "version_number": version_number,
            "path": file_obj.path,
            "content": file_obj.content,
            "file_type": file_obj.file_type,
            "is_protected": file_obj.is_protected,
            "checksum": file_obj.checksum,
        },
        prefer="resolution=merge-duplicates,return=minimal",
    )


def _select(table: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
    rows = _request("GET", table, params=params)
    return rows if isinstance(rows, list) else []


def hydrate() -> int:
    """Load projects, specs, versions and files from Supabase into the caches."""
    if not enabled():
        logger.info("Supabase persistence disabled; using in-memory storage only")
        return 0

    from app.db.repositories.files_repo import files_repo
    from app.db.repositories.project_repo import project_repo
    from app.models.files import GeneratedFile
    from app.models.project import Project

    rows = _select("projects", {"select": "*", "order": "created_at.asc"})
    loaded = 0

    for row in rows:
        try:
            project = Project(**{k: row.get(k) for k in (
                "id",
                "user_id",
                "name",
                "description",
                "board_id",
                "interface_type",
                "lifecycle",
                "version",
                "deployed_version",
                "created_at",
                "updated_at",
            )})
        except Exception as exc:
            logger.warning("Skipping unreadable project row %s: %s", row.get("id"), exc)
            continue

        project_repo._projects[project.id] = project

        versions = _select(
            "spec_versions",
            {
                "select": "*",
                "project_id": f"eq.{project.id}",
                "order": "version_number.asc",
            },
        )
        records = []
        for v in versions:
            records.append(
                {
                    "version_number": v["version_number"],
                    "created_at": v.get("created_at") or project.created_at,
                    "author": v.get("author") or "Hardware Engineer",
                    "summary": v.get("summary") or "",
                    "lifecycle": project.lifecycle if v is versions[-1] else "confirmed",
                    "spec": v.get("spec") or {},
                    "diff": v.get("diff"),
                }
            )
        if records:
            project_repo._versions[project.id] = records

        current_spec = row.get("current_spec") or (records[-1]["spec"] if records else None)
        if current_spec:
            project_repo._specs[project.id] = current_spec

        file_rows = _select(
            "generated_files",
            {
                "select": "id,project_id,version_number,path,content,file_type,is_protected,checksum,created_at",
                "project_id": f"eq.{project.id}",
            },
        )
        if file_rows:
            files_repo._files[project.id] = {
                f["path"]: GeneratedFile(
                    id=str(f.get("id") or f"{project.id}-{f['path']}"),
                    project_id=project.id,
                    version_number=int(f.get("version_number") or project.version),
                    path=f["path"],
                    content=f.get("content") or "",
                    file_type=f.get("file_type") or "firmware",
                    is_protected=bool(f.get("is_protected")),
                    checksum=f.get("checksum") or "",
                    created_at=f.get("created_at") or project.created_at,
                )
                for f in file_rows
            }

        loaded += 1

    logger.info("Hydrated %s project(s) from Supabase", loaded)
    return loaded
