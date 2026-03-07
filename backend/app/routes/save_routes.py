"""REST endpoints for save/restore functionality."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.engine.event_log import EventReplayer
from app.models.actions import CreateGameResponse, ListSavesResponse, SaveInfo
from app.routes.game_routes import engine, event_logger

router = APIRouter(prefix="/saves", tags=["saves"])

replayer = EventReplayer()


@router.get("/", response_model=ListSavesResponse)
def list_saves() -> ListSavesResponse:
    """List all available save files with metadata."""
    raw = replayer.list_saves()
    saves = [SaveInfo(**s) for s in raw]
    return ListSavesResponse(saves=saves)


@router.post("/restore/{game_id}", response_model=CreateGameResponse)
def restore_game(game_id: str) -> CreateGameResponse:
    """Replay a save file to restore a game, then register it in the active engine."""
    try:
        replay_engine, state = replayer.replay(game_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No save file for game {game_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay failed: {e}")

    # Transfer the restored game into the live engine so it can be played
    engine.games[game_id] = state
    return CreateGameResponse(game_id=game_id, state=state)


@router.delete("/{game_id}")
def delete_save(game_id: str) -> dict:
    """Delete a save file."""
    deleted = event_logger.delete(game_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No save file for game {game_id}")
    return {"deleted": True, "game_id": game_id}
