"""Scene model and validation."""

from __future__ import annotations

from dataclasses import dataclass, field

from factory_gui.constants import GRID_HEIGHT, GRID_WIDTH
from factory_gui.model.grid import Coord, in_bounds


class SceneValidationError(ValueError):
    """Raised when a scene is invalid."""


@dataclass(slots=True)
class SceneModel:
    width: int = GRID_WIDTH
    height: int = GRID_HEIGHT
    obstacles: set[Coord] = field(default_factory=set)
    start: Coord | None = None
    pickup: Coord | None = None
    dropoff: Coord | None = None

    @classmethod
    def empty(cls) -> "SceneModel":
        return cls()

    def copy(self) -> "SceneModel":
        return SceneModel(
            width=self.width,
            height=self.height,
            obstacles=set(self.obstacles),
            start=self.start,
            pickup=self.pickup,
            dropoff=self.dropoff,
        )

    def all_markers(self) -> dict[str, Coord | None]:
        return {
            "start": self.start,
            "pickup": self.pickup,
            "dropoff": self.dropoff,
        }

    def validate_static(self) -> None:
        if self.width != GRID_WIDTH or self.height != GRID_HEIGHT:
            raise SceneValidationError(
                f"Only {GRID_WIDTH}x{GRID_HEIGHT} scenes are supported."
            )

        for cell in self.obstacles:
            self._validate_coord(cell, "Obstacle")

        occupied: set[Coord] = set()
        for name, cell in self.all_markers().items():
            if cell is None:
                continue
            self._validate_coord(cell, name.capitalize())
            if cell in self.obstacles:
                raise SceneValidationError(f"{name.capitalize()} cannot be on an obstacle.")
            if cell in occupied:
                raise SceneValidationError("Start, pickup, and dropoff must be on distinct cells.")
            occupied.add(cell)

    def validate_for_run(self) -> None:
        self.validate_static()
        missing = [name for name, cell in self.all_markers().items() if cell is None]
        if missing:
            raise SceneValidationError(
                f"Scene is missing required points: {', '.join(missing)}."
            )

    def _validate_coord(self, coord: Coord, label: str) -> None:
        if not in_bounds(coord, self.width, self.height):
            raise SceneValidationError(f"{label} coordinate {coord} is out of bounds.")

    def clear_cell(self, coord: Coord) -> None:
        self.obstacles.discard(coord)
        if self.start == coord:
            self.start = None
        if self.pickup == coord:
            self.pickup = None
        if self.dropoff == coord:
            self.dropoff = None

    def set_tool_at(self, tool: str, coord: Coord) -> None:
        self._validate_coord(coord, "Cell")
        if tool == "erase":
            self.clear_cell(coord)
            return
        if tool == "obstacle":
            if coord in self.obstacles:
                self.obstacles.remove(coord)
                return
            self.clear_cell(coord)
            self.obstacles.add(coord)
            return

        self.clear_cell(coord)
        self.obstacles.discard(coord)
        if tool == "start":
            self.start = coord
        elif tool == "pickup":
            self.pickup = coord
        elif tool == "dropoff":
            self.dropoff = coord
        else:
            raise SceneValidationError(f"Unknown tool: {tool}")
