"""Simulation controller for multiple agents and multiple tasks."""

from __future__ import annotations

from dataclasses import dataclass

from factory_gui.algorithms.base import AgentSnapshot, PlannerResult, PlannerState, TaskSnapshot
from factory_gui.algorithms.dispatch.greedy_nearest import GreedyNearestPlanner
from factory_gui.model.grid import Coord
from factory_gui.model.runtime import AgentRuntimeState, TaskRuntimeState
from factory_gui.model.scene import SceneModel, SceneValidationError
from factory_gui.planner.astar import AStarPlanner


class SimulationError(ValueError):
    """Raised when the simulation cannot start."""

    def __init__(self, message_key: str) -> None:
        self.message_key = message_key
        super().__init__(message_key)


@dataclass(slots=True)
class SimulationSummary:
    time_s: float
    total_tasks: int
    completed_tasks: int
    idle_agents: int


class SimulationController:
    """Drive multiple agents through task execution and return-home phases."""

    def __init__(self, planner: GreedyNearestPlanner | None = None) -> None:
        self.planner = planner or GreedyNearestPlanner()
        self.path_planner = AStarPlanner()
        self.speed_multiplier = 1
        self.reset()

    def set_speed_multiplier(self, multiplier: int) -> None:
        self.speed_multiplier = max(1, multiplier)

    def start(self, scene: SceneModel) -> None:
        try:
            scene.validate_for_run()
        except SceneValidationError as exc:
            raise SimulationError(str(exc)) from exc
        self._validate_reachability(scene)

        self.scene = scene.copy()
        self.initial_scene = scene.copy()
        self.time_ms = 0.0
        self.running = True
        self.agent_states = {
            agent.id: AgentRuntimeState(spec=agent, position=agent.home)
            for agent in self.scene.agents
        }
        self.task_states = {
            task.id: TaskRuntimeState(spec=task)
            for task in self.scene.tasks
        }
        self._dispatch_tasks()

    def reset(self) -> None:
        self.scene: SceneModel | None = None
        self.initial_scene: SceneModel | None = None
        self.agent_states: dict[str, AgentRuntimeState] = {}
        self.task_states: dict[str, TaskRuntimeState] = {}
        self.time_ms = 0.0
        self.running = False

    def update(self, dt_ms: int) -> None:
        if not self.running:
            return

        scaled_dt = float(max(0, dt_ms)) * self.speed_multiplier
        self.time_ms += scaled_dt

        for state in self.agent_states.values():
            self._advance_agent(state, scaled_dt)

        self._dispatch_tasks()

        if self._all_tasks_completed() and all(state.phase == "idle" for state in self.agent_states.values()):
            self.running = False

    def current_paths(self) -> dict[str, list[Coord]]:
        return {
            agent_id: state.active_path[state.path_index :]
            for agent_id, state in self.agent_states.items()
            if state.phase in {"moving_to_task", "returning_home"} and state.active_path
        }

    def status_key(self) -> str:
        if not self.scene:
            return "sim_ready"
        if self.running:
            return "sim_running"
        if self._all_tasks_completed():
            return "sim_completed"
        return "sim_ready"

    def phase_key(self, agent_id: str) -> str:
        phase = self.agent_states[agent_id].phase
        return {
            "idle": "phase_idle",
            "moving_to_task": "phase_moving_to_task",
            "servicing": "phase_servicing",
            "returning_home": "phase_returning_home",
        }.get(phase, "phase_idle")

    def summary(self) -> SimulationSummary:
        completed = sum(1 for task in self.task_states.values() if task.status == "completed")
        idle_agents = sum(1 for agent in self.agent_states.values() if agent.phase == "idle")
        return SimulationSummary(
            time_s=self.time_ms / 1000.0,
            total_tasks=len(self.task_states),
            completed_tasks=completed,
            idle_agents=idle_agents,
        )

    def task_status_counts(self) -> dict[str, int]:
        counts = {"pending": 0, "assigned": 0, "in_service": 0, "completed": 0}
        for task in self.task_states.values():
            counts[task.status] += 1
        return counts

    def travel_time(self, agent_id: str, start: Coord, goal: Coord) -> float:
        if self.scene is None:
            return float("inf")
        agent = self.agent_states.get(agent_id)
        if agent is None:
            return float("inf")
        path = self.path_planner.find_path(
            self.scene.width,
            self.scene.height,
            self.scene.obstacles,
            start,
            goal,
        )
        if not path:
            return float("inf")
        return (len(path) - 1) / max(agent.spec.speed_cells_per_s, 0.1)

    def _advance_agent(self, state: AgentRuntimeState, dt_ms: float) -> None:
        remaining = dt_ms
        while remaining > 0:
            if state.phase == "idle":
                return

            if state.phase in {"moving_to_task", "returning_home"}:
                if not state.active_path:
                    state.phase = "idle"
                    state.assigned_task_id = None
                    return
                step_ms = 1000.0 / max(state.spec.speed_cells_per_s, 0.1)
                needed = step_ms - state.move_progress_ms
                consume = min(remaining, needed)
                state.move_progress_ms += consume
                remaining -= consume
                if state.move_progress_ms + 1e-9 < step_ms:
                    return
                state.move_progress_ms = 0.0
                self._advance_path_step(state)
                continue

            if state.phase == "servicing":
                consume = min(remaining, state.service_remaining_ms)
                state.service_remaining_ms -= consume
                remaining -= consume
                if state.service_remaining_ms > 0:
                    return
                self._finish_service(state)
                continue

            return

    def _advance_path_step(self, state: AgentRuntimeState) -> None:
        if state.path_index < len(state.active_path) - 1:
            state.path_index += 1
            state.position = state.active_path[state.path_index]

        if state.path_index < len(state.active_path) - 1:
            return

        if state.phase == "moving_to_task":
            task_state = self.task_states[state.assigned_task_id]
            task_state.status = "in_service"
            state.phase = "servicing"
            state.active_path = []
            state.path_index = 0
            state.service_remaining_ms = task_state.spec.service_time_s * 1000.0
            return

        if state.phase == "returning_home":
            state.phase = "idle"
            state.active_path = []
            state.path_index = 0
            state.assigned_task_id = None

    def _finish_service(self, state: AgentRuntimeState) -> None:
        task_state = self.task_states[state.assigned_task_id]
        task_state.status = "completed"
        state.completed_task_ids.append(task_state.spec.id)
        path_home = self._path_between(state.position, state.spec.home)
        if not path_home:
            raise SimulationError("error_unreachable_home")
        state.phase = "returning_home"
        state.active_path = path_home
        state.path_index = 0
        state.move_progress_ms = 0.0
        state.service_remaining_ms = 0.0

    def _dispatch_tasks(self) -> None:
        if self.scene is None:
            return

        state = PlannerState(
            t_now_s=self.time_ms / 1000.0,
            agents=[
                AgentSnapshot(
                    id=agent_id,
                    type=runtime.spec.type,
                    position=runtime.position,
                    home=runtime.spec.home,
                    speed_cells_per_s=runtime.spec.speed_cells_per_s,
                    capabilities=set(runtime.spec.capabilities),
                    phase=runtime.phase,
                )
                for agent_id, runtime in self.agent_states.items()
            ],
            tasks=[
                TaskSnapshot(
                    id=task_id,
                    type=runtime.spec.type,
                    location=runtime.spec.location,
                    service_time_s=runtime.spec.service_time_s,
                    release_time_s=runtime.spec.release_time_s,
                    due_time_s=runtime.spec.due_time_s,
                    required_capabilities=set(runtime.spec.required_capabilities),
                    status=runtime.status,
                )
                for task_id, runtime in self.task_states.items()
            ],
            travel_time=self.travel_time,
        )
        result = self.planner.plan(state)
        self._apply_plan(result)

    def _apply_plan(self, result: PlannerResult) -> None:
        for agent_id, task_id in result.assignments.items():
            agent_state = self.agent_states.get(agent_id)
            task_state = self.task_states.get(task_id)
            if agent_state is None or task_state is None:
                continue
            if agent_state.phase != "idle" or task_state.status != "pending":
                continue
            if task_state.spec.release_time_s > self.time_ms / 1000.0:
                continue

            path = self._path_between(agent_state.position, task_state.spec.location)
            if not path:
                continue
            task_state.status = "assigned"
            task_state.assigned_agent_id = agent_id
            agent_state.phase = "moving_to_task"
            agent_state.assigned_task_id = task_id
            agent_state.active_path = path
            agent_state.path_index = 0
            agent_state.move_progress_ms = 0.0

    def _path_between(self, start: Coord, goal: Coord) -> list[Coord]:
        if self.scene is None:
            return []
        return self.path_planner.find_path(
            self.scene.width,
            self.scene.height,
            self.scene.obstacles,
            start,
            goal,
        )

    def _all_tasks_completed(self) -> bool:
        return bool(self.task_states) and all(task.status == "completed" for task in self.task_states.values())

    def _validate_reachability(self, scene: SceneModel) -> None:
        for task in scene.tasks:
            reachable = False
            for agent in scene.agents:
                if not task.required_capabilities.issubset(agent.capabilities):
                    continue
                outward = self.path_planner.find_path(
                    scene.width,
                    scene.height,
                    scene.obstacles,
                    agent.home,
                    task.location,
                )
                back = self.path_planner.find_path(
                    scene.width,
                    scene.height,
                    scene.obstacles,
                    task.location,
                    agent.home,
                )
                if outward and back:
                    reachable = True
                    break
            if not reachable:
                raise SimulationError("error_unreachable_task")
