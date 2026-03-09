"""Greedy Best-First Search path planner."""

from __future__ import annotations

import heapq
from itertools import count

from factory_gui.model.grid import Coord, in_bounds, manhattan, neighbors


class GreedyBestFirstPlanner:
    """Fast heuristic path planner (not guaranteed optimal)."""

    name = "greedy_best_first"

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
        visited: set[Coord] = {start}

        while frontier:
            _, _, current = heapq.heappop(frontier)
            if current == goal:
                return self._reconstruct_path(came_from, goal)

            for nxt in neighbors(current, width, height):
                if nxt in obstacles or nxt in visited:
                    continue
                visited.add(nxt)
                came_from[nxt] = current
                heapq.heappush(frontier, (manhattan(nxt, goal), next(seq), nxt))

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
