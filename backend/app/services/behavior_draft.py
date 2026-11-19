import json
import logging
from typing import List, Tuple

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
    """Draft the behavior via agno + Gemini.

    The caller falls back to the deterministic template when this raises or
    returns an empty string, so a missing/unreachable model never breaks the
    wizard.
    """
    from app.agents.llm import complete

    text = await complete(SYSTEM_INSTRUCTION, _context(payload), temperature=0.4)
    return text.strip()


OUTPUT_HINTS = (
    "relay",
    "fan",
    "led",
    "motor",
    "buzzer",
    "valve",
    "pump",
    "servo",
    "switch",
    "solenoid",
    "heater",
)


def _split_parts(items: List[str]) -> Tuple[List[str], List[str]]:
    """Separate things the device reads from things it switches on and off."""
    outputs = [item for item in items if any(hint in item.lower() for hint in OUTPUT_HINTS)]
    sensors = [item for item in items if item not in outputs]
    return sensors, outputs


def _template_behavior(payload: BehaviorDraftRequest) -> str:
    """Deterministic fallback when Gemini is not configured or unreachable.

    Written in plain language because the wizard shows it to users who are not
    engineers; they can edit it before submitting.
    """
    sensors, outputs = _split_parts(payload.peripherals + payload.custom_peripherals)
    read = ", ".join(sensors) or "every connected sensor"
    board = "your board"
    if payload.board_id:
        try:
            from app.db.repositories.library_repo import library_repo

            found = library_repo.get_board(payload.board_id)
            board = found.name if found else payload.board_id
        except Exception:
            board = payload.board_id
    goal = (payload.goal or "").strip().rstrip(".")
    sentences = [f"Using {board}, read {read} every 30 seconds"]
    if outputs:
        sentences.append(
            f"switch {', '.join(outputs)} on when a reading goes above the limit "
            "you set, and off again once it drops below the lower limit"
        )
    if goal:
        sentences.append(f"This supports the goal: {goal}")
    sentences.append(
        "Send each reading to your dashboard, and keep the radio off between "
        "readings, sleeping deeply when the device runs on batteries"
    )
    sentences.append(
        "Raise an alert if a reading stays above the limit for more than five minutes"
    )
    sentences.append(
        "Accept the on/off commands from your dashboard and confirm each one "
        "within two seconds"
    )
    sentences.append(
        "If a sensor read fails, try twice more, then reconnect on its own"
    )
    return ". ".join(
        sentence[0].upper() + sentence[1:] for sentence in sentences
    ) + "."


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
