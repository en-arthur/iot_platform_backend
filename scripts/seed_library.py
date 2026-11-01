#!/usr/bin/env python3
"""
Seed script for Hardware Library.
Populates Supabase PostgreSQL database tables:
- library_boards
- library_peripherals
- patterns
"""

import json
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.config import settings
from app.db.repositories.library_repo import (
    SEED_BOARDS,
    SEED_PERIPHERALS,
    SEED_PATTERNS,
)
from app.db.supabase_client import get_supabase_admin


def seed_library():
    print(f"Connecting to Supabase at: {settings.SUPABASE_URL}")
    supabase = get_supabase_admin()

    # 1. Seed Boards
    print(f"Seeding {len(SEED_BOARDS)} hardware boards...")
    for board in SEED_BOARDS:
        board_data = {
            "id": board.id,
            "name": board.name,
            "vendor": board.vendor,
            "mcu": board.mcu,
            "status": board.status,
            "specs": board.specs.model_dump(),
            "pin_map": {k: v.model_dump() for k, v in board.pin_map.items()},
            "tested_notes": board.tested_notes,
        }
        res = (
            supabase.table("library_boards")
            .upsert(board_data, on_conflict="id")
            .execute()
        )
        print(f"  [✓] Board: {board.name} ({board.id})")

    # 2. Seed Peripherals
    print(f"\nSeeding {len(SEED_PERIPHERALS)} peripheral components...")
    for p in SEED_PERIPHERALS:
        peri_data = {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "interface": p.interface,
            "default_address": p.default_address,
            "pins_required": p.pins_required,
            "status": p.status,
            "description": p.description,
        }
        res = (
            supabase.table("library_peripherals")
            .upsert(peri_data, on_conflict="id")
            .execute()
        )
        print(f"  [✓] Peripheral: {p.name} ({p.id})")

    # 3. Seed Patterns
    print(f"\nSeeding {len(SEED_PATTERNS)} architecture patterns...")
    for pt in SEED_PATTERNS:
        pt_data = {
            "id": pt.id,
            "name": pt.name,
            "description": pt.description,
            "category": pt.category,
            "template_slots": pt.template_slots,
            "status": pt.status,
        }
        res = (
            supabase.table("patterns")
            .upsert(pt_data, on_conflict="id")
            .execute()
        )
        print(f"  [✓] Pattern: {pt.name} ({pt.id})")

    print("\nHardware library seeded successfully!")


if __name__ == "__main__":
    try:
        seed_library()
    except Exception as e:
        print(f"Seeding failed: {e}", file=sys.stderr)
        sys.exit(1)
