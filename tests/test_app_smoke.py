import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from factory_gui.app import FactoryGuiApp
from factory_gui.model.agent import AgentSpec
from factory_gui.model.scene import SceneModel
from factory_gui.model.task import TaskSpec


def test_app_smoke_runs_and_completes():
    app = FactoryGuiApp(headless=True)
    try:
        # Switch away from GA for this smoke test to avoid artifact writes.
        app._handle_action("task_algorithm")
        app.scene = SceneModel(
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
        app.canvas.reset_view(app.scene)
        app._handle_action("start")
        assert app.app_state.mode == "run"
        for _ in range(20):
            app.process_frame([], 500)
        assert app.controller.status_key() == "sim_completed"
    finally:
        app.shutdown()


def test_app_can_toggle_language_labels():
    app = FactoryGuiApp(headless=True)
    try:
        app.draw()
        labels = [button.label for button in app.panel.buttons]
        assert "障碍" in labels
        assert "语言 / EN" in labels

        app._handle_action("language")
        app.draw()
        labels = [button.label for button in app.panel.buttons]
        assert app.app_state.language == "en"
        assert "Obstacle" in labels
        assert "Language / 中文" in labels
    finally:
        app.shutdown()


def test_app_random_obstacles_action_updates_scene():
    app = FactoryGuiApp(headless=True)
    try:
        app.scene.clear_obstacles()
        app._handle_action("random_obstacles")
        assert len(app.scene.obstacles) > 0
    finally:
        app.shutdown()


def test_app_can_switch_task_and_path_algorithms():
    app = FactoryGuiApp(headless=True)
    try:
        assert app.app_state.selected_task_algorithm == "genetic_assignment"
        assert app.app_state.selected_path_algorithm == "astar"
        app._handle_action("task_algorithm")
        app._handle_action("path_algorithm")
        assert app.app_state.selected_task_algorithm == "greedy_nearest"
        assert app.app_state.selected_path_algorithm == "greedy_best_first"
    finally:
        app.shutdown()


def test_app_can_pause_once_and_insert_tasks():
    app = FactoryGuiApp(headless=True)
    try:
        app._handle_action("task_algorithm")
        app._handle_action("start")
        assert app.app_state.mode == "run"

        app._handle_action("pause")
        assert app.app_state.paused is True

        target_cell = None
        for y in range(app.scene.height):
            for x in range(app.scene.width):
                cell = (x, y)
                if app.controller.can_insert_task_at(cell):
                    target_cell = cell
                    break
            if target_cell is not None:
                break
        assert target_cell is not None

        click_pos = (
            int(app.canvas.offset_x + target_cell[0] * app.canvas.cell_size_px + 2),
            int(app.canvas.offset_y + target_cell[1] * app.canvas.cell_size_px + 2),
        )
        app._handle_left_click(click_pos)
        assert len(app.app_state.selected_insert_cells) == 1

        app._handle_action("insert_task_type")
        app._handle_action("insert_task")
        assert app.app_state.inserted_once is True
        assert app.app_state.paused is True

        previous_error = app.app_state.error
        app._handle_action("insert_task")
        assert app.app_state.error is not None
        assert app.app_state.error != previous_error
    finally:
        app.shutdown()
