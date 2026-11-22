"""Behavior draft generation endpoint using AI."""
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.llm_client import LLMClient
from app.core.config import settings
import logging

router = APIRouter(prefix="/projects", tags=["Behavior Draft"])
logger = logging.getLogger("app.api.behavior")


class BehaviorDraftRequest(BaseModel):
    """Request payload for behavior draft generation."""
    name: Optional[str] = None
    goal: Optional[str] = None
    board_id: Optional[str] = None
    peripherals: List[str] = []
    custom_peripherals: List[str] = []
    interface_type: str = "dashboard"


class BehaviorDraftResponse(BaseModel):
    """Response with generated behavior specification."""
    behavior: str
    source: str  # 'ai' | 'template' | 'error'


@router.post("/behavior-draft", response_model=BehaviorDraftResponse)
async def generate_behavior_draft(payload: BehaviorDraftRequest) -> BehaviorDraftResponse:
    """Generate a behavior specification draft from user context using AI.
    
    Takes the project name, goal, hardware selection, and interface type
    and generates a plain-language behavior specification that describes
    how the device should work.
    
    Falls back to a template-based draft if AI is unavailable.
    """
    # Build components list
    components = payload.peripherals + payload.custom_peripherals
    components_str = ', '.join(components) if components else 'all attached sensors'
    
    # Build prompt for AI
    system_instruction = (
        "You are an expert IoT systems engineer writing behavior specifications for embedded devices. "
        "Given a project goal and hardware components, write a clear, detailed behavior specification "
        "that describes: sampling frequency, data publishing, power management, actuator logic with hysteresis, "
        "error handling, and command acknowledgement. Write in plain language, not code."
    )
    
    user_prompt = f"""Project: {payload.name or 'Untitled IoT device'}
Board: {payload.board_id or 'ESP32'}
Components: {components_str}
Interface: {payload.interface_type}
Goal: {payload.goal or 'Monitor sensor data and control actuators'}

Write a comprehensive behavior specification for this IoT device. Include:
1. How often to read sensors
2. When and how to publish telemetry over MQTT
3. Power management strategy (sleep cycles, battery optimization)
4. Actuator control logic with thresholds and hysteresis
5. Error handling and retry logic
6. Command handling and acknowledgements

Keep it concise but complete. Write in plain technical language."""

    # Try AI generation
    try:
        logger.info(f"Generating behavior draft with {settings.AI_MODEL_PROVIDER}/{settings.AI_MODEL_NAME}")
        
        # Stream tokens and collect full response
        tokens = []
        async for token in LLMClient.stream_tokens(system_instruction, user_prompt):
            tokens.append(token)
        
        behavior_text = ''.join(tokens).strip()
        
        if behavior_text and len(behavior_text) > 50:
            return BehaviorDraftResponse(behavior=behavior_text, source='ai')
        else:
            logger.warning("AI generated empty or too short response, falling back to template")
            raise ValueError("AI response too short")
            
    except Exception as e:
        logger.warning(f"AI generation failed: {e}, using template fallback")
        
        # Fallback to template-based draft
        goal_text = (payload.goal or '').strip().rstrip('.')
        behavior_template = (
            f"On {payload.board_id or 'the target board'}, read {components_str} every 30 seconds"
            + (f" to support this goal: {goal_text}" if goal_text else '')
            + ". Publish each reading as a JSON telemetry frame over MQTT and keep the radio off between cycles, "
            "entering deep sleep when the device is battery powered. "
            "Apply hysteresis to actuation: energise the output when the measured value crosses the configured "
            "upper threshold and release it once the value falls back below the lower threshold. "
            "Publish an alert when a threshold stays exceeded for more than five minutes, "
            "and accept control commands with an acknowledgement within two seconds. "
            "If a sensor read fails, log the fault locally, retry twice, then reconnect to the broker "
            "with exponential backoff."
        )
        
        return BehaviorDraftResponse(behavior=behavior_template, source='template')
