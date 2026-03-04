"""A* path planner for four-neighbor grid movement."""

from __future__ import annotations

import heapq
from itertools import count

from factory_gui.model.grid import Coord, in_bounds, manhattan, neighbors


class AStarPlanner:
    """Compute a shortest path with unit traversal costs."""

    def find_path(
        self,
        width: int,
        height: int,
        obstacles: set[Coord],
        start: Coord,
        goal: Coord,
    ) -> list[Coord]:
        if not in_bounds(start, width, height) or not in_bounds(goal, width, height):
            return []
        if start in obstacles or goal in obstacles:
            return []
        if start == goal:
            return [start]

        frontier: list[tuple[int, int, Coord]] = []
        seq = count()
        heapq.heappush(frontier, (manhattan(start, goal), next(seq), start))
        came_from: dict[Coord, Coord | None] = {start: None}
        g_score: dict[Coord, int] = {start: 0}

        while frontier:
            _, _, current = heapq.heappop(frontier)
            if current == goal:
                return self._reconstruct_path(came_from, goal)

            for nxt in neighbors(current, width, height):
                if nxt in obstacles:
                    continue
                tentative = g_score[current] + 1
                if tentative >= g_score.get(nxt, 1_000_000_000):
                    continue
                came_from[nxt] = current
                g_score[nxt] = tentative
                f_score = tentative + manhattan(nxt, goal)
                heapq.heappush(frontier, (f_score, next(seq), nxt))

        return []

    def _reconstruct_path(
        self,
        came_from: dict[Coord, Coord | None],
        goal: Coord,
    ) -> list[Coord]:
        path = [goal]
        current = goal
        while came_from[current] is not None:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path
