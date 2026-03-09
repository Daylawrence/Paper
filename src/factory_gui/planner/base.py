"""Path planning interfaces."""

from __future__ import annotations

from typing import Protocol

from factory_gui.model.grid import Coord


class PathPlannerProtocol(Protocol):
    name: str

    def find_path(
        self,
        width: int,
        height: int,
        obstacles: set[Coord],
        start: Coord,
        goal: Coord,
    ) -> list[Coord]:
        """Return a path that includes start and goal when reachable."""
