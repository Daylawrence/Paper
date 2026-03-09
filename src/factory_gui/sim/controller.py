"""Simulation controller for multiple agents and multiple tasks."""

from __future__ import annotations

from dataclasses import dataclass
import random

from factory_gui.algorithms.base import (
    AgentSnapshot,
    PlannerResult,
    PlannerState,
    TaskPlannerProtocol,
    TaskSnapshot,
)
from factory_gui.algorithms.registry import create_task_planner
from factory_gui.model.grid import Coord, in_bounds
from factory_gui.model.runtime import AgentRuntimeState, TaskRuntimeState
from factory_gui.model.scene import SceneModel, SceneValidationError, TASK_PRESETS
from factory_gui.model.task import TaskSpec
from factory_gui.planner.base import PathPlannerProtocol
from factory_gui.planner.registry import create_path_planner


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

    def __init__(
        self,
        planner: TaskPlannerProtocol | None = None,
        path_planner: PathPlannerProtocol | None = None,
    ) -> None:
        self.planner = planner or create_task_planner("greedy_nearest")
        self.path_planner = path_planner or create_path_planner("astar")
        self.speed_multiplier = 1
        self._training_output_dir: str | None = None
        self._planner_run_finalized = True
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
        self._planner_run_finalized = False
        self.agent_states = {
            agent.id: AgentRuntimeState(spec=agent, position=agent.home)
            for agent in self.scene.agents
        }
        self.task_states = {
            task.id: TaskRuntimeState(spec=task)
            for task in self.scene.tasks
        }
        self._planner_begin_run()
        self._dispatch_tasks()

    def reset(self) -> None:
        if not self._planner_run_finalized:
            self._planner_finalize_run(aborted=True)
        self.scene: SceneModel | None = None
        self.initial_scene: SceneModel | None = None
        self.agent_states: dict[str, AgentRuntimeState] = {}
        self.task_states: dict[str, TaskRuntimeState] = {}
        self.time_ms = 0.0
        self.running = False
        self._training_output_dir = None

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
            self._planner_finalize_run()

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
            "waiting_for_team": "phase_moving_to_task",
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

    def training_output_dir(self) -> str | None:
        return self._training_output_dir

    def can_insert_task_at(self, cell: Coord) -> bool:
        if self.scene is None:
            return False
        if not in_bounds(cell, self.scene.width, self.scene.height):
            return False
        return self._cell_available_for_insert(cell)

    def insert_tasks_at_cells(
        self,
        task_type: str,
        cells: list[Coord],
        seed: int | None = None,
    ) -> int:
        if self.scene is None or not self.running:
            raise SimulationError("error_insert_requires_run")
        if task_type not in TASK_PRESETS:
            raise SimulationError("error_insert_tasks_failed")
        if not cells:
            raise SimulationError("error_insert_tasks_failed")

        rng = random.Random(seed if seed is not None else int(self.time_ms) + len(self.task_states) * 977)
        now_s = int(self.time_ms / 1000.0)
        inserted = 0
        for cell in cells:
            if self.scene is None:
                break
            if not in_bounds(cell, self.scene.width, self.scene.height):
                raise SimulationError("error_insert_cell_blocked")
            if not self._cell_available_for_insert(cell):
                raise SimulationError("error_insert_cell_blocked")
            task = self._build_insert_task(task_type=task_type, location=cell, now_s=now_s, rng=rng)
            if not self._task_reachable_for_team(task):
                raise SimulationError("error_insert_tasks_failed")
            self.scene.tasks.append(task)
            self.task_states[task.id] = TaskRuntimeState(spec=task)
            inserted += 1

        if inserted <= 0:
            raise SimulationError("error_insert_tasks_failed")

        self._dispatch_tasks()
        return inserted

    def insert_random_tasks(
        self,
        count: int,
        seed: int | None = None,
        task_type: str | None = None,
    ) -> int:
        if self.scene is None or not self.running:
            raise SimulationError("error_insert_requires_run")
        if count <= 0:
            raise SimulationError("error_insert_tasks_failed")
        if task_type is not None and task_type not in TASK_PRESETS:
            raise SimulationError("error_insert_tasks_failed")

        rng = random.Random(seed if seed is not None else int(self.time_ms) + len(self.task_states) * 977)
        now_s = int(self.time_ms / 1000.0)
        added = 0
        attempts = 0
        max_attempts = max(40, count * 80)
        while added < count and attempts < max_attempts:
            attempts += 1
            chosen_task_type = task_type if task_type is not None else rng.choice(tuple(TASK_PRESETS.keys()))

            coord = self._sample_free_task_cell(rng)
            if coord is None:
                break
            task = self._build_insert_task(
                task_type=chosen_task_type,
                location=coord,
                now_s=now_s,
                rng=rng,
            )
            if not self._task_reachable_for_team(task):
                continue

            self.scene.tasks.append(task)
            self.task_states[task.id] = TaskRuntimeState(spec=task)
            added += 1

        if added <= 0:
            raise SimulationError("error_insert_tasks_failed")

        self._dispatch_tasks()
        return added

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

            if state.phase == "waiting_for_team":
                return

            return

    def _advance_path_step(self, state: AgentRuntimeState) -> None:
        if state.path_index < len(state.active_path) - 1:
            state.path_index += 1
            state.position = state.active_path[state.path_index]

        if state.path_index < len(state.active_path) - 1:
            return

        if state.phase == "moving_to_task":
            task_state = self.task_states[state.assigned_task_id]
            if state.spec.id not in task_state.arrived_agent_ids:
                task_state.arrived_agent_ids.append(state.spec.id)
            state.phase = "waiting_for_team"
            state.active_path = []
            state.path_index = 0
            state.move_progress_ms = 0.0
            state.service_remaining_ms = 0.0
            if self._task_team_ready(task_state):
                self._start_task_service(task_state)
            return

        if state.phase == "returning_home":
            state.phase = "idle"
            state.active_path = []
            state.path_index = 0
            state.assigned_task_id = None

    def _finish_service(self, state: AgentRuntimeState) -> None:
        task_state = self.task_states[state.assigned_task_id]
        if state.spec.id not in task_state.finished_agent_ids:
            task_state.finished_agent_ids.append(state.spec.id)
        if task_state.status == "in_service" and self._task_service_finished(task_state):
            task_state.status = "completed"
        if task_state.spec.id not in state.completed_task_ids:
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

        max_rounds = max(1, len(self.agent_states))
        for _ in range(max_rounds):
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
                        max_tasks_total=runtime.spec.max_tasks_total,
                        completed_task_count=len(runtime.completed_task_ids),
                        task_proficiency=dict(runtime.spec.task_proficiency),
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
                        required_proficiency=runtime.spec.required_proficiency,
                        min_agents=runtime.spec.min_agents,
                        max_agents=runtime.spec.max_agents,
                        status=self._planner_task_status(runtime),
                    )
                    for task_id, runtime in self.task_states.items()
                ],
                conflicts=set(self.scene.agent_task_conflicts),
                travel_time=self.travel_time,
            )
            result = self.planner.plan(state)
            applied = self._apply_plan(result)
            if applied <= 0:
                break
        self._sync_training_output_dir()

    def _apply_plan(self, result: PlannerResult) -> int:
        applied = 0
        for agent_id, task_id in result.assignments.items():
            agent_state = self.agent_states.get(agent_id)
            task_state = self.task_states.get(task_id)
            if agent_state is None or task_state is None:
                continue
            if agent_state.phase != "idle":
                continue
            if task_state.status not in {"pending", "assigned"}:
                continue
            if not self._task_accepts_more_agents(task_state):
                continue
            if task_state.spec.release_time_s > self.time_ms / 1000.0:
                continue
            if len(agent_state.completed_task_ids) >= agent_state.spec.max_tasks_total:
                continue
            if (agent_id, task_id) in self.scene.agent_task_conflicts:
                continue
            if agent_id in task_state.assigned_agent_ids:
                continue
            if not task_state.spec.required_capabilities.issubset(agent_state.spec.capabilities):
                continue
            if (
                self._agent_task_proficiency(agent_state.spec.task_proficiency, task_state.spec.type)
                < task_state.spec.required_proficiency
            ):
                continue

            path = self._path_between(agent_state.position, task_state.spec.location)
            if not path:
                continue
            task_state.status = "assigned"
            task_state.assigned_agent_ids.append(agent_id)
            agent_state.phase = "moving_to_task"
            agent_state.assigned_task_id = task_id
            agent_state.active_path = path
            agent_state.path_index = 0
            agent_state.move_progress_ms = 0.0
            agent_state.service_remaining_ms = 0.0
            applied += 1
        return applied

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
            required_team = max(1, min(task.min_agents, task.max_agents))
            reachable_count = 0
            for agent in scene.agents:
                if not task.required_capabilities.issubset(agent.capabilities):
                    continue
                if (
                    self._agent_task_proficiency(agent.task_proficiency, task.type)
                    < task.required_proficiency
                ):
                    continue
                if (agent.id, task.id) in scene.agent_task_conflicts:
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
                    reachable_count += 1
                    if reachable_count >= required_team:
                        break
            if reachable_count < required_team:
                raise SimulationError("error_unreachable_task")

    def _planner_begin_run(self) -> None:
        if self.scene is None:
            return
        begin_run = getattr(self.planner, "begin_run", None)
        if callable(begin_run):
            begin_run(
                scene_name=self.scene.name,
                path_planner_name=self.path_planner.name,
                agent_count=len(self.scene.agents),
                task_count=len(self.scene.tasks),
            )
        self._sync_training_output_dir()

    def _planner_finalize_run(self, aborted: bool = False) -> None:
        if self._planner_run_finalized:
            return
        end_run = getattr(self.planner, "end_run", None)
        if callable(end_run):
            summary = self.summary()
            end_run(
                {
                    "aborted": aborted,
                    "time_s": summary.time_s,
                    "total_tasks": summary.total_tasks,
                    "completed_tasks": summary.completed_tasks,
                    "idle_agents": summary.idle_agents,
                }
            )
        self._planner_run_finalized = True
        self._sync_training_output_dir()

    def _sync_training_output_dir(self) -> None:
        latest_dir = getattr(self.planner, "latest_run_dir", None)
        if latest_dir is None:
            return
        self._training_output_dir = str(latest_dir)

    def _agent_task_proficiency(self, profile: dict[str, float], task_type: str) -> float:
        if task_type in profile:
            return profile[task_type]
        if not profile:
            return 1.0
        return 0.0

    def _planner_task_status(self, task_state: TaskRuntimeState) -> str:
        if task_state.status in {"completed", "in_service"}:
            return task_state.status
        if self._task_accepts_more_agents(task_state):
            return "pending"
        return "assigned"

    def _required_team_size(self, task_state: TaskRuntimeState) -> int:
        return max(1, min(task_state.spec.min_agents, task_state.spec.max_agents))

    def _task_accepts_more_agents(self, task_state: TaskRuntimeState) -> bool:
        if task_state.status not in {"pending", "assigned"}:
            return False
        return len(task_state.assigned_agent_ids) < self._required_team_size(task_state)

    def _task_team_ready(self, task_state: TaskRuntimeState) -> bool:
        if task_state.status not in {"pending", "assigned"}:
            return False
        return len(task_state.arrived_agent_ids) >= self._required_team_size(task_state)

    def _task_service_finished(self, task_state: TaskRuntimeState) -> bool:
        if not task_state.active_agent_ids:
            return False
        finished = set(task_state.finished_agent_ids)
        return all(agent_id in finished for agent_id in task_state.active_agent_ids)

    def _start_task_service(self, task_state: TaskRuntimeState) -> None:
        if task_state.status == "in_service":
            return
        required = self._required_team_size(task_state)
        task_state.active_agent_ids = list(task_state.arrived_agent_ids[:required])
        if len(task_state.active_agent_ids) < required:
            return
        task_state.status = "in_service"
        service_ms = task_state.spec.service_time_s * 1000.0
        for agent_id in task_state.active_agent_ids:
            agent_state = self.agent_states.get(agent_id)
            if agent_state is None:
                continue
            agent_state.phase = "servicing"
            agent_state.active_path = []
            agent_state.path_index = 0
            agent_state.move_progress_ms = 0.0
            agent_state.service_remaining_ms = service_ms

    def _next_task_id(self, task_type: str) -> str:
        if self.scene is None:
            return f"{task_type}_1"
        prefix = f"{task_type}_"
        highest = 0
        for task in self.scene.tasks:
            if not task.id.startswith(prefix):
                continue
            suffix = task.id.removeprefix(prefix)
            if suffix.isdigit():
                highest = max(highest, int(suffix))
        return f"{task_type}_{highest + 1}"

    def _sample_free_task_cell(self, rng: random.Random) -> Coord | None:
        if self.scene is None:
            return None
        candidates = [
            (x, y)
            for y in range(self.scene.height)
            for x in range(self.scene.width)
            if self._cell_available_for_insert((x, y))
        ]
        if not candidates:
            return None
        return candidates[rng.randrange(len(candidates))]

    def _cell_available_for_insert(self, cell: Coord) -> bool:
        if self.scene is None:
            return False
        if cell in self.scene.obstacles:
            return False
        if any(task.spec.location == cell for task in self.task_states.values()):
            return False
        if any(agent.spec.home == cell for agent in self.agent_states.values()):
            return False
        if any(agent.position == cell for agent in self.agent_states.values()):
            return False
        return True

    def _build_insert_task(
        self,
        task_type: str,
        location: Coord,
        now_s: int,
        rng: random.Random,
    ) -> TaskSpec:
        preset = TASK_PRESETS[task_type]
        min_agents = int(preset.get("min_agents", 1))
        max_agents = int(preset.get("max_agents", min_agents))
        team_size = rng.randint(min_agents, max(min_agents, max_agents))
        task_id = self._next_task_id(task_type)
        service_time = int(preset["service_time_s"])
        return TaskSpec(
            id=task_id,
            type=task_type,
            location=location,
            service_time_s=service_time,
            release_time_s=now_s,
            due_time_s=now_s + service_time * 8,
            required_capabilities=set(preset["required_capabilities"]),
            required_proficiency=float(preset["required_proficiency"]),
            min_agents=team_size,
            max_agents=team_size,
        )

    def _task_reachable_for_team(self, task: TaskSpec) -> bool:
        if self.scene is None:
            return False
        required_team = max(1, min(task.min_agents, task.max_agents))
        reachable_count = 0
        for agent in self.agent_states.values():
            if not task.required_capabilities.issubset(agent.spec.capabilities):
                continue
            if (
                self._agent_task_proficiency(agent.spec.task_proficiency, task.type)
                < task.required_proficiency
            ):
                continue
            if (agent.spec.id, task.id) in self.scene.agent_task_conflicts:
                continue
            outward = self.path_planner.find_path(
                self.scene.width,
                self.scene.height,
                self.scene.obstacles,
                agent.position,
                task.location,
            )
            back = self.path_planner.find_path(
                self.scene.width,
                self.scene.height,
                self.scene.obstacles,
                task.location,
                agent.spec.home,
            )
            if outward and back:
                reachable_count += 1
                if reachable_count >= required_team:
                    return True
        return False
