from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CardType(str, Enum):
    ITEM = "item"
    TRAP = "trap"


class SpaceType(str, Enum):
    HALLWAY = "hallway"
    ROOM = "room"
    CODE_ROOM = "code_room"
    ESCAPE_POD = "escape_pod"
    BIO_VAT = "bio_vat"
    AIRLOCK = "airlock"


class GamePhase(str, Enum):
    SETUP = "setup"
    MOVEMENT = "movement"
    ACTION = "action"
    ROUND_END = "round_end"
    GAME_OVER = "game_over"


class CodeValue(str, Enum):
    A = "A"
    B = "B"
    UNSET = "UNSET"


class ActionType(str, Enum):
    PICK = "pick"
    FIGHT = "fight"
    PUSH = "push"
    HEAL = "heal"
    PASS = "pass"
    SHOOT = "shoot"
    DUCK = "duck"


class Card(BaseModel):
    id: str
    name: str
    card_type: CardType
    weight: int = 0
    description: str = ""
    combat_bonus: int = 0
    movement_bonus: int = 0
    code_bonus: int = 0
    is_weapon: bool = False
    is_shooting_weapon: bool = False
    damage_dice: int = 0
    damage_bonus: int = 0
    weapon_range: int = 0
    special_effect: Optional[str] = None


class SpaceState(BaseModel):
    space_id: str
    cards: list[str] = Field(default_factory=list)
    characters: list[str] = Field(default_factory=list)


class CharacterState(BaseModel):
    id: str
    name: str
    player_id: int
    health: int
    max_health: int
    position: str
    hand: list[Card] = Field(default_factory=list)
    movement_mod: int = 0
    combat_mod: int = 0
    capacity: int = 5
    is_in_bio_vat: bool = False
    has_been_regrown: bool = False
    is_permanently_dead: bool = False
    actions_per_turn: int = 1
    actions_taken_this_turn: int = 0
    actions_used_this_turn: list[ActionType] = Field(default_factory=list)
    has_moved_this_turn: bool = False
    color: str = "#888888"
    escape_code: str = ""


class CodeRoomState(BaseModel):
    room_number: int
    value: CodeValue = CodeValue.UNSET


class GameState(BaseModel):
    id: str
    players: list[CharacterState] = Field(default_factory=list)
    spaces: dict[str, SpaceState] = Field(default_factory=dict)
    code_rooms: list[CodeRoomState] = Field(default_factory=list)
    recycling_bin: list[Card] = Field(default_factory=list)
    turn_order: list[str] = Field(default_factory=list)
    current_player_index: int = 0
    phase: GamePhase = GamePhase.SETUP
    round_number: int = 0
    bio_vat_active: bool = True
    game_log: list[str] = Field(default_factory=list)
    winner: Optional[str] = None
    available_actions: list[ActionType] = Field(default_factory=list)
    card_registry: dict[str, Card] = Field(default_factory=dict)
    pending_movement_roll: Optional[int] = None
    pending_reachable_spaces: list[str] = Field(default_factory=list)


class GameConfig(BaseModel):
    player_characters: list[str]
    player_codes: list[str]
    player_names: list[str] = Field(default_factory=list)
