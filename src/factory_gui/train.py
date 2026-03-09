"""Offline training entrypoint for large assignment experiments."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
from pathlib import Path
import random

from factory_gui.algorithms.base import AgentSnapshot, PlannerState, TaskSnapshot
from factory_gui.algorithms.metaheuristics.genetic_assignment import GeneticAssignmentPlanner
from factory_gui.io.scene_yaml import SceneYamlStore
from factory_gui.model.agent import AgentSpec
from factory_gui.model.grid import Coord
from factory_gui.model.scene import AGENT_PRESETS, TASK_PRESETS, SceneModel
from factory_gui.model.task import TaskSpec
from factory_gui.planner.registry import create_path_planner


@dataclass(slots=True)
class TaskSlot:
    slot_id: str
    task_id: str
    task_type: str
    location: Coord
    service_time_s: int
    release_time_s: int
    due_time_s: int | None
    required_capabilities: set[str]
    required_proficiency: float


def main() -> int:
    args = _build_parser().parse_args()
    result_root = Path(args.result_dir).resolve()
    scene = _build_random_scene(
        agents=args.agents,
        tasks=args.tasks,
        width=args.width,
        height=args.height,
        seed=args.seed,
        obstacle_density=args.obstacle_density,
        conflict_density=args.conflict_density,
        team_min=args.team_min,
        team_max=args.team_max,
        release_waves=args.release_waves,
        release_gap=args.release_gap,
    )

    planner = GeneticAssignmentPlanner(
        population_size=args.population,
        generations=args.generations,
        mutation_rate=args.mutation_rate,
        seed=args.seed,
        output_dir=result_root,
    )
    path_planner = create_path_planner(args.path_algorithm)
    travel_time = _build_travel_time(scene, path_planner)

    task_slots = _expand_required_slots(scene)
    slot_by_id = {slot.slot_id: slot for slot in task_slots}
    slot_status = {slot.slot_id: "pending" for slot in task_slots}
    agent_by_id = {agent.id: agent for agent in scene.agents}
    agent_completed_count = {agent.id: 0 for agent in scene.agents}
    slot_conflicts = _expand_slot_conflicts(scene, task_slots)
    assignment_records: list[dict[str, object]] = []
    assigned_agent_task_pairs: set[tuple[str, str]] = set()

    planner.begin_run(
        scene_name=scene.name,
        path_planner_name=path_planner.name,
        agent_count=len(scene.agents),
        task_count=len(task_slots),
    )

    release_points = sorted({slot.release_time_s for slot in task_slots})
    dispatch_round = 0
    for t_now in release_points:
        dispatch_round = _dispatch_until_stable(
            dispatch_round=dispatch_round,
            t_now_s=float(t_now),
            scene=scene,
            planner=planner,
            task_slots=task_slots,
            slot_status=slot_status,
            slot_conflicts=slot_conflicts,
            agent_completed_count=agent_completed_count,
            assignment_records=assignment_records,
            assigned_agent_task_pairs=assigned_agent_task_pairs,
            travel_time=travel_time,
            slot_by_id=slot_by_id,
            agent_by_id=agent_by_id,
        )

    inserted_tasks: list[TaskSpec] = []
    if args.insert_tasks > 0:
        insert_seed = args.insert_seed if args.insert_seed is not None else (args.seed + 100_003)
        insert_release = (release_points[-1] if release_points else 0) + max(1, args.insert_release_offset)
        inserted_tasks = _append_inserted_tasks(
            scene=scene,
            count=args.insert_tasks,
            release_time_s=insert_release,
            team_min=args.team_min,
            team_max=args.team_max,
            conflict_density=args.conflict_density,
            seed=insert_seed,
        )
        inserted_slots = _expand_required_slots_from_tasks(inserted_tasks)
        task_slots.extend(inserted_slots)
        slot_by_id.update({slot.slot_id: slot for slot in inserted_slots})
        slot_status.update({slot.slot_id: "pending" for slot in inserted_slots})
        slot_conflicts = _expand_slot_conflicts(scene, task_slots)
        release_points.append(insert_release)
        release_points = sorted(set(release_points))

        dispatch_round = _dispatch_until_stable(
            dispatch_round=dispatch_round,
            t_now_s=float(insert_release),
            scene=scene,
            planner=planner,
            task_slots=task_slots,
            slot_status=slot_status,
            slot_conflicts=slot_conflicts,
            agent_completed_count=agent_completed_count,
            assignment_records=assignment_records,
            assigned_agent_task_pairs=assigned_agent_task_pairs,
            travel_time=travel_time,
            slot_by_id=slot_by_id,
            agent_by_id=agent_by_id,
        )

    pending_slots = [slot_id for slot_id, status in slot_status.items() if status == "pending"]
    tail_time = float(release_points[-1] + args.release_gap) if release_points else 0.0
    if pending_slots:
        dispatch_round = _dispatch_until_stable(
            dispatch_round=dispatch_round,
            t_now_s=tail_time,
            scene=scene,
            planner=planner,
            task_slots=task_slots,
            slot_status=slot_status,
            slot_conflicts=slot_conflicts,
            agent_completed_count=agent_completed_count,
            assignment_records=assignment_records,
            assigned_agent_task_pairs=assigned_agent_task_pairs,
            travel_time=travel_time,
            slot_by_id=slot_by_id,
            agent_by_id=agent_by_id,
        )

    run_dir = planner.latest_run_dir
    if run_dir is None:
        raise RuntimeError("Training run directory was not created.")

    _export_training_side_artifacts(
        run_dir=run_dir,
        scene=scene,
        assignment_records=assignment_records,
        travel_time=travel_time,
    )

    assigned_slots = len([slot_id for slot_id, status in slot_status.items() if status == "completed"])
    planner.end_run(
        {
            "aborted": False,
            "offline_training": True,
            "path_algorithm": path_planner.name,
            "base_tasks": args.tasks,
            "inserted_tasks": len(inserted_tasks),
            "total_tasks_after_insert": len(scene.tasks),
            "assigned_slots": assigned_slots,
            "total_slots": len(task_slots),
            "unassigned_slots": max(0, len(task_slots) - assigned_slots),
            "distinct_tasks_assigned": len({record["task_id"] for record in assignment_records}),
            "dispatch_rounds": len({record["dispatch_round"] for record in assignment_records}),
            "last_dispatch_round": dispatch_round,
        }
    )

    print(f"Training completed. Results written to: {run_dir}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run offline GA training for large random scenarios.")
    parser.add_argument("--agents", type=int, default=120)
    parser.add_argument("--tasks", type=int, default=30)
    parser.add_argument("--width", type=int, default=120)
    parser.add_argument("--height", type=int, default=80)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--generations", type=int, default=200)
    parser.add_argument("--population", type=int, default=120)
    parser.add_argument("--mutation-rate", type=float, default=0.2)
    parser.add_argument("--obstacle-density", type=float, default=0.08)
    parser.add_argument("--conflict-density", type=float, default=0.15)
    parser.add_argument("--path-algorithm", type=str, default="astar")
    parser.add_argument("--team-min", type=int, default=2)
    parser.add_argument("--team-max", type=int, default=4)
    parser.add_argument("--release-waves", type=int, default=1)
    parser.add_argument("--release-gap", type=int, default=30)
    parser.add_argument("--insert-tasks", type=int, default=0)
    parser.add_argument("--insert-release-offset", type=int, default=30)
    parser.add_argument("--insert-seed", type=int, default=None)
    parser.add_argument(
        "--result-dir",
        type=str,
        default=str(Path(__file__).resolve().parents[2] / "result"),
    )
    return parser


def _build_random_scene(
    agents: int,
    tasks: int,
    width: int,
    height: int,
    seed: int,
    obstacle_density: float,
    conflict_density: float,
    team_min: int,
    team_max: int,
    release_waves: int,
    release_gap: int,
) -> SceneModel:
    rng = random.Random(seed)
    scene = SceneModel(
        name=f"train_a{agents}_t{tasks}_seed{seed}",
        width=max(20, min(120, width)),
        height=max(12, min(80, height)),
        obstacle_seed=seed,
        obstacle_density=obstacle_density,
    )

    agent_types = ("agv", "forklift", "picker")
    task_types = tuple(TASK_PRESETS.keys())
    used_cells: set[Coord] = set()
    counters: dict[str, int] = {name: 0 for name in agent_types}

    for idx in range(agents):
        agent_type = agent_types[idx % len(agent_types)]
        counters[agent_type] += 1
        agent_id = f"{agent_type}_{counters[agent_type]}"
        coord = _sample_free_cell(scene.width, scene.height, used_cells, rng, left_bias=True)
        preset = AGENT_PRESETS[agent_type]
        scene.agents.append(
            AgentSpec(
                id=agent_id,
                type=agent_type,
                home=coord,
                speed_cells_per_s=float(preset["speed"]),
                capabilities=set(preset["capabilities"]),
                max_tasks_total=int(preset["max_tasks_total"]),
                task_proficiency=_sample_proficiency(agent_type, rng),
            )
        )
        used_cells.add(coord)

    task_counters: dict[str, int] = {name: 0 for name in task_types}
    team_min = max(1, team_min)
    team_max = max(team_min, team_max)
    release_waves = max(1, release_waves)
    release_gap = max(1, release_gap)

    for idx in range(tasks):
        task_type = rng.choice(task_types)
        task_counters[task_type] += 1
        task_id = f"{task_type}_{task_counters[task_type]}"
        coord = _sample_free_cell(scene.width, scene.height, used_cells, rng, left_bias=False)
        preset = TASK_PRESETS[task_type]
        release_wave = rng.randrange(release_waves)
        release = release_wave * release_gap
        service = int(preset["service_time_s"])
        due = release + rng.randint(service * 6, service * 14)
        team_size = rng.randint(team_min, team_max)
        scene.tasks.append(
            TaskSpec(
                id=task_id,
                type=task_type,
                location=coord,
                service_time_s=service,
                release_time_s=release,
                due_time_s=due,
                required_capabilities=set(preset["required_capabilities"]),
                required_proficiency=float(preset["required_proficiency"]),
                min_agents=team_size,
                max_agents=team_size,
            )
        )
        used_cells.add(coord)

    scene.generate_random_obstacles(seed=seed, density=obstacle_density)
    scene.generate_random_conflicts(density=conflict_density, seed=seed + 131)
    scene.validate_static()
    return scene


def _append_inserted_tasks(
    scene: SceneModel,
    count: int,
    release_time_s: int,
    team_min: int,
    team_max: int,
    conflict_density: float,
    seed: int,
) -> list[TaskSpec]:
    rng = random.Random(seed)
    team_min = max(1, int(team_min))
    team_max = max(team_min, int(team_max))
    conflict_density = max(0.0, min(0.8, float(conflict_density)))
    if count <= 0:
        return []

    task_types = tuple(TASK_PRESETS.keys())
    used_cells: set[Coord] = set(scene.special_cells()) | set(scene.obstacles)
    counters = _build_task_type_counters(scene.tasks)
    inserted: list[TaskSpec] = []

    for _ in range(count):
        task_type, team_size = _sample_insert_task_profile(
            scene=scene,
            task_types=task_types,
            team_min=team_min,
            team_max=team_max,
            rng=rng,
        )
        counters[task_type] = counters.get(task_type, 0) + 1
        task_id = f"{task_type}_{counters[task_type]}"
        coord = _sample_free_cell(scene.width, scene.height, used_cells, rng, left_bias=False)
        preset = TASK_PRESETS[task_type]
        service = int(preset["service_time_s"])
        due = release_time_s + rng.randint(service * 6, service * 14)

        task = TaskSpec(
            id=task_id,
            type=task_type,
            location=coord,
            service_time_s=service,
            release_time_s=release_time_s,
            due_time_s=due,
            required_capabilities=set(preset["required_capabilities"]),
            required_proficiency=float(preset["required_proficiency"]),
            min_agents=team_size,
            max_agents=team_size,
        )
        scene.tasks.append(task)
        inserted.append(task)
        used_cells.add(coord)

        blocked_agent_ids = _sample_conflicted_agents_for_task(
            scene=scene,
            task=task,
            conflict_density=conflict_density,
            rng=rng,
        )
        for agent_id in blocked_agent_ids:
            scene.agent_task_conflicts.add((agent_id, task.id))

    scene.validate_static()
    return inserted


def _sample_insert_task_profile(
    scene: SceneModel,
    task_types: tuple[str, ...],
    team_min: int,
    team_max: int,
    rng: random.Random,
) -> tuple[str, int]:
    best_type = task_types[0]
    best_capacity = 0
    for _ in range(32):
        task_type = rng.choice(task_types)
        team_size = rng.randint(team_min, team_max)
        capacity = _base_eligible_agents_for_task_type(scene, task_type)
        if capacity > best_capacity:
            best_capacity = capacity
            best_type = task_type
        if capacity >= team_size:
            return task_type, team_size

    if best_capacity <= 0:
        raise RuntimeError("Unable to insert task: no compatible agent for sampled task types.")
    fallback_team = max(1, min(team_max, best_capacity))
    return best_type, fallback_team


def _base_eligible_agents_for_task_type(scene: SceneModel, task_type: str) -> int:
    preset = TASK_PRESETS[task_type]
    required_capabilities = set(preset["required_capabilities"])
    required_proficiency = float(preset["required_proficiency"])
    count = 0
    for agent in scene.agents:
        if not required_capabilities.issubset(agent.capabilities):
            continue
        proficiency = agent.task_proficiency.get(task_type, 1.0 if not agent.task_proficiency else 0.0)
        if proficiency < required_proficiency:
            continue
        count += 1
    return count


def _sample_conflicted_agents_for_task(
    scene: SceneModel,
    task: TaskSpec,
    conflict_density: float,
    rng: random.Random,
) -> set[str]:
    eligible: list[str] = []
    for agent in scene.agents:
        if not task.required_capabilities.issubset(agent.capabilities):
            continue
        proficiency = agent.task_proficiency.get(task.type, 1.0 if not agent.task_proficiency else 0.0)
        if proficiency < task.required_proficiency:
            continue
        eligible.append(agent.id)

    if not eligible:
        return set()
    max_block = max(0, len(eligible) - task.min_agents)
    block_count = min(max_block, int(len(eligible) * conflict_density))
    if block_count <= 0:
        return set()
    return set(rng.sample(eligible, block_count))


def _build_task_type_counters(tasks: list[TaskSpec]) -> dict[str, int]:
    counters: dict[str, int] = {}
    for task in tasks:
        task_type = task.type
        counters.setdefault(task_type, 0)
        prefix = f"{task_type}_"
        if task.id.startswith(prefix):
            suffix = task.id.removeprefix(prefix)
            if suffix.isdigit():
                counters[task_type] = max(counters[task_type], int(suffix))
                continue
        counters[task_type] += 1
    return counters


def _sample_free_cell(
    width: int,
    height: int,
    used_cells: set[Coord],
    rng: random.Random,
    left_bias: bool,
) -> Coord:
    for _ in range(5000):
        if left_bias:
            x = rng.randint(1, max(2, width // 4))
        else:
            x = rng.randint(max(1, width // 3), width - 2)
        y = rng.randint(1, height - 2)
        coord = (x, y)
        if coord not in used_cells:
            return coord
    raise RuntimeError("Unable to sample a free cell for random scene generation.")


def _sample_proficiency(agent_type: str, rng: random.Random) -> dict[str, float]:
    profile_center = AGENT_PRESETS[agent_type]["profile_center"]
    profile: dict[str, float] = {}
    for task_type, center in profile_center.items():
        value = float(center) + rng.uniform(-0.15, 0.15)
        profile[task_type] = round(max(0.1, min(1.5, value)), 3)
    return profile


def _expand_required_slots(scene: SceneModel) -> list[TaskSlot]:
    return _expand_required_slots_from_tasks(scene.tasks)


def _expand_required_slots_from_tasks(tasks: list[TaskSpec]) -> list[TaskSlot]:
    slots: list[TaskSlot] = []
    for task in tasks:
        for idx in range(task.min_agents):
            slot_id = f"{task.id}__slot{idx + 1}"
            slots.append(
                TaskSlot(
                    slot_id=slot_id,
                    task_id=task.id,
                    task_type=task.type,
                    location=task.location,
                    service_time_s=task.service_time_s,
                    release_time_s=task.release_time_s,
                    due_time_s=task.due_time_s,
                    required_capabilities=set(task.required_capabilities),
                    required_proficiency=task.required_proficiency,
                )
            )
    return slots


def _expand_slot_conflicts(scene: SceneModel, task_slots: list[TaskSlot]) -> set[tuple[str, str]]:
    slots_by_task: dict[str, list[str]] = {}
    for slot in task_slots:
        slots_by_task.setdefault(slot.task_id, []).append(slot.slot_id)
    expanded: set[tuple[str, str]] = set()
    for agent_id, task_id in scene.agent_task_conflicts:
        for slot_id in slots_by_task.get(task_id, []):
            expanded.add((agent_id, slot_id))
    return expanded


def _build_travel_time(scene: SceneModel, path_planner):
    cache: dict[tuple[str, Coord, Coord], float] = {}
    speed_lookup = {agent.id: max(agent.speed_cells_per_s, 0.1) for agent in scene.agents}

    def travel_time(agent_id: str, start: Coord, goal: Coord) -> float:
        key = (agent_id, start, goal)
        if key in cache:
            return cache[key]
        path = path_planner.find_path(
            scene.width,
            scene.height,
            scene.obstacles,
            start,
            goal,
        )
        if not path:
            cache[key] = float("inf")
            return cache[key]
        cache[key] = (len(path) - 1) / speed_lookup[agent_id]
        return cache[key]

    return travel_time


def _dispatch_until_stable(
    dispatch_round: int,
    t_now_s: float,
    scene: SceneModel,
    planner: GeneticAssignmentPlanner,
    task_slots: list[TaskSlot],
    slot_status: dict[str, str],
    slot_conflicts: set[tuple[str, str]],
    agent_completed_count: dict[str, int],
    assignment_records: list[dict[str, object]],
    assigned_agent_task_pairs: set[tuple[str, str]],
    travel_time,
    slot_by_id: dict[str, TaskSlot],
    agent_by_id: dict[str, AgentSpec],
) -> int:
    progressed = True
    current_round = dispatch_round
    while progressed:
        active_slots = [
            slot for slot in task_slots if slot_status[slot.slot_id] == "pending" and slot.release_time_s <= t_now_s
        ]
        if not active_slots:
            break
        dynamic_conflicts = set(slot_conflicts)
        for agent_id, task_id in assigned_agent_task_pairs:
            for slot in active_slots:
                if slot.task_id == task_id:
                    dynamic_conflicts.add((agent_id, slot.slot_id))

        state = PlannerState(
            t_now_s=t_now_s,
            agents=[
                AgentSnapshot(
                    id=agent.id,
                    type=agent.type,
                    position=agent.home,
                    home=agent.home,
                    speed_cells_per_s=agent.speed_cells_per_s,
                    capabilities=set(agent.capabilities),
                    max_tasks_total=agent.max_tasks_total,
                    completed_task_count=agent_completed_count[agent.id],
                    task_proficiency=dict(agent.task_proficiency),
                    phase="idle",
                )
                for agent in scene.agents
            ],
            tasks=[
                TaskSnapshot(
                    id=slot.slot_id,
                    type=slot.task_type,
                    location=slot.location,
                    service_time_s=slot.service_time_s,
                    release_time_s=slot.release_time_s,
                    due_time_s=slot.due_time_s,
                    required_capabilities=set(slot.required_capabilities),
                    required_proficiency=slot.required_proficiency,
                    min_agents=1,
                    max_agents=1,
                    status="pending",
                )
                for slot in active_slots
            ],
            conflicts=dynamic_conflicts,
            travel_time=travel_time,
        )

        result = planner.plan(state)
        if not result.assignments:
            break

        changed = 0
        current_round += 1
        for agent_id, slot_id in result.assignments.items():
            if slot_status.get(slot_id) != "pending":
                continue
            agent = agent_by_id[agent_id]
            if agent_completed_count[agent_id] >= agent.max_tasks_total:
                continue
            slot = slot_by_id[slot_id]
            if (agent_id, slot.task_id) in assigned_agent_task_pairs:
                continue
            slot_status[slot_id] = "completed"
            agent_completed_count[agent_id] += 1
            assigned_agent_task_pairs.add((agent_id, slot.task_id))
            assignment_records.append(
                {
                    "dispatch_round": current_round,
                    "dispatch_time_s": t_now_s,
                    "agent_id": agent_id,
                    "task_id": slot.task_id,
                    "slot_id": slot.slot_id,
                    "task_type": slot.task_type,
                    "travel_time_s": round(travel_time(agent_id, agent.home, slot.location), 3),
                    "proficiency": agent.task_proficiency.get(slot.task_type, 0.0),
                    "due_time_s": slot.due_time_s,
                }
            )
            changed += 1
        progressed = changed > 0
    return current_round


def _export_training_side_artifacts(
    run_dir: Path,
    scene: SceneModel,
    assignment_records: list[dict[str, object]],
    travel_time,
) -> None:
    store = SceneYamlStore()
    store.save(run_dir / "scenario_snapshot.yaml", scene)
    _write_proficiency_matrix(run_dir / "proficiency_matrix.csv", scene)
    _write_conflict_matrix(run_dir / "conflict_matrix.csv", scene)
    _write_assignment(run_dir / "best_assignment.csv", assignment_records)
    _write_task_team_summary(run_dir / "task_team_summary.csv", assignment_records, scene)
    _write_assignment_mapping_json(run_dir / "assignment_mapping.json", assignment_records, scene)


def _write_proficiency_matrix(path: Path, scene: SceneModel) -> None:
    task_ids = [task.id for task in scene.tasks]
    task_by_id = {task.id: task for task in scene.tasks}
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["agent_id", *task_ids])
        for agent in scene.agents:
            row = [agent.id]
            for task_id in task_ids:
                task = task_by_id[task_id]
                row.append(agent.task_proficiency.get(task.type, 0.0))
            writer.writerow(row)


def _write_conflict_matrix(path: Path, scene: SceneModel) -> None:
    task_ids = [task.id for task in scene.tasks]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["agent_id", *task_ids])
        for agent in scene.agents:
            row = [agent.id]
            for task_id in task_ids:
                row.append(1 if (agent.id, task_id) in scene.agent_task_conflicts else 0)
            writer.writerow(row)


def _write_assignment(path: Path, assignment_records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "dispatch_round",
                "dispatch_time_s",
                "agent_id",
                "task_id",
                "slot_id",
                "task_type",
                "travel_time_s",
                "proficiency",
                "due_time_s",
            ]
        )
        for record in assignment_records:
            writer.writerow(
                [
                    record["dispatch_round"],
                    record["dispatch_time_s"],
                    record["agent_id"],
                    record["task_id"],
                    record["slot_id"],
                    record["task_type"],
                    record["travel_time_s"],
                    record["proficiency"],
                    record["due_time_s"],
                ]
            )


def _write_task_team_summary(path: Path, assignment_records: list[dict[str, object]], scene: SceneModel) -> None:
    assigned_count: dict[str, int] = {}
    for record in assignment_records:
        task_id = str(record["task_id"])
        assigned_count[task_id] = assigned_count.get(task_id, 0) + 1

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["task_id", "task_type", "required_agents", "assigned_agents", "gap"])
        for task in scene.tasks:
            assigned = assigned_count.get(task.id, 0)
            required = task.min_agents
            writer.writerow(
                [
                    task.id,
                    task.type,
                    required,
                    assigned,
                    max(0, required - assigned),
                ]
            )


def _write_assignment_mapping_json(
    path: Path,
    assignment_records: list[dict[str, object]],
    scene: SceneModel,
) -> None:
    by_agent: dict[str, list[str]] = {agent.id: [] for agent in scene.agents}
    by_task: dict[str, list[str]] = {task.id: [] for task in scene.tasks}
    for record in assignment_records:
        agent_id = str(record["agent_id"])
        slot_id = str(record["slot_id"])
        task_id = str(record["task_id"])
        by_agent.setdefault(agent_id, []).append(slot_id)
        by_task.setdefault(task_id, []).append(agent_id)

    payload = {
        "by_agent_slots": {k: sorted(v) for k, v in by_agent.items() if v},
        "by_task_agents": {k: sorted(v) for k, v in by_task.items() if v},
        "records": assignment_records,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
