import re
from typing import Tuple

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s+prompt",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"bypass\s+(all\s+)?security",
    r"exfiltrate",
    r"jailbreak",
    r"<script.*?>.*?</script>",
]


class InjectionGuardrail:
    """Sanitizes untrusted engineer inputs, logs, and datasheets to prevent injection."""

    @classmethod
    def sanitize_input(cls, text: str) -> Tuple[str, bool]:
        """Returns sanitized string and a flag indicating if injection was detected."""
        was_flagged = False
        sanitized = text

        for pattern in INJECTION_PATTERNS:
            match = re.search(pattern, sanitized, re.IGNORECASE)
            if match:
                was_flagged = True
                # Redact the suspect instruction
                sanitized = re.sub(pattern, "[REDACTED_INSTRUCTION]", sanitized, flags=re.IGNORECASE)

        return sanitized.strip(), was_flagged
