"""Event logging and replay for deterministic save/restore."""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.engine.rng import RngRecord, replay_rng

SAVES_DIR = Path(__file__).resolve().parent.parent.parent / "saves"


def _serialize_rng_state(state: Any) -> list:
    """Convert random.getstate() tuple to a JSON-serialisable list.

    The state is (version, internalstate_tuple, gauss_next).
    internalstate_tuple is a tuple of 625 ints.
    """
    version, internalstate, gauss = state
    return [version, list(internalstate), gauss]


def _deserialize_rng_state(data: list) -> tuple:
    """Convert JSON list back to random.setstate()-compatible tuple."""
    version, internalstate, gauss = data
    return (version, tuple(internalstate), gauss)


class EventLogger:
    """Appends game events as JSONL lines to per-game save files."""

    def __init__(self, saves_dir: Path | None = None) -> None:
        self._dir = saves_dir or SAVES_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._seqs: dict[str, int] = {}  # game_id -> next seq number

    def _path(self, game_id: str) -> Path:
        return self._dir / f"game_{game_id}.jsonl"

    def log(
        self,
        game_id: str,
        cmd: str,
        args: dict[str, Any],
        rng: RngRecord,
        *,
        extra: dict[str, Any] | None = None,
    ) -> None:
        seq = self._seqs.get(game_id, 0) + 1
        self._seqs[game_id] = seq

        entry: dict[str, Any] = {
            "seq": seq,
            "ts": datetime.now(timezone.utc).isoformat(),
            "cmd": cmd,
            "args": args,
            "rng_state": _serialize_rng_state(rng.state),
        }
        if extra:
            entry.update(extra)

        with open(self._path(game_id), "a") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")

    def delete(self, game_id: str) -> bool:
        p = self._path(game_id)
        if p.exists():
            p.unlink()
            self._seqs.pop(game_id, None)
            return True
        return False


class EventReplayer:
    """Reads a JSONL save file and replays events through a GameEngine."""

    def __init__(self, saves_dir: Path | None = None) -> None:
        self._dir = saves_dir or SAVES_DIR

    def list_saves(self) -> list[dict[str, Any]]:
        """Return metadata for all save files."""
        if not self._dir.exists():
            return []

        saves: list[dict[str, Any]] = []
        for p in sorted(self._dir.glob("game_*.jsonl")):
            game_id = p.stem.removeprefix("game_")
            events = self._read_events(p)
            if not events:
                continue

            # Extract metadata from the create_game event
            create_evt = events[0]
            args = create_evt.get("args", {})
            player_names = args.get("player_names", [])
            player_characters = args.get("player_characters", [])

            last_ts = events[-1].get("ts", "")

            saves.append({
                "game_id": game_id,
                "player_names": player_names,
                "player_characters": player_characters,
                "event_count": len(events),
                "last_activity": last_ts,
            })

        return saves

    def replay(self, game_id: str) -> Any:
        """Replay all events for a game, returning the restored GameState.

        Imports GameEngine locally to avoid circular imports.
        """
        from app.engine.game import GameEngine

        p = self._dir / f"game_{game_id}.jsonl"
        if not p.exists():
            raise FileNotFoundError(f"No save file for game {game_id}")

        events = self._read_events(p)
        if not events:
            raise ValueError(f"Save file for game {game_id} is empty")

        # Create a replay engine (no logger, replaying flag set)
        engine = GameEngine(_replaying=True)

        for evt in events:
            cmd = evt["cmd"]
            args = evt.get("args", {})
            rng_state = _deserialize_rng_state(evt["rng_state"])

            with replay_rng(rng_state):
                if cmd == "create_game":
                    from app.models.game_state import GameConfig

                    config = GameConfig(
                        player_characters=args["player_characters"],
                        player_codes=args["player_codes"],
                        player_names=args.get("player_names", []),
                    )
                    preserved_id = evt.get("game_id")
                    engine.create_game(config, game_id=preserved_id)
                elif cmd == "roll_movement":
                    engine.roll_movement(game_id, args["character_id"])
                elif cmd == "move":
                    engine.move_character(
                        game_id, args["character_id"], args["target_space_id"]
                    )
                elif cmd == "action":
                    from app.models.actions import ActionRequest
                    from app.models.game_state import ActionType, CodeValue

                    action_kwargs: dict[str, Any] = {
                        "character_id": args["character_id"],
                        "action_type": ActionType(args["action_type"]),
                    }
                    if "target_character_id" in args:
                        action_kwargs["target_character_id"] = args["target_character_id"]
                    if "code_value" in args:
                        action_kwargs["code_value"] = CodeValue(args["code_value"])
                    if "card_ids_to_pick" in args:
                        action_kwargs["card_ids_to_pick"] = args["card_ids_to_pick"]
                    if "weapon_card_id" in args:
                        action_kwargs["weapon_card_id"] = args["weapon_card_id"]
                    if "continue_fighting" in args:
                        action_kwargs["continue_fighting"] = args["continue_fighting"]

                    req = ActionRequest(**action_kwargs)
                    engine.perform_action(game_id, args["character_id"], req)
                elif cmd == "drop_cards":
                    engine.drop_cards(
                        game_id, args["character_id"], args["card_ids"]
                    )

        state = engine.get_state(game_id)
        return engine, state

    @staticmethod
    def _read_events(path: Path) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events
