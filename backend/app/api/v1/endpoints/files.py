import asyncio
import json
from typing import List
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.core.auth import get_current_user
from app.core.exceptions import NotFoundError
from app.db.repositories.files_repo import files_repo
from app.db.repositories.project_repo import project_repo
from app.models.auth import AuthUser
from app.models.files import FileContentUpdate, FileListItem, GeneratedFile

router = APIRouter(prefix="/projects/{project_id}", tags=["Code Generation & Files"])


@router.get("/files", response_model=List[FileListItem])
async def list_files(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> List[FileListItem]:
    """Retrieve list of synthesized project code files and their checksums."""
    project_repo.get_project(project_id, current_user.id)
    files = files_repo.list_files(project_id)
    return [
        FileListItem(
            path=f.path,
            file_type=f.file_type,
            size_bytes=len(f.content.encode("utf-8")),
            is_protected=f.is_protected,
            checksum=f.checksum,
        )
        for f in files
    ]


@router.get("/files/{path:path}", response_model=GeneratedFile)
async def get_file_content(
    project_id: str,
    path: str,
    current_user: AuthUser = Depends(get_current_user),
) -> GeneratedFile:
    """Retrieve code content for a specific file path."""
    project_repo.get_project(project_id, current_user.id)
    f = files_repo.get_file(project_id, path)
    if not f:
        raise NotFoundError(f"File '{path}' not found in project '{project_id}'")
    return f


@router.put("/files/{path:path}", response_model=GeneratedFile)
async def update_file_content(
    project_id: str,
    path: str,
    payload: FileContentUpdate,
    current_user: AuthUser = Depends(get_current_user),
) -> GeneratedFile:
    """Apply manual edits to a generated file, preserving protected user code regions."""
    project_repo.get_project(project_id, current_user.id)
    return files_repo.update_file_content(
        project_id=project_id, path=path, new_content=payload.content
    )


@router.post("/generate", response_class=StreamingResponse)
async def generate_code_sse(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Synthesize complete project code (Arduino firmware, Cloud worker, Web app) over SSE."""
    project_repo.get_project(project_id, current_user.id)

    async def event_generator():
        yield f"event: status\ndata: {json.dumps({'message': 'Initializing code synthesis pipeline...'})}\n\n"
        await asyncio.sleep(0.05)

        yield f"event: log\ndata: {json.dumps({'level': 'info', 'message': 'Generating Arduino firmware (PlatformIO / C++)...'})}\n\n"
        await asyncio.sleep(0.05)

        files = files_repo.generate_project_code(project_id=project_id, user_id=current_user.id)

        yield f"event: log\ndata: {json.dumps({'level': 'info', 'message': f'Generated {len(files)} files successfully.'})}\n\n"
        await asyncio.sleep(0.05)

        yield f"event: done\ndata: {json.dumps({'status': 'completed', 'file_count': len(files)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
