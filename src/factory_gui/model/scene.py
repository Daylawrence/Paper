"""Scene model, presets, and obstacle generation."""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from factory_gui import constants
from factory_gui.model.agent import AgentSpec
from factory_gui.model.grid import Coord, in_bounds, neighbors
from factory_gui.model.task import TaskSpec


class SceneValidationError(ValueError):
    """Raised when a scene is invalid."""


AGENT_PRESETS: dict[str, dict[str, object]] = {
    "agv": {"speed": 3.0, "capabilities": {"transport"}},
    "forklift": {"speed": 2.0, "capabilities": {"heavy_load"}},
    "picker": {"speed": 2.5, "capabilities": {"precision_pick"}},
}

TASK_PRESETS: dict[str, dict[str, object]] = {
    "transport": {"service_time_s": 15, "required_capabilities": {"transport"}},
    "heavy": {"service_time_s": 24, "required_capabilities": {"heavy_load"}},
    "precision": {"service_time_s": 18, "required_capabilities": {"precision_pick"}},
}

DEFAULT_AGENT_LAYOUT: tuple[tuple[str, Coord], ...] = (
    ("agv", (2, 2)),
    ("agv", (2, 4)),
    ("forklift", (2, 8)),
    ("forklift", (2, 10)),
    ("picker", (2, 14)),
    ("picker", (2, 16)),
)

DEFAULT_TASK_LAYOUT: tuple[tuple[str, tuple[float, float]], ...] = (
    ("transport", (0.42, 0.18)),
    ("heavy", (0.58, 0.25)),
    ("precision", (0.68, 0.36)),
    ("transport", (0.74, 0.58)),
    ("heavy", (0.55, 0.72)),
    ("precision", (0.38, 0.62)),
)


@dataclass(slots=True)
class SceneModel:
    width: int = constants.DEFAULT_GRID_WIDTH
    height: int = constants.DEFAULT_GRID_HEIGHT
    cell_size_px: int = constants.DEFAULT_CELL_SIZE_PX
    name: str = "factory_multi_agent"
    obstacles: set[Coord] = field(default_factory=set)
    obstacle_seed: int = 42
    obstacle_density: float = 0.12
    agents: list[AgentSpec] = field(default_factory=list)
    tasks: list[TaskSpec] = field(default_factory=list)

    @classmethod
    def empty(cls) -> "SceneModel":
        return cls()

    @classmethod
    def default_scene(cls) -> "SceneModel":
        scene = cls()
        scene.add_default_agents()
        scene.add_default_tasks()
        return scene

    def copy(self) -> "SceneModel":
        return SceneModel(
            width=self.width,
            height=self.height,
            cell_size_px=self.cell_size_px,
            name=self.name,
            obstacles=set(self.obstacles),
            obstacle_seed=self.obstacle_seed,
            obstacle_density=self.obstacle_density,
            agents=[
                AgentSpec(
                    id=agent.id,
                    type=agent.type,
                    home=agent.home,
                    speed_cells_per_s=agent.speed_cells_per_s,
                    capabilities=set(agent.capabilities),
                )
                for agent in self.agents
            ],
            tasks=[
                TaskSpec(
                    id=task.id,
                    type=task.type,
                    location=task.location,
                    service_time_s=task.service_time_s,
                    release_time_s=task.release_time_s,
                    due_time_s=task.due_time_s,
                    required_capabilities=set(task.required_capabilities),
                )
                for task in self.tasks
            ],
        )

    def validate_static(self) -> None:
        if not (constants.MIN_GRID_WIDTH <= self.width <= constants.MAX_GRID_WIDTH):
            raise SceneValidationError(
                f"Grid width must be between {constants.MIN_GRID_WIDTH} and {constants.MAX_GRID_WIDTH}."
            )
        if not (constants.MIN_GRID_HEIGHT <= self.height <= constants.MAX_GRID_HEIGHT):
            raise SceneValidationError(
                f"Grid height must be between {constants.MIN_GRID_HEIGHT} and {constants.MAX_GRID_HEIGHT}."
            )

        occupied: dict[Coord, str] = {}
        for cell in self.obstacles:
            self._validate_coord(cell, "Obstacle")
            occupied[cell] = "obstacle"

        seen_agent_ids: set[str] = set()
        for agent in self.agents:
            if agent.id in seen_agent_ids:
                raise SceneValidationError(f"Duplicate agent id: {agent.id}")
            seen_agent_ids.add(agent.id)
            self._validate_coord(agent.home, f"Agent {agent.id}")
            if agent.home in self.obstacles:
                raise SceneValidationError(f"Agent {agent.id} cannot be on an obstacle.")
            if agent.home in occupied:
                raise SceneValidationError(f"Cell {agent.home} cannot contain multiple entities.")
            occupied[agent.home] = agent.id

        seen_task_ids: set[str] = set()
        for task in self.tasks:
            if task.id in seen_task_ids:
                raise SceneValidationError(f"Duplicate task id: {task.id}")
            seen_task_ids.add(task.id)
            self._validate_coord(task.location, f"Task {task.id}")
            if task.location in self.obstacles:
                raise SceneValidationError(f"Task {task.id} cannot be on an obstacle.")
            if task.location in occupied:
                raise SceneValidationError(f"Cell {task.location} cannot contain multiple entities.")
            occupied[task.location] = task.id

    def validate_for_run(self) -> None:
        self.validate_static()
        if not self.agents:
            raise SceneValidationError("Scene must contain at least one agent.")
        if not self.tasks:
            raise SceneValidationError("Scene must contain at least one task.")

    def add_default_agents(self) -> None:
        self.agents.clear()
        counters = {key: 0 for key in AGENT_PRESETS}
        for agent_type, coord in DEFAULT_AGENT_LAYOUT:
            safe_coord = self._fit_coord(coord)
            preset = AGENT_PRESETS[agent_type]
            counters[agent_type] += 1
            agent_id = f"{agent_type}_{counters[agent_type]}"
            self.clear_cell(safe_coord)
            self.agents.append(
                AgentSpec(
                    id=agent_id,
                    type=agent_type,
                    home=safe_coord,
                    speed_cells_per_s=float(preset["speed"]),
                    capabilities=set(preset["capabilities"]),
                )
            )

    def add_default_tasks(self) -> None:
        self.tasks.clear()
        counters = {key: 0 for key in TASK_PRESETS}
        for task_type, normalized in DEFAULT_TASK_LAYOUT:
            location = (
                min(self.width - 1, max(0, int(self.width * normalized[0]))),
                min(self.height - 1, max(0, int(self.height * normalized[1]))),
            )
            preset = TASK_PRESETS[task_type]
            counters[task_type] += 1
            task_id = f"{task_type}_{counters[task_type]}"
            self.clear_cell(location)
            release = len(self.tasks) * 10
            service_time = int(preset["service_time_s"])
            self.tasks.append(
                TaskSpec(
                    id=task_id,
                    type=task_type,
                    location=location,
                    service_time_s=service_time,
                    release_time_s=release,
                    due_time_s=release + service_time * 8,
                    required_capabilities=set(preset["required_capabilities"]),
                )
            )

    def generate_random_obstacles(
        self,
        seed: int | None = None,
        density: float | None = None,
        max_attempts: int = 20,
    ) -> bool:
        protected = self.special_cells()
        density = self.obstacle_density if density is None else density
        density = max(0.0, min(0.35, density))
        base_seed = (self.obstacle_seed + 1) if seed is None else seed

        candidate_cells = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in protected
        ]
        obstacle_count = int(len(candidate_cells) * density)
        rng = random.Random(base_seed)

        for attempt in range(max_attempts):
            current_seed = base_seed + attempt
            rng.seed(current_seed)
            sampled = set(rng.sample(candidate_cells, obstacle_count)) if obstacle_count else set()
            if self._special_cells_connected(sampled, protected):
                self.obstacles = sampled
                self.obstacle_seed = current_seed
                self.obstacle_density = density
                return True
        return False

    def clear_obstacles(self) -> None:
        self.obstacles.clear()

    def special_cells(self) -> set[Coord]:
        return {agent.home for agent in self.agents} | {task.location for task in self.tasks}

    def clear_cell(self, coord: Coord) -> None:
        self.obstacles.discard(coord)
        self.agents = [agent for agent in self.agents if agent.home != coord]
        self.tasks = [task for task in self.tasks if task.location != coord]

    def set_tool_at(self, tool: str, coord: Coord) -> None:
        self._validate_coord(coord, "Cell")
        if tool == "erase":
            self.clear_cell(coord)
            return
        if tool == "obstacle":
            if coord in self.obstacles:
                self.obstacles.remove(coord)
                return
            if coord in self.special_cells():
                self.clear_cell(coord)
            self.obstacles.add(coord)
            return
        if tool.startswith("agent_"):
            agent_type = tool.split("_", 1)[1]
            self.clear_cell(coord)
            self._add_agent(agent_type, coord)
            return
        if tool.startswith("task_"):
            task_type = tool.split("_", 1)[1]
            self.clear_cell(coord)
            self._add_task(task_type, coord)
            return
        raise SceneValidationError(f"Unknown tool: {tool}")

    def _add_agent(self, agent_type: str, coord: Coord) -> None:
        preset = AGENT_PRESETS.get(agent_type)
        if preset is None:
            raise SceneValidationError(f"Unknown agent type: {agent_type}")
        agent_id = self._next_agent_id(agent_type)
        self.agents.append(
            AgentSpec(
                id=agent_id,
                type=agent_type,
                home=coord,
                speed_cells_per_s=float(preset["speed"]),
                capabilities=set(preset["capabilities"]),
            )
        )

    def _add_task(self, task_type: str, coord: Coord) -> None:
        preset = TASK_PRESETS.get(task_type)
        if preset is None:
            raise SceneValidationError(f"Unknown task type: {task_type}")
        task_id = self._next_task_id(task_type)
        release = len(self.tasks) * 10
        service_time = int(preset["service_time_s"])
        self.tasks.append(
            TaskSpec(
                id=task_id,
                type=task_type,
                location=coord,
                service_time_s=service_time,
                release_time_s=release,
                due_time_s=release + service_time * 8,
                required_capabilities=set(preset["required_capabilities"]),
            )
        )

    def _next_agent_id(self, agent_type: str) -> str:
        prefix = f"{agent_type}_"
        highest = 0
        for agent in self.agents:
            if agent.id.startswith(prefix):
                suffix = agent.id.removeprefix(prefix)
                if suffix.isdigit():
                    highest = max(highest, int(suffix))
        return f"{agent_type}_{highest + 1}"

    def _next_task_id(self, task_type: str) -> str:
        prefix = f"{task_type}_"
        highest = 0
        for task in self.tasks:
            if task.id.startswith(prefix):
                suffix = task.id.removeprefix(prefix)
                if suffix.isdigit():
                    highest = max(highest, int(suffix))
        return f"{task_type}_{highest + 1}"

    def _validate_coord(self, coord: Coord, label: str) -> None:
        if not in_bounds(coord, self.width, self.height):
            raise SceneValidationError(f"{label} coordinate {coord} is out of bounds.")

    def _special_cells_connected(self, obstacles: set[Coord], protected: set[Coord]) -> bool:
        if len(protected) <= 1:
            return True
        start = next(iter(protected))
        frontier = [start]
        visited = {start}

        while frontier:
            current = frontier.pop()
            for neighbor in neighbors(current, self.width, self.height):
                if neighbor in obstacles or neighbor in visited:
                    continue
                visited.add(neighbor)
                frontier.append(neighbor)
        return protected.issubset(visited)

    def _fit_coord(self, coord: Coord) -> Coord:
        return (
            max(0, min(self.width - 1, coord[0])),
            max(0, min(self.height - 1, coord[1])),
        )
