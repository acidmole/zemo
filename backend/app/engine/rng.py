"""RNG capture and replay utilities for deterministic event sourcing.

Instead of recording individual random calls, we snapshot the full
``random`` module state before each event.  Restoring that state before
replay guarantees identical results regardless of which internal
``Random`` methods are used (``getrandbits``, ``random``, ``shuffle``,
etc.).
"""

from __future__ import annotations

import random
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator


@dataclass
class RngRecord:
    """Captured random state from before a block of code ran."""

    state: Any = None  # result of random.getstate()


@contextmanager
def record_rng() -> Generator[RngRecord, None, None]:
    """Snapshot the random state before the block runs.

    Usage::

        with record_rng() as rec:
            random.shuffle(deck)
            val = random.randint(1, 6)
        # rec.state holds the random state from *before* the block
    """
    rec = RngRecord(state=random.getstate())
    yield rec


@contextmanager
def replay_rng(state: Any) -> Generator[None, None, None]:
    """Restore a previously captured random state for deterministic replay.

    Usage::

        with replay_rng(saved_state):
            random.shuffle(deck)      # same result as original
            val = random.randint(1, 6) # same result as original
    """
    old_state = random.getstate()
    random.setstate(state)
    try:
        yield
    finally:
        # Don't restore old state — let the RNG advance naturally
        pass
