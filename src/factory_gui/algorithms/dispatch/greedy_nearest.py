"""Nearest-task greedy assignment."""

from __future__ import annotations

from factory_gui.algorithms.base import PlannerResult, PlannerState


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
            best_pair: tuple[float, int, str, str] | None = None
            for task in available_tasks:
                for agent in available_agents:
                    if agent.id in used_agents:
                        continue
                    if not task.required_capabilities.issubset(agent.capabilities):
                        continue
                    travel = state.travel_time(agent.id, agent.position, task.location)
                    if travel == float("inf"):
                        continue
                    due = task.due_time_s if task.due_time_s is not None else 1_000_000_000
                    candidate = (travel, due, agent.id, task.id)
                    if best_pair is None or candidate < best_pair:
                        best_pair = candidate
            if best_pair is None:
                break

            _, _, agent_id, task_id = best_pair
            assignments[agent_id] = task_id
            used_agents.add(agent_id)
            available_tasks = [task for task in available_tasks if task.id != task_id]

        return PlannerResult(assignments=assignments)
