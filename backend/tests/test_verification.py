import base64
import pytest
from types import SimpleNamespace
from app.agents.debug_agent import DebugAgent
from app.core.config import settings
from app.db.repositories.verification_repo import verification_repo
from app.sandbox.artifacts import human_size, parse_flash_args
from app.sandbox.e2b_runner import E2BSandboxRunner


@pytest.mark.asyncio
async def test_sandbox_refuses_to_run_without_e2b_key(monkeypatch):
    """A missing E2B key must fail loudly, never produce a fake pass."""
    monkeypatch.setattr(settings, "E2B_API_KEY", None)
    runner = E2BSandboxRunner(template="esp32-pio")
    assert runner.configured is False
    with pytest.raises(RuntimeError, match="E2B is not configured"):
        await runner.create()


def test_parse_flash_args_reads_offsets_and_skips_flags():
    text = """--flash_mode dio --flash_size 8MB
0x0000 bootloader.bin
0x8000 partitions.bin
0xe000 boot_app0.bin
0x10000 firmware.bin
0x10000 firmware.bin
"""
    assert parse_flash_args(text) == [
        (0x0000, "bootloader.bin"),
        (0x8000, "partitions.bin"),
        (0xE000, "boot_app0.bin"),
        (0x10000, "firmware.bin"),
    ]


def test_human_size():
    assert human_size(512) == "512 B"
    assert human_size(2048) == "2.0 KB"


def test_get_verification_run_unknown_is_404(client, create_test_token):
    token = create_test_token()
    response = client.get(
        "/api/v1/runs/run-does-not-exist",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_trigger_verification_run(client, create_test_token):
    token = create_test_token()
    response = client.post(
        "/api/v1/projects/proj-greenhouse-01/verify",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "running"
    assert "e2b" in data["message"].lower()


def test_list_verification_runs(client, create_test_token):
    token = create_test_token()
    verification_repo.create_run("proj-greenhouse-01", "test-user-uuid-1")
    response = client.get(
        "/api/v1/projects/proj-greenhouse-01/runs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    runs = response.json()
    assert isinstance(runs, list)
    assert any(run["project_id"] == "proj-greenhouse-01" for run in runs)


def test_stream_verification_logs(client, create_test_token):
    token = create_test_token()
    run = verification_repo.create_run("proj-greenhouse-01", "test-user-uuid-1")
    response = client.get(
        f"/api/v1/runs/{run.run_id}/stream",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    content = response.text
    assert "event: status" in content
    assert "event: done" in content


def test_artifact_is_not_fabricated(client, create_test_token):
    """A run without a real build must not serve a binary."""
    token = create_test_token()
    run = verification_repo.create_run("proj-greenhouse-01", "test-user-uuid-1")
    response = client.get(
        f"/api/v1/runs/{run.run_id}/artifact",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert "No verified firmware artifact" in response.text


@pytest.mark.asyncio
async def test_pipeline_fails_honestly_without_e2b_key(client, create_test_token, monkeypatch):
    monkeypatch.setattr(settings, "E2B_API_KEY", None)
    run = verification_repo.create_run("proj-greenhouse-01", "test-user-uuid-1")
    result = await verification_repo.execute_run_pipeline(run.run_id, "test-user-uuid-1")

    assert result.status == "failed"
    assert "E2B is not configured" in result.logs
    assert result.artifact_available is False
    assert result.artifact_name is None


class _FakeSandbox:
    """Returns the files a PlatformIO build would leave behind."""

    def __init__(self, flash_args, binaries):
        self.flash_args = flash_args
        self.binaries = binaries

    async def run_command(self, sandbox_id, cmd):
        if "-type d" in cmd:
            return 0, "/home/user/project/firmware/.pio/build/esp32s3\n", ""
        if "-printf" in cmd:
            lines = [f"{name} {len(data)}" for name, data in self.binaries.items()]
            if self.flash_args is not None:
                lines.append(f"flash_args {len(self.flash_args)}")
            return 0, "\n".join(lines) + "\n", ""
        if cmd.startswith("cat ") and "flash_args" in cmd:
            return 0, self.flash_args or "", ""
        return 1, "", "unexpected command"

    async def download_file(self, sandbox_id, path):
        return self.binaries[path.rsplit("/", 1)[-1]]


@pytest.mark.asyncio
async def test_artifact_uses_flash_args_offsets_for_esp32():
    binaries = {
        "bootloader.bin": b"BOOT",
        "partitions.bin": b"PART",
        "boot_app0.bin": b"OTA0",
        "firmware.bin": b"APP-IMAGE",
    }
    flash_args = """--flash_mode dio --flash_size 8MB
0x0000 bootloader.bin
0x8000 partitions.bin
0xe000 boot_app0.bin
0x10000 firmware.bin
"""
    verification_repo.runner = _FakeSandbox(flash_args, binaries)
    try:
        artifact, reason = await verification_repo._collect_artifact(
            "sandbox-1",
            "firmware",
            SimpleNamespace(platform="espressif32", id="esp32-s3-devkitc-1"),
            "run-unit-1",
            "proj-unit-1",
        )
    finally:
        verification_repo.runner = E2BSandboxRunner()

    assert artifact is not None, reason
    assert artifact.format == "esp-segments"
    assert artifact.artifact_name == "firmware.bin"
    assert artifact.total_bytes == sum(len(item) for item in binaries.values())
    assert [(item.name, item.offset) for item in artifact.segments] == [
        ("bootloader.bin", 0x0000),
        ("partitions.bin", 0x8000),
        ("boot_app0.bin", 0xE000),
        ("firmware.bin", 0x10000),
    ]
    decoded = {
        item.name: base64.b64decode(item.data_b64) for item in artifact.segments
    }
    assert decoded == binaries


@pytest.mark.asyncio
async def test_esp8266_single_image_flashes_at_zero():
    verification_repo.runner = _FakeSandbox(None, {"firmware.bin": b"ESP8266"})
    try:
        artifact, reason = await verification_repo._collect_artifact(
            "sandbox-2",
            "firmware",
            SimpleNamespace(platform="espressif8266", id="nodemcuv2"),
            "run-unit-2",
            "proj-unit-2",
        )
    finally:
        verification_repo.runner = E2BSandboxRunner()

    assert artifact is not None, reason
    assert artifact.format == "esp-segments"
    assert [(item.name, item.offset) for item in artifact.segments] == [
        ("firmware.bin", 0)
    ]


@pytest.mark.asyncio
async def test_debug_agent_compiler_error_analysis():
    stderr_sample = "error: 'D4' was not declared in this scope; did you mean 'GPIO4'?"
    proposal = DebugAgent.analyze_compiler_error(
        "proj-greenhouse-01", stderr_sample, ""
    )
    assert proposal is not None
    assert "debug agent" in proposal.summary.lower()
    assert len(proposal.changes) > 0
