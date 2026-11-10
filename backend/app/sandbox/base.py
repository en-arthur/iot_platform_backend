from abc import ABC, abstractmethod
from typing import Dict, Tuple


class SandboxRunner(ABC):
    """Abstract interface for ephemeral sandboxes (E2B and Daytona).
    Sandboxes must run isolated with outbound network blocked during compilation/test.
    """

    @abstractmethod
    async def create(
        self,
        snapshot: str = "esp32-arduino-toolchain",
        labels: Dict[str, str] = None,
        network_blocked: bool = True,
    ) -> str:
        """Create an ephemeral sandbox container and return its ID."""
        pass

    @abstractmethod
    async def upload_files(self, sandbox_id: str, files: Dict[str, str]) -> None:
        """Upload source files into sandbox filesystem."""
        pass

    @abstractmethod
    async def run_command(self, sandbox_id: str, cmd: str) -> Tuple[int, str, str]:
        """Execute command in sandbox; returns (exit_code, stdout, stderr)."""
        pass

    @abstractmethod
    async def download_file(self, sandbox_id: str, path: str) -> bytes:
        """Download compiled binary or artifact from sandbox."""
        pass

    @abstractmethod
    async def destroy(self, sandbox_id: str) -> None:
        """Terminate and clean up ephemeral sandbox resources."""
        pass
