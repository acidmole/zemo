"""Character template definitions for Space Station Zemo."""

from __future__ import annotations

CHARACTER_TEMPLATES: dict[str, dict] = {
    "chuckie": {
        "name": "Chuckie the Zombie",
        "max_health": 20,
        "movement_mod": 0,
        "combat_mod": 2,
        "capacity": 5,
        "actions_per_turn": 1,
        "special": "Exploding Polyps",
        "color": "#4CAF50",
    },
    "floyd": {
        "name": "Floyd the Droid",
        "max_health": 18,
        "movement_mod": 0,
        "combat_mod": 0,
        "capacity": 5,
        "actions_per_turn": 1,
        "special": "Transformer Chassis",
        "color": "#2196F3",
    },
    "mush": {
        "name": "Mush the Abomination",
        "max_health": 19,
        "movement_mod": 0,
        "combat_mod": 2,
        "capacity": 5,
        "actions_per_turn": 1,
        "special": "Der Blinkenteleporten",
        "color": "#9C27B0",
    },
    "pete": {
        "name": "Pete the Cook",
        "max_health": 13,
        "movement_mod": 0,
        "combat_mod": 0,
        "capacity": 5,
        "actions_per_turn": 2,
        "special": "Commando Training",
        "color": "#FF9800",
    },
    "rats": {
        "name": "The Rats",
        "max_health": 9,
        "movement_mod": 0,
        "combat_mod": 0,
        "capacity": 5,
        "actions_per_turn": 1,
        "special": "Rat Packs",
        "color": "#795548",
    },
}

VALID_ESCAPE_CODES: list[str] = [
    "AAA", "AAB", "ABA", "ABB",
    "BAA", "BAB", "BBA", "BBB",
]
