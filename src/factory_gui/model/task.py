"""Task specifications."""

from __future__ import annotations

from dataclasses import dataclass, field

from factory_gui.model.grid import Coord


@dataclass(slots=True)
class TaskSpec:
    id: str
    type: str
    location: Coord
    service_time_s: int
    release_time_s: int
    due_time_s: int | None
    required_capabilities: set[str] = field(default_factory=set)
