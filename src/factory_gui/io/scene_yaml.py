"""YAML persistence for scenes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from factory_gui.constants import CELL_SIZE_PX, GRID_HEIGHT, GRID_WIDTH
from factory_gui.model.grid import Coord
from factory_gui.model.scene import SceneModel, SceneValidationError


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
        if raw.get("version") != 1:
            raise SceneFileError("Only scene format version 1 is supported.")
        scene_data = raw.get("scene")
        if not isinstance(scene_data, dict):
            raise SceneFileError("Scene file must contain a 'scene' mapping.")

        grid_data = scene_data.get("grid")
        if not isinstance(grid_data, dict):
            raise SceneFileError("Scene file must contain a 'scene.grid' mapping.")
        if grid_data.get("width") != GRID_WIDTH or grid_data.get("height") != GRID_HEIGHT:
            raise SceneFileError(f"Only {GRID_WIDTH}x{GRID_HEIGHT} scenes are supported.")
        if grid_data.get("cell_size_px") != CELL_SIZE_PX:
            raise SceneFileError(f"cell_size_px must be {CELL_SIZE_PX}.")

        scene = SceneModel(
            width=GRID_WIDTH,
            height=GRID_HEIGHT,
            obstacles=self._read_coords(scene_data.get("obstacles", []), "obstacles"),
            start=self._read_optional_coord(scene_data.get("start"), "start"),
            pickup=self._read_optional_coord(scene_data.get("pickup"), "pickup"),
            dropoff=self._read_optional_coord(scene_data.get("dropoff"), "dropoff"),
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
        obstacles = [[x, y] for x, y in sorted(scene.obstacles, key=lambda cell: (cell[1], cell[0]))]
        payload = {
            "version": 1,
            "scene": {
                "name": file_path.stem,
                "grid": {
                    "width": GRID_WIDTH,
                    "height": GRID_HEIGHT,
                    "cell_size_px": CELL_SIZE_PX,
                },
                "start": list(scene.start) if scene.start is not None else None,
                "pickup": list(scene.pickup) if scene.pickup is not None else None,
                "dropoff": list(scene.dropoff) if scene.dropoff is not None else None,
                "obstacles": obstacles,
            },
        }
        file_path.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )

    def _read_coords(self, value: Any, label: str) -> set[Coord]:
        if not isinstance(value, list):
            raise SceneFileError(f"'{label}' must be a list of [x, y] pairs.")
        coords: set[Coord] = set()
        for idx, raw_coord in enumerate(value):
            coords.add(self._read_coord(raw_coord, f"{label}[{idx}]"))
        return coords

    def _read_optional_coord(self, value: Any, label: str) -> Coord | None:
        if value is None:
            return None
        return self._read_coord(value, label)

    def _read_coord(self, value: Any, label: str) -> Coord:
        if (
            not isinstance(value, list)
            or len(value) != 2
            or not all(isinstance(entry, int) for entry in value)
        ):
            raise SceneFileError(f"'{label}' must be a two-item integer list.")
        return (value[0], value[1])
