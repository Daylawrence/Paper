"""Base planning interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

from factory_gui.model.grid import Coord


@dataclass(slots=True)
class AgentSnapshot:
    id: str
    type: str
    position: Coord
    home: Coord
    speed_cells_per_s: float
    capabilities: set[str]
    max_tasks_total: int
    completed_task_count: int
    task_proficiency: dict[str, float]
    phase: str


@dataclass(slots=True)
class TaskSnapshot:
    id: str
    type: str
    location: Coord
    service_time_s: int
    release_time_s: int
    due_time_s: int | None
    required_capabilities: set[str]
    required_proficiency: float
    min_agents: int
    max_agents: int
    status: str


@dataclass(slots=True)
class PlannerState:
    t_now_s: float
    agents: list[AgentSnapshot]
    tasks: list[TaskSnapshot]
    conflicts: set[tuple[str, str]]
    travel_time: Callable[[str, Coord, Coord], float]


@dataclass(slots=True)
class PlannerResult:
    assignments: dict[str, str] = field(default_factory=dict)


class TaskPlannerProtocol(Protocol):
    name: str

    def plan(self, state: PlannerState) -> PlannerResult:
        """Return task assignments for currently idle agents."""
