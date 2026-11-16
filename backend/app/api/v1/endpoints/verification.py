import asyncio
import json
from typing import List
from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from app.core.auth import get_current_user
from app.db.repositories.verification_repo import verification_repo
from app.models.auth import AuthUser
from app.models.verification import (
    FirmwareArtifact,
    VerificationRun,
    VerificationTriggerResponse,
)

router = APIRouter(tags=["Verification & Sandboxes"])


@router.post("/projects/{project_id}/verify", response_model=VerificationTriggerResponse)
async def trigger_verification_run(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> VerificationTriggerResponse:
    """Compile the generated project inside an isolated ephemeral E2B sandbox."""
    run_obj = verification_repo.create_run(project_id, current_user.id)
    asyncio.create_task(
        verification_repo.execute_run_pipeline(run_obj.run_id, current_user.id)
    )
    return VerificationTriggerResponse(
        run_id=run_obj.run_id,
        status="running",
        message="Build started in an E2B sandbox with outbound network blocked.",
    )


@router.get("/projects/{project_id}/runs", response_model=List[VerificationRun])
async def list_verification_runs(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> List[VerificationRun]:
    """Recent real builds for a project, newest first."""
    return verification_repo.list_runs(project_id, current_user.id)


@router.get("/runs/{run_id}", response_model=VerificationRun)
async def get_verification_run(
    run_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> VerificationRun:
    """Execution status, real compiler logs, and artifact metadata."""
    return verification_repo.get_run(run_id, current_user.id)


@router.get("/runs/{run_id}/stream", response_class=StreamingResponse)
async def stream_verification_logs(
    run_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Stream the compiler output captured from the E2B sandbox over SSE."""
    run_obj = verification_repo.get_run(run_id, current_user.id)

    async def log_streamer():
        yield f"event: status\ndata: {json.dumps({'status': run_obj.status})}\n\n"
        await asyncio.sleep(0.05)

        for line in run_obj.logs.split("\n"):
            if line:
                yield f"event: log\ndata: {json.dumps({'line': line})}\n\n"
                await asyncio.sleep(0.02)

        yield f"event: done\ndata: {json.dumps({'status': run_obj.status})}\n\n"

    return StreamingResponse(
        log_streamer(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/runs/{run_id}/artifact", response_model=FirmwareArtifact)
async def get_firmware_artifact(
    run_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> FirmwareArtifact:
    """Every image the build produced, with the offsets the toolchain chose."""
    return verification_repo.get_artifact(run_id, current_user.id)


@router.get("/runs/{run_id}/firmware")
async def get_firmware_binary(
    run_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Serve the primary image for a plain file download."""
    artifact = verification_repo.get_artifact(run_id, current_user.id)
    binary_bytes = verification_repo.get_firmware_binary(run_id, current_user.id)
    return Response(
        content=binary_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{artifact.artifact_name}"'
        },
    )
