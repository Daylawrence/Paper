"""Task runtime state."""

from __future__ import annotations

from dataclasses import dataclass

from factory_gui.model.grid import Coord


@dataclass(slots=True)
class ItemState:
    pickup: Coord | None = None
    dropoff: Coord | None = None
    at_pickup: bool = False
    carried: bool = False
    delivered: bool = False
