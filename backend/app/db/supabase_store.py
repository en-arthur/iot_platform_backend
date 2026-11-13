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
    strict: bool = False,
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
        if strict:
            raise RuntimeError(
                f"Supabase {method} {table} failed with HTTP {response.status_code}"
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

    try:
        _request(
            "POST",
            "projects",
            params={"on_conflict": "id"},
            json=payload,
            prefer="resolution=merge-duplicates,return=minimal",
            strict=True,
        )
    except RuntimeError:
        # Older schemas do not have projects.current_spec yet; still persist the
        # project row so nothing is lost, and pick the spec up from versions.
        payload.pop("current_spec", None)
        _request(
            "POST",
            "projects",
            params={"on_conflict": "id"},
            json=payload,
            prefer="resolution=merge-duplicates,return=minimal",
        )


def delete_project(project_id: str) -> None:
    _request("DELETE", "projects", params={"id": f"eq.{project_id}"})
    # readings has no FK to projects, so cascade does not reach it.
    _request("DELETE", "readings", params={"project_id": f"eq.{project_id}"})


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


# ---------------------------------------------------------------------------
# Devices, telemetry, proposals, verification runs and audit entries
# ---------------------------------------------------------------------------

# The devices table constrains status to offline/online/error; the API also uses
# "provisioned" before the first telemetry arrives.
_DEVICE_STATUS_MAP = {"provisioned": "offline"}


def save_device(device: Any) -> None:
    """Upsert one provisioned device (id mirrors device_id)."""
    _request(
        "POST",
        "devices",
        params={"on_conflict": "id"},
        json={
            "id": device.device_id,
            "device_id": device.device_id,
            "project_id": device.project_id,
            "name": device.name,
            "secret_hash": device.token_hash,
            "status": _DEVICE_STATUS_MAP.get(device.status, device.status),
            "last_seen_at": device.last_seen_at,
            "created_at": device.created_at,
        },
        prefer="resolution=merge-duplicates,return=minimal",
    )


def delete_device(device_id: str) -> None:
    _request("DELETE", "devices", params={"id": f"eq.{device_id}"})
    _request("DELETE", "readings", params={"device_id": f"eq.{device_id}"})


def save_reading(
    device_id: str,
    project_id: Optional[str],
    metric: str,
    value: Any,
    recorded_at: str,
    unit: Optional[str] = None,
) -> None:
    """Insert one numeric telemetry sample (non-numeric metrics are skipped)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return
    _request(
        "POST",
        "readings",
        json={
            "device_id": device_id,
            "project_id": project_id,
            "metric": metric,
            "value": value,
            "unit": unit,
            "recorded_at": recorded_at,
        },
        prefer="return=minimal",
    )


def save_proposal(proposal: Any) -> None:
    _request(
        "POST",
        "proposals",
        params={"on_conflict": "id"},
        json={
            "id": proposal.proposal_id,
            "project_id": proposal.project_id,
            "status": proposal.status,
            "summary": proposal.summary,
            "changes": [c.model_dump() for c in proposal.changes],
            "created_at": proposal.created_at,
            "resolved_at": proposal.resolved_at,
        },
        prefer="resolution=merge-duplicates,return=minimal",
    )


def resolve_proposal(proposal_id: str, status: str, resolved_at: Optional[str]) -> None:
    _request(
        "PATCH",
        "proposals",
        params={"id": f"eq.{proposal_id}"},
        json={"status": status, "resolved_at": resolved_at},
        prefer="return=minimal",
    )


def save_verification_run(run: Any) -> None:
    _request(
        "POST",
        "verification_runs",
        params={"on_conflict": "id"},
        json={
            "id": run.run_id,
            "project_id": run.project_id,
            "version_number": run.version_number,
            "status": run.status if run.status != "queued" else "queued",
            "sandbox_provider": run.sandbox_provider,
            "logs": run.logs,
            "firmware_binary_url": run.firmware_binary_url,
            "selftest_results": run.selftest_results,
            "created_at": run.created_at,
            "completed_at": run.completed_at,
        },
        prefer="resolution=merge-duplicates,return=minimal",
    )


def save_audit_entry(entry: Any) -> None:
    _request(
        "POST",
        "audit_log",
        json={
            "user_id": entry.user_id,
            "project_id": entry.project_id,
            "action": entry.action,
            "payload": entry.payload,
            "created_at": entry.created_at,
        },
        prefer="return=minimal",
    )

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

    _hydrate_devices_and_telemetry()
    _hydrate_proposals()
    _hydrate_verification_runs()
    _hydrate_audit_log()

    logger.info("Hydrated %s project(s) from Supabase", loaded)
    return loaded


def _hydrate_devices_and_telemetry() -> None:
    from app.db.repositories.device_repo import DeviceRecord, device_repo
    from app.models.devices import TelemetryReading

    rows = _select(
        "devices",
        {
            "select": "id,device_id,project_id,name,secret_hash,status,last_seen_at,created_at",
            "order": "created_at.asc",
        },
    )
    for row in rows:
        try:
            device_id = row.get("device_id") or row.get("id")
            record = DeviceRecord(
                device_id=device_id,
                project_id=row["project_id"],
                name=row.get("name") or device_id,
                token_hash=row.get("secret_hash") or "",
                status=row.get("status") or "offline",
                created_at=row.get("created_at"),
                last_seen_at=row.get("last_seen_at"),
            )
        except Exception as exc:
            logger.warning("Skipping unreadable device row %s: %s", row.get("id"), exc)
            continue
        device_repo._devices[device_id] = record
        device_repo._telemetry.setdefault(device_id, [])

    # `readings` stores one row per metric; regroup rows that share a timestamp
    # back into a single TelemetryReading.
    reading_rows = _select(
        "readings",
        {
            "select": "device_id,metric,value,recorded_at",
            "order": "recorded_at.asc",
            "limit": "2000",
        },
    )
    grouped: Dict[tuple, Dict[str, Any]] = {}
    for row in reading_rows:
        key = (row.get("device_id"), row.get("recorded_at"))
        grouped.setdefault(key, {})[row.get("metric")] = row.get("value")
    for (device_id, recorded_at), metrics in grouped.items():
        if device_id not in device_repo._devices:
            continue
        device_repo._telemetry.setdefault(device_id, []).append(
            TelemetryReading(
                device_id=device_id,
                timestamp=recorded_at,
                metrics=metrics,
            )
        )


def _hydrate_proposals() -> None:
    from app.db.repositories.proposal_repo import proposal_repo
    from app.models.proposals import SpecChangeItem, SpecProposal

    rows = _select(
        "proposals",
        {"select": "id,project_id,status,summary,changes,created_at,resolved_at"},
    )
    for row in rows:
        try:
            proposal = SpecProposal(
                proposal_id=row["id"],
                project_id=row["project_id"],
                summary=row.get("summary") or "",
                changes=[SpecChangeItem(**c) for c in (row.get("changes") or [])],
                status=row.get("status") or "pending",
                created_at=row.get("created_at"),
                resolved_at=row.get("resolved_at"),
            )
        except Exception as exc:
            logger.warning("Skipping unreadable proposal row %s: %s", row.get("id"), exc)
            continue
        proposal_repo._proposals.setdefault(proposal.project_id, {})[proposal.proposal_id] = proposal


def _hydrate_verification_runs() -> None:
    from app.db.repositories.verification_repo import verification_repo
    from app.models.verification import VerificationRun

    rows = _select(
        "verification_runs",
        {
            "select": "id,project_id,version_number,status,sandbox_provider,logs,firmware_binary_url,selftest_results,created_at,completed_at",
            "order": "created_at.asc",
            "limit": "200",
        },
    )
    for row in rows:
        try:
            run = VerificationRun(
                run_id=row["id"],
                project_id=row["project_id"],
                version_number=int(row.get("version_number") or 1),
                status=row.get("status") or "failed",
                sandbox_provider=row.get("sandbox_provider") or "e2b",
                logs=row.get("logs") or "",
                firmware_binary_url=row.get("firmware_binary_url"),
                selftest_results=row.get("selftest_results"),
                created_at=row.get("created_at"),
                completed_at=row.get("completed_at"),
            )
        except Exception as exc:
            logger.warning("Skipping unreadable verification run %s: %s", row.get("id"), exc)
            continue
        verification_repo._runs[run.run_id] = run


def _hydrate_audit_log() -> None:
    from app.db.repositories.audit_repo import audit_repo
    from app.models.audit import AuditLogEntry

    rows = _select(
        "audit_log",
        {
            "select": "id,user_id,project_id,action,payload,created_at",
            "order": "created_at.asc",
            "limit": "1000",
        },
    )
    for row in rows:
        try:
            audit_repo._logs.append(
                AuditLogEntry(
                    id=str(row["id"]),
                    user_id=str(row.get("user_id") or ""),
                    project_id=row.get("project_id"),
                    action=row.get("action") or "UNKNOWN",
                    payload=row.get("payload") or {},
                    created_at=row.get("created_at"),
                )
            )
        except Exception as exc:
            logger.warning("Skipping unreadable audit row %s: %s", row.get("id"), exc)
