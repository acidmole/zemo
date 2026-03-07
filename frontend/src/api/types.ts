// Types matching backend Pydantic models (lowercase enum values to match Python)

export type CardType = "item" | "trap";
export type SpaceType = "hallway" | "room" | "code_room" | "escape_pod" | "bio_vat" | "airlock";
export type GamePhase = "setup" | "movement" | "action" | "round_end" | "game_over";
export type CodeValue = "A" | "B" | "UNSET";
export type ActionType = "pick" | "fight" | "push" | "heal" | "pass" | "shoot" | "duck";

export interface Card {
  id: string;
  name: string;
  card_type: CardType;
  weight: number;
  description: string;
  combat_bonus: number;
  movement_bonus: number;
  code_bonus: number;
  is_weapon: boolean;
  is_shooting_weapon: boolean;
  damage_dice: number;
  damage_bonus: number;
  weapon_range: number;
  special_effect: string | null;
}

export interface SpaceState {
  space_id: string;
  cards: string[];
  characters: string[];
}

export interface CharacterState {
  id: string;
  name: string;
  player_id: number;
  health: number;
  max_health: number;
  position: string;
  hand: Card[];
  movement_mod: number;
  combat_mod: number;
  capacity: number;
  is_in_bio_vat: boolean;
  has_been_regrown: boolean;
  is_permanently_dead: boolean;
  actions_per_turn: number;
  actions_taken_this_turn: number;
  actions_used_this_turn: ActionType[];
  has_moved_this_turn: boolean;
  color: string;
  escape_code: string;
}

export interface CodeRoomState {
  room_number: number;
  value: CodeValue;
}

export interface GameState {
  id: string;
  players: CharacterState[];
  spaces: Record<string, SpaceState>;
  code_rooms: CodeRoomState[];
  recycling_bin: Card[];
  turn_order: string[];
  current_player_index: number;
  phase: GamePhase;
  round_number: number;
  bio_vat_active: boolean;
  game_log: string[];
  winner: string | null;
  available_actions: ActionType[];
  card_registry: Record<string, Card>;
  pending_movement_roll: number | null;
  pending_reachable_spaces: string[];
}

export interface GameConfig {
  player_characters: string[];
  player_codes: string[];
  player_names: string[];
}

// API request/response types
export interface CreateGameRequest {
  config: GameConfig;
}

export interface CreateGameResponse {
  game_id: string;
  state: GameState;
}

export interface RollMovementRequest {
  character_id: string;
}

export interface RollMovementResponse {
  roll: number;
  reachable_spaces: string[];
  state: GameState;
}

export interface MoveRequest {
  character_id: string;
  target_space_id: string;
}

export interface MoveResponse {
  state: GameState;
  rolled: number;
  moved_to: string;
}

export interface ActionRequest {
  character_id: string;
  action_type: ActionType;
  target_character_id?: string;
  code_value?: CodeValue;
  card_ids_to_pick?: string[];
  weapon_card_id?: string;
  continue_fighting?: boolean;
}

export interface ActionResponse {
  state: GameState;
  result: Record<string, unknown>;
}

export interface DropCardsRequest {
  character_id: string;
  card_ids: string[];
}

export interface GameStateResponse {
  state: GameState;
}

// Save/restore types
export interface SaveInfo {
  game_id: string;
  player_names: string[];
  player_characters: string[];
  event_count: number;
  last_activity: string;
}

export interface ListSavesResponse {
  saves: SaveInfo[];
}
