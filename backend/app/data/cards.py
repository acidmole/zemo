"""Card definitions for Space Station Zemo.

36 total cards:
- 7x Pod ATM Card
- 3x Lite Saber
- 3x Get Out of Bio-Vat Free
- 3x ACME Rocket Skates
- 2x Banana Peel (trap)
- 2x Bucket of Anti-Matter (trap)
- 1x each of remaining unique items (16 cards)
= 7 + 3 + 3 + 3 + 2 + 2 + 16 = 36
"""

from __future__ import annotations

from app.models.game_state import Card, CardType


def _make_card(
    id: str,
    name: str,
    card_type: CardType,
    weight: int = 0,
    description: str = "",
    combat_bonus: int = 0,
    movement_bonus: int = 0,
    code_bonus: int = 0,
    is_weapon: bool = False,
    is_shooting_weapon: bool = False,
    damage_dice: int = 0,
    damage_bonus: int = 0,
    weapon_range: int = 0,
    special_effect: str | None = None,
) -> Card:
    return Card(
        id=id,
        name=name,
        card_type=card_type,
        weight=weight,
        description=description,
        combat_bonus=combat_bonus,
        movement_bonus=movement_bonus,
        code_bonus=code_bonus,
        is_weapon=is_weapon,
        is_shooting_weapon=is_shooting_weapon,
        damage_dice=damage_dice,
        damage_bonus=damage_bonus,
        weapon_range=weapon_range,
        special_effect=special_effect,
    )


def build_card_deck() -> list[Card]:
    """Build the full 36-card deck."""
    cards: list[Card] = []

    # --- Pod ATM Card (x7) ---
    for i in range(1, 8):
        cards.append(_make_card(
            id=f"pod_atm_{i}",
            name="Pod ATM Card",
            card_type=CardType.ITEM,
            weight=2,
            description="Required to win. +3 to code room push rolls.",
            code_bonus=3,
        ))

    # --- Lite Saber (x3) ---
    for i in range(1, 4):
        cards.append(_make_card(
            id=f"lite_saber_{i}",
            name="Lite Saber",
            card_type=CardType.ITEM,
            weight=0,
            description="Melee weapon +2.",
            combat_bonus=2,
            is_weapon=True,
        ))

    # --- Get Out of Bio-Vat Free (x3) ---
    for i in range(1, 4):
        cards.append(_make_card(
            id=f"get_out_biovat_{i}",
            name="Get Out of Bio-Vat Free",
            card_type=CardType.ITEM,
            weight=1,
            description="On death, instantly restore to max HP instead.",
            special_effect="get_out_of_biovat",
        ))

    # --- ACME Rocket Skates (x3) ---
    for i in range(1, 4):
        cards.append(_make_card(
            id=f"acme_rocket_skates_{i}",
            name="ACME Rocket Skates",
            card_type=CardType.ITEM,
            weight=2,
            description="+3 to all movement rolls.",
            movement_bonus=3,
        ))

    # --- Banana Peel (x2, trap) ---
    for i in range(1, 3):
        cards.append(_make_card(
            id=f"banana_peel_{i}",
            name="Banana Peel",
            card_type=CardType.TRAP,
            weight=0,
            description="Trap: take 1d6 damage, lose next action.",
            special_effect="banana_peel",
        ))

    # --- Bucket of Anti-Matter (x2, trap) ---
    for i in range(1, 3):
        cards.append(_make_card(
            id=f"bucket_antimatter_{i}",
            name="Bucket of Anti-Matter",
            card_type=CardType.TRAP,
            weight=0,
            description="Trap: roll 1d6, on 1 = instant death, otherwise nothing.",
            special_effect="bucket_antimatter",
        ))

    # --- Unique items (1 each) ---

    cards.append(_make_card(
        id="gadzooka_1",
        name="Gadzooka",
        card_type=CardType.ITEM,
        weight=2,
        description="Shooting weapon 2d6 range 8. Also usable as melee +3.",
        combat_bonus=3,
        is_weapon=True,
        is_shooting_weapon=True,
        damage_dice=2,
        damage_bonus=0,
        weapon_range=8,
    ))

    cards.append(_make_card(
        id="implosion_belt_1",
        name="Implosion Belt",
        card_type=CardType.ITEM,
        weight=1,
        description="Play at start of fight round - both fighters go to 0 HP.",
        special_effect="implosion_belt",
    ))

    cards.append(_make_card(
        id="bat_named_leth_1",
        name="A Bat Named Leth",
        card_type=CardType.ITEM,
        weight=2,
        description="Fighting +1d6, shooting 1d6 range 6.",
        is_weapon=True,
        is_shooting_weapon=True,
        damage_dice=1,
        damage_bonus=0,
        weapon_range=6,
        special_effect="bat_melee_1d6",
    ))

    cards.append(_make_card(
        id="machete_launcher_1",
        name="Machete Launcher",
        card_type=CardType.ITEM,
        weight=4,
        description="Shooting weapon 4d6 range 8, min range 3.",
        is_shooting_weapon=True,
        damage_dice=4,
        damage_bonus=0,
        weapon_range=8,
        special_effect="min_range_3",
    ))

    cards.append(_make_card(
        id="lysol_zippo_1",
        name="Can of Lysol & Zippo Lighter",
        card_type=CardType.ITEM,
        weight=1,
        description="Fighting 1d6+1, shooting 1d6 range 3, cannot be ducked.",
        is_weapon=True,
        is_shooting_weapon=True,
        combat_bonus=0,
        damage_dice=1,
        damage_bonus=1,
        weapon_range=3,
        special_effect="cannot_be_ducked",
    ))

    cards.append(_make_card(
        id="atomic_stapler_1",
        name="Atomic Stapler",
        card_type=CardType.ITEM,
        weight=2,
        description="Shooting weapon 1d6+3 range 7, even on miss target loses 1 HP.",
        is_shooting_weapon=True,
        damage_dice=1,
        damage_bonus=3,
        weapon_range=7,
        special_effect="miss_1_damage",
    ))

    cards.append(_make_card(
        id="telepathy_helmet_1",
        name="Telepathy Helmet",
        card_type=CardType.ITEM,
        weight=1,
        description="Action: look at any one player's hand within 10 spaces.",
        special_effect="telepathy_helmet",
    ))

    cards.append(_make_card(
        id="witless_relocation_1",
        name="Witless Relocation Program",
        card_type=CardType.ITEM,
        weight=2,
        description="Before movement: roll 2d6 multiply, teleport to that space. 36 = death.",
        special_effect="witless_relocation",
    ))

    cards.append(_make_card(
        id="particle_accelerator_1",
        name="Particle Accelerator",
        card_type=CardType.ITEM,
        weight=1,
        description="During movement move extra 2d6 but take 1d6 damage. Cannot use with teleport.",
        special_effect="particle_accelerator",
    ))

    cards.append(_make_card(
        id="really_heavy_remote_1",
        name="Really Heavy Remote Control",
        card_type=CardType.ITEM,
        weight=4,
        description="Action: change any Code Room to A or B.",
        special_effect="remote_control",
    ))

    cards.append(_make_card(
        id="portable_black_hole_1",
        name="Portable Black Hole",
        card_type=CardType.ITEM,
        weight=0,
        description="Carry any one item with no weight penalty. On roll 1-2 that item is destroyed.",
        special_effect="portable_black_hole",
    ))

    cards.append(_make_card(
        id="deluxe_moon_pie_1",
        name="Deluxe Moon Pie",
        card_type=CardType.ITEM,
        weight=1,
        description="Reveal in fight for +1d6. Consumed after use.",
        special_effect="deluxe_moon_pie",
    ))

    cards.append(_make_card(
        id="inquest_0_1",
        name="InQuest #0",
        card_type=CardType.ITEM,
        weight=1,
        description="Before fight: force opponent to trade a random card.",
        special_effect="inquest_0",
    ))

    cards.append(_make_card(
        id="lucky_lemmings_foot_1",
        name="Lucky Lemming's Foot",
        card_type=CardType.ITEM,
        weight=0,
        description="Auto-duck on shooting combat.",
        special_effect="lucky_lemmings_foot",
    ))

    cards.append(_make_card(
        id="infrax_goggles_1",
        name="InfraX-Goggles",
        card_type=CardType.ITEM,
        weight=0,
        description="During movement: peek at one face-down card in adjacent space.",
        special_effect="infrax_goggles",
    ))

    cards.append(_make_card(
        id="molecular_blender_1",
        name="Molecular Blender",
        card_type=CardType.ITEM,
        weight=2,
        description="Once during movement: move through a wall as normal movement.",
        special_effect="molecular_blender",
    ))

    assert len(cards) == 36, f"Expected 36 cards, got {len(cards)}"
    return cards
