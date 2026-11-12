import logging
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.sandbox.base import SandboxRunner

logger = logging.getLogger(__name__)

# Everything one verification needs lives under this directory inside the
# sandbox: platformio.ini, src/main.cpp, etc.
PROJECT_DIR = "/home/user/project"
PLATFORMIO_CORE_DIR = "/opt/platformio"


class E2BSandboxRunner(SandboxRunner):
    """Real E2B implementation of SandboxRunner.

    Every verification creates a fresh microVM from a shared template that has
    PlatformIO and the ESP32 toolchain pre-installed (see
    ``scripts/build_e2b_template.py``). Project files are uploaded per run, so a
    new template is NOT needed per device or per project.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        template: Optional[str] = None,
    ):
        self.api_key = api_key or settings.E2B_API_KEY
        self.template = template or settings.E2B_TEMPLATE
        self._sandboxes: Dict[str, Any] = {}

    @property
    def configured(self) -> bool:
        """True when a real E2B sandbox can actually be created."""
        return bool(self.api_key and self.template)

    def _get(self, sandbox_id: str):
        sandbox = self._sandboxes.get(sandbox_id)
        if sandbox is None:
            raise RuntimeError(f"Sandbox '{sandbox_id}' not found")
        return sandbox

    async def create(
        self,
        snapshot: str = "esp32-arduino-toolchain",
        labels: Optional[Dict[str, str]] = None,
        network_blocked: bool = True,
    ) -> str:
        if not self.configured:
            raise RuntimeError(
                "E2B is not configured: set E2B_API_KEY and E2B_TEMPLATE "
                "(build the template once with scripts/build_e2b_template.py)."
            )

        from e2b import AsyncSandbox

        sandbox = await AsyncSandbox.create(
            template=self.template or snapshot,
            timeout=settings.E2B_TIMEOUT_SECONDS,
            metadata={k: str(v) for k, v in (labels or {}).items()},
            envs={"PLATFORMIO_CORE_DIR": PLATFORMIO_CORE_DIR},
            # Verification runs are hermetic: no network, only the pre-baked
            # toolchain and libraries.
            allow_internet_access=not network_blocked,
            api_key=self.api_key,
        )
        sandbox_id = sandbox.sandbox_id
        self._sandboxes[sandbox_id] = sandbox
        logger.info("Created E2B sandbox %s from template %s", sandbox_id, self.template)
        return sandbox_id

    async def upload_files(self, sandbox_id: str, files: Dict[str, str]) -> None:
        sandbox = self._get(sandbox_id)
        entries = []
        for path, content in files.items():
            clean = path.lstrip("/").replace("\\", "/")
            entries.append({"path": f"{PROJECT_DIR}/{clean}", "data": content})
        if entries:
            await sandbox.files.write_files(entries)

    async def run_command(self, sandbox_id: str, cmd: str) -> Tuple[int, str, str]:
        sandbox = self._get(sandbox_id)
        result = await sandbox.commands.run(
            cmd,
            cwd=PROJECT_DIR,
            envs={"PLATFORMIO_CORE_DIR": PLATFORMIO_CORE_DIR},
            timeout=settings.E2B_COMMAND_TIMEOUT_SECONDS,
        )
        return result.exit_code, result.stdout or "", result.stderr or ""

    async def download_file(self, sandbox_id: str, path: str) -> bytes:
        sandbox = self._get(sandbox_id)
        data = await sandbox.files.read(path, format="bytes")
        return bytes(data)

    async def destroy(self, sandbox_id: str) -> None:
        sandbox = self._sandboxes.pop(sandbox_id, None)
        if sandbox is None:
            return
        try:
            await sandbox.kill()
        except Exception as exc:  # pragma: no cover - best-effort cleanup
            logger.warning("Could not kill E2B sandbox %s: %s", sandbox_id, exc)
