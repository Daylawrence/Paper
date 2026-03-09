"""Genetic algorithm task assignment planner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random

from factory_gui.algorithms.base import (
    AgentSnapshot,
    PlannerResult,
    PlannerState,
    TaskSnapshot,
)
from factory_gui.algorithms.feasibility import is_agent_task_feasible
from factory_gui.training.exporter import TrainingResultExporter


@dataclass(slots=True)
class _Evaluation:
    objective: float
    assignments: dict[int, int]
    assigned_tasks: int
    cmax: float
    tardiness: float
    travel: float
    fit_sum: float
    load_variance: float


class GeneticAssignmentPlanner:
    """GA-based assignment heuristic for idle-agent to released-task matching."""

    name = "genetic_assignment"

    def __init__(
        self,
        population_size: int = 48,
        generations: int = 60,
        mutation_rate: float = 0.2,
        elite_count: int = 3,
        seed: int = 7,
        output_dir: Path | None = None,
        w_cmax: float = 1.0,
        w_tardiness: float = 1.0,
        w_travel: float = 0.25,
        w_unassigned: float = 10.0,
        w_balance: float = 0.3,
        w_fit: float = 0.8,
    ) -> None:
        self.population_size = max(10, population_size)
        self.generations = max(4, generations)
        self.mutation_rate = max(0.0, min(1.0, mutation_rate))
        self.elite_count = max(1, min(elite_count, self.population_size))
        self.seed = seed
        self.exporter = TrainingResultExporter(base_dir=output_dir)
        self._dispatch_index = 0
        self._run_started = False

        self.w_cmax = float(w_cmax)
        self.w_tardiness = float(w_tardiness)
        self.w_travel = float(w_travel)
        self.w_unassigned = float(w_unassigned)
        self.w_balance = float(w_balance)
        self.w_fit = float(w_fit)

    @property
    def latest_run_dir(self) -> Path | None:
        return self.exporter.run_dir

    def begin_run(
        self,
        scene_name: str,
        path_planner_name: str,
        agent_count: int,
        task_count: int,
    ) -> None:
        self._dispatch_index = 0
        self.exporter.start_run(
            scene_name=scene_name,
            planner_name=self.name,
            path_planner_name=path_planner_name,
            agent_count=agent_count,
            task_count=task_count,
        )
        self._run_started = True

    def end_run(self, summary: dict[str, object]) -> None:
        if not self._run_started:
            return
        self.exporter.finalize_run(summary)
        self._run_started = False

    def plan(self, state: PlannerState) -> PlannerResult:
        idle_agents = [
            agent
            for agent in state.agents
            if agent.phase == "idle" and agent.completed_task_count < agent.max_tasks_total
        ]
        released_tasks = [
            task
            for task in state.tasks
            if task.status == "pending" and task.release_time_s <= state.t_now_s
        ]
        if not idle_agents or not released_tasks:
            return PlannerResult()

        if not self._run_started:
            self.begin_run(
                scene_name="adhoc",
                path_planner_name="unknown_path",
                agent_count=len(state.agents),
                task_count=len(state.tasks),
            )

        pair_costs = self._build_pair_costs(idle_agents, released_tasks, state)
        feasible_task_indices = [
            task_idx for task_idx in range(len(released_tasks)) if any(
                task_idx in per_agent for per_agent in pair_costs.values()
            )
        ]
        if not feasible_task_indices:
            return PlannerResult()

        self._dispatch_index += 1
        rng = random.Random(
            self.seed + self._dispatch_index * 1009 + int(state.t_now_s * 1000.0)
        )

        population = self._initialize_population(feasible_task_indices, rng)
        history: list[dict[str, float | int]] = []
        global_best: _Evaluation | None = None

        for generation in range(self.generations):
            evaluated = [
                (self._evaluate(chromosome, idle_agents, released_tasks, pair_costs, state), chromosome)
                for chromosome in population
            ]
            evaluated.sort(key=lambda item: item[0].objective)
            best_eval = evaluated[0][0]
            avg_objective = sum(item[0].objective for item in evaluated) / len(evaluated)
            history.append(
                {
                    "generation": generation,
                    "best_objective": best_eval.objective,
                    "avg_objective": avg_objective,
                    "assigned_tasks": best_eval.assigned_tasks,
                    "cmax": best_eval.cmax,
                    "tardiness": best_eval.tardiness,
                    "travel": best_eval.travel,
                    "fit_sum": best_eval.fit_sum,
                    "load_variance": best_eval.load_variance,
                }
            )

            if global_best is None or best_eval.objective < global_best.objective:
                global_best = _Evaluation(
                    objective=best_eval.objective,
                    assignments=dict(best_eval.assignments),
                    assigned_tasks=best_eval.assigned_tasks,
                    cmax=best_eval.cmax,
                    tardiness=best_eval.tardiness,
                    travel=best_eval.travel,
                    fit_sum=best_eval.fit_sum,
                    load_variance=best_eval.load_variance,
                )

            if generation == self.generations - 1:
                continue

            next_population = [chromosome for _, chromosome in evaluated[: self.elite_count]]
            while len(next_population) < self.population_size:
                parent_a = self._tournament(evaluated, rng)
                parent_b = self._tournament(evaluated, rng)
                child = self._order_crossover(parent_a, parent_b, rng)
                if rng.random() < self.mutation_rate:
                    child = self._mutate(child, rng)
                next_population.append(child)
            population = next_population

        if global_best is None:
            return PlannerResult()

        final_assignments = {
            idle_agents[agent_idx].id: released_tasks[task_idx].id
            for agent_idx, task_idx in global_best.assignments.items()
        }
        self.exporter.export_dispatch(
            dispatch_index=self._dispatch_index,
            history=history,
            best_objective=global_best.objective,
            assigned_tasks=len(final_assignments),
        )
        return PlannerResult(assignments=final_assignments)

    def _build_pair_costs(
        self,
        agents: list[AgentSnapshot],
        tasks: list[TaskSnapshot],
        state: PlannerState,
    ) -> dict[int, dict[int, tuple[float, float, float]]]:
        costs: dict[int, dict[int, tuple[float, float, float]]] = {}
        for agent_idx, agent in enumerate(agents):
            per_agent: dict[int, tuple[float, float, float]] = {}
            for task_idx, task in enumerate(tasks):
                if not is_agent_task_feasible(agent, task, state):
                    continue
                to_task = state.travel_time(agent.id, agent.position, task.location)
                to_home = state.travel_time(agent.id, task.location, agent.home)
                if to_task == float("inf") or to_home == float("inf"):
                    continue
                proficiency = max(self._resolve_proficiency(agent, task.type), 0.001)
                per_agent[task_idx] = (to_task, to_home, proficiency)
            if per_agent:
                costs[agent_idx] = per_agent
        return costs

    def _initialize_population(
        self,
        task_indices: list[int],
        rng: random.Random,
    ) -> list[tuple[int, ...]]:
        population: list[tuple[int, ...]] = []
        base = tuple(task_indices)
        population.append(base)
        reversed_base = tuple(reversed(task_indices))
        if reversed_base != base:
            population.append(reversed_base)
        while len(population) < self.population_size:
            shuffled = list(task_indices)
            rng.shuffle(shuffled)
            population.append(tuple(shuffled))
        return population[: self.population_size]

    def _evaluate(
        self,
        chromosome: tuple[int, ...],
        agents: list[AgentSnapshot],
        tasks: list[TaskSnapshot],
        pair_costs: dict[int, dict[int, tuple[float, float, float]]],
        state: PlannerState,
    ) -> _Evaluation:
        available_agents = set(range(len(agents)))
        assignments: dict[int, int] = {}
        finish_times: list[float] = []
        total_tardiness = 0.0
        total_travel = 0.0
        fit_sum = 0.0

        for task_idx in chromosome:
            best_agent: tuple[float, int, float, float, float, float] | None = None
            for agent_idx in available_agents:
                pair = pair_costs.get(agent_idx, {}).get(task_idx)
                if pair is None:
                    continue
                task = tasks[task_idx]
                agent = agents[agent_idx]
                to_task, to_home, proficiency = pair
                effective_service = task.service_time_s / max(proficiency, 0.2)
                finish = state.t_now_s + to_task + effective_service + to_home
                due = task.due_time_s if task.due_time_s is not None else finish
                tardiness = max(0.0, finish - due)
                projected_load = (agent.completed_task_count + 1) / max(agent.max_tasks_total, 1)
                ranking_cost = finish + 1.6 * tardiness + 0.2 * to_task + 0.3 * projected_load - 0.7 * proficiency
                candidate = (
                    ranking_cost,
                    agent_idx,
                    finish,
                    tardiness,
                    to_task,
                    proficiency,
                )
                if best_agent is None or candidate < best_agent:
                    best_agent = candidate

            if best_agent is None:
                continue
            _, agent_idx, finish, tardiness, to_task, proficiency = best_agent
            assignments[agent_idx] = task_idx
            available_agents.remove(agent_idx)
            finish_times.append(finish)
            total_tardiness += tardiness
            total_travel += to_task
            fit_sum += proficiency
            if not available_agents:
                break

        if not assignments:
            return _Evaluation(
                objective=1_000_000.0,
                assignments={},
                assigned_tasks=0,
                cmax=0.0,
                tardiness=0.0,
                travel=0.0,
                fit_sum=0.0,
                load_variance=1.0,
            )

        cmax = max(finish_times)
        assignable_limit = min(len(chromosome), len(agents))
        unassigned = max(0, assignable_limit - len(assignments))
        load_variance = self._load_variance(agents, assignments)
        objective = (
            self.w_cmax * cmax
            + self.w_tardiness * total_tardiness
            + self.w_travel * total_travel
            + self.w_unassigned * unassigned
            + self.w_balance * load_variance
            - self.w_fit * fit_sum
        )
        return _Evaluation(
            objective=objective,
            assignments=assignments,
            assigned_tasks=len(assignments),
            cmax=cmax,
            tardiness=total_tardiness,
            travel=total_travel,
            fit_sum=fit_sum,
            load_variance=load_variance,
        )

    def _load_variance(self, agents: list[AgentSnapshot], assignments: dict[int, int]) -> float:
        loads = []
        for idx, agent in enumerate(agents):
            projected = agent.completed_task_count + (1 if idx in assignments else 0)
            loads.append(projected / max(agent.max_tasks_total, 1))
        if not loads:
            return 0.0
        mean = sum(loads) / len(loads)
        return sum((item - mean) ** 2 for item in loads) / len(loads)

    def _tournament(
        self,
        evaluated: list[tuple[_Evaluation, tuple[int, ...]]],
        rng: random.Random,
    ) -> tuple[int, ...]:
        pool_size = min(4, len(evaluated))
        candidates = rng.sample(evaluated, pool_size)
        winner = min(candidates, key=lambda item: item[0].objective)
        return winner[1]

    def _order_crossover(
        self,
        parent_a: tuple[int, ...],
        parent_b: tuple[int, ...],
        rng: random.Random,
    ) -> tuple[int, ...]:
        size = len(parent_a)
        if size < 2:
            return parent_a
        left, right = sorted(rng.sample(range(size), 2))
        child = [-1] * size
        child[left : right + 1] = parent_a[left : right + 1]
        fill = [gene for gene in parent_b if gene not in child]
        fill_idx = 0
        for idx in range(size):
            if child[idx] != -1:
                continue
            child[idx] = fill[fill_idx]
            fill_idx += 1
        return tuple(child)

    def _mutate(self, chromosome: tuple[int, ...], rng: random.Random) -> tuple[int, ...]:
        if len(chromosome) < 2:
            return chromosome
        i, j = rng.sample(range(len(chromosome)), 2)
        mutated = list(chromosome)
        mutated[i], mutated[j] = mutated[j], mutated[i]
        return tuple(mutated)

    def _resolve_proficiency(self, agent: AgentSnapshot, task_type: str) -> float:
        if task_type in agent.task_proficiency:
            return agent.task_proficiency[task_type]
        if not agent.task_proficiency:
            return 1.0
        return 0.0
