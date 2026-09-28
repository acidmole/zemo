"""Tests for the board graph traced from the original Space Station Zemo board."""

from __future__ import annotations

from collections import deque

import pytest
from fastapi.testclient import TestClient

from app.data.board_layout import BOARD_DATA, BOARD_LAYOUT, NUMBERED_SPACE_IDS, ROOM_SPACE_IDS
from app.engine import board
from app.engine.game import GameEngine
from app.main import app
from app.models.game_state import GameConfig, SpaceType

SPECIAL_ROOMS = {"code_room_1", "code_room_2", "code_room_3", "escape_pod", "bio_vat", "airlock"}


def _hallways() -> set[str]:
    return {sid for sid, s in BOARD_LAYOUT.items() if s["type"] == SpaceType.HALLWAY}


# ---------------------------------------------------------------------------
# Graph structure
# ---------------------------------------------------------------------------

class TestGraph:
    def test_rooms_are_numbered_and_special(self):
        assert ROOM_SPACE_IDS == set(NUMBERED_SPACE_IDS) | SPECIAL_ROOMS

    def test_space_counts(self):
        assert len(ROOM_SPACE_IDS) == 38
        assert len(_hallways()) == 112

    def test_adjacency_is_symmetric(self):
        for sid, space in BOARD_LAYOUT.items():
            for neighbor in space["adjacent"]:
                assert sid in BOARD_LAYOUT[neighbor]["adjacent"], (sid, neighbor)

    def test_no_duplicate_edges(self):
        pairs = [frozenset((e["a"], e["b"])) for e in BOARD_DATA["edges"]]
        assert len(pairs) == len(set(pairs))

    def test_board_is_connected(self):
        seen = {"1"}
        queue = deque(["1"])
        while queue:
            for neighbor in board.get_adjacent_spaces(queue.popleft()):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        assert seen == set(BOARD_LAYOUT)

    def test_every_room_has_a_door_to_a_hallway(self):
        hallways = _hallways()
        for rid in ROOM_SPACE_IDS:
            assert any(n in hallways for n in board.get_adjacent_spaces(rid)), rid

    def test_rooms_only_connect_to_hallways(self):
        hallways = _hallways()
        for rid in ROOM_SPACE_IDS:
            assert set(board.get_adjacent_spaces(rid)) <= hallways, rid

    def test_escape_pod_has_four_approach_spaces(self):
        assert sorted(board.get_adjacent_spaces("escape_pod")) == [
            "ring_ne", "ring_nw", "ring_se", "ring_sw",
        ]

    def test_x_ray_sectors_are_tagged(self):
        tagged = {sid for sid, s in BOARD_LAYOUT.items() if "x_ray" in s["tags"]}
        assert tagged == {"ring_e", "ring_w"}


# ---------------------------------------------------------------------------
# Distances match the printed board
# ---------------------------------------------------------------------------

class TestDistances:
    @pytest.mark.parametrize(
        ("a", "b", "expected"),
        [
            ("2", "6", 2),                     # both doors open onto the same square
            ("code_room_1", "1", 3),           # CR1 -> h_0_1 -> h_0_2 -> room 1
            ("32", "h_12_0", 1),               # Control Room door
            ("h_9_12", "h_12_12", 2),          # bottom corridor passes through the Airlock
            ("h_8_6", "h_12_6", 5),            # middle corridor goes round the pod ring
            ("13", "ne_3", 2),                 # Brig -> branch -> NE corridor
            ("escape_pod", "25", 4),           # pod -> ring_se -> sebelt_1 -> sebelt_2 -> Casino
        ],
    )
    def test_distance(self, a: str, b: str, expected: int):
        assert board.get_distance(a, b) == expected


# ---------------------------------------------------------------------------
# Movement rules on the new graph
# ---------------------------------------------------------------------------

class TestMovement:
    def test_occupied_hallway_blocks_passage(self):
        free = board.get_reachable_spaces("2", 2, occupied_hallways=set())
        blocked = board.get_reachable_spaces("2", 2, occupied_hallways={"h_3_3"})
        assert "6" in free
        assert "6" not in blocked
        assert "h_3_3" not in blocked

    def test_rooms_can_be_passed_through(self):
        # The Airlock is a room, so it never blocks the bottom corridor
        reachable = board.get_reachable_spaces("h_9_12", 2, occupied_hallways=set())
        assert "h_12_12" in reachable

    def test_entering_a_room_costs_one_step(self):
        assert board.get_reachable_spaces("h_3_3", 1, occupied_hallways=set()) == [
            "h_3_3", *board.get_adjacent_spaces("h_3_3"),
        ]


# ---------------------------------------------------------------------------
# Engine integration
# ---------------------------------------------------------------------------

def _config() -> GameConfig:
    return GameConfig(
        player_characters=["chuckie", "pete", "floyd", "rats"],
        player_codes=["AAA", "BBB", "ABA", "BAB"],
        player_names=["A", "B", "C", "D"],
    )


class TestEngine:
    def test_characters_start_in_numbered_rooms(self):
        engine = GameEngine()
        for _ in range(25):
            state = engine.create_game(_config())
            for p in state.players:
                assert p.position in NUMBERED_SPACE_IDS

    def test_cards_are_dealt_to_rooms_only(self):
        state = GameEngine().create_game(_config())
        for sid, space in state.spaces.items():
            if space.cards:
                assert sid in NUMBERED_SPACE_IDS

    def test_fight_reaches_across_a_door(self):
        engine = GameEngine()
        state = engine.create_game(_config())
        a, b, c, d = state.players
        a.position, b.position = "2", "h_3_3"   # room 2's door opens onto h_3_3
        c.position, d.position = "12", "20"     # far apart
        assert b.id in engine._get_fight_targets(state, a)
        assert c.id not in engine._get_fight_targets(state, a)


def test_board_endpoint_serves_board_data():
    response = TestClient(app).get("/board")
    assert response.status_code == 200
    body = response.json()
    assert body["image"]["src"] == "/board.webp"
    assert len(body["spaces"]) == len(BOARD_LAYOUT)
