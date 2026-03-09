"""Agent specifications."""

from __future__ import annotations

from dataclasses import dataclass, field

from factory_gui.model.grid import Coord


@dataclass(slots=True)
class AgentSpec:
    id: str
    type: str
    home: Coord
    speed_cells_per_s: float
    capabilities: set[str] = field(default_factory=set)
    max_tasks_total: int = 3
    task_proficiency: dict[str, float] = field(default_factory=dict)
