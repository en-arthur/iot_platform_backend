import base64
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.agents.debug_agent import DebugAgent
from app.codegen.firmware_generator import ArduinoFirmwareGenerator
from app.core.exceptions import NotFoundError
from app.db import supabase_store
from app.db.repositories.files_repo import files_repo
from app.db.repositories.project_repo import project_repo
from app.models.verification import (
    ArtifactSegment,
    FirmwareArtifact,
    VerificationRun,
)
from app.sandbox.artifacts import human_size, parse_flash_args
from app.sandbox.e2b_runner import E2BSandboxRunner, PROJECT_DIR

logger = logging.getLogger(__name__)


class VerificationRepository:
    """Compiles generated projects in an ephemeral E2B sandbox.

    The repository reports exactly what happened: the compiler exit code, its
    output, and the images PlatformIO produced. There is no emulation step and
    no simulated self-test pass; a run can only reach ``passed`` when a real
    build produced a flashable artifact.
    """

    def __init__(self):
        self._runs: Dict[str, VerificationRun] = {}
        self._artifacts: Dict[str, FirmwareArtifact] = {}
        self._artifact_meta: Dict[str, Dict] = {}
        self._artifact_checked: Dict[str, bool] = {}
        self.runner = E2BSandboxRunner()

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _log(self, run_obj: VerificationRun, line: str) -> None:
        run_obj.logs += line.rstrip("\n") + "\n"

    def _fail(self, run_obj: VerificationRun, message: str) -> None:
        run_obj.status = "failed"
        run_obj.completed_at = self._now()
        self._log(run_obj, message)

    def _attach_artifact_meta(self, run_obj: VerificationRun) -> None:
        """Populate artifact fields from the in-memory copy or object storage."""
        artifact = self._artifacts.get(run_obj.run_id)
        if artifact is not None:
            run_obj.artifact_name = artifact.artifact_name
            run_obj.artifact_size_bytes = artifact.total_bytes
            run_obj.artifact_format = artifact.format
            run_obj.artifact_available = True
            return

        meta = self._artifact_meta.get(run_obj.run_id)
        if meta is None and not self._artifact_checked.get(run_obj.run_id):
            meta = supabase_store.load_verification_artifact_meta(run_obj.run_id)
            self._artifact_checked[run_obj.run_id] = True
            if meta:
                self._artifact_meta[run_obj.run_id] = meta
        if meta:
            run_obj.artifact_name = meta.get("artifact_name")
            run_obj.artifact_size_bytes = meta.get("total_bytes")
            run_obj.artifact_format = meta.get("format")
            run_obj.artifact_available = True

    # -- lifecycle -------------------------------------------------------
    def create_run(self, project_id: str, user_id: str) -> VerificationRun:
        project = project_repo.get_project(project_id, user_id)
        run_id = f"run-{uuid.uuid4().hex[:8]}"

        board_id = project.board_id
        try:
            spec = project_repo.get_spec(project_id, user_id)
            board_id = (
                spec.get("hardware", {}).get("fields", {}).get("board_id", {}).get("value")
                or board_id
            )
        except Exception:
            pass

        run_obj = VerificationRun(
            run_id=run_id,
            project_id=project_id,
            version_number=project.version,
            status="running",
            sandbox_provider="e2b",
            board_id=board_id,
            logs=(
                "Starting an ephemeral E2B microVM with outbound network blocked "
                f"(template: {self.runner.template}).\n"
            ),
        )
        self._runs[run_id] = run_obj
        supabase_store.save_verification_run(run_obj)

        from app.db.repositories.audit_repo import audit_repo

        audit_repo.record_action(
            action="VERIFICATION_RUN",
            user_id=user_id,
            project_id=project_id,
            payload={"run_id": run_id, "provider": "e2b", "board_id": board_id},
        )

        return run_obj

    async def execute_run_pipeline(self, run_id: str, user_id: str) -> VerificationRun:
        run_obj = self._runs.get(run_id)
        if not run_obj:
            raise NotFoundError(f"Run '{run_id}' not found")

        project = project_repo.get_project(run_obj.project_id, user_id)

        # Resolve the board and pins before spending a sandbox. This is the
        # same preflight the generate endpoint runs, so a project that cannot
        # generate also cannot claim a build.
        try:
            spec = project_repo.get_spec(run_obj.project_id, user_id)
            target = ArduinoFirmwareGenerator.resolve_target(spec)
        except Exception as exc:
            self._fail(run_obj, f"[PREFLIGHT ERROR] {exc}")
            supabase_store.save_verification_run(run_obj)
            return run_obj

        board = target["board"]
        run_obj.board_id = board.id
        self._log(run_obj, f"Target board: {board.name} ({board.platform}/{board.pio_board})")

        files_list = files_repo.list_files(run_obj.project_id)
        if not files_list:
            files_list = files_repo.generate_project_code(run_obj.project_id, user_id)
        file_map = {f.path: f.content for f in files_list}
        project_dir = "firmware" if any(p.startswith("firmware/") for p in file_map) else "."

        try:
            sandbox_id = await self.runner.create(
                labels={"project_id": run_obj.project_id, "run_id": run_id},
                network_blocked=True,
            )
        except Exception as exc:
            self._fail(run_obj, f"[SANDBOX ERROR] {exc}")
            supabase_store.save_verification_run(run_obj)
            return run_obj

        try:
            await self.runner.upload_files(sandbox_id, file_map)

            self._log(run_obj, f"$ pio run -d {project_dir}")
            exit_code, stdout, stderr = await self.runner.run_command(
                sandbox_id, f"pio run -d {project_dir}"
            )
            if stdout:
                run_obj.logs += stdout if stdout.endswith("\n") else stdout + "\n"
            if stderr:
                run_obj.logs += stderr if stderr.endswith("\n") else stderr + "\n"

            if exit_code != 0:
                self._fail(
                    run_obj,
                    f"[BUILD FAILED] PlatformIO exited with code {exit_code}.",
                )
                DebugAgent.analyze_compiler_error(run_obj.project_id, stderr, stdout)
                return run_obj

            # Real flash/RAM numbers straight from the toolchain.
            size_code, size_out, size_err = await self.runner.run_command(
                sandbox_id, f"pio run -d {project_dir} -t size"
            )
            if size_code == 0 and size_out.strip():
                run_obj.logs += "\n[BUILD SIZE]\n" + size_out
                if not size_out.endswith("\n"):
                    run_obj.logs += "\n"
            elif size_err.strip():
                self._log(run_obj, f"[SIZE REPORT SKIPPED] {size_err.strip()[:200]}")

            artifact, reason = await self._collect_artifact(
                sandbox_id, project_dir, board, run_id, run_obj.project_id
            )
            if artifact is None:
                self._fail(run_obj, f"[ARTIFACT ERROR] {reason}")
                return run_obj

            self._artifacts[run_id] = artifact
            run_obj.artifact_name = artifact.artifact_name
            run_obj.artifact_size_bytes = artifact.total_bytes
            run_obj.artifact_format = artifact.format
            run_obj.artifact_available = True
            run_obj.firmware_binary_url = f"/api/v1/runs/{run_id}/artifact"
            run_obj.status = "passed"
            run_obj.completed_at = self._now()

            offsets = ", ".join(
                f"{segment.name}@{hex(segment.offset)}" for segment in artifact.segments
            )
            self._log(
                run_obj,
                f"[ARTIFACT] {artifact.artifact_name} ({human_size(artifact.total_bytes)}): {offsets}",
            )

            meta = artifact.model_dump(exclude={"segments"})
            persisted = supabase_store.save_verification_artifact(
                run_id, meta, artifact.model_dump_json().encode("utf-8")
            )
            if not persisted:
                self._log(
                    run_obj,
                    "[ARTIFACT WARNING] Artifact stored in memory only; it will not "
                    "survive a backend restart because object storage is unavailable.",
                )

            project.lifecycle = "verified"
            supabase_store.save_project(project, current_spec=spec)
        except Exception as exc:
            self._fail(run_obj, f"[VERIFICATION ERROR] {type(exc).__name__}: {exc}")
            logger.exception("Verification run %s failed", run_id)
        finally:
            supabase_store.save_verification_run(run_obj)
            await self.runner.destroy(sandbox_id)

        return run_obj

    @staticmethod
    def _offset(value) -> Optional[int]:
        """Accept 0x10000, 65536 or 0 from PlatformIO metadata."""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value, 0)
            except ValueError:
                return None
        return None

    @staticmethod
    def _sandbox_path(project_dir: str, path: str) -> str:
        if path.startswith("/"):
            return path
        if path.startswith("./"):
            path = path[2:]
        return f"{PROJECT_DIR}/{project_dir}/{path}"

    @staticmethod
    def _app_image(env: Dict, build_dir: str, sizes: Dict[str, int]) -> Optional[str]:
        """Path of the application image that belongs at ``application_offset``."""
        prog = env.get("prog_path")
        if isinstance(prog, str) and prog.endswith(".elf"):
            candidate = prog[:-4] + ".bin"
            if candidate.rsplit("/", 1)[-1] in sizes or candidate.startswith("/"):
                return candidate
        if "firmware.bin" in sizes:
            return f"{PROJECT_DIR}/{build_dir}/firmware.bin"
        return None

    async def _collect_artifact(
        self,
        sandbox_id: str,
        project_dir: str,
        board,
        run_id: str,
        project_id: str,
    ) -> Tuple[Optional[FirmwareArtifact], str]:
        """Download the images PlatformIO produced, with real flash offsets.

        PlatformIO's project metadata carries the upload plan it would use
        (``extra.flash_images`` plus ``application_offset``), so the offsets come
        from the toolchain rather than a hard-coded table.
        """
        build_root = f"{project_dir}/.pio/build"
        _, out, _ = await self.runner.run_command(
            sandbox_id, f"find {build_root} -mindepth 1 -maxdepth 1 -type d 2>/dev/null"
        )
        build_dirs = [line.strip() for line in out.splitlines() if line.strip()]
        if not build_dirs:
            return None, f"No build directory under {build_root}; the image was not produced."
        build_dir = build_dirs[0]

        _, listing, _ = await self.runner.run_command(
            sandbox_id,
            f"find {build_dir} -maxdepth 1 -type f "
            "\\( -name '*.bin' -o -name '*.uf2' -o -name '*.hex' -o -name 'flash_args' \\) "
            "-printf '%f %s\\n' 2>/dev/null",
        )
        sizes: Dict[str, int] = {}
        for line in listing.splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].isdigit():
                sizes[parts[0]] = int(parts[1])

        candidates: List[Tuple[int, str]] = []
        artifact_format = "esp-segments"

        # 1. The toolchain's own upload plan (ESP32 family).
        code, meta_out, _ = await self.runner.run_command(
            sandbox_id, f"pio project metadata --json-output -d {project_dir}"
        )
        if code == 0 and meta_out.strip():
            try:
                meta = json.loads(meta_out)
            except ValueError:
                meta = None
            if isinstance(meta, dict) and meta:
                env_name = getattr(board, "env_name", None)
                env = meta.get(env_name) if env_name else None
                if not isinstance(env, dict):
                    env = next(iter(meta.values()))
                extra = env.get("extra") if isinstance(env, dict) else None
                extra = extra if isinstance(extra, dict) else {}
                plan: List[Tuple[int, str]] = []
                for item in extra.get("flash_images") or []:
                    offset = self._offset(item.get("offset"))
                    path = item.get("path")
                    if offset is None or not isinstance(path, str):
                        plan = []
                        break
                    plan.append((offset, path))
                app_offset = self._offset(extra.get("application_offset"))
                if plan and app_offset is not None:
                    app = self._app_image(env, build_dir, sizes)
                    if app:
                        plan.append((app_offset, app))
                    else:
                        plan = []
                if plan:
                    candidates = [
                        (offset, self._sandbox_path(project_dir, path))
                        for offset, path in plan
                    ]

        # 2. Older platforms write a flash_args file next to the images.
        if not candidates and "flash_args" in sizes:
            _, flash_args, _ = await self.runner.run_command(
                sandbox_id, f"cat {build_dir}/flash_args 2>/dev/null"
            )
            candidates = [
                (offset, f"{PROJECT_DIR}/{build_dir}/{name}")
                for offset, name in parse_flash_args(flash_args)
                if name in sizes and "/" not in name and ".." not in name
            ]
            if not candidates:
                return None, "flash_args was present but listed no images that exist."

        # 3. Single-image platforms: UF2 (RP2040) and ESP8266.
        if not candidates:
            uf2 = next((name for name in sizes if name.endswith(".uf2")), None)
            if uf2:
                candidates = [(0, f"{PROJECT_DIR}/{build_dir}/{uf2}")]
                artifact_format = "uf2"
            elif board.platform == "espressif8266" and "firmware.bin" in sizes:
                # The ESP8266 Arduino core emits one combined image at 0x0.
                candidates = [(0, f"{PROJECT_DIR}/{build_dir}/firmware.bin")]
            else:
                return None, (
                    "PlatformIO did not report a flashable image for this board, "
                    "so there is nowhere safe to write the firmware."
                )

        flashed: List[ArtifactSegment] = []
        seen = set()
        for offset, path in candidates:
            name = path.rsplit("/", 1)[-1]
            if (offset, name) in seen:
                continue
            seen.add((offset, name))
            try:
                raw = await self.runner.download_file(sandbox_id, path)
            except Exception as exc:
                return None, f"Could not download {name}: {exc}"
            flashed.append(
                ArtifactSegment(
                    name=name,
                    offset=offset,
                    size=len(raw),
                    data_b64=base64.b64encode(raw).decode("ascii"),
                )
            )

        if not flashed:
            return None, "The build produced no downloadable images."

        flashed.sort(key=lambda segment: segment.offset)
        primary = next(
            (segment.name for segment in flashed if segment.name == "firmware.bin"),
            flashed[-1].name,
        )
        if artifact_format == "uf2":
            primary = flashed[0].name

        return (
            FirmwareArtifact(
                run_id=run_id,
                project_id=project_id,
                board_id=board.id,
                format=artifact_format,
                artifact_name=primary,
                total_bytes=sum(segment.size for segment in flashed),
                segments=flashed,
            ),
            "",
        )

    # -- reads -----------------------------------------------------------
    def get_run(self, run_id: str, user_id: str) -> VerificationRun:
        run_obj = self._runs.get(run_id)
        if not run_obj:
            raise NotFoundError(f"Verification run '{run_id}' not found")
        project_repo.get_project(run_obj.project_id, user_id)
        if run_obj.status == "passed" and not run_obj.artifact_available:
            self._attach_artifact_meta(run_obj)
        return run_obj

    def list_runs(self, project_id: str, user_id: str, limit: int = 20) -> List[VerificationRun]:
        project_repo.get_project(project_id, user_id)
        runs = [run for run in self._runs.values() if run.project_id == project_id]
        runs.sort(key=lambda run: run.created_at, reverse=True)
        runs = runs[:limit]
        for run_obj in runs:
            if run_obj.status == "passed" and not run_obj.artifact_available:
                self._attach_artifact_meta(run_obj)
        return runs

    def get_artifact(self, run_id: str, user_id: str) -> FirmwareArtifact:
        self.get_run(run_id, user_id)
        artifact = self._artifacts.get(run_id)
        if artifact is not None:
            return artifact

        payload = supabase_store.load_verification_artifact(run_id)
        if not payload:
            raise NotFoundError(
                f"No verified firmware artifact is available for run '{run_id}'. "
                "Run verification again to rebuild it."
            )
        try:
            artifact = FirmwareArtifact.model_validate_json(payload)
        except Exception as exc:
            raise NotFoundError(f"Stored artifact for run '{run_id}' is unreadable: {exc}")
        self._artifacts[run_id] = artifact
        return artifact

    def get_firmware_binary(self, run_id: str, user_id: str) -> bytes:
        """The primary image, used by the plain download button."""
        artifact = self.get_artifact(run_id, user_id)
        segment = next(
            (
                item
                for item in artifact.segments
                if item.name == artifact.artifact_name
            ),
            artifact.segments[-1],
        )
        return base64.b64decode(segment.data_b64)


verification_repo = VerificationRepository()
