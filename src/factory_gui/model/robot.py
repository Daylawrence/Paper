"""Robot runtime state."""

from __future__ import annotations

from dataclasses import dataclass, field

from factory_gui.model.grid import Coord


@dataclass(slots=True)
class RobotState:
    grid_pos: Coord | None = None
    phase: str = "idle"
    active_path: list[Coord] = field(default_factory=list)
    path_index: int = 0
    has_item: bool = False
    move_elapsed_ms: int = 0
    dwell_elapsed_ms: int = 0
