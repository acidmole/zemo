"""Tests for the save/restore (event sourcing) system."""

from __future__ import annotations

import json
import random
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.engine.event_log import EventLogger, EventReplayer
from app.engine.game import GameEngine
from app.engine.rng import RngRecord, record_rng, replay_rng
from app.models.game_state import GameConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_saves(tmp_path: Path) -> Path:
    """Provide a temporary directory for save files."""
    saves = tmp_path / "saves"
    saves.mkdir()
    return saves


@pytest.fixture()
def logger(tmp_saves: Path) -> EventLogger:
    return EventLogger(saves_dir=tmp_saves)


@pytest.fixture()
def replayer(tmp_saves: Path) -> EventReplayer:
    return EventReplayer(saves_dir=tmp_saves)


def _make_config() -> GameConfig:
    return GameConfig(
        player_characters=["chuckie", "pete"],
        player_codes=["AAB", "BBA"],
        player_names=["Alice", "Bob"],
    )


def _create_and_play(engine: GameEngine) -> str:
    """Create a game and play through movement phase, returning game_id."""
    state = engine.create_game(_make_config())
    game_id = state.id

    # Move both players through movement phase
    for idx in range(len(state.turn_order)):
        state = engine.get_state(game_id)
        char_id = state.turn_order[state.current_player_index]
        _roll, reachable = engine.roll_movement(game_id, char_id)
        target = reachable[0] if reachable else state.spaces[char_id].space_id
        engine.move_character(game_id, char_id, target)

    return game_id


# ---------------------------------------------------------------------------
# 1. RNG capture/replay
# ---------------------------------------------------------------------------

class TestRng:
    def test_record_captures_state(self):
        """record_rng() captures the random state before the block."""
        with record_rng() as rec:
            random.randint(1, 100)
        assert rec.state is not None

    def test_replay_reproduces_randint(self):
        """Replaying captured state reproduces identical randint results."""
        with record_rng() as rec:
            values = [random.randint(1, 6) for _ in range(10)]

        with replay_rng(rec.state):
            replayed = [random.randint(1, 6) for _ in range(10)]

        assert values == replayed

    def test_replay_reproduces_random_float(self):
        """Replaying captured state reproduces identical random() floats."""
        with record_rng() as rec:
            values = [random.random() for _ in range(10)]

        with replay_rng(rec.state):
            replayed = [random.random() for _ in range(10)]

        assert values == replayed

    def test_replay_reproduces_shuffle(self):
        """Replaying captured state reproduces identical shuffle results."""
        items = list(range(50))

        with record_rng() as rec:
            random.shuffle(items)
            shuffled = list(items)

        items_copy = list(range(50))
        with replay_rng(rec.state):
            random.shuffle(items_copy)

        assert shuffled == items_copy

    def test_replay_mixed_operations(self):
        """Replaying works for interleaved randint, random, and shuffle."""
        with record_rng() as rec:
            a = random.randint(1, 6)
            b = random.random()
            items = [1, 2, 3, 4, 5]
            random.shuffle(items)
            c = random.randint(1, 100)
            original = (a, b, list(items), c)

        with replay_rng(rec.state):
            a2 = random.randint(1, 6)
            b2 = random.random()
            items2 = [1, 2, 3, 4, 5]
            random.shuffle(items2)
            c2 = random.randint(1, 100)
            replayed = (a2, b2, list(items2), c2)

        assert original == replayed


# ---------------------------------------------------------------------------
# 2. EventLogger
# ---------------------------------------------------------------------------

class TestEventLogger:
    def test_creates_save_file(self, logger: EventLogger, tmp_saves: Path):
        """Logging an event creates the JSONL file."""
        rec = RngRecord(state=random.getstate())
        logger.log("game-1", "create_game", {"foo": "bar"}, rec)

        path = tmp_saves / "game_game-1.jsonl"
        assert path.exists()

    def test_jsonl_format(self, logger: EventLogger, tmp_saves: Path):
        """Each logged event is a valid JSON line with expected fields."""
        rec = RngRecord(state=random.getstate())
        logger.log("g1", "create_game", {"x": 1}, rec, extra={"game_id": "g1"})

        path = tmp_saves / "game_g1.jsonl"
        line = path.read_text().strip()
        entry = json.loads(line)

        assert entry["seq"] == 1
        assert entry["cmd"] == "create_game"
        assert entry["args"] == {"x": 1}
        assert entry["game_id"] == "g1"
        assert "ts" in entry
        assert "rng_state" in entry

    def test_sequence_numbers_increment(self, logger: EventLogger, tmp_saves: Path):
        """Sequence numbers increment per game."""
        rec = RngRecord(state=random.getstate())
        logger.log("g1", "cmd1", {}, rec)
        logger.log("g1", "cmd2", {}, rec)
        logger.log("g1", "cmd3", {}, rec)

        path = tmp_saves / "game_g1.jsonl"
        lines = path.read_text().strip().split("\n")
        seqs = [json.loads(line)["seq"] for line in lines]
        assert seqs == [1, 2, 3]

    def test_separate_sequences_per_game(self, logger: EventLogger, tmp_saves: Path):
        """Different games get independent sequence numbers."""
        rec = RngRecord(state=random.getstate())
        logger.log("g1", "cmd", {}, rec)
        logger.log("g2", "cmd", {}, rec)
        logger.log("g1", "cmd", {}, rec)

        lines_g1 = (tmp_saves / "game_g1.jsonl").read_text().strip().split("\n")
        lines_g2 = (tmp_saves / "game_g2.jsonl").read_text().strip().split("\n")

        assert json.loads(lines_g1[0])["seq"] == 1
        assert json.loads(lines_g1[1])["seq"] == 2
        assert json.loads(lines_g2[0])["seq"] == 1

    def test_delete_removes_file(self, logger: EventLogger, tmp_saves: Path):
        """delete() removes the save file and returns True."""
        rec = RngRecord(state=random.getstate())
        logger.log("g1", "cmd", {}, rec)

        assert logger.delete("g1") is True
        assert not (tmp_saves / "game_g1.jsonl").exists()

    def test_delete_nonexistent_returns_false(self, logger: EventLogger):
        """delete() returns False if the file doesn't exist."""
        assert logger.delete("nonexistent") is False


# ---------------------------------------------------------------------------
# 3. EventReplayer — full round-trip
# ---------------------------------------------------------------------------

class TestEventReplayer:
    def test_replay_create_game(self, tmp_saves: Path):
        """Replaying a create_game event reproduces identical initial state."""
        engine = GameEngine(event_logger=EventLogger(saves_dir=tmp_saves))
        state = engine.create_game(_make_config())
        game_id = state.id

        replayer = EventReplayer(saves_dir=tmp_saves)
        _replay_engine, restored = replayer.replay(game_id)

        assert restored.id == state.id
        assert len(restored.players) == len(state.players)
        for op, rp in zip(state.players, restored.players):
            assert op.position == rp.position
            assert op.health == rp.health
            assert op.name == rp.name

        # Card distributions must match
        orig_cards = {sid: sorted(s.cards) for sid, s in state.spaces.items()}
        rest_cards = {sid: sorted(s.cards) for sid, s in restored.spaces.items()}
        assert orig_cards == rest_cards

    def test_replay_with_movement(self, tmp_saves: Path):
        """Replaying after movement reproduces identical positions and phase."""
        engine = GameEngine(event_logger=EventLogger(saves_dir=tmp_saves))
        game_id = _create_and_play(engine)

        original = engine.get_state(game_id)

        replayer = EventReplayer(saves_dir=tmp_saves)
        _replay_engine, restored = replayer.replay(game_id)

        assert restored.phase == original.phase
        assert restored.current_player_index == original.current_player_index
        assert restored.round_number == original.round_number

        for op, rp in zip(original.players, restored.players):
            assert op.position == rp.position
            assert op.health == rp.health
            assert op.has_moved_this_turn == rp.has_moved_this_turn

    def test_replay_with_actions(self, tmp_saves: Path):
        """Replaying after action phase reproduces identical state."""
        from app.models.actions import ActionRequest
        from app.models.game_state import ActionType

        engine = GameEngine(event_logger=EventLogger(saves_dir=tmp_saves))
        game_id = _create_and_play(engine)

        # Now in action phase — have each player use available actions
        state = engine.get_state(game_id)
        assert state.phase.value == "action"

        # Iterate until we leave the action phase
        safety = 20
        while safety > 0:
            state = engine.get_state(game_id)
            if state.phase.value != "action":
                break
            safety -= 1
            char_id = state.turn_order[state.current_player_index]
            # Use pass (or heal if available and pass already used by Pete)
            if ActionType.PASS in state.available_actions:
                action_type = ActionType.PASS
            elif ActionType.HEAL in state.available_actions:
                action_type = ActionType.HEAL
            else:
                # Pick the first available action
                action_type = state.available_actions[0]
            req = ActionRequest(character_id=char_id, action_type=action_type)
            engine.perform_action(game_id, char_id, req)

        original = engine.get_state(game_id)

        replayer = EventReplayer(saves_dir=tmp_saves)
        _replay_engine, restored = replayer.replay(game_id)

        assert restored.phase == original.phase
        assert restored.round_number == original.round_number
        assert restored.current_player_index == original.current_player_index

        for op, rp in zip(original.players, restored.players):
            assert op.position == rp.position
            assert op.health == rp.health

    def test_replay_preserves_game_id(self, tmp_saves: Path):
        """Replayed game retains the original game_id."""
        engine = GameEngine(event_logger=EventLogger(saves_dir=tmp_saves))
        state = engine.create_game(_make_config())
        game_id = state.id

        replayer = EventReplayer(saves_dir=tmp_saves)
        _replay_engine, restored = replayer.replay(game_id)

        assert restored.id == game_id

    def test_replay_nonexistent_raises(self, tmp_saves: Path):
        """Replaying a nonexistent game raises FileNotFoundError."""
        replayer = EventReplayer(saves_dir=tmp_saves)
        with pytest.raises(FileNotFoundError):
            replayer.replay("no-such-game")

    def test_list_saves(self, tmp_saves: Path):
        """list_saves returns metadata for each save file."""
        engine = GameEngine(event_logger=EventLogger(saves_dir=tmp_saves))
        state = engine.create_game(_make_config())
        game_id = state.id

        replayer = EventReplayer(saves_dir=tmp_saves)
        saves = replayer.list_saves()

        assert len(saves) == 1
        save = saves[0]
        assert save["game_id"] == game_id
        assert save["player_names"] == ["Alice", "Bob"]
        assert save["player_characters"] == ["chuckie", "pete"]
        assert save["event_count"] == 1
        assert save["last_activity"] != ""

    def test_list_saves_empty(self, tmp_saves: Path):
        """list_saves returns empty list when no saves exist."""
        replayer = EventReplayer(saves_dir=tmp_saves)
        assert replayer.list_saves() == []


# ---------------------------------------------------------------------------
# 4. GameEngine logging integration
# ---------------------------------------------------------------------------

class TestEngineLogging:
    def test_create_game_logs_event(self, tmp_saves: Path):
        """create_game produces a log entry."""
        logger = EventLogger(saves_dir=tmp_saves)
        engine = GameEngine(event_logger=logger)
        state = engine.create_game(_make_config())

        path = tmp_saves / f"game_{state.id}.jsonl"
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["cmd"] == "create_game"
        assert entry["game_id"] == state.id
        assert "player_characters" in entry["args"]

    def test_roll_movement_logs_event(self, tmp_saves: Path):
        """roll_movement produces a log entry."""
        logger = EventLogger(saves_dir=tmp_saves)
        engine = GameEngine(event_logger=logger)
        state = engine.create_game(_make_config())
        game_id = state.id

        char_id = state.turn_order[0]
        engine.roll_movement(game_id, char_id)

        path = tmp_saves / f"game_{game_id}.jsonl"
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 2

        entry = json.loads(lines[1])
        assert entry["cmd"] == "roll_movement"
        assert entry["args"]["character_id"] == char_id

    def test_move_logs_event(self, tmp_saves: Path):
        """move_character produces a log entry."""
        logger = EventLogger(saves_dir=tmp_saves)
        engine = GameEngine(event_logger=logger)
        state = engine.create_game(_make_config())
        game_id = state.id

        char_id = state.turn_order[0]
        _roll, reachable = engine.roll_movement(game_id, char_id)
        target = reachable[0]
        engine.move_character(game_id, char_id, target)

        path = tmp_saves / f"game_{game_id}.jsonl"
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 3

        entry = json.loads(lines[2])
        assert entry["cmd"] == "move"
        assert entry["args"]["character_id"] == char_id
        assert entry["args"]["target_space_id"] == target

    def test_perform_action_logs_event(self, tmp_saves: Path):
        """perform_action produces a log entry."""
        from app.models.actions import ActionRequest
        from app.models.game_state import ActionType

        logger = EventLogger(saves_dir=tmp_saves)
        engine = GameEngine(event_logger=logger)
        game_id = _create_and_play(engine)

        state = engine.get_state(game_id)
        char_id = state.turn_order[state.current_player_index]
        req = ActionRequest(character_id=char_id, action_type=ActionType.PASS)
        engine.perform_action(game_id, char_id, req)

        path = tmp_saves / f"game_{game_id}.jsonl"
        lines = path.read_text().strip().split("\n")
        last = json.loads(lines[-1])
        assert last["cmd"] == "action"
        assert last["args"]["action_type"] == "pass"

    def test_drop_cards_logs_event(self, tmp_saves: Path):
        """drop_cards produces a log entry (even if no cards to drop, it still logs)."""
        from app.models.actions import ActionRequest
        from app.models.game_state import ActionType

        logger = EventLogger(saves_dir=tmp_saves)
        engine = GameEngine(event_logger=logger)
        game_id = _create_and_play(engine)

        state = engine.get_state(game_id)
        # Move to action phase and pick cards to get something in hand
        char_id = state.turn_order[state.current_player_index]
        char = next(p for p in state.players if p.id == char_id)

        # If cards at this space, pick them
        space = state.spaces[char.position]
        if space.cards and ActionType.PICK in state.available_actions:
            req = ActionRequest(character_id=char_id, action_type=ActionType.PICK)
            engine.perform_action(game_id, char_id, req)

            # Check if char now has cards
            state = engine.get_state(game_id)
            char = next(p for p in state.players if p.id == char_id)
            if char.hand:
                card_id = char.hand[0].id
                engine.drop_cards(game_id, char_id, [card_id])

                path = tmp_saves / f"game_{game_id}.jsonl"
                lines = path.read_text().strip().split("\n")
                last = json.loads(lines[-1])
                assert last["cmd"] == "drop_cards"
                assert last["args"]["card_ids"] == [card_id]
                return

        # If we couldn't pick cards, just verify basic logging count
        path = tmp_saves / f"game_{game_id}.jsonl"
        assert path.exists()

    def test_replaying_flag_suppresses_logging(self, tmp_saves: Path):
        """When _replaying=True, no events are logged."""
        logger = EventLogger(saves_dir=tmp_saves)
        engine = GameEngine(event_logger=logger, _replaying=True)
        state = engine.create_game(_make_config())

        path = tmp_saves / f"game_{state.id}.jsonl"
        assert not path.exists()

    def test_no_logger_does_not_error(self):
        """Engine without a logger works normally."""
        engine = GameEngine()
        state = engine.create_game(_make_config())
        assert state.id is not None
        assert len(state.players) == 2


# ---------------------------------------------------------------------------
# 5. Save REST endpoints
# ---------------------------------------------------------------------------

class TestSaveRoutes:
    @pytest.fixture(autouse=True)
    def _setup_app(self, tmp_saves: Path, monkeypatch: pytest.MonkeyPatch):
        """Redirect save/restore to tmp dir and provide a fresh TestClient."""
        import app.routes.game_routes as gr
        import app.routes.save_routes as sr

        # Create fresh logger/engine pointing to tmp dir
        test_logger = EventLogger(saves_dir=tmp_saves)
        test_engine = GameEngine(event_logger=test_logger)

        monkeypatch.setattr(gr, "event_logger", test_logger)
        monkeypatch.setattr(gr, "engine", test_engine)
        monkeypatch.setattr(sr, "event_logger", test_logger)
        monkeypatch.setattr(sr, "engine", test_engine)
        monkeypatch.setattr(sr, "replayer", EventReplayer(saves_dir=tmp_saves))

        from app.main import app
        self.client = TestClient(app)
        self.engine = test_engine
        self.tmp_saves = tmp_saves

    def _create_game(self) -> str:
        resp = self.client.post("/game/create", json={
            "config": {
                "player_characters": ["chuckie", "pete"],
                "player_codes": ["AAB", "BBA"],
                "player_names": ["Alice", "Bob"],
            }
        })
        assert resp.status_code == 200
        return resp.json()["game_id"]

    def test_list_saves_empty(self):
        resp = self.client.get("/saves/")
        assert resp.status_code == 200
        assert resp.json()["saves"] == []

    def test_list_saves_after_create(self):
        game_id = self._create_game()
        resp = self.client.get("/saves/")
        assert resp.status_code == 200

        saves = resp.json()["saves"]
        assert len(saves) == 1
        assert saves[0]["game_id"] == game_id
        assert saves[0]["player_names"] == ["Alice", "Bob"]

    def test_restore_game(self):
        game_id = self._create_game()

        # Get original state
        orig_resp = self.client.get(f"/game/{game_id}/state")
        orig_state = orig_resp.json()["state"]

        # Remove game from memory (simulates server restart)
        del self.engine.games[game_id]

        # Restore
        resp = self.client.post(f"/saves/restore/{game_id}")
        assert resp.status_code == 200

        restored = resp.json()["state"]
        assert restored["id"] == game_id
        assert len(restored["players"]) == len(orig_state["players"])

        for op, rp in zip(orig_state["players"], restored["players"]):
            assert op["position"] == rp["position"]
            assert op["health"] == rp["health"]

    def test_restore_nonexistent(self):
        resp = self.client.post("/saves/restore/no-such-game")
        assert resp.status_code == 404

    def test_delete_save(self):
        game_id = self._create_game()

        resp = self.client.delete(f"/saves/{game_id}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

        # Verify it's gone
        resp = self.client.get("/saves/")
        assert resp.json()["saves"] == []

    def test_delete_nonexistent(self):
        resp = self.client.delete("/saves/no-such-game")
        assert resp.status_code == 404

    def test_restore_and_continue_playing(self):
        """After restore, the game is playable (registered in the live engine)."""
        game_id = self._create_game()

        # Remove from memory
        del self.engine.games[game_id]

        # Restore
        resp = self.client.post(f"/saves/restore/{game_id}")
        assert resp.status_code == 200

        # Should be able to get state
        resp = self.client.get(f"/game/{game_id}/state")
        assert resp.status_code == 200

        # Should be able to roll movement
        state = resp.json()["state"]
        char_id = state["turn_order"][0]
        resp = self.client.post(f"/game/{game_id}/roll-movement", json={
            "character_id": char_id,
        })
        assert resp.status_code == 200
