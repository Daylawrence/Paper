"""Capability-first heuristic placeholder."""

from __future__ import annotations

from factory_gui.algorithms.base import PlannerResult, PlannerState


class CapabilityFirstPlanner:
    name = "capability_first"

    def plan(self, state: PlannerState) -> PlannerResult:
        return PlannerResult()
