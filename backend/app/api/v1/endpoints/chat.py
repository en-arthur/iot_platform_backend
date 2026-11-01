from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.intent_agent import IntentAgent
from app.core.auth import get_current_user
from app.db.repositories.project_repo import project_repo
from app.models.auth import AuthUser

router = APIRouter(prefix="/projects/{project_id}/chat", tags=["AI Chat & Proposals"])


class ChatRequest(BaseModel):
    prompt: str


@router.post("", response_class=StreamingResponse)
async def chat_sse(
    project_id: str,
    payload: ChatRequest,
    request: Request,
    current_user: AuthUser = Depends(get_current_user),
):
    """Streams AI responses, questions, tool calls, and spec proposals via SSE (text/event-stream).
    Event types: token | question | spec_proposal | tool_call | log | status | error | done
    """
    # Verify project exists and user has access
    project_repo.get_project(project_id, current_user.id)

    generator = IntentAgent.stream_chat_response(project_id=project_id, prompt=payload.prompt)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
