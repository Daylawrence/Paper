import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from factory_gui.app import FactoryGuiApp
from factory_gui.model.agent import AgentSpec
from factory_gui.model.scene import SceneModel
from factory_gui.model.task import TaskSpec


def test_app_smoke_runs_and_completes():
    app = FactoryGuiApp(headless=True)
    try:
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
