from typing import List, Optional
from fastapi import APIRouter, Query
from app.core.exceptions import NotFoundError
from app.db.repositories.library_repo import library_repo
from app.models.library import Board, Pattern, Peripheral

router = APIRouter(prefix="/library", tags=["Hardware Library"])


@router.get("/boards", response_model=List[Board])
async def list_boards(
    include_untested: bool = Query(
        False, description="Whether to include draft/unverified boards (default tested only)"
    ),
) -> List[Board]:
    """Retrieve verified microcontroller boards from the hardware library."""
    return library_repo.list_boards(include_all=include_untested)


@router.get("/boards/{board_id}", response_model=Board)
async def get_board(board_id: str) -> Board:
    """Retrieve full hardware pinout, capabilities, and electrical specs for a board."""
    board = library_repo.get_board(board_id)
    if not board:
        raise NotFoundError(f"Board '{board_id}' not found in hardware library")
    return board


@router.get("/peripherals", response_model=List[Peripheral])
async def list_peripherals(
    query: Optional[str] = Query(
        None, description="Filter peripherals by component name, category, or interface"
    ),
) -> List[Peripheral]:
    """Retrieve verified sensors, actuators, and peripherals."""
    return library_repo.list_peripherals(query=query)


@router.get("/peripherals/{peripheral_id}", response_model=Peripheral)
async def get_peripheral(peripheral_id: str) -> Peripheral:
    """Retrieve specifications for a single peripheral component."""
    peripheral = library_repo.get_peripheral(peripheral_id)
    if not peripheral:
        raise NotFoundError(f"Peripheral '{peripheral_id}' not found in hardware library")
    return peripheral


@router.get("/patterns", response_model=List[Pattern])
async def list_patterns() -> List[Pattern]:
    """Retrieve architectural design patterns (deep sleep, periodic sampling, offline buffering)."""
    return library_repo.list_patterns()
