"""Path planner registry."""

from __future__ import annotations

from factory_gui.planner.astar import AStarPlanner
from factory_gui.planner.base import PathPlannerProtocol
from factory_gui.planner.greedy_best_first import GreedyBestFirstPlanner


def create_path_planner(name: str) -> PathPlannerProtocol:
    if name == "astar":
        return AStarPlanner()
    if name == "greedy_best_first":
        return GreedyBestFirstPlanner()
    raise ValueError(f"Unknown path planner: {name}")
