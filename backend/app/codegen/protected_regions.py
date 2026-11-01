import re
from typing import Dict, Tuple

# Regex pattern for C/C++/Arduino protected regions
C_REGION_PATTERN = re.compile(
    r"/\*\s*USER CODE BEGIN\s+([A-Za-z0-9_-]+)\s*\*/(.*?)/\*\s*USER CODE END\s+\1\s*\*/",
    re.DOTALL,
)

# Regex pattern for Python / INI / YAML protected regions
HASH_REGION_PATTERN = re.compile(
    r"#\s*USER CODE BEGIN\s+([A-Za-z0-9_-]+)\s*(.*?)#\s*USER CODE END\s+\1",
    re.DOTALL,
)


class ProtectedRegionManager:
    """Detects and preserves manual developer edits across code regeneration."""

    @classmethod
    def extract_regions(cls, content: str) -> Dict[str, str]:
        """Extracts all user-edited regions from existing file content."""
        regions: Dict[str, str] = {}

        # 1. Check C-style comments
        for match in C_REGION_PATTERN.finditer(content):
            region_name = match.group(1).strip()
            region_code = match.group(2)
            regions[region_name] = region_code

        # 2. Check hash-style comments
        for match in HASH_REGION_PATTERN.finditer(content):
            region_name = match.group(1).strip()
            region_code = match.group(2)
            regions[region_name] = region_code

        return regions

    @classmethod
    def merge_protected_regions(
        cls, newly_generated: str, existing_file: str
    ) -> Tuple[str, int]:
        """Merges user code from existing_file into newly_generated template.
        Returns (merged_code, count_of_preserved_regions).
        """
        user_regions = cls.extract_regions(existing_file)
        if not user_regions:
            return newly_generated, 0

        merged = newly_generated
        preserved_count = 0

        # Replace in C-style comments
        def replace_c_region(match):
            nonlocal preserved_count
            name = match.group(1).strip()
            if name in user_regions and user_regions[name].strip():
                preserved_count += 1
                return f"/* USER CODE BEGIN {name} */{user_regions[name]}/* USER CODE END {name} */"
            return match.group(0)

        merged = C_REGION_PATTERN.sub(replace_c_region, merged)

        # Replace in hash-style comments
        def replace_hash_region(match):
            nonlocal preserved_count
            name = match.group(1).strip()
            if name in user_regions and user_regions[name].strip():
                preserved_count += 1
                return f"# USER CODE BEGIN {name}{user_regions[name]}# USER CODE END {name}"
            return match.group(0)

        merged = HASH_REGION_PATTERN.sub(replace_hash_region, merged)

        return merged, preserved_count
