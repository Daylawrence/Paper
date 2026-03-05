"""Runtime state models."""

from __future__ import annotations

from dataclasses import dataclass, field

from factory_gui.model.agent import AgentSpec
from factory_gui.model.grid import Coord
from factory_gui.model.task import TaskSpec


@dataclass(slots=True)
class AgentRuntimeState:
    spec: AgentSpec
    position: Coord
    phase: str = "idle"
    assigned_task_id: str | None = None
    active_path: list[Coord] = field(default_factory=list)
    path_index: int = 0
    move_progress_ms: float = 0.0
    service_remaining_ms: float = 0.0
    completed_task_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TaskRuntimeState:
    spec: TaskSpec
    status: str = "pending"
    assigned_agent_id: str | None = None
