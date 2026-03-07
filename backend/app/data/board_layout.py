"""Board layout definition for Space Station Zemo.

32 numbered spaces forming a rectangular perimeter loop,
plus special interior spaces (code rooms, escape pod, bio-vat, airlock).
"""

from __future__ import annotations

from app.models.game_state import SpaceType

# Named rooms mapped by space ID
ROOM_NAMES: dict[str, str] = {
    "7": "Reactor Room",
    "11": "Security",
    "13": "The Brig",
    "17": "The Armory",
    "21": "Vending Machines",
    "22": "Lavatory",
    "23": "Lost and Found",
    "25": "Casino",
    "26": "The Zemo Zoo",
    "29": "Kitchen",
    "32": "Command Control",
    "code_room_1": "Code Room 1",
    "code_room_2": "Code Room 2",
    "code_room_3": "Code Room 3",
    "escape_pod": "Escape Pod",
    "bio_vat": "Bio-Vat",
    "airlock": "Airlock",
}

ROOM_SPACE_IDS: set[str] = {
    "7", "11", "13", "17", "21", "22", "23", "25", "26", "29", "32",
    "code_room_1", "code_room_2", "code_room_3",
    "escape_pod", "bio_vat", "airlock",
}


def _get_space_type(space_id: str) -> SpaceType:
    if space_id.startswith("code_room"):
        return SpaceType.CODE_ROOM
    if space_id == "escape_pod":
        return SpaceType.ESCAPE_POD
    if space_id == "bio_vat":
        return SpaceType.BIO_VAT
    if space_id == "airlock":
        return SpaceType.AIRLOCK
    if space_id in ROOM_SPACE_IDS:
        return SpaceType.ROOM
    return SpaceType.HALLWAY


def _build_board() -> dict[str, dict]:
    """Build the complete board layout graph."""
    board: dict[str, dict] = {}

    # --- Numbered spaces 1-32 around the perimeter ---

    # Top row: spaces 1-9, y=80, x from 60 to 860
    top_count = 9
    top_x_start = 60.0
    top_x_end = 860.0
    top_y = 80.0
    top_spacing = (top_x_end - top_x_start) / (top_count - 1)

    for i in range(top_count):
        sid = str(i + 1)
        board[sid] = {
            "type": _get_space_type(sid),
            "name": ROOM_NAMES.get(sid, f"Space {sid}"),
            "adjacent": [],
            "x": top_x_start + i * top_spacing,
            "y": top_y,
        }

    # Right column: spaces 10-16, x=860, y from 180 to 780
    right_count = 7
    right_y_start = 180.0
    right_y_end = 780.0
    right_x = 860.0
    right_spacing = (right_y_end - right_y_start) / (right_count - 1)

    for i in range(right_count):
        sid = str(10 + i)
        board[sid] = {
            "type": _get_space_type(sid),
            "name": ROOM_NAMES.get(sid, f"Space {sid}"),
            "adjacent": [],
            "x": right_x,
            "y": right_y_start + i * right_spacing,
        }

    # Bottom row: spaces 17-24, y=780, x from 760 to 60
    bottom_count = 8
    bottom_x_start = 760.0
    bottom_x_end = 60.0
    bottom_y = 780.0
    bottom_spacing = (bottom_x_end - bottom_x_start) / (bottom_count - 1)

    for i in range(bottom_count):
        sid = str(17 + i)
        board[sid] = {
            "type": _get_space_type(sid),
            "name": ROOM_NAMES.get(sid, f"Space {sid}"),
            "adjacent": [],
            "x": bottom_x_start + i * bottom_spacing,
            "y": bottom_y,
        }

    # Left column: spaces 25-32, x=60, y from 680 to 180
    left_count = 8
    left_y_start = 680.0
    left_y_end = 180.0
    left_x = 60.0
    left_spacing = (left_y_end - left_y_start) / (left_count - 1)

    for i in range(left_count):
        sid = str(25 + i)
        board[sid] = {
            "type": _get_space_type(sid),
            "name": ROOM_NAMES.get(sid, f"Space {sid}"),
            "adjacent": [],
            "x": left_x,
            "y": left_y_start + i * left_spacing,
        }

    # --- Build perimeter loop adjacency (1-2-3-...-32-1) ---
    for i in range(1, 33):
        sid = str(i)
        prev_sid = str(32 if i == 1 else i - 1)
        next_sid = str(1 if i == 32 else i + 1)
        board[sid]["adjacent"] = [prev_sid, next_sid]

    # --- Special interior spaces ---
    board["code_room_1"] = {
        "type": SpaceType.CODE_ROOM,
        "name": "Code Room 1",
        "adjacent": ["3", "4"],
        "x": 300.0,
        "y": 200.0,
    }
    board["code_room_2"] = {
        "type": SpaceType.CODE_ROOM,
        "name": "Code Room 2",
        "adjacent": ["1", "32"],
        "x": 160.0,
        "y": 130.0,
    }
    board["code_room_3"] = {
        "type": SpaceType.CODE_ROOM,
        "name": "Code Room 3",
        "adjacent": ["15", "16"],
        "x": 700.0,
        "y": 680.0,
    }
    board["escape_pod"] = {
        "type": SpaceType.ESCAPE_POD,
        "name": "Escape Pod",
        "adjacent": ["5", "12", "20", "28"],
        "x": 460.0,
        "y": 430.0,
    }
    board["bio_vat"] = {
        "type": SpaceType.BIO_VAT,
        "name": "Bio-Vat",
        "adjacent": ["6"],
        "x": 460.0,
        "y": 250.0,
    }
    board["airlock"] = {
        "type": SpaceType.AIRLOCK,
        "name": "Airlock",
        "adjacent": ["19"],
        "x": 460.0,
        "y": 600.0,
    }

    # --- Add reverse adjacency for special spaces ---
    # Each special space's neighbors should also list the special space.
    for special_id in ["code_room_1", "code_room_2", "code_room_3",
                        "escape_pod", "bio_vat", "airlock"]:
        for neighbor_id in board[special_id]["adjacent"]:
            if special_id not in board[neighbor_id]["adjacent"]:
                board[neighbor_id]["adjacent"].append(special_id)

    return board


BOARD_LAYOUT: dict[str, dict] = _build_board()

# Set of all space IDs
ALL_SPACE_IDS: set[str] = set(BOARD_LAYOUT.keys())

# Set of numbered space IDs (1-32) where cards are dealt
NUMBERED_SPACE_IDS: list[str] = [str(i) for i in range(1, 33)]
