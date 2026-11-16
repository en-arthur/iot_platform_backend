"""Parsing helpers for PlatformIO build artifacts.

PlatformIO writes a ``flash_args`` file next to the built images. It is the
authoritative list of offsets for the current board, so flashing uses exactly
what the toolchain produced instead of guessed addresses.
"""

import re
from typing import List, Tuple

# "0x0000 bootloader.bin" / "0x10000 firmware.bin"
_FLASH_LINE = re.compile(r"^(0x[0-9a-fA-F]+)\s+(\S+)\s*$")


def parse_flash_args(text: str) -> List[Tuple[int, str]]:
    """Return (offset, filename) pairs from a PlatformIO ``flash_args`` file.

    Flag lines (``--flash_mode dio``) are ignored. Malformed lines are skipped
    rather than silently producing a wrong address.
    """
    segments: List[Tuple[int, str]] = []
    for line in text.splitlines():
        match = _FLASH_LINE.match(line.strip())
        if not match:
            continue
        # The same file is never flashed twice; keep the first offset if it is.
        if any(name == match.group(2) for _, name in segments):
            continue
        segments.append((int(match.group(1), 16), match.group(2)))
    return segments


def human_size(num_bytes: int) -> str:
    """Compact byte count for logs, e.g. '412.3 KB'."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.2f} MB"
