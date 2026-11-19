"""Shared agno + Gemini LLM access for the platform's AI agents.

Every AI call goes through agno's ``Agent`` with the configured Gemini model,
so the model id, provider and API key live in one place. Callers keep their
deterministic fallbacks for local/test runs where no API key is configured.

The model defaults to ``gemini-3.8-flash`` (see ``Settings.AI_MODEL_NAME``);
override it with the ``AI_MODEL_NAME`` env var.
"""
import logging
from typing import AsyncGenerator, Optional

from agno.agent import Agent
from agno.models.google import Gemini
from agno.run.agent import RunContentEvent

from app.core.config import settings

logger = logging.getLogger("app.agents.llm")


def is_available() -> bool:
    """True only when a real Gemini call can be made right now."""
    return settings.AI_MODEL_PROVIDER == "gemini" and bool(settings.GEMINI_API_KEY)


def _model(temperature: Optional[float] = None) -> Gemini:
    kwargs: dict = {
        "id": settings.AI_MODEL_NAME,
        "api_key": settings.GEMINI_API_KEY,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    return Gemini(**kwargs)


def _agent(system_instruction: str, temperature: Optional[float] = None) -> Agent:
    # Stateless one-shot agent: no session db, no history, no markdown.
    return Agent(model=_model(temperature), instructions=system_instruction)


async def complete(
    system_instruction: str, prompt: str, temperature: Optional[float] = None
) -> str:
    """One-shot completion. Returns the model's text, or '' if it produced none."""
    agent = _agent(system_instruction, temperature)
    response = await agent.arun(prompt)
    content = getattr(response, "content", None)
    if content is None:
        return ""
    return content if isinstance(content, str) else str(content)


async def stream(
    system_instruction: str, prompt: str, temperature: Optional[float] = None
) -> AsyncGenerator[str, None]:
    """Yield model content deltas as they arrive (for SSE token streaming)."""
    agent = _agent(system_instruction, temperature)
    async for event in agent.arun(prompt, stream=True):
        if isinstance(event, RunContentEvent):
            delta = getattr(event, "content", None)
            if isinstance(delta, str) and delta:
                yield delta
