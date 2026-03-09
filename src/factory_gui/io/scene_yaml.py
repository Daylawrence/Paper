"""YAML persistence for factory scenes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from factory_gui import constants
from factory_gui.model.agent import AgentSpec
from factory_gui.model.grid import Coord
from factory_gui.model.scene import (
    AGENT_PRESETS,
    TASK_PRESETS,
    SceneModel,
    SceneValidationError,
)
from factory_gui.model.task import TaskSpec


class SceneFileError(ValueError):
    """Raised when a scene file cannot be loaded or saved."""


class SceneYamlStore:
    """Persist SceneModel to YAML."""

    def load(self, path: str | Path) -> SceneModel:
        file_path = Path(path)
        try:
            raw = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise SceneFileError(f"Scene file not found: {file_path}") from exc
        except yaml.YAMLError as exc:
            raise SceneFileError(f"Invalid YAML: {exc}") from exc

        if not isinstance(raw, dict):
            raise SceneFileError("Scene file must contain a mapping at the top level.")
        if raw.get("version") != 2:
            raise SceneFileError("Only scene format version 2 is supported.")
        scene_data = raw.get("scene")
        if not isinstance(scene_data, dict):
            raise SceneFileError("Scene file must contain a 'scene' mapping.")

        grid_data = scene_data.get("grid")
        if not isinstance(grid_data, dict):
            raise SceneFileError("Scene file must contain a 'scene.grid' mapping.")

        scene = SceneModel(
            name=str(scene_data.get("name", "factory_multi_agent")),
            width=self._read_int(grid_data.get("width"), "scene.grid.width"),
            height=self._read_int(grid_data.get("height"), "scene.grid.height"),
            cell_size_px=self._read_int(
                grid_data.get("cell_size_px", constants.DEFAULT_CELL_SIZE_PX),
                "scene.grid.cell_size_px",
            ),
            obstacle_seed=self._read_int(
                scene_data.get("obstacle_generation", {}).get("seed", 42),
                "scene.obstacle_generation.seed",
            ),
            obstacle_density=float(
                scene_data.get("obstacle_generation", {}).get("density", 0.12)
            ),
            obstacles=self._read_coords(scene_data.get("obstacles", []), "obstacles"),
            agents=self._read_agents(scene_data.get("agents", [])),
            tasks=self._read_tasks(scene_data.get("tasks", [])),
            agent_task_conflicts=self._read_conflicts(
                scene_data.get("agent_task_conflicts", []),
                "scene.agent_task_conflicts",
            ),
        )
        try:
            scene.validate_static()
        except SceneValidationError as exc:
            raise SceneFileError(str(exc)) from exc
        return scene

    def save(self, path: str | Path, scene: SceneModel) -> None:
        try:
            scene.validate_static()
        except SceneValidationError as exc:
            raise SceneFileError(str(exc)) from exc

        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 2,
            "scene": {
                "name": scene.name,
                "grid": {
                    "width": scene.width,
                    "height": scene.height,
                    "cell_size_px": scene.cell_size_px,
                },
                "obstacle_generation": {
                    "seed": scene.obstacle_seed,
                    "density": scene.obstacle_density,
                },
                "obstacles": [
                    [x, y]
                    for x, y in sorted(scene.obstacles, key=lambda cell: (cell[1], cell[0]))
                ],
                "agents": [
                    {
                        "id": agent.id,
                        "type": agent.type,
                        "home": list(agent.home),
                        "speed_cells_per_s": agent.speed_cells_per_s,
                        "max_tasks_total": agent.max_tasks_total,
                        "capabilities": sorted(agent.capabilities),
                        "task_proficiency": {
                            key: agent.task_proficiency[key]
                            for key in sorted(agent.task_proficiency)
                        },
                    }
                    for agent in scene.agents
                ],
                "tasks": [
                    {
                        "id": task.id,
                        "type": task.type,
                        "location": list(task.location),
                        "service_time_s": task.service_time_s,
                        "release_time_s": task.release_time_s,
                        "due_time_s": task.due_time_s,
                        "required_capabilities": sorted(task.required_capabilities),
                        "required_proficiency": task.required_proficiency,
                        "min_agents": task.min_agents,
                        "max_agents": task.max_agents,
                    }
                    for task in scene.tasks
                ],
                "agent_task_conflicts": [
                    {"agent_id": agent_id, "task_id": task_id}
                    for agent_id, task_id in sorted(scene.agent_task_conflicts)
                ],
            },
        }
        file_path.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    def _read_coords(self, value: Any, label: str) -> set[Coord]:
        if not isinstance(value, list):
            raise SceneFileError(f"'{label}' must be a list of [x, y] pairs.")
        return {self._read_coord(item, f"{label}[{idx}]") for idx, item in enumerate(value)}

    def _read_agents(self, value: Any) -> list[AgentSpec]:
        if not isinstance(value, list):
            raise SceneFileError("'agents' must be a list.")
        agents: list[AgentSpec] = []
        for idx, item in enumerate(value):
            if not isinstance(item, dict):
                raise SceneFileError(f"'agents[{idx}]' must be a mapping.")
            agents.append(
                AgentSpec(
                    id=str(item.get("id")),
                    type=str(item.get("type")),
                    home=self._read_coord(item.get("home"), f"agents[{idx}].home"),
                    speed_cells_per_s=float(item.get("speed_cells_per_s", 1.0)),
                    max_tasks_total=self._read_int(
                        item.get("max_tasks_total", 3),
                        f"agents[{idx}].max_tasks_total",
                    ),
                    capabilities=self._read_string_set(
                        item.get("capabilities", []),
                        f"agents[{idx}].capabilities",
                    ),
                    task_proficiency=self._read_proficiency(
                        item.get("task_proficiency"),
                        str(item.get("type")),
                        f"agents[{idx}].task_proficiency",
                    ),
                )
            )
        return agents

    def _read_tasks(self, value: Any) -> list[TaskSpec]:
        if not isinstance(value, list):
            raise SceneFileError("'tasks' must be a list.")
        tasks: list[TaskSpec] = []
        for idx, item in enumerate(value):
            if not isinstance(item, dict):
                raise SceneFileError(f"'tasks[{idx}]' must be a mapping.")
            due = item.get("due_time_s")
            task_type = str(item.get("type"))
            default_required = float(
                TASK_PRESETS.get(task_type, {}).get("required_proficiency", 0.5)
            )
            tasks.append(
                TaskSpec(
                    id=str(item.get("id")),
                    type=task_type,
                    location=self._read_coord(item.get("location"), f"tasks[{idx}].location"),
                    service_time_s=self._read_int(
                        item.get("service_time_s"),
                        f"tasks[{idx}].service_time_s",
                    ),
                    release_time_s=self._read_int(
                        item.get("release_time_s", 0),
                        f"tasks[{idx}].release_time_s",
                    ),
                    due_time_s=None if due is None else self._read_int(due, f"tasks[{idx}].due_time_s"),
                    required_capabilities=self._read_string_set(
                        item.get("required_capabilities", []),
                        f"tasks[{idx}].required_capabilities",
                    ),
                    required_proficiency=float(
                        item.get("required_proficiency", default_required)
                    ),
                    min_agents=self._read_int(
                        item.get("min_agents", 1),
                        f"tasks[{idx}].min_agents",
                    ),
                    max_agents=self._read_int(
                        item.get("max_agents", 1),
                        f"tasks[{idx}].max_agents",
                    ),
                )
            )
        return tasks

    def _read_conflicts(self, value: Any, label: str) -> set[tuple[str, str]]:
        if not isinstance(value, list):
            raise SceneFileError(f"'{label}' must be a list.")
        conflicts: set[tuple[str, str]] = set()
        for idx, item in enumerate(value):
            if isinstance(item, list) and len(item) == 2 and all(isinstance(v, str) for v in item):
                conflicts.add((item[0], item[1]))
                continue
            if isinstance(item, dict):
                agent_id = item.get("agent_id")
                task_id = item.get("task_id")
                if isinstance(agent_id, str) and isinstance(task_id, str):
                    conflicts.add((agent_id, task_id))
                    continue
            raise SceneFileError(
                f"'{label}[{idx}]' must be {{agent_id, task_id}} or [agent_id, task_id]."
            )
        return conflicts

    def _read_coord(self, value: Any, label: str) -> Coord:
        if (
            not isinstance(value, list)
            or len(value) != 2
            or not all(isinstance(entry, int) for entry in value)
        ):
            raise SceneFileError(f"'{label}' must be a two-item integer list.")
        return (value[0], value[1])

    def _read_int(self, value: Any, label: str) -> int:
        if not isinstance(value, int):
            raise SceneFileError(f"'{label}' must be an integer.")
        return value

    def _read_string_set(self, value: Any, label: str) -> set[str]:
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise SceneFileError(f"'{label}' must be a list of strings.")
        return set(value)

    def _read_proficiency(self, value: Any, agent_type: str, label: str) -> dict[str, float]:
        default_profile = self._default_proficiency(agent_type)
        if value is None:
            return default_profile
        if not isinstance(value, dict):
            raise SceneFileError(f"'{label}' must be a mapping of task type to float.")

        merged = dict(default_profile)
        for key, score in value.items():
            if not isinstance(key, str):
                raise SceneFileError(f"'{label}' keys must be strings.")
            if not isinstance(score, (int, float)):
                raise SceneFileError(f"'{label}[{key}]' must be a number.")
            merged[key] = float(score)
        return merged

    def _default_proficiency(self, agent_type: str) -> dict[str, float]:
        profile_center = AGENT_PRESETS.get(agent_type, {}).get("profile_center")
        if isinstance(profile_center, dict):
            return {str(k): float(v) for k, v in profile_center.items()}
        return {task_type: 0.5 for task_type in TASK_PRESETS}
