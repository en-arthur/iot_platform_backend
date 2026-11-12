import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from app.agents.debug_agent import DebugAgent
from app.core.exceptions import NotFoundError
from app.db.repositories.files_repo import files_repo
from app.db.repositories.project_repo import project_repo
from app.models.verification import VerificationRun
from app.sandbox.e2b_runner import E2BSandboxRunner, PROJECT_DIR

logger = logging.getLogger(__name__)


class VerificationRepository:
    """Manages compilation, simulation, ephemeral E2B sandboxes, firmware binaries,
    and browser self-test verification.
    """

    def __init__(self):
        # In-memory storage for test suites & session cache
        self._runs: Dict[str, VerificationRun] = {}
        self._binaries: Dict[str, bytes] = {}
        self.runner = E2BSandboxRunner()

        # Prepopulate demo run for 'proj-greenhouse-01'
        demo_run_id = "run-greenhouse-01"
        self._runs[demo_run_id] = VerificationRun(
            run_id=demo_run_id,
            project_id="proj-greenhouse-01",
            version_number=1,
            status="passed",
            sandbox_provider="e2b",
            logs="[DEMO] PlatformIO compiled firmware.bin (424 KB flash, 32 KB RAM). Ready for browser flashing.",
            firmware_binary_url=f"/api/v1/runs/{demo_run_id}/firmware",
            selftest_results={"wifi_connected": True, "bme280_ack": True, "fan_relay_switched": True},
        )
        self._binaries[demo_run_id] = b"\xe9\x04\x02\x20DEMO_ESP32_FIRMWARE_BINARY"

    def create_run(self, project_id: str, user_id: str) -> VerificationRun:
        project = project_repo.get_project(project_id, user_id)
        run_id = f"run-{uuid.uuid4().hex[:8]}"

        run_obj = VerificationRun(
            run_id=run_id,
            project_id=project_id,
            version_number=project.version,
            status="running",
            sandbox_provider="e2b",
            logs=(
                "Starting ephemeral E2B microVM with network blocked "
                f"(template: {self.runner.template})...\n"
            ),
            firmware_binary_url=f"/api/v1/runs/{run_id}/firmware",
        )
        self._runs[run_id] = run_obj

        # Record audit log
        from app.db.repositories.audit_repo import audit_repo
        audit_repo.record_action(
            action="VERIFICATION_RUN",
            user_id=user_id,
            project_id=project_id,
            payload={"run_id": run_id, "provider": "e2b"},
        )

        return run_obj

    async def execute_run_pipeline(self, run_id: str, user_id: str) -> VerificationRun:
        run_obj = self._runs.get(run_id)
        if not run_obj:
            raise NotFoundError(f"Run '{run_id}' not found")

        project = project_repo.get_project(run_obj.project_id, user_id)

        # 1. Fetch generated files
        files_list = files_repo.list_files(run_obj.project_id)
        if not files_list:
            files_list = files_repo.generate_project_code(run_obj.project_id, user_id)

        file_map = {f.path: f.content for f in files_list}

        # Generated firmware lives in firmware/ (platformio.ini next to src/).
        project_dir = "firmware" if any(p.startswith("firmware/") for p in file_map) else "."
        binary_candidates = [
            f"{PROJECT_DIR}/{project_dir}/.pio/build/esp32s3/firmware.bin",
        ]

        # 2. Spin up a fresh E2B sandbox from the shared ESP32 template.
        try:
            sandbox_id = await self.runner.create(
                labels={"project_id": run_obj.project_id, "run_id": run_id},
                network_blocked=True,
            )
        except Exception as exc:
            run_obj.status = "failed"
            run_obj.logs += f"[SANDBOX ERROR] {exc}\n"
            run_obj.completed_at = datetime.now(timezone.utc).isoformat()
            return run_obj

        try:
            # 3. Upload source code
            await self.runner.upload_files(sandbox_id, file_map)

            # 4. Compile in sandbox
            exit_code, stdout, stderr = await self.runner.run_command(
                sandbox_id, f"pio run -d {project_dir}"
            )
            run_obj.logs += stdout + ("\n" + stderr if stderr else "")

            if exit_code == 0:
                # 5. Extract compiled binary
                binary = None
                last_error: Optional[Exception] = None
                for candidate in binary_candidates:
                    try:
                        binary = await self.runner.download_file(sandbox_id, candidate)
                        break
                    except Exception as exc:  # try the next known location
                        last_error = exc
                if binary is None:
                    run_obj.status = "failed"
                    run_obj.logs += f"\n[ARTIFACT ERROR] firmware.bin not found: {last_error}\n"
                    run_obj.completed_at = datetime.now(timezone.utc).isoformat()
                    return run_obj

                self._binaries[run_id] = binary
                run_obj.status = "passed"
                run_obj.completed_at = datetime.now(timezone.utc).isoformat()
                project.lifecycle = "verified"
            else:
                run_obj.status = "failed"
                run_obj.completed_at = datetime.now(timezone.utc).isoformat()
                # 6. Trigger Debug Agent to synthesize spec fix proposal
                DebugAgent.analyze_compiler_error(run_obj.project_id, stderr, stdout)

        except Exception as exc:
            run_obj.status = "failed"
            run_obj.completed_at = datetime.now(timezone.utc).isoformat()
            run_obj.logs += f"\n[VERIFICATION ERROR] {type(exc).__name__}: {exc}\n"
            logger.exception("Verification run %s failed", run_id)

        finally:
            # Ephemeral destruction
            await self.runner.destroy(sandbox_id)

        return run_obj

    def get_run(self, run_id: str, user_id: str) -> VerificationRun:
        run_obj = self._runs.get(run_id)
        if not run_obj:
            raise NotFoundError(f"Verification run '{run_id}' not found")
        project_repo.get_project(run_obj.project_id, user_id)
        return run_obj

    def get_firmware_binary(self, run_id: str, user_id: str) -> bytes:
        self.get_run(run_id, user_id)
        binary = self._binaries.get(run_id)
        if not binary:
            raise NotFoundError(f"Firmware binary not available for run '{run_id}'")
        return binary

    def submit_selftest(self, run_id: str, results: dict, user_id: str) -> VerificationRun:
        run_obj = self.get_run(run_id, user_id)
        run_obj.selftest_results = results

        all_passed = all(bool(v) for v in results.values() if isinstance(v, bool))
        if all_passed:
            run_obj.status = "passed"
            run_obj.logs += "\n[SELF-TEST PASSED] Hardware successfully verified on physical silicon."
        else:
            run_obj.status = "failed"
            run_obj.logs += "\n[SELF-TEST FAILED] Sensor or peripheral failed hardware self-test."
            DebugAgent.analyze_selftest_failure(run_obj.project_id, results)

        return run_obj


verification_repo = VerificationRepository()
