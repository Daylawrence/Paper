"""Nearest-task greedy assignment."""

from __future__ import annotations

from factory_gui.algorithms.base import PlannerResult, PlannerState
from factory_gui.algorithms.feasibility import (
    assignment_priority_score,
    is_agent_task_feasible,
)


class GreedyNearestPlanner:
    name = "greedy_nearest"

    def plan(self, state: PlannerState) -> PlannerResult:
        available_agents = [agent for agent in state.agents if agent.phase == "idle"]
        available_tasks = [
            task
            for task in state.tasks
            if task.status == "pending" and task.release_time_s <= state.t_now_s
        ]

        assignments: dict[str, str] = {}
        used_agents: set[str] = set()

        while available_tasks:
            best_pair: tuple[tuple[float, float, int], str, str] | None = None
            for task in available_tasks:
                for agent in available_agents:
                    if agent.id in used_agents:
                        continue
                    if not is_agent_task_feasible(agent, task, state):
                        continue
                    candidate = (assignment_priority_score(agent, task, state), agent.id, task.id)
                    if best_pair is None or candidate < best_pair:
                        best_pair = candidate
            if best_pair is None:
                break

            _, agent_id, task_id = best_pair
            assignments[agent_id] = task_id
            used_agents.add(agent_id)
            available_tasks = [task for task in available_tasks if task.id != task_id]

        return PlannerResult(assignments=assignments)
