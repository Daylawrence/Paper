import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from factory_gui.app import FactoryGuiApp


def test_app_smoke_runs_and_starts():
    app = FactoryGuiApp(headless=True)
    try:
        app.scene.start = (0, 0)
        app.scene.pickup = (1, 0)
        app.scene.dropoff = (2, 0)
        app._handle_action("start")
        assert app.app_state.mode == "run"
        app.process_frame([], 200)
        assert app.controller.current_robot_cell() == (1, 0)
        app.process_frame([], 500)
        assert app.controller.robot.has_item is True
        app.process_frame([], 200)
        app.process_frame([], 500)
        assert app.controller.robot.phase == "done"
    finally:
        app.shutdown()


def test_app_reports_unreachable_scene():
    app = FactoryGuiApp(headless=True)
    try:
        app.scene.start = (0, 1)
        app.scene.pickup = (2, 1)
        app.scene.dropoff = (2, 2)
        app.scene.obstacles = {(1, y) for y in range(12)}
        app._handle_action("start")
        assert app.app_state.mode == "edit"
        assert app.app_state.error is not None
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
