"""Combat resolution for Space Station Zemo."""

from __future__ import annotations

from typing import Optional

from app.engine.dice import roll_2d6, roll_d6, roll_nd6
from app.models.game_state import Card, CharacterState


def resolve_melee_round(
    attacker: CharacterState,
    defender: CharacterState,
    attacker_weapon: Optional[Card],
    defender_weapon: Optional[Card],
) -> dict:
    """Resolve a single round of melee combat.

    Each side rolls 2d6 + combat_mod + weapon_bonus.
    Higher total wins. Loser takes damage equal to the difference.

    Returns dict with:
        attacker_roll, defender_roll, attacker_total, defender_total,
        damage, loser_id, winner_id (None if tie)
    """
    attacker_roll = roll_2d6()
    defender_roll = roll_2d6()

    attacker_weapon_bonus = 0
    defender_weapon_bonus = 0

    if attacker_weapon:
        if attacker_weapon.special_effect == "bat_melee_1d6":
            # A Bat Named Leth: fighting bonus is +1d6
            attacker_weapon_bonus = roll_nd6(1)
        elif attacker_weapon.special_effect == "cannot_be_ducked":
            # Lysol & Zippo: fighting 1d6+1
            attacker_weapon_bonus = roll_nd6(1) + 1
        else:
            attacker_weapon_bonus = attacker_weapon.combat_bonus

    if defender_weapon:
        if defender_weapon.special_effect == "bat_melee_1d6":
            defender_weapon_bonus = roll_nd6(1)
        elif defender_weapon.special_effect == "cannot_be_ducked":
            defender_weapon_bonus = roll_nd6(1) + 1
        else:
            defender_weapon_bonus = defender_weapon.combat_bonus

    # Pete gets +2 combat in Kitchen (space "29") - handled externally
    attacker_total = attacker_roll + attacker.combat_mod + attacker_weapon_bonus
    defender_total = defender_roll + defender.combat_mod + defender_weapon_bonus

    damage = abs(attacker_total - defender_total)

    if attacker_total > defender_total:
        winner_id = attacker.id
        loser_id = defender.id
    elif defender_total > attacker_total:
        winner_id = defender.id
        loser_id = attacker.id
    else:
        # Tie: no damage, no winner
        winner_id = None
        loser_id = None
        damage = 0

    return {
        "attacker_roll": attacker_roll,
        "defender_roll": defender_roll,
        "attacker_weapon_bonus": attacker_weapon_bonus,
        "defender_weapon_bonus": defender_weapon_bonus,
        "attacker_total": attacker_total,
        "defender_total": defender_total,
        "damage": damage,
        "loser_id": loser_id,
        "winner_id": winner_id,
    }


def resolve_uncontested_attack(
    attacker: CharacterState,
    attacker_weapon: Optional[Card],
) -> dict:
    """Resolve an attack where the defender does not fight back.

    Attacker does full damage for 1 round (rolls 2d6 + combat_mod + weapon_bonus).
    """
    attacker_roll = roll_2d6()

    weapon_bonus = 0
    if attacker_weapon:
        if attacker_weapon.special_effect == "bat_melee_1d6":
            weapon_bonus = roll_nd6(1)
        elif attacker_weapon.special_effect == "cannot_be_ducked":
            weapon_bonus = roll_nd6(1) + 1
        else:
            weapon_bonus = attacker_weapon.combat_bonus

    total_damage = attacker_roll + attacker.combat_mod + weapon_bonus

    return {
        "attacker_roll": attacker_roll,
        "weapon_bonus": weapon_bonus,
        "total_damage": total_damage,
    }


def resolve_shooting(
    shooter: CharacterState,
    target: CharacterState,
    weapon: Card,
    target_ducks: bool,
    duck_roll: int | None = None,
) -> dict:
    """Resolve a shooting attack.

    Shooter rolls weapon damage dice. Target can duck (roll 2d6 to avoid).
    If duck roll >= shoot roll, shot misses.
    Cannot duck Lysol & Zippo.

    Returns dict with shoot_roll, duck_roll, hit, damage.
    """
    shoot_roll = roll_nd6(weapon.damage_dice) + weapon.damage_bonus

    result: dict = {
        "shoot_roll": shoot_roll,
        "duck_roll": None,
        "hit": True,
        "damage": shoot_roll,
        "special": None,
    }

    cannot_duck = weapon.special_effect == "cannot_be_ducked"

    if target_ducks and not cannot_duck:
        actual_duck_roll = duck_roll if duck_roll is not None else roll_2d6()
        result["duck_roll"] = actual_duck_roll

        if actual_duck_roll >= shoot_roll:
            result["hit"] = False
            result["damage"] = 0

            # Atomic Stapler: even on miss, target loses 1 HP
            if weapon.special_effect == "miss_1_damage":
                result["damage"] = 1
                result["special"] = "miss_1_damage"

    return result


def apply_damage(character: CharacterState, damage: int) -> bool:
    """Apply damage to a character.

    Returns True if the character died (health reached 0 or below).
    """
    character.health = max(0, character.health - damage)
    return character.health <= 0
