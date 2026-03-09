"""Shared feasibility checks for task assignment."""

from __future__ import annotations

from factory_gui.algorithms.base import AgentSnapshot, PlannerState, TaskSnapshot


def is_agent_task_feasible(
    agent: AgentSnapshot,
    task: TaskSnapshot,
    state: PlannerState,
) -> bool:
    if agent.phase != "idle":
        return False
    if task.status != "pending":
        return False
    if task.release_time_s > state.t_now_s:
        return False
    if agent.completed_task_count >= agent.max_tasks_total:
        return False
    if not task.required_capabilities.issubset(agent.capabilities):
        return False
    proficiency = _resolve_proficiency(agent, task.type)
    if proficiency < task.required_proficiency:
        return False
    if (agent.id, task.id) in state.conflicts:
        return False
    travel = state.travel_time(agent.id, agent.position, task.location)
    if travel == float("inf"):
        return False
    return True


def assignment_travel_time(
    agent: AgentSnapshot,
    task: TaskSnapshot,
    state: PlannerState,
) -> float:
    return state.travel_time(agent.id, agent.position, task.location)


def assignment_priority_score(
    agent: AgentSnapshot,
    task: TaskSnapshot,
    state: PlannerState,
) -> tuple[float, float, int]:
    """Return a sortable tuple; smaller is better."""
    travel = assignment_travel_time(agent, task, state)
    due = task.due_time_s if task.due_time_s is not None else 1_000_000_000
    # Use inverse proficiency as penalty so better suitability ranks first.
    proficiency_penalty = 1.0 / max(_resolve_proficiency(agent, task.type), 0.001)
    remaining_capacity = max(agent.max_tasks_total - agent.completed_task_count, 0)
    return (travel + 0.15 * proficiency_penalty, due, -remaining_capacity)


def _resolve_proficiency(agent: AgentSnapshot, task_type: str) -> float:
    if task_type in agent.task_proficiency:
        return agent.task_proficiency[task_type]
    # Backward compatibility: old scenes may not define this matrix.
    if not agent.task_proficiency:
        return 1.0
    return 0.0
