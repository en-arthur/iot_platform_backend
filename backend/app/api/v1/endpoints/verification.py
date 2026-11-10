import asyncio
import json
from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from app.core.auth import get_current_user
from app.db.repositories.verification_repo import verification_repo
from app.models.auth import AuthUser
from app.models.verification import (
    SelfTestPayload,
    VerificationRun,
    VerificationTriggerResponse,
)

router = APIRouter(tags=["Verification & Sandboxes"])


@router.post("/projects/{project_id}/verify", response_model=VerificationTriggerResponse)
async def trigger_verification_run(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> VerificationTriggerResponse:
    """Schedule compilation and simulation inside an isolated ephemeral E2B sandbox."""
    run_obj = verification_repo.create_run(project_id, current_user.id)
    # Execute verification pipeline
    asyncio.create_task(
        verification_repo.execute_run_pipeline(run_obj.run_id, current_user.id)
    )
    return VerificationTriggerResponse(
        run_id=run_obj.run_id,
        status="running",
        message="Verification pipeline started in E2B sandbox with network blocked.",
    )


@router.get("/runs/{run_id}", response_model=VerificationRun)
async def get_verification_run(
    run_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> VerificationRun:
    """Retrieve execution status, compiler logs, and self-test verification data."""
    return verification_repo.get_run(run_id, current_user.id)


@router.get("/runs/{run_id}/stream", response_class=StreamingResponse)
async def stream_verification_logs(
    run_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Stream live compiler output from the E2B sandbox over SSE."""
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


@router.get("/runs/{run_id}/firmware")
async def get_firmware_binary(
    run_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Serve compiled Arduino binary for in-browser Web Serial flashing."""
    binary_bytes = verification_repo.get_firmware_binary(run_id, current_user.id)
    return Response(
        content=binary_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename=firmware-{run_id}.bin"},
    )


@router.post("/runs/{run_id}/selftest", response_model=VerificationRun)
async def submit_selftest_results(
    run_id: str,
    payload: SelfTestPayload,
    current_user: AuthUser = Depends(get_current_user),
) -> VerificationRun:
    """Record on-device physical verification results posted from browser Web Serial."""
    return verification_repo.submit_selftest(
        run_id=run_id, results=payload.results, user_id=current_user.id
    )
