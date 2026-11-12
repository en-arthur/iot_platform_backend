import json
import logging
from typing import Tuple

import httpx

from app.core.config import settings
from app.models.project import BehaviorDraftRequest

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are an embedded IoT engineer. Write a concise, testable behavior "
    "specification for firmware in natural language. Cover sampling rate, power "
    "mode / sleep, threshold logic, actuation, MQTT telemetry and command topics, "
    "and failure handling. Use only the components and constraints given by the "
    "user. Reply with plain prose (3-5 sentences), no markdown, no headings and "
    "no bullet lists."
)


def _context(payload: BehaviorDraftRequest) -> str:
    parts = [f"Project: {payload.name or 'Untitled IoT device'}"]
    if payload.goal:
        parts.append(f"Goal and context: {payload.goal}")
    if payload.board_id:
        parts.append(f"Board: {payload.board_id}")
    if payload.peripherals:
        parts.append(f"Peripherals: {', '.join(payload.peripherals)}")
    if payload.custom_peripherals:
        parts.append(f"Custom components: {', '.join(payload.custom_peripherals)}")
    if payload.interface_type:
        parts.append(f"User interface: {payload.interface_type}")
    return "\n".join(parts)


async def _gemini_behavior(payload: BehaviorDraftRequest) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.AI_MODEL_NAME}:generateContent?key={settings.GEMINI_API_KEY}"
    )
    body = {
        "contents": [{"parts": [{"text": _context(payload)}]}],
        "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 512},
    }
    async with httpx.AsyncClient(timeout=25.0) as client:
        response = await client.post(url, json=body)
    if response.status_code != 200:
        raise RuntimeError(f"Gemini HTTP {response.status_code}: {response.text[:200]}")

    candidates = response.json().get("candidates", [])
    if not candidates:
        return ""
    text = "".join(
        part.get("text", "")
        for part in candidates[0].get("content", {}).get("parts", [])
    )
    return text.strip()


def _template_behavior(payload: BehaviorDraftRequest) -> str:
    """Deterministic fallback when Gemini is not configured or unreachable."""
    sensors = ", ".join(payload.peripherals + payload.custom_peripherals) or "all attached sensors"
    board = payload.board_id or "the target board"
    goal = (payload.goal or "").strip().rstrip(".")
    intro = f"On {board}, read {sensors} every 30 seconds"
    if goal:
        intro += f" to support this goal: {goal}"

    return (
        f"{intro}. Publish each reading as a JSON telemetry frame over MQTT to "
        "devices/<device_id>/telemetry and keep the radio off between cycles, "
        "entering deep sleep when the device is battery powered. Apply hysteresis "
        "to actuation: energise the output when the measured value crosses the "
        "configured upper threshold and release it once the value falls back "
        "below the lower threshold. Publish an alert to devices/<device_id>/alerts "
        "when a threshold stays exceeded for more than five minutes, and expose "
        "the declared commands on devices/<device_id>/cmd with an acknowledgement "
        "within two seconds. If a sensor read fails, log the fault locally, retry "
        "twice, then reconnect to the broker with exponential backoff."
    )


async def generate_behavior_draft(
    payload: BehaviorDraftRequest,
) -> Tuple[str, str]:
    """Return (behavior text, source) where source is 'ai' or 'template'."""
    if settings.AI_MODEL_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        try:
            text = await _gemini_behavior(payload)
            if text:
                return text, "ai"
            logger.warning("Gemini returned an empty behavior draft; using template")
        except Exception as exc:
            logger.warning(f"Gemini behavior draft failed ({exc}); using template")
    return _template_behavior(payload), "template"
