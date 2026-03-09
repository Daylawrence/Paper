"""Earliest due date heuristic placeholder."""

from __future__ import annotations

from factory_gui.algorithms.base import PlannerResult, PlannerState
from factory_gui.algorithms.feasibility import (
    assignment_priority_score,
    is_agent_task_feasible,
)


class EarliestDueDatePlanner:
    name = "earliest_due_date"

    def plan(self, state: PlannerState) -> PlannerResult:
        available_agents = [agent for agent in state.agents if agent.phase == "idle"]
        available_tasks = [
            task
            for task in state.tasks
            if task.status == "pending" and task.release_time_s <= state.t_now_s
        ]
        available_tasks.sort(
            key=lambda task: (task.due_time_s if task.due_time_s is not None else 1_000_000_000, task.id)
        )

        assignments: dict[str, str] = {}
        used_agents: set[str] = set()

        for task in available_tasks:
            best_agent: tuple[tuple[float, float, int], str] | None = None
            for agent in available_agents:
                if agent.id in used_agents:
                    continue
                if not is_agent_task_feasible(agent, task, state):
                    continue
                candidate = (assignment_priority_score(agent, task, state), agent.id)
                if best_agent is None or candidate < best_agent:
                    best_agent = candidate
            if best_agent is None:
                continue
            _, agent_id = best_agent
            assignments[agent_id] = task.id
            used_agents.add(agent_id)

        return PlannerResult(assignments=assignments)
