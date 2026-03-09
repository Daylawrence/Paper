import pytest

from factory_gui.algorithms.metaheuristics.genetic_assignment import GeneticAssignmentPlanner
from factory_gui.algorithms.registry import create_task_planner
from factory_gui.model.agent import AgentSpec
from factory_gui.model.scene import SceneModel
from factory_gui.model.task import TaskSpec
from factory_gui.planner.registry import create_path_planner
from factory_gui.sim.controller import SimulationController, SimulationError


def build_simple_scene() -> SceneModel:
    return SceneModel(
        width=20,
        height=12,
        agents=[
            AgentSpec(
                id="agv_1",
                type="agv",
                home=(0, 0),
                speed_cells_per_s=2.0,
                capabilities={"transport"},
            )
        ],
        tasks=[
            TaskSpec(
                id="transport_1",
                type="transport",
                location=(2, 0),
                service_time_s=1,
                release_time_s=0,
                due_time_s=20,
                required_capabilities={"transport"},
            )
        ],
    )


def build_team_scene() -> SceneModel:
    return SceneModel(
        width=20,
        height=12,
        agents=[
            AgentSpec(
                id="agv_1",
                type="agv",
                home=(0, 0),
                speed_cells_per_s=2.0,
                capabilities={"transport"},
            ),
            AgentSpec(
                id="agv_2",
                type="agv",
                home=(0, 4),
                speed_cells_per_s=2.0,
                capabilities={"transport"},
            ),
        ],
        tasks=[
            TaskSpec(
                id="transport_1",
                type="transport",
                location=(2, 0),
                service_time_s=1,
                release_time_s=0,
                due_time_s=20,
                required_capabilities={"transport"},
                min_agents=2,
                max_agents=2,
            )
        ],
    )


def test_controller_completes_task_and_returns_home():
    scene = build_simple_scene()
    controller = SimulationController()
    controller.start(scene)

    for _ in range(20):
        controller.update(500)

    agent = controller.agent_states["agv_1"]
    task = controller.task_states["transport_1"]
    assert agent.phase == "idle"
    assert agent.position == agent.spec.home
    assert task.status == "completed"
    assert controller.status_key() == "sim_completed"


def test_controller_waits_for_team_before_service():
    scene = build_team_scene()
    controller = SimulationController(
        planner=create_task_planner("greedy_nearest"),
        path_planner=create_path_planner("astar"),
    )
    controller.start(scene)
    controller.update(1000)
    assert controller.task_states["transport_1"].status == "assigned"
    assert controller.agent_states["agv_1"].phase == "waiting_for_team"
    assert controller.agent_states["agv_2"].phase == "moving_to_task"


def test_controller_completes_team_task_with_all_assigned_agents():
    scene = build_team_scene()
    controller = SimulationController(
        planner=create_task_planner("greedy_nearest"),
        path_planner=create_path_planner("astar"),
    )
    controller.start(scene)
    for _ in range(24):
        controller.update(500)

    task = controller.task_states["transport_1"]
    assert task.status == "completed"
    assert len(task.assigned_agent_ids) == 2
    assert set(task.assigned_agent_ids) == {"agv_1", "agv_2"}
    assert set(task.active_agent_ids) == {"agv_1", "agv_2"}
    assert set(task.finished_agent_ids) == {"agv_1", "agv_2"}
    for agent_id in ("agv_1", "agv_2"):
        agent = controller.agent_states[agent_id]
        assert agent.phase == "idle"
        assert agent.position == agent.spec.home
        assert "transport_1" in agent.completed_task_ids


def test_controller_respects_release_time():
    scene = build_simple_scene()
    scene.tasks[0].release_time_s = 5
    controller = SimulationController()
    controller.start(scene)
    assert controller.task_states["transport_1"].status == "pending"
    controller.update(4000)
    assert controller.task_states["transport_1"].status == "pending"
    controller.update(1500)
    assert controller.task_states["transport_1"].status in {"assigned", "in_service", "completed"}


def test_controller_rejects_unreachable_task():
    scene = build_simple_scene()
    scene.obstacles = {(1, y) for y in range(12)}
    controller = SimulationController()
    with pytest.raises(SimulationError) as exc_info:
        controller.start(scene)
    assert exc_info.value.message_key == "error_unreachable_task"


def test_speed_multiplier_changes_progress():
    scene = build_simple_scene()
    controller = SimulationController()
    controller.set_speed_multiplier(4)
    controller.start(scene)
    controller.update(500)
    assert controller.agent_states["agv_1"].position != (0, 0)


def test_controller_runs_with_alternative_algorithm_combination():
    scene = build_simple_scene()
    controller = SimulationController(
        planner=create_task_planner("earliest_due_date"),
        path_planner=create_path_planner("greedy_best_first"),
    )
    controller.start(scene)
    for _ in range(20):
        controller.update(500)
    assert controller.status_key() == "sim_completed"


def test_controller_can_insert_random_tasks_mid_run():
    scene = SceneModel.default_scene()
    controller = SimulationController(
        planner=create_task_planner("greedy_nearest"),
        path_planner=create_path_planner("astar"),
    )
    controller.start(scene)
    inserted = controller.insert_random_tasks(2, seed=17)
    assert inserted == 2
    assert len(controller.task_states) >= 3


def test_controller_can_insert_specific_task_type_mid_run():
    scene = SceneModel.default_scene()
    controller = SimulationController(
        planner=create_task_planner("greedy_nearest"),
        path_planner=create_path_planner("astar"),
    )
    controller.start(scene)
    inserted = controller.insert_random_tasks(1, seed=19, task_type="heavy")
    assert inserted == 1
    assert any(state.spec.type == "heavy" for state in controller.task_states.values())


def test_controller_rejects_insert_when_not_running():
    controller = SimulationController()
    with pytest.raises(SimulationError) as exc_info:
        controller.insert_random_tasks(1)
    assert exc_info.value.message_key == "error_insert_requires_run"


def test_task_planner_registry_includes_genetic_assignment():
    assert create_task_planner("genetic_assignment").name == "genetic_assignment"


def test_genetic_planner_exports_training_artifacts(tmp_path):
    scene = build_simple_scene()
    planner = GeneticAssignmentPlanner(
        population_size=12,
        generations=8,
        mutation_rate=0.3,
        output_dir=tmp_path,
        seed=3,
    )
    controller = SimulationController(
        planner=planner,
        path_planner=create_path_planner("astar"),
    )
    controller.start(scene)
    for _ in range(20):
        controller.update(500)

    run_dir = planner.latest_run_dir
    assert run_dir is not None
    assert run_dir.exists()
    dispatch_dir = run_dir / "dispatch"
    assert any(dispatch_dir.glob("dispatch_*.csv"))
    assert any(dispatch_dir.glob("dispatch_*.png"))
    assert (run_dir / "dispatch_summary.png").exists()
    assert (run_dir / "simulation_summary.json").exists()
    assert controller.training_output_dir() == str(run_dir)
