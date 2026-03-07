"""Dice rolling utilities for Space Station Zemo."""

from __future__ import annotations

import random


def roll_d6() -> int:
    """Roll a single d6."""
    return random.randint(1, 6)


def roll_2d6() -> int:
    """Roll 2d6 and return the sum."""
    return roll_d6() + roll_d6()


def roll_nd6(n: int) -> int:
    """Roll nd6 and return the sum."""
    return sum(roll_d6() for _ in range(n))


def roll_2d6_multiply() -> int:
    """Roll 2d6 and multiply them together.

    Used for starting position. Rerolls if result is > 32 or == 36.
    Returns a value in range [1, 32] (excluding impossible products > 32).
    """
    while True:
        d1 = roll_d6()
        d2 = roll_d6()
        result = d1 * d2
        if result <= 32:
            return result
