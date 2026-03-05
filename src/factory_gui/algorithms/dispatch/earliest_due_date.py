"""Earliest due date heuristic placeholder."""

from __future__ import annotations

from factory_gui.algorithms.base import PlannerResult, PlannerState


class EarliestDueDatePlanner:
    name = "earliest_due_date"

    def plan(self, state: PlannerState) -> PlannerResult:
        return PlannerResult()
