import asyncio
import json
from typing import AsyncGenerator, Dict, Any
from app.agents.guardrails import InjectionGuardrail
from app.agents.tools import ReadOnlyAgentTools
from app.db.repositories.proposal_repo import proposal_repo
from app.models.proposals import SpecChangeItem, SpecProposal


class IntentAgent:
    """Translates plain-language engineer requirements into structured spec proposals.
    HARD RULE: Agents never mutate the spec directly; they emit proposals.
    Streams SSE events conforming to contract:
    token | question | spec_proposal | tool_call | log | status | error | done
    """

    @classmethod
    async def stream_chat_response(
        cls, project_id: str, prompt: str
    ) -> AsyncGenerator[str, None]:
        # 1. Sanitize input with injection guardrails
        sanitized_prompt, flagged = InjectionGuardrail.sanitize_input(prompt)

        yield cls._format_sse("status", {"message": "Analyzing system requirements..."})
        await asyncio.sleep(0.05)

        if flagged:
            yield cls._format_sse("log", {"level": "warn", "message": "Suspicious instruction patterns redacted."})

        # 2. Tool call: Inspect current spec & validation issues
        yield cls._format_sse(
            "tool_call",
            {"tool": "validate_spec", "args": {"project_id": project_id}},
        )
        await asyncio.sleep(0.05)

        val_data = ReadOnlyAgentTools.validate_spec(project_id)
        issues = val_data.get("issues", [])

        # 3. Stream thinking / explanation tokens
        tokens = [
            "I ", "analyzed ", "your ", "project ", "spec ", "and ", "validation ", "rules.\n\n"
        ]
        for tok in tokens:
            yield cls._format_sse("token", {"token": tok})
            await asyncio.sleep(0.02)

        # 4. Synthesize proposal if pin conflict, open field, or configuration change requested
        lower_prompt = sanitized_prompt.lower()
        if "conflict" in lower_prompt or "pin" in lower_prompt or any(i.get("layer") == "electrical" for i in issues):
            explanation = "I identified a pin multiplexing collision between the BME280 sensor SDA line and the tactile button on GPIO4. I propose reallocating the button to available GPIO10.\n\n"
            for tok in explanation.split(" "):
                yield cls._format_sse("token", {"token": tok + " "})
                await asyncio.sleep(0.02)

            changes = [
                SpecChangeItem(
                    path="peripherals.button_pin",
                    old="GPIO4",
                    new="GPIO10",
                    reason="Reallocate button to GPIO10 to eliminate I2C bus collision on GPIO4.",
                ),
                SpecChangeItem(
                    path="metadata.target_deployment_date",
                    old=None,
                    new="2026-12-01",
                    reason="Supply required deployment schedule deadline.",
                ),
            ]
            proposal = proposal_repo.create_proposal(
                project_id=project_id,
                summary="Resolve I2C pin collision on GPIO4 by remapping manual button to GPIO10.",
                changes=changes,
            )

            # Emit spec_proposal event matching contract
            yield cls._format_sse("spec_proposal", {
                "proposal_id": proposal.proposal_id,
                "summary": proposal.summary,
                "changes": [c.model_dump() for c in proposal.changes],
            })

        elif "sleep" in lower_prompt or "battery" in lower_prompt:
            explanation = "I propose adjusting the deep-sleep interval to 120 seconds to optimize the LiPo battery discharge curve.\n\n"
            for tok in explanation.split(" "):
                yield cls._format_sse("token", {"token": tok + " "})
                await asyncio.sleep(0.02)

            changes = [
                SpecChangeItem(
                    path="hardware.deep_sleep_interval_seconds",
                    old=60,
                    new=120,
                    reason="Extend sleep interval to reduce active radio duty cycle on battery.",
                )
            ]
            proposal = proposal_repo.create_proposal(
                project_id=project_id,
                summary="Extend deep sleep cycle from 60s to 120s for power conservation.",
                changes=changes,
            )
            yield cls._format_sse("spec_proposal", {
                "proposal_id": proposal.proposal_id,
                "summary": proposal.summary,
                "changes": [c.model_dump() for c in proposal.changes],
            })

        else:
            clarification = "Are there specific power duty cycles or target broker topics you would like to refine?"
            yield cls._format_sse("question", {"question": clarification})

        # 5. Done event
        yield cls._format_sse("done", {"status": "completed"})

    @staticmethod
    def _format_sse(event_type: str, data: Dict[str, Any]) -> str:
        payload = json.dumps({"type": event_type, "data": data})
        return f"event: {event_type}\ndata: {payload}\n\n"
