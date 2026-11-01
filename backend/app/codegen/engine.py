from typing import Any, Dict, List, Optional
from app.codegen.cloud_generator import CloudBackendGenerator
from app.codegen.firmware_generator import ArduinoFirmwareGenerator
from app.codegen.interface_generator import InterfaceGenerator
from app.codegen.protected_regions import ProtectedRegionManager
from app.models.files import GeneratedFile


class CodegenEngine:
    """Orchestrates generation of Arduino firmware, cloud backend worker, and interface.
    Applies scoped regeneration and preserves protected user code regions.
    """

    @classmethod
    def generate_all(
        cls,
        project_id: str,
        version: int,
        spec: Dict[str, Any],
        existing_files: Optional[Dict[str, str]] = None,
        scope: Optional[List[str]] = None,
    ) -> List[GeneratedFile]:
        raw_files: List[GeneratedFile] = []

        # Determine scopes (default: all)
        should_gen_firmware = not scope or any(s in ("firmware", "hardware", "peripherals") for s in scope)
        should_gen_cloud = not scope or any(s in ("backend", "cloud_backend", "data_model") for s in scope)
        should_gen_interface = not scope or any(s in ("interface", "data_model") for s in scope)

        # 1. Arduino Firmware
        if should_gen_firmware:
            raw_files.extend(ArduinoFirmwareGenerator.generate(project_id, version, spec))

        # 2. Cloud Backend
        if should_gen_cloud:
            raw_files.extend(CloudBackendGenerator.generate(project_id, version, spec))

        # 3. Web Interface
        if should_gen_interface:
            raw_files.extend(InterfaceGenerator.generate(project_id, version, spec))

        # 4. Merge Protected User Code Regions from existing files
        final_files: List[GeneratedFile] = []
        existing_map = existing_files or {}

        for gen_file in raw_files:
            old_content = existing_map.get(gen_file.path)
            if old_content:
                merged_content, count = ProtectedRegionManager.merge_protected_regions(
                    newly_generated=gen_file.content, existing_file=old_content
                )
                final_files.append(
                    GeneratedFile(
                        id=gen_file.id,
                        project_id=project_id,
                        version_number=version,
                        path=gen_file.path,
                        content=merged_content,
                        file_type=gen_file.file_type,
                        is_protected=count > 0,
                    )
                )
            else:
                final_files.append(gen_file)

        return final_files


codegen_engine = CodegenEngine()
