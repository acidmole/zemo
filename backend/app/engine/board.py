"""Board graph operations for Space Station Zemo."""

from __future__ import annotations

from collections import deque

from app.data.board_layout import BOARD_LAYOUT, ROOM_SPACE_IDS
from app.models.game_state import SpaceType


def get_adjacent_spaces(space_id: str) -> list[str]:
    """Return list of space IDs adjacent to the given space."""
    space = BOARD_LAYOUT.get(space_id)
    if space is None:
        return []
    return list(space["adjacent"])


def get_space_type(space_id: str) -> SpaceType:
    """Return the SpaceType of the given space."""
    space = BOARD_LAYOUT.get(space_id)
    if space is None:
        return SpaceType.HALLWAY
    return space["type"]


def is_room(space_id: str) -> bool:
    """Check if a space is a 'room' type (allows multiple occupants).

    Rooms, code rooms, escape pod, bio-vat, and airlock are all room-like.
    """
    return space_id in ROOM_SPACE_IDS


def get_reachable_spaces(
    space_id: str,
    max_distance: int,
    occupied_hallways: set[str],
    exclude_current: str | None = None,
) -> list[str]:
    """BFS to find all spaces reachable from space_id within max_distance steps.

    Rules:
    - Cannot enter or pass through a hallway occupied by another character.
    - CAN enter and pass through rooms even if occupied.
    - The starting space is always included (you can stay put).
    - exclude_current: the character's own space_id, so their own hallway
      doesn't block them from staying put (they are already there).

    Returns a list of reachable space IDs (including starting space).
    """
    reachable: list[str] = [space_id]
    visited: set[str] = {space_id}

    queue: deque[tuple[str, int]] = deque()
    queue.append((space_id, 0))

    while queue:
        current, dist = queue.popleft()

        if dist >= max_distance:
            continue

        for neighbor in get_adjacent_spaces(current):
            if neighbor in visited:
                continue

            # Check if the neighbor is a blocked hallway
            if not is_room(neighbor) and neighbor in occupied_hallways:
                # This hallway is occupied by another character; skip it
                if neighbor != exclude_current:
                    continue

            visited.add(neighbor)
            reachable.append(neighbor)
            queue.append((neighbor, dist + 1))

    return reachable


def get_distance(space_a: str, space_b: str) -> int:
    """Compute BFS shortest distance between two spaces (ignoring occupancy).

    Returns -1 if no path exists.
    """
    if space_a == space_b:
        return 0

    visited: set[str] = {space_a}
    queue: deque[tuple[str, int]] = deque()
    queue.append((space_a, 0))

    while queue:
        current, dist = queue.popleft()
        for neighbor in get_adjacent_spaces(current):
            if neighbor == space_b:
                return dist + 1
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))

    return -1


def get_space_info(space_id: str) -> dict | None:
    """Return the full space info dict from the board layout."""
    return BOARD_LAYOUT.get(space_id)
