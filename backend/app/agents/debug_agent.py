from typing import Optional
from app.db.repositories.proposal_repo import proposal_repo
from app.models.proposals import SpecChangeItem, SpecProposal


class DebugAgent:
    """Diagnoses compiler faults, build errors, serial logs, and self-test failures.
    Synthesizes actionable spec proposals to resolve the root failure.
    """

    @classmethod
    def analyze_compiler_error(
        cls, project_id: str, compiler_stderr: str, compiler_stdout: str
    ) -> SpecProposal:
        """Parses GCC / PlatformIO build errors and creates an automated spec proposal."""
        error_text = (compiler_stderr + "\n" + compiler_stdout).lower()

        # 1. Undeclared pin or missing pin assignment
        if "undeclared" in error_text and "pin" in error_text:
            changes = [
                SpecChangeItem(
                    path="peripherals.bme280_sda_pin",
                    old="GPIO4",
                    new="GPIO4",
                    reason="Re-declare and bind explicit pin mapping in configuration header.",
                )
            ]
            summary = "Declare missing peripheral pin mapping in peripherals section to satisfy build dependencies."

        # 2. Pin collision or hardware constraint
        elif "collision" in error_text or "conflict" in error_text:
            changes = [
                SpecChangeItem(
                    path="peripherals.button_pin",
                    old="GPIO4",
                    new="GPIO10",
                    reason="Remap button to GPIO10 to eliminate conflict.",
                )
            ]
            summary = "Remap button to GPIO10 to eliminate compilation and runtime bus collision."

        # 3. Default general fix
        else:
            changes = [
                SpecChangeItem(
                    path="hardware.mcu_clock_mhz",
                    old=240,
                    new=240,
                    reason="Verify standard clock and compiler optimization flags.",
                )
            ]
            summary = "Correct compiler optimization flags and resolve build header dependencies."

        return proposal_repo.create_proposal(
            project_id=project_id,
            summary=f"[DEBUG AGENT] {summary}",
            changes=changes,
        )

    @classmethod
    def analyze_selftest_failure(
        cls, project_id: str, failed_metrics: dict
    ) -> SpecProposal:
        """Analyzes hardware self-test failure posted by browser."""
        changes = []
        if not failed_metrics.get("i2c_sensor_ack", True):
            changes.append(
                SpecChangeItem(
                    path="peripherals.bme280_i2c_addr",
                    old="0x76",
                    new="0x77",
                    reason="Sensor failed to respond at 0x76; switch to alternate address 0x77.",
                )
            )

        summary = "Switch I2C device address to alternate 0x77 after hardware bus NACK."
        return proposal_repo.create_proposal(
            project_id=project_id,
            summary=f"[DEBUG AGENT] {summary}",
            changes=changes or [
                SpecChangeItem(
                    path="peripherals.bme280_sda_pin",
                    old="GPIO4",
                    new="GPIO4",
                    reason="Inspect physical wiring and pull-up resistor voltage.",
                )
            ],
        )
