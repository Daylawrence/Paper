"""Simulation controller for a single pickup and dropoff task."""

from __future__ import annotations

from factory_gui.constants import BASE_MOVE_MS, SERVICE_DWELL_MS
from factory_gui.model.robot import RobotState
from factory_gui.model.scene import SceneModel, SceneValidationError
from factory_gui.model.task import ItemState
from factory_gui.planner.astar import AStarPlanner


class SimulationError(ValueError):
    """Raised when the simulation cannot start."""

    def __init__(self, message_key: str) -> None:
        self.message_key = message_key
        super().__init__(message_key)


class SimulationController:
    """Drive a single robot through pickup and dropoff phases."""

    def __init__(self, planner: AStarPlanner | None = None) -> None:
        self.planner = planner or AStarPlanner()
        self.robot = RobotState()
        self.item = ItemState()
        self.initial_scene: SceneModel | None = None
        self.scene: SceneModel | None = None
        self.path_to_pickup: list[tuple[int, int]] = []
        self.path_to_dropoff: list[tuple[int, int]] = []
        self.planned_path: list[tuple[int, int]] = []
        self.speed_multiplier = 1

    def set_speed_multiplier(self, multiplier: int) -> None:
        self.speed_multiplier = max(1, multiplier)

    def start(self, scene: SceneModel) -> None:
        try:
            scene.validate_for_run()
        except SceneValidationError as exc:
            raise SimulationError(str(exc)) from exc

        path_to_pickup = self.planner.find_path(
            scene.width,
            scene.height,
            scene.obstacles,
            scene.start,
            scene.pickup,
        )
        if not path_to_pickup:
            raise SimulationError("error_unreachable_pickup")

        path_to_dropoff = self.planner.find_path(
            scene.width,
            scene.height,
            scene.obstacles,
            scene.pickup,
            scene.dropoff,
        )
        if not path_to_dropoff:
            raise SimulationError("error_unreachable_dropoff")

        self.initial_scene = scene.copy()
        self.scene = scene.copy()
        self.path_to_pickup = path_to_pickup
        self.path_to_dropoff = path_to_dropoff
        self.planned_path = path_to_pickup + path_to_dropoff[1:]
        self.robot = RobotState(
            grid_pos=scene.start,
            phase="moving_to_pickup",
            active_path=path_to_pickup,
            path_index=0,
            has_item=False,
        )
        self.item = ItemState(
            pickup=scene.pickup,
            dropoff=scene.dropoff,
            at_pickup=True,
            carried=False,
            delivered=False,
        )

    def reset(self) -> None:
        self.robot = RobotState()
        self.item = ItemState()
        self.scene = None
        self.path_to_pickup = []
        self.path_to_dropoff = []
        self.planned_path = []

    def update(self, dt_ms: int) -> None:
        phase = self.robot.phase
        if phase in {"idle", "done"}:
            return
        if phase in {"moving_to_pickup", "moving_to_dropoff"}:
            self.robot.move_elapsed_ms += max(0, dt_ms)
            step_ms = max(1, BASE_MOVE_MS // self.speed_multiplier)
            while self.robot.move_elapsed_ms >= step_ms and self.robot.phase in {
                "moving_to_pickup",
                "moving_to_dropoff",
            }:
                self.robot.move_elapsed_ms -= step_ms
                self._advance_move()
            return

        self.robot.dwell_elapsed_ms += max(0, dt_ms)
        if self.robot.dwell_elapsed_ms < SERVICE_DWELL_MS:
            return
        self.robot.dwell_elapsed_ms = 0
        if phase == "loading":
            self.item.at_pickup = False
            self.item.carried = True
            self.robot.has_item = True
            self.robot.phase = "moving_to_dropoff"
            self.robot.active_path = list(self.path_to_dropoff)
            self.robot.path_index = 0
            self.robot.move_elapsed_ms = 0
        elif phase == "unloading":
            self.item.carried = False
            self.item.delivered = True
            self.robot.has_item = False
            self.robot.phase = "done"
            self.robot.active_path = []
            self.robot.path_index = 0

    def current_robot_cell(self) -> tuple[int, int] | None:
        return self.robot.grid_pos

    def current_path(self) -> list[tuple[int, int]]:
        if self.robot.phase not in {"moving_to_pickup", "moving_to_dropoff"}:
            return []
        return self.robot.active_path[self.robot.path_index :]

    def status_text(self) -> str:
        return {
            "phase_idle": "Idle",
            "phase_moving_to_pickup": "Moving to pickup",
            "phase_loading": "Loading item",
            "phase_moving_to_dropoff": "Moving to dropoff",
            "phase_unloading": "Unloading item",
            "phase_done": "Task complete",
        }[self.status_key()]

    def status_key(self) -> str:
        phase = self.robot.phase
        if phase == "idle":
            return "phase_idle"
        if phase == "moving_to_pickup":
            return "phase_moving_to_pickup"
        if phase == "loading":
            return "phase_loading"
        if phase == "moving_to_dropoff":
            return "phase_moving_to_dropoff"
        if phase == "unloading":
            return "phase_unloading"
        if phase == "done":
            return "phase_done"
        return "phase_idle"

    def _advance_move(self) -> None:
        if self.robot.path_index < len(self.robot.active_path) - 1:
            self.robot.path_index += 1
            self.robot.grid_pos = self.robot.active_path[self.robot.path_index]

        if self.robot.path_index < len(self.robot.active_path) - 1:
            return

        if self.robot.phase == "moving_to_pickup":
            self.robot.phase = "loading"
            self.robot.active_path = []
            self.robot.path_index = 0
            self.robot.move_elapsed_ms = 0
            self.robot.dwell_elapsed_ms = 0
        elif self.robot.phase == "moving_to_dropoff":
            self.robot.phase = "unloading"
            self.robot.active_path = []
            self.robot.path_index = 0
            self.robot.move_elapsed_ms = 0
            self.robot.dwell_elapsed_ms = 0
