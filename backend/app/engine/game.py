"""Main game engine / state machine for Space Station Zemo."""

from __future__ import annotations

import random
import uuid
from typing import TYPE_CHECKING, Optional

from app.data.board_layout import BOARD_LAYOUT, NUMBERED_SPACE_IDS, ROOM_NAMES
from app.data.cards import build_card_deck
from app.data.characters import CHARACTER_TEMPLATES
from app.engine import board, combat, dice
from app.engine.rng import record_rng
from app.models.actions import ActionRequest
from app.models.game_state import (
    ActionType,
    Card,
    CardType,
    CharacterState,
    CodeRoomState,
    CodeValue,
    GameConfig,
    GamePhase,
    GameState,
    SpaceState,
    SpaceType,
)

if TYPE_CHECKING:
    from app.engine.event_log import EventLogger


class GameError(Exception):
    """Raised when an invalid game operation is attempted."""


class GameEngine:
    """Manages active games and provides the game logic API."""

    def __init__(
        self,
        event_logger: EventLogger | None = None,
        _replaying: bool = False,
    ) -> None:
        self.games: dict[str, GameState] = {}
        self._event_logger = event_logger
        self._replaying = _replaying

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_game(self, config: GameConfig, *, game_id: str | None = None) -> GameState:
        """Create and set up a new game from the given configuration."""
        num_players = len(config.player_characters)
        if num_players < 2 or num_players > 4:
            raise GameError("Game requires 2-4 players.")

        if len(config.player_codes) != num_players:
            raise GameError("Each player must have an escape code.")

        if len(set(config.player_characters)) != num_players:
            raise GameError("All players must choose different characters.")

        for char_id in config.player_characters:
            if char_id not in CHARACTER_TEMPLATES:
                raise GameError(f"Unknown character template: {char_id}")

        # Fill in default player names if not provided
        player_names = list(config.player_names) if config.player_names else []
        while len(player_names) < num_players:
            player_names.append(f"Player {len(player_names) + 1}")

        game_id = game_id or str(uuid.uuid4())

        with record_rng() as rng_rec:
            # --- Build spaces ---
            spaces: dict[str, SpaceState] = {}
            for space_id in BOARD_LAYOUT:
                spaces[space_id] = SpaceState(space_id=space_id)

            # --- Build card deck, shuffle, deal ---
            deck = build_card_deck()
            random.shuffle(deck)

            # Card registry for lookup by ID
            card_registry: dict[str, Card] = {c.id: c for c in deck}

            # Deal 1 card face-down to each of the 32 numbered spaces
            for i, space_id in enumerate(NUMBERED_SPACE_IDS):
                if i < len(deck):
                    spaces[space_id].cards.append(deck[i].id)

            # Remaining 4 go to recycling bin
            recycling_bin = deck[32:36]

            # --- Create character states ---
            players: list[CharacterState] = []

            for player_idx, char_template_id in enumerate(config.player_characters):
                tmpl = CHARACTER_TEMPLATES[char_template_id]

                # Roll starting position
                start_space = self._roll_starting_position()

                char_state = CharacterState(
                    id=f"{char_template_id}_{player_idx}",
                    name=tmpl["name"],
                    player_id=player_idx,
                    health=tmpl["max_health"],
                    max_health=tmpl["max_health"],
                    position=start_space,
                    movement_mod=tmpl["movement_mod"],
                    combat_mod=tmpl["combat_mod"],
                    capacity=tmpl["capacity"],
                    actions_per_turn=tmpl["actions_per_turn"],
                    color=tmpl["color"],
                    escape_code=config.player_codes[player_idx],
                )

                players.append(char_state)
                spaces[start_space].characters.append(char_state.id)

            # --- Code rooms start unset ---
            code_rooms = [
                CodeRoomState(room_number=1),
                CodeRoomState(room_number=2),
                CodeRoomState(room_number=3),
            ]

            # --- Build initial game state ---
            state = GameState(
                id=game_id,
                players=players,
                spaces=spaces,
                code_rooms=code_rooms,
                recycling_bin=recycling_bin,
                card_registry=card_registry,
                turn_order=[],
                current_player_index=0,
                phase=GamePhase.MOVEMENT,
                round_number=1,
                bio_vat_active=True,
                game_log=[],
            )

            # Compute turn order (by health descending, ties by character list order)
            state.turn_order = self._compute_turn_order(state)
            state.game_log.append(
                f"Game started! Round 1. Turn order: "
                f"{', '.join(self._char_name(state, cid) for cid in state.turn_order)}"
            )

            # Log starting positions
            for p in players:
                space_name = ROOM_NAMES.get(p.position, "a hallway")
                state.game_log.append(f"{p.name} starts in {space_name}.")

            # Compute available actions (not applicable in movement phase but keep consistent)
            current_char = self._get_current_character(state)
            if current_char:
                state.available_actions = self._compute_available_actions(state, current_char.id)

        self.games[game_id] = state

        if self._event_logger and not self._replaying:
            self._event_logger.log(
                game_id,
                "create_game",
                {
                    "player_characters": list(config.player_characters),
                    "player_codes": list(config.player_codes),
                    "player_names": player_names,
                },
                rng_rec,
                extra={"game_id": game_id},
            )

        return state

    def get_state(self, game_id: str) -> GameState:
        """Retrieve the current state of a game."""
        state = self.games.get(game_id)
        if state is None:
            raise GameError(f"Game not found: {game_id}")
        return state

    def roll_movement(self, game_id: str, character_id: str) -> tuple[int, list[str]]:
        """Roll movement dice for the specified character.

        Returns (roll_result, list_of_reachable_space_ids).
        """
        state = self.get_state(game_id)

        if state.phase != GamePhase.MOVEMENT:
            raise GameError("Not in movement phase.")

        current_char = self._get_current_character(state)
        if current_char is None or current_char.id != character_id:
            raise GameError(f"It is not {character_id}'s turn to move.")

        if current_char.has_moved_this_turn:
            raise GameError(f"{current_char.name} has already moved this turn.")

        if current_char.is_permanently_dead:
            raise GameError(f"{current_char.name} is permanently dead.")

        with record_rng() as rng_rec:
            # Roll 2d6 + movement modifier + item bonuses
            roll = dice.roll_2d6()
            total_movement = roll + current_char.movement_mod

            # Add movement bonus from items in hand (e.g., ACME Rocket Skates)
            for card in current_char.hand:
                total_movement += card.movement_bonus

            total_movement = max(0, total_movement)

            # Characters in bio-vat can only leave if HP > 0; movement is from bio_vat
            if current_char.is_in_bio_vat:
                if current_char.health <= 0:
                    # Can't move, stuck in bio-vat
                    state.pending_movement_roll = 0
                    state.pending_reachable_spaces = ["bio_vat"]
                    state.game_log.append(
                        f"{current_char.name} is in the Bio-Vat with 0 HP and cannot move."
                    )
                    if self._event_logger and not self._replaying:
                        self._event_logger.log(
                            game_id, "roll_movement",
                            {"character_id": character_id}, rng_rec,
                        )
                    return (0, ["bio_vat"])

            occupied_hallways = self._get_occupied_hallways(state)
            reachable = board.get_reachable_spaces(
                current_char.position,
                total_movement,
                occupied_hallways,
                exclude_current=current_char.position,
            )

            state.pending_movement_roll = total_movement
            state.pending_reachable_spaces = reachable

            state.game_log.append(
                f"{current_char.name} rolls {roll} for movement (total: {total_movement})."
            )

        if self._event_logger and not self._replaying:
            self._event_logger.log(
                game_id, "roll_movement",
                {"character_id": character_id}, rng_rec,
            )

        return (total_movement, reachable)

    def move_character(
        self, game_id: str, character_id: str, target_space_id: str
    ) -> GameState:
        """Move a character to the specified space, then advance the turn."""
        state = self.get_state(game_id)

        if state.phase != GamePhase.MOVEMENT:
            raise GameError("Not in movement phase.")

        current_char = self._get_current_character(state)
        if current_char is None or current_char.id != character_id:
            raise GameError(f"It is not {character_id}'s turn to move.")

        if current_char.has_moved_this_turn:
            raise GameError(f"{current_char.name} has already moved this turn.")

        # Validate the target is reachable
        if state.pending_reachable_spaces and target_space_id not in state.pending_reachable_spaces:
            raise GameError(
                f"Space {target_space_id} is not reachable. "
                f"Reachable: {state.pending_reachable_spaces}"
            )

        # Validate hallway occupancy
        if not board.is_room(target_space_id):
            for p in state.players:
                if (
                    p.id != character_id
                    and p.position == target_space_id
                    and not p.is_in_bio_vat
                    and not p.is_permanently_dead
                ):
                    raise GameError(
                        f"Space {target_space_id} is a hallway occupied by {p.name}."
                    )

        with record_rng() as rng_rec:
            # Move character
            old_position = current_char.position
            state.spaces[old_position].characters = [
                cid for cid in state.spaces[old_position].characters if cid != character_id
            ]
            current_char.position = target_space_id
            state.spaces[target_space_id].characters.append(character_id)

            # If leaving bio-vat
            if current_char.is_in_bio_vat and target_space_id != "bio_vat":
                current_char.is_in_bio_vat = False
                current_char.has_been_regrown = True
                state.game_log.append(f"{current_char.name} leaves the Bio-Vat!")

            current_char.has_moved_this_turn = True
            space_name = ROOM_NAMES.get(target_space_id, "a hallway")
            state.game_log.append(f"{current_char.name} moves to {space_name}.")

            # Clear pending movement data
            state.pending_movement_roll = None
            state.pending_reachable_spaces = []

            # Advance to next player or phase
            self._advance_turn(state)

        if self._event_logger and not self._replaying:
            self._event_logger.log(
                game_id, "move",
                {"character_id": character_id, "target_space_id": target_space_id},
                rng_rec,
            )

        return state

    def perform_action(
        self, game_id: str, character_id: str, action: ActionRequest
    ) -> tuple[GameState, dict]:
        """Execute an action for the given character."""
        state = self.get_state(game_id)

        if state.phase != GamePhase.ACTION:
            raise GameError("Not in action phase.")

        current_char = self._get_current_character(state)
        if current_char is None or current_char.id != character_id:
            raise GameError(f"It is not {character_id}'s turn to act.")

        if current_char.is_permanently_dead:
            raise GameError(f"{current_char.name} is permanently dead.")

        if current_char.actions_taken_this_turn >= current_char.actions_per_turn:
            raise GameError(f"{current_char.name} has no more actions this turn.")

        # Pete cannot repeat the same action type
        if (
            current_char.actions_per_turn > 1
            and action.action_type in current_char.actions_used_this_turn
        ):
            raise GameError(
                f"{current_char.name} cannot perform {action.action_type.value} again "
                f"(Commando Training: must use different actions)."
            )

        # Validate action is available
        available = self._compute_available_actions(state, character_id)
        if action.action_type not in available:
            raise GameError(
                f"Action {action.action_type.value} is not available. "
                f"Available: {[a.value for a in available]}"
            )

        with record_rng() as rng_rec:
            # Reactor Room damage: lose 1 HP at start of action while in space 7
            if current_char.position == "7" and current_char.actions_taken_this_turn == 0:
                current_char.health = max(0, current_char.health - 1)
                state.game_log.append(
                    f"{current_char.name} takes 1 damage from the Reactor Room radiation!"
                )
                if current_char.health <= 0:
                    result = {"action": "reactor_death", "message": "Killed by reactor radiation."}
                    self._handle_death(state, character_id)
                    self._advance_turn(state)
                    if self._event_logger and not self._replaying:
                        self._event_logger.log(
                            game_id, "action",
                            self._action_args(character_id, action), rng_rec,
                        )
                    return (state, result)

            # Dispatch to action handler
            result: dict
            match action.action_type:
                case ActionType.PICK:
                    result = self._action_pick(state, current_char, action)
                case ActionType.FIGHT:
                    result = self._action_fight(state, current_char, action)
                case ActionType.PUSH:
                    result = self._action_push(state, current_char, action)
                case ActionType.HEAL:
                    result = self._action_heal(state, current_char)
                case ActionType.PASS:
                    result = self._action_pass(state, current_char)
                case _:
                    raise GameError(f"Unsupported action type: {action.action_type}")

            current_char.actions_taken_this_turn += 1
            current_char.actions_used_this_turn.append(action.action_type)

            # Check win conditions
            winner = self._check_win_conditions(state)
            if winner:
                state.winner = winner
                state.phase = GamePhase.GAME_OVER
                winner_char = self._get_character(state, winner)
                state.game_log.append(f"{winner_char.name if winner_char else winner} WINS THE GAME!")
                if self._event_logger and not self._replaying:
                    self._event_logger.log(
                        game_id, "action",
                        self._action_args(character_id, action), rng_rec,
                    )
                return (state, result)

            # Advance turn if all actions used
            if current_char.actions_taken_this_turn >= current_char.actions_per_turn:
                self._advance_turn(state)
            else:
                # Recompute available actions for next action
                state.available_actions = self._compute_available_actions(state, character_id)

        if self._event_logger and not self._replaying:
            self._event_logger.log(
                game_id, "action",
                self._action_args(character_id, action), rng_rec,
            )

        return (state, result)

    def drop_cards(
        self, game_id: str, character_id: str, card_ids: list[str]
    ) -> GameState:
        """Drop cards from a character's hand to handle carry capacity."""
        state = self.get_state(game_id)
        char = self._get_character(state, character_id)
        if char is None:
            raise GameError(f"Character not found: {character_id}")

        cards_to_drop: list[Card] = []
        for card_id in card_ids:
            card = next((c for c in char.hand if c.id == card_id), None)
            if card is None:
                raise GameError(f"Card {card_id} not in {char.name}'s hand.")
            cards_to_drop.append(card)

        with record_rng() as rng_rec:
            for card in cards_to_drop:
                char.hand.remove(card)
                # Drop to current space if room, otherwise nearest room
                drop_space = char.position if board.is_room(char.position) else self._nearest_room(char.position)
                state.spaces[drop_space].cards.append(card.id)
                state.game_log.append(
                    f"{char.name} drops {card.name} at {ROOM_NAMES.get(drop_space, drop_space)}."
                )

        if self._event_logger and not self._replaying:
            self._event_logger.log(
                game_id, "drop_cards",
                {"character_id": character_id, "card_ids": card_ids}, rng_rec,
            )

        return state

    # ------------------------------------------------------------------
    # Action Handlers
    # ------------------------------------------------------------------

    def _action_pick(
        self, state: GameState, char: CharacterState, action: ActionRequest
    ) -> dict:
        """Pick up face-down cards at the current space."""
        space = state.spaces[char.position]
        if not space.cards:
            raise GameError("No cards at this space to pick up.")

        picked_cards: list[Card] = []
        triggered_traps: list[dict] = []

        # Pick specific cards or all
        card_ids_to_pick = action.card_ids_to_pick or list(space.cards)

        for card_id in card_ids_to_pick:
            if card_id not in space.cards:
                continue

            card = state.card_registry.get(card_id)
            if card is None:
                continue

            space.cards.remove(card_id)

            if card.card_type == CardType.TRAP:
                # Trap triggers immediately
                trap_result = self._trigger_trap(state, char, card)
                triggered_traps.append(trap_result)
                state.game_log.append(
                    f"{char.name} triggered a trap: {card.name}! {trap_result.get('message', '')}"
                )
                # Trap is removed from game (not added to hand or recycling)
            else:
                # Item goes to hand
                char.hand.append(card)
                picked_cards.append(card)
                state.game_log.append(f"{char.name} picks up {card.name}.")

        return {
            "action": "pick",
            "picked": [c.name for c in picked_cards],
            "traps_triggered": triggered_traps,
        }

    def _action_fight(
        self, state: GameState, attacker: CharacterState, action: ActionRequest
    ) -> dict:
        """Initiate melee combat with a target character."""
        if not action.target_character_id:
            raise GameError("Fight action requires a target_character_id.")

        defender = self._get_character(state, action.target_character_id)
        if defender is None:
            raise GameError(f"Target character not found: {action.target_character_id}")

        if defender.is_permanently_dead or defender.is_in_bio_vat:
            raise GameError(f"Cannot fight {defender.name} (dead or in Bio-Vat).")

        # Check adjacency: same space or adjacent space
        same_space = attacker.position == defender.position
        adjacent = defender.position in board.get_adjacent_spaces(attacker.position)
        if not same_space and not adjacent:
            raise GameError(f"{defender.name} is not in the same or adjacent space.")

        # Get weapons
        attacker_weapon = None
        if action.weapon_card_id:
            attacker_weapon = next(
                (c for c in attacker.hand if c.id == action.weapon_card_id and c.is_weapon),
                None,
            )

        # Pete gets +2 combat in Kitchen
        pete_kitchen_bonus = 0
        if attacker.name == "Pete the Cook" and attacker.position == "29":
            pete_kitchen_bonus = 2

        # Resolve one round of melee combat
        combat_result = combat.resolve_melee_round(
            attacker, defender, attacker_weapon, None
        )

        # Apply Pete's kitchen bonus to attacker total
        if pete_kitchen_bonus:
            combat_result["attacker_total"] += pete_kitchen_bonus
            # Recalculate result
            diff = combat_result["attacker_total"] - combat_result["defender_total"]
            if diff > 0:
                combat_result["winner_id"] = attacker.id
                combat_result["loser_id"] = defender.id
                combat_result["damage"] = diff
            elif diff < 0:
                combat_result["winner_id"] = defender.id
                combat_result["loser_id"] = attacker.id
                combat_result["damage"] = abs(diff)
            else:
                combat_result["winner_id"] = None
                combat_result["loser_id"] = None
                combat_result["damage"] = 0

        # Apply damage to loser
        death_occurred = False
        if combat_result["loser_id"]:
            loser = self._get_character(state, combat_result["loser_id"])
            if loser:
                died = combat.apply_damage(loser, combat_result["damage"])
                state.game_log.append(
                    f"Combat: {attacker.name} ({combat_result['attacker_total']}) vs "
                    f"{defender.name} ({combat_result['defender_total']}). "
                    f"{loser.name} takes {combat_result['damage']} damage."
                )
                if died:
                    death_occurred = True
                    state.game_log.append(f"{loser.name} has been defeated!")
                    self._handle_death(state, loser.id)
        else:
            state.game_log.append(
                f"Combat: {attacker.name} ({combat_result['attacker_total']}) vs "
                f"{defender.name} ({combat_result['defender_total']}). Tie! No damage."
            )

        combat_result["action"] = "fight"
        combat_result["death_occurred"] = death_occurred
        return combat_result

    def _action_push(
        self, state: GameState, char: CharacterState, action: ActionRequest
    ) -> dict:
        """Attempt to set a code room value."""
        space_type = board.get_space_type(char.position)
        if space_type != SpaceType.CODE_ROOM:
            raise GameError("Push action requires being in a Code Room.")

        if action.code_value is None or action.code_value == CodeValue.UNSET:
            raise GameError("Push action requires a code_value (A or B).")

        # Determine which code room number
        code_room_num: int
        if char.position == "code_room_1":
            code_room_num = 1
        elif char.position == "code_room_2":
            code_room_num = 2
        elif char.position == "code_room_3":
            code_room_num = 3
        else:
            raise GameError("Not in a recognized Code Room.")

        # Roll 1d6 + Pod ATM Card bonus
        roll = dice.roll_d6()
        bonus = sum(c.code_bonus for c in char.hand)
        total = roll + bonus

        success = total >= 4

        code_room_state = state.code_rooms[code_room_num - 1]

        if success:
            code_room_state.value = action.code_value
            state.game_log.append(
                f"{char.name} pushes Code Room {code_room_num} to {action.code_value.value}! "
                f"(rolled {roll} + {bonus} bonus = {total})"
            )
        else:
            state.game_log.append(
                f"{char.name} fails to push Code Room {code_room_num}. "
                f"(rolled {roll} + {bonus} bonus = {total}, needed 4+)"
            )

        return {
            "action": "push",
            "code_room": code_room_num,
            "roll": roll,
            "bonus": bonus,
            "total": total,
            "success": success,
            "new_value": code_room_state.value.value if success else None,
        }

    def _action_heal(self, state: GameState, char: CharacterState) -> dict:
        """Heal in the Bio-Vat."""
        if char.position != "bio_vat":
            raise GameError("Heal action requires being in the Bio-Vat.")

        roll = dice.roll_2d6()
        old_health = char.health
        char.health = min(char.max_health, char.health + roll)
        healed = char.health - old_health

        state.game_log.append(
            f"{char.name} heals for {healed} HP in the Bio-Vat (rolled {roll}). "
            f"HP: {old_health} -> {char.health}/{char.max_health}"
        )

        return {
            "action": "heal",
            "roll": roll,
            "healed": healed,
            "new_health": char.health,
        }

    def _action_pass(self, state: GameState, char: CharacterState) -> dict:
        """Do nothing."""
        state.game_log.append(f"{char.name} passes.")
        return {"action": "pass"}

    # ------------------------------------------------------------------
    # Trap Handling
    # ------------------------------------------------------------------

    def _trigger_trap(self, state: GameState, char: CharacterState, card: Card) -> dict:
        """Trigger a trap card effect."""
        match card.special_effect:
            case "banana_peel":
                damage = dice.roll_d6()
                combat.apply_damage(char, damage)
                result = {
                    "trap": "banana_peel",
                    "damage": damage,
                    "message": f"Slipped on a Banana Peel! Took {damage} damage and loses next action.",
                    "new_health": char.health,
                }
                if char.health <= 0:
                    result["message"] += f" {char.name} has died!"
                    self._handle_death(state, char.id)
                return result

            case "bucket_antimatter":
                roll = dice.roll_d6()
                if roll == 1:
                    char.health = 0
                    result = {
                        "trap": "bucket_antimatter",
                        "roll": roll,
                        "message": f"Bucket of Anti-Matter! Rolled {roll} - INSTANT DEATH!",
                        "new_health": 0,
                    }
                    self._handle_death(state, char.id)
                    return result
                else:
                    return {
                        "trap": "bucket_antimatter",
                        "roll": roll,
                        "message": f"Bucket of Anti-Matter! Rolled {roll} - safe!",
                        "new_health": char.health,
                    }

            case _:
                return {"trap": "unknown", "message": "Unknown trap effect."}

    # ------------------------------------------------------------------
    # Turn / Phase Management
    # ------------------------------------------------------------------

    def _advance_turn(self, state: GameState) -> None:
        """Advance to the next player or next phase."""
        # Find next alive, non-permanently-dead player
        active_players = [
            cid for cid in state.turn_order
            if not self._is_player_skipped(state, cid)
        ]

        if not active_players:
            # Everyone is dead or permanently dead
            winner = self._check_win_conditions(state)
            if winner:
                state.winner = winner
                state.phase = GamePhase.GAME_OVER
            return

        # Move to next player index
        state.current_player_index += 1

        # Check if we've gone through all players in current phase
        if state.current_player_index >= len(state.turn_order):
            if state.phase == GamePhase.MOVEMENT:
                # Transition to action phase
                state.phase = GamePhase.ACTION
                state.current_player_index = 0
                state.game_log.append("--- Action Phase ---")

                # Reset action counts for all players
                for p in state.players:
                    p.actions_taken_this_turn = 0
                    p.actions_used_this_turn = []

                # Skip to first active player
                self._skip_to_next_active(state)

            elif state.phase == GamePhase.ACTION:
                # End of round - check carry capacity, start new round
                self._end_round(state)
            return

        # Skip dead/eliminated players
        self._skip_to_next_active(state)

        # Update available actions
        current_char = self._get_current_character(state)
        if current_char:
            state.available_actions = self._compute_available_actions(state, current_char.id)

    def _skip_to_next_active(self, state: GameState) -> None:
        """Skip over dead/eliminated players to find the next active one."""
        attempts = 0
        total = len(state.turn_order)

        while attempts < total:
            if state.current_player_index >= total:
                # Wrapped around: transition phase
                if state.phase == GamePhase.MOVEMENT:
                    state.phase = GamePhase.ACTION
                    state.current_player_index = 0
                    state.game_log.append("--- Action Phase ---")
                    for p in state.players:
                        p.actions_taken_this_turn = 0
                        p.actions_used_this_turn = []
                    attempts = 0
                    # Continue loop to find first active action player
                elif state.phase == GamePhase.ACTION:
                    self._end_round(state)
                    return
                else:
                    return

            cid = state.turn_order[state.current_player_index]
            if not self._is_player_skipped(state, cid):
                # Found an active player
                current_char = self._get_current_character(state)
                if current_char:
                    state.available_actions = self._compute_available_actions(
                        state, current_char.id
                    )
                return

            state.current_player_index += 1
            attempts += 1

        # All players skipped - end round
        if state.phase == GamePhase.ACTION:
            self._end_round(state)

    def _is_player_skipped(self, state: GameState, character_id: str) -> bool:
        """Check if a player should be skipped in the turn order."""
        char = self._get_character(state, character_id)
        if char is None:
            return True
        return char.is_permanently_dead

    def _end_round(self, state: GameState) -> None:
        """Handle end-of-round logic and start a new round."""
        # Check carry capacity for all players
        for p in state.players:
            if not p.is_permanently_dead:
                total_weight = sum(c.weight for c in p.hand)
                if total_weight > p.capacity:
                    state.game_log.append(
                        f"WARNING: {p.name} is over capacity "
                        f"({total_weight}/{p.capacity}). Must drop cards."
                    )

        # Check win conditions
        winner = self._check_win_conditions(state)
        if winner:
            state.winner = winner
            state.phase = GamePhase.GAME_OVER
            winner_char = self._get_character(state, winner)
            state.game_log.append(
                f"{winner_char.name if winner_char else winner} WINS THE GAME!"
            )
            return

        # Start new round
        state.round_number += 1
        state.phase = GamePhase.MOVEMENT
        state.current_player_index = 0

        # Recalculate turn order
        state.turn_order = self._compute_turn_order(state)

        # Reset per-turn flags
        for p in state.players:
            p.has_moved_this_turn = False
            p.actions_taken_this_turn = 0
            p.actions_used_this_turn = []

        state.game_log.append(
            f"--- Round {state.round_number} ---"
        )
        state.game_log.append(
            f"Turn order: "
            f"{', '.join(self._char_name(state, cid) for cid in state.turn_order)}"
        )

        # Skip to first active player
        self._skip_to_next_active(state)

    # ------------------------------------------------------------------
    # Win Condition Checks
    # ------------------------------------------------------------------

    def _check_win_conditions(self, state: GameState) -> Optional[str]:
        """Check for win conditions. Returns winner character_id or None."""
        alive_players = [
            p for p in state.players if not p.is_permanently_dead
        ]

        # Last survivor: all other players permanently dead
        if len(alive_players) == 1:
            return alive_players[0].id

        # Escape Pod win: code rooms match secret code, in escape pod, have Pod ATM Card
        for p in alive_players:
            if p.position != "escape_pod":
                continue

            has_pod_atm = any(c.name == "Pod ATM Card" for c in p.hand)
            if not has_pod_atm:
                continue

            # Check if all 3 code rooms match player's secret code
            if len(p.escape_code) != 3:
                continue

            all_match = True
            for i, code_char in enumerate(p.escape_code):
                room_value = state.code_rooms[i].value
                if room_value == CodeValue.UNSET:
                    all_match = False
                    break
                if room_value.value != code_char:
                    all_match = False
                    break

            if all_match:
                return p.id

        return None

    # ------------------------------------------------------------------
    # Death / Bio-Vat
    # ------------------------------------------------------------------

    def _handle_death(self, state: GameState, character_id: str) -> None:
        """Handle a character dying: move to Bio-Vat, drop items, check shutdown."""
        char = self._get_character(state, character_id)
        if char is None:
            return

        # Check for Get Out of Bio-Vat Free card
        biovat_card = next(
            (c for c in char.hand if c.special_effect == "get_out_of_biovat"),
            None,
        )
        if biovat_card:
            char.hand.remove(biovat_card)
            char.health = char.max_health
            state.game_log.append(
                f"{char.name} uses Get Out of Bio-Vat Free! "
                f"Restored to {char.max_health} HP!"
            )
            return

        # Check if Bio-Vat is active
        if not state.bio_vat_active:
            # Permanent death
            char.is_permanently_dead = True
            char.health = 0
            state.game_log.append(
                f"{char.name} is PERMANENTLY DEAD! (Bio-Vat is shut down)"
            )
        else:
            char.is_in_bio_vat = True
            char.health = 0
            state.game_log.append(
                f"{char.name} dies and is sent to the Bio-Vat."
            )

        # Drop all items at death location
        death_space = char.position
        drop_space = death_space if board.is_room(death_space) else self._nearest_room(death_space)

        for card in char.hand:
            state.spaces[drop_space].cards.append(card.id)

        if char.hand:
            state.game_log.append(
                f"{char.name}'s items dropped at "
                f"{ROOM_NAMES.get(drop_space, drop_space)}."
            )
        char.hand = []

        # Move character to Bio-Vat (if not permanently dead)
        if not char.is_permanently_dead:
            old_pos = char.position
            state.spaces[old_pos].characters = [
                cid for cid in state.spaces[old_pos].characters if cid != character_id
            ]
            char.position = "bio_vat"
            state.spaces["bio_vat"].characters.append(character_id)

        # Check Bio-Vat shutdown condition:
        # All characters that have been in the game must have been regrown at least once
        all_regrown = all(
            p.has_been_regrown or p.is_permanently_dead
            for p in state.players
        )
        if all_regrown and state.bio_vat_active:
            # Only shut down if at least one character has died and regrown
            any_regrown = any(p.has_been_regrown for p in state.players)
            if any_regrown:
                state.bio_vat_active = False
                state.game_log.append(
                    "The Bio-Vat has shut down! All characters have been regrown. "
                    "Future deaths are permanent!"
                )

    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------

    def _roll_starting_position(self) -> str:
        """Roll 2d6 multiply for the starting room (1-32).

        Every result is a room, and rooms hold any number of characters.
        """
        return str(dice.roll_2d6_multiply())

    def _compute_turn_order(self, state: GameState) -> list[str]:
        """Compute turn order: highest health first, ties broken by player index."""
        active = [
            p for p in state.players if not p.is_permanently_dead
        ]
        active.sort(key=lambda p: (-p.health, p.player_id))
        return [p.id for p in active]

    def _get_occupied_hallways(self, state: GameState) -> set[str]:
        """Get the set of hallway space IDs that have a character in them."""
        occupied: set[str] = set()
        for p in state.players:
            if (
                not p.is_permanently_dead
                and not p.is_in_bio_vat
                and not board.is_room(p.position)
            ):
                occupied.add(p.position)
        return occupied

    def _compute_available_actions(
        self, state: GameState, character_id: str
    ) -> list[ActionType]:
        """Determine what actions are available for a character."""
        char = self._get_character(state, character_id)
        if char is None:
            return []

        if char.is_permanently_dead:
            return []

        actions: list[ActionType] = []

        # PASS is always available
        actions.append(ActionType.PASS)

        # PICK: if current space has face-down cards
        space = state.spaces.get(char.position)
        if space and space.cards:
            actions.append(ActionType.PICK)

        # FIGHT: if there's an enemy in same or adjacent space
        potential_targets = self._get_fight_targets(state, char)
        if potential_targets:
            actions.append(ActionType.FIGHT)

        # PUSH: if in a code room
        if board.get_space_type(char.position) == SpaceType.CODE_ROOM:
            actions.append(ActionType.PUSH)

        # HEAL: if in Bio-Vat
        if char.position == "bio_vat":
            actions.append(ActionType.HEAL)

        # SHOOT: if character has a shooting weapon and there's a target in range
        shooting_weapons = [c for c in char.hand if c.is_shooting_weapon]
        if shooting_weapons:
            for p in state.players:
                if (
                    p.id != character_id
                    and not p.is_permanently_dead
                    and not p.is_in_bio_vat
                ):
                    dist = board.get_distance(char.position, p.position)
                    for weapon in shooting_weapons:
                        if 0 < dist <= weapon.weapon_range:
                            actions.append(ActionType.SHOOT)
                            break
                    if ActionType.SHOOT in actions:
                        break

        # Filter out already-used actions for Pete
        if char.actions_per_turn > 1:
            actions = [a for a in actions if a not in char.actions_used_this_turn]

        return actions

    def _get_fight_targets(
        self, state: GameState, char: CharacterState
    ) -> list[str]:
        """Get character IDs that can be fought (same space or adjacent)."""
        targets: list[str] = []
        adjacent_spaces = board.get_adjacent_spaces(char.position)

        for p in state.players:
            if p.id == char.id:
                continue
            if p.is_permanently_dead or p.is_in_bio_vat:
                continue
            if p.position == char.position or p.position in adjacent_spaces:
                targets.append(p.id)

        return targets

    def _get_character(
        self, state: GameState, character_id: str
    ) -> Optional[CharacterState]:
        """Look up a character by ID."""
        return next((p for p in state.players if p.id == character_id), None)

    def _get_current_character(self, state: GameState) -> Optional[CharacterState]:
        """Get the character whose turn it currently is."""
        if state.current_player_index >= len(state.turn_order):
            return None
        cid = state.turn_order[state.current_player_index]
        return self._get_character(state, cid)

    def _char_name(self, state: GameState, character_id: str) -> str:
        """Get a character's display name."""
        char = self._get_character(state, character_id)
        return char.name if char else character_id

    @staticmethod
    def _action_args(character_id: str, action: ActionRequest) -> dict:
        """Build a serialisable args dict from an ActionRequest."""
        args: dict = {
            "character_id": character_id,
            "action_type": action.action_type.value,
        }
        if action.target_character_id is not None:
            args["target_character_id"] = action.target_character_id
        if action.code_value is not None:
            args["code_value"] = action.code_value.value
        if action.card_ids_to_pick is not None:
            args["card_ids_to_pick"] = action.card_ids_to_pick
        if action.weapon_card_id is not None:
            args["weapon_card_id"] = action.weapon_card_id
        if action.continue_fighting:
            args["continue_fighting"] = action.continue_fighting
        return args

    def _nearest_room(self, space_id: str) -> str:
        """Find the nearest room to a given space (BFS)."""
        if board.is_room(space_id):
            return space_id

        from collections import deque

        visited: set[str] = {space_id}
        queue: deque[str] = deque()
        queue.append(space_id)

        while queue:
            current = queue.popleft()
            for neighbor in board.get_adjacent_spaces(current):
                if neighbor not in visited:
                    if board.is_room(neighbor):
                        return neighbor
                    visited.add(neighbor)
                    queue.append(neighbor)

        # Fallback (should never happen on a connected board)
        return space_id
