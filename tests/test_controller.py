import pytest

from factory_gui.model.agent import AgentSpec
from factory_gui.model.scene import SceneModel
from factory_gui.model.task import TaskSpec
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
