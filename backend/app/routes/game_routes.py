"""FastAPI routes for Space Station Zemo game API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.engine.event_log import EventLogger
from app.engine.game import GameEngine, GameError
from app.models.actions import (
    ActionRequest,
    ActionResponse,
    CreateGameRequest,
    CreateGameResponse,
    DropCardsRequest,
    GameStateResponse,
    MoveRequest,
    MoveResponse,
    RollMovementRequest,
    RollMovementResponse,
)

router = APIRouter(prefix="/game", tags=["game"])

# Global game engine instance with event logging
event_logger = EventLogger()
engine = GameEngine(event_logger=event_logger)


@router.post("/create", response_model=CreateGameResponse)
def create_game(request: CreateGameRequest) -> CreateGameResponse:
    """Create a new game with the specified configuration."""
    try:
        state = engine.create_game(request.config)
        return CreateGameResponse(game_id=state.id, state=state)
    except GameError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/roll-movement", response_model=RollMovementResponse)
def roll_movement(game_id: str, request: RollMovementRequest) -> RollMovementResponse:
    """Roll dice for the current player's movement."""
    try:
        state = engine.get_state(game_id)
        roll, reachable = engine.roll_movement(game_id, request.character_id)
        # Re-fetch state after roll (it may have been updated)
        state = engine.get_state(game_id)
        return RollMovementResponse(roll=roll, reachable_spaces=reachable, state=state)
    except GameError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/move", response_model=MoveResponse)
def move_character(game_id: str, request: MoveRequest) -> MoveResponse:
    """Move a character to a target space."""
    try:
        state = engine.get_state(game_id)
        rolled = state.pending_movement_roll or 0
        state = engine.move_character(game_id, request.character_id, request.target_space_id)
        return MoveResponse(state=state, rolled=rolled, moved_to=request.target_space_id)
    except GameError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/action", response_model=ActionResponse)
def perform_action(game_id: str, request: ActionRequest) -> ActionResponse:
    """Perform a game action (pick, fight, push, heal, pass, etc.)."""
    try:
        state, result = engine.perform_action(game_id, request.character_id, request)
        return ActionResponse(state=state, result=result)
    except GameError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/drop-cards", response_model=GameStateResponse)
def drop_cards(game_id: str, request: DropCardsRequest) -> GameStateResponse:
    """Drop cards from a character's hand (for carry capacity)."""
    try:
        state = engine.drop_cards(game_id, request.character_id, request.card_ids)
        return GameStateResponse(state=state)
    except GameError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{game_id}/state", response_model=GameStateResponse)
def get_state(game_id: str) -> GameStateResponse:
    """Get the current state of a game."""
    try:
        state = engine.get_state(game_id)
        return GameStateResponse(state=state)
    except GameError as e:
        raise HTTPException(status_code=404, detail=str(e))
