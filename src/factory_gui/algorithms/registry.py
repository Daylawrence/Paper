"""Task assignment planner registry."""

from __future__ import annotations

from factory_gui.algorithms.base import TaskPlannerProtocol
from factory_gui.algorithms.dispatch.earliest_due_date import EarliestDueDatePlanner
from factory_gui.algorithms.dispatch.greedy_nearest import GreedyNearestPlanner
from factory_gui.algorithms.metaheuristics.genetic_assignment import GeneticAssignmentPlanner


def create_task_planner(name: str) -> TaskPlannerProtocol:
    if name == "genetic_assignment":
        return GeneticAssignmentPlanner()
    if name == "greedy_nearest":
        return GreedyNearestPlanner()
    if name == "earliest_due_date":
        return EarliestDueDatePlanner()
    raise ValueError(f"Unknown task planner: {name}")
