"""Board layout definition for Space Station Zemo.

Loaded from board.json, which tools/board_trace.py generates from the traced
original board. Rooms 1-32 and the special rooms (code rooms, escape pod,
bio-vat, airlock) are joined by hallway squares; doors link a room to the
hallway squares it opens onto.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.models.game_state import SpaceType

BOARD_JSON_PATH = Path(__file__).resolve().parent / "board.json"

BOARD_DATA: dict = json.loads(BOARD_JSON_PATH.read_text())


def _build_board() -> dict[str, dict]:
    """Build the adjacency graph keyed by space ID."""
    board: dict[str, dict] = {}
    for space in BOARD_DATA["spaces"]:
        board[space["id"]] = {
            "type": SpaceType(space["type"]),
            "name": space["name"],
            "adjacent": [],
            "x": space["x"],
            "y": space["y"],
            "tags": space.get("tags", []),
        }
    for edge in BOARD_DATA["edges"]:
        board[edge["a"]]["adjacent"].append(edge["b"])
        board[edge["b"]]["adjacent"].append(edge["a"])
    return board


BOARD_LAYOUT: dict[str, dict] = _build_board()

# Set of all space IDs
ALL_SPACE_IDS: set[str] = set(BOARD_LAYOUT.keys())

# Every non-hallway space allows multiple occupants
ROOM_SPACE_IDS: set[str] = {
    sid for sid, space in BOARD_LAYOUT.items() if space["type"] != SpaceType.HALLWAY
}

# Named rooms mapped by space ID (hallway squares are unnamed)
ROOM_NAMES: dict[str, str] = {sid: BOARD_LAYOUT[sid]["name"] for sid in ROOM_SPACE_IDS}

# Numbered rooms (1-32) where cards are dealt and characters start
NUMBERED_SPACE_IDS: list[str] = [str(i) for i in range(1, 33)]
