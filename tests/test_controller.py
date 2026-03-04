from factory_gui.model.scene import SceneModel
from factory_gui.sim.controller import SimulationController, SimulationError


def test_controller_completes_delivery():
    scene = SceneModel(
        start=(0, 0),
        pickup=(1, 0),
        dropoff=(2, 0),
    )
    controller = SimulationController()
    controller.start(scene)
    assert controller.robot.phase == "moving_to_pickup"

    controller.update(200)
    assert controller.current_robot_cell() == (1, 0)
    assert controller.robot.phase == "loading"

    controller.update(500)
    assert controller.robot.has_item is True
    assert controller.robot.phase == "moving_to_dropoff"

    controller.update(200)
    assert controller.current_robot_cell() == (2, 0)
    assert controller.robot.phase == "unloading"

    controller.update(500)
    assert controller.robot.phase == "done"
    assert controller.item.delivered is True


def test_controller_reset_clears_runtime_state():
    scene = SceneModel(
        start=(0, 0),
        pickup=(1, 0),
        dropoff=(2, 0),
    )
    controller = SimulationController()
    controller.start(scene)
    controller.reset()
    assert controller.robot.phase == "idle"
    assert controller.current_robot_cell() is None
    assert controller.planned_path == []


def test_controller_rejects_unreachable_goal():
    scene = SceneModel(
        obstacles={(1, y) for y in range(12)},
        start=(0, 1),
        pickup=(2, 1),
        dropoff=(2, 2),
    )
    controller = SimulationController()
    try:
        controller.start(scene)
    except SimulationError as exc:
        assert exc.message_key == "error_unreachable_pickup"
    else:
        raise AssertionError("Expected SimulationError")


def test_speed_multiplier_changes_move_timing():
    scene = SceneModel(
        start=(0, 0),
        pickup=(2, 0),
        dropoff=(3, 0),
    )
    controller = SimulationController()
    controller.set_speed_multiplier(4)
    controller.start(scene)
    controller.update(50)
    assert controller.current_robot_cell() == (1, 0)
