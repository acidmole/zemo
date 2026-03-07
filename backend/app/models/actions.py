from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.models.game_state import ActionType, CodeValue, GameConfig, GameState


class CreateGameRequest(BaseModel):
    config: GameConfig


class CreateGameResponse(BaseModel):
    game_id: str
    state: GameState


class MoveRequest(BaseModel):
    character_id: str
    target_space_id: str


class MoveResponse(BaseModel):
    state: GameState
    rolled: int
    moved_to: str


class RollMovementRequest(BaseModel):
    character_id: str


class RollMovementResponse(BaseModel):
    roll: int
    reachable_spaces: list[str]
    state: GameState


class ActionRequest(BaseModel):
    character_id: str
    action_type: ActionType
    target_character_id: Optional[str] = None
    code_value: Optional[CodeValue] = None
    card_ids_to_pick: Optional[list[str]] = None
    weapon_card_id: Optional[str] = None
    continue_fighting: bool = False


class ActionResponse(BaseModel):
    state: GameState
    result: dict


class DropCardsRequest(BaseModel):
    character_id: str
    card_ids: list[str]


class GameStateResponse(BaseModel):
    state: GameState


class SaveInfo(BaseModel):
    game_id: str
    player_names: list[str]
    player_characters: list[str]
    event_count: int
    last_activity: str


class ListSavesResponse(BaseModel):
    saves: list[SaveInfo]
