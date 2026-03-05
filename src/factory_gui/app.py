"""Pygame desktop application."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Literal

import pygame

from factory_gui import constants
from factory_gui.fonts import load_ui_fonts
from factory_gui.i18n import Language, cycle_language, tr
from factory_gui.io.scene_yaml import SceneFileError, SceneYamlStore
from factory_gui.model.scene import SceneModel, SceneValidationError
from factory_gui.sim.controller import SimulationController, SimulationError
from factory_gui.ui.canvas import GridCanvas
from factory_gui.ui.dialogs import ask_open_path, ask_save_path
from factory_gui.ui.panel import PanelRenderer
from factory_gui.ui.status_bar import StatusBarRenderer


@dataclass(slots=True)
class AppState:
    mode: Literal["edit", "run"] = "edit"
    selected_tool: str = constants.TOOLS[0]
    selected_algorithm: str = constants.ALGORITHMS[0]
    speed_multiplier: int = 1
    language: Language = "zh"
    message: str = tr("zh", "message_setup")
    error: str | None = None


class FactoryGuiApp:
    """Main desktop app."""

    def __init__(self, headless: bool = False) -> None:
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

        self.screen = pygame.display.set_mode((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.headless = headless
        self.dragging = False

        self.font, self.small_font = load_ui_fonts()
        self.canvas = GridCanvas(self.font, self.small_font)
        self.panel = PanelRenderer(self.font, self.small_font)
        self.status_bar = StatusBarRenderer(self.font, self.small_font)
        self.store = SceneYamlStore()
        self.controller = SimulationController()
        self.app_state = AppState()
        self.scene = SceneModel.default_scene()
        self.scene_before_run: SceneModel | None = None
        self.is_running = True
        self.scenarios_dir = self._resolve_scenarios_dir()
        self.scenarios_dir.mkdir(parents=True, exist_ok=True)
        self.canvas.reset_view(self.scene)
        self._refresh_window_caption()

    def run(self, max_frames: int | None = None) -> int:
        frames = 0
        while self.is_running:
            dt_ms = self.clock.tick(constants.FPS)
            self.process_frame(pygame.event.get(), dt_ms)
            frames += 1
            if max_frames is not None and frames >= max_frames:
                break
        return 0

    def process_frame(self, events: list[pygame.event.Event], dt_ms: int) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.is_running = False
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                self.dragging = False
            if event.type == pygame.MOUSEMOTION and self.dragging:
                self.canvas.pan(event.rel[0], event.rel[1])
            if event.type == pygame.MOUSEWHEEL:
                self.canvas.zoom(event.y, pygame.mouse.get_pos())

        if self.app_state.mode == "run":
            self.controller.update(dt_ms)
            if self.controller.status_key() == "sim_completed" and self.app_state.error is None:
                self.app_state.message = tr(self.app_state.language, "phase_done")

        self.draw()

    def draw(self) -> None:
        self.screen.fill(constants.BG_COLOR)
        self.canvas.draw(self.screen, self.scene, self.controller, self.app_state)
        self.panel.draw(self.screen, self.app_state, self.controller, self.scene)
        self.status_bar.draw(self.screen, self.app_state, self.controller)
        pygame.display.flip()

    def shutdown(self) -> None:
        pygame.quit()

    def _handle_mouse_down(self, event: pygame.event.Event) -> None:
        if event.button == 1:
            self._handle_left_click(event.pos)
        elif event.button == 3 and self.canvas.rect.collidepoint(event.pos):
            self.dragging = True

    def _handle_left_click(self, pos: tuple[int, int]) -> None:
        action = self.panel.action_at(pos)
        if action is not None:
            self._handle_action(action)
            return

        if self.app_state.mode != "edit":
            return
        cell = self.canvas.cell_from_pos(pos, self.scene)
        if cell is None:
            return
        try:
            self.scene.set_tool_at(self.app_state.selected_tool, cell)
            self.app_state.error = None
            self.app_state.message = tr(
                self.app_state.language,
                "message_updated_cell",
                tool=tr(self.app_state.language, f"tool_{self.app_state.selected_tool}"),
                cell=cell,
            )
        except SceneValidationError as exc:
            self.app_state.error = str(exc)

    def _handle_action(self, action: str) -> None:
        if action.startswith("tool:"):
            if self.app_state.mode == "edit":
                self.app_state.selected_tool = action.split(":", 1)[1]
                self.app_state.error = None
                self.app_state.message = tr(
                    self.app_state.language,
                    "message_selected_tool",
                    tool=tr(self.app_state.language, f"tool_{self.app_state.selected_tool}"),
                )
            return

        if action == "new":
            self._new_scene()
        elif action == "load":
            self._load_scene()
        elif action == "save":
            self._save_scene()
        elif action == "preset_agents":
            self._preset_agents()
        elif action == "preset_tasks":
            self._preset_tasks()
        elif action == "random_obstacles":
            self._random_obstacles()
        elif action == "clear_obstacles":
            self._clear_obstacles()
        elif action == "algorithm":
            self._cycle_algorithm()
        elif action == "start":
            self._start_simulation()
        elif action == "reset":
            self._reset_scene()
        elif action == "speed":
            self._cycle_speed()
        elif action == "language":
            self._cycle_language()

    def _new_scene(self) -> None:
        self.scene = SceneModel.default_scene()
        self.canvas.reset_view(self.scene)
        self.controller.reset()
        self.scene_before_run = None
        self.app_state.mode = "edit"
        self.app_state.error = None
        self.app_state.message = tr(self.app_state.language, "message_new_scene")

    def _load_scene(self) -> None:
        try:
            path = ask_open_path(self.scenarios_dir, self.app_state.language)
        except Exception as exc:  # pragma: no cover
            self.app_state.error = f"Open dialog failed: {exc}"
            return
        if path is None:
            return
        try:
            self.scene = self.store.load(path)
        except SceneFileError as exc:
            self.app_state.error = str(exc)
            return

        self.controller.reset()
        self.scene_before_run = None
        self.canvas.reset_view(self.scene)
        self.app_state.mode = "edit"
        self.app_state.error = None
        self.app_state.message = tr(self.app_state.language, "message_loaded_scene", name=path.name)

    def _save_scene(self) -> None:
        try:
            path = ask_save_path(self.scenarios_dir, self.app_state.language)
        except Exception as exc:  # pragma: no cover
            self.app_state.error = f"Save dialog failed: {exc}"
            return
        if path is None:
            return
        try:
            self.store.save(path, self.scene)
        except SceneFileError as exc:
            self.app_state.error = str(exc)
            return
        self.app_state.error = None
        self.app_state.message = tr(self.app_state.language, "message_saved_scene", name=path.name)

    def _preset_agents(self) -> None:
        self.scene.add_default_agents()
        self.app_state.error = None
        self.app_state.message = tr(self.app_state.language, "message_preset_agents")

    def _preset_tasks(self) -> None:
        self.scene.add_default_tasks()
        self.app_state.error = None
        self.app_state.message = tr(self.app_state.language, "message_preset_tasks")

    def _random_obstacles(self) -> None:
        success = self.scene.generate_random_obstacles()
        if not success:
            self.app_state.error = tr(self.app_state.language, "error_random_obstacles_failed")
            return
        self.app_state.error = None
        self.app_state.message = tr(self.app_state.language, "message_random_obstacles")

    def _clear_obstacles(self) -> None:
        self.scene.clear_obstacles()
        self.app_state.error = None
        self.app_state.message = tr(self.app_state.language, "message_clear_obstacles")

    def _cycle_algorithm(self) -> None:
        current_index = constants.ALGORITHMS.index(self.app_state.selected_algorithm)
        next_index = (current_index + 1) % len(constants.ALGORITHMS)
        self.app_state.selected_algorithm = constants.ALGORITHMS[next_index]
        self.controller = SimulationController()
        self.controller.set_speed_multiplier(self.app_state.speed_multiplier)
        self.app_state.error = None

    def _start_simulation(self) -> None:
        self.controller.set_speed_multiplier(self.app_state.speed_multiplier)
        try:
            self.controller.start(self.scene)
        except SimulationError as exc:
            self.app_state.error = tr(self.app_state.language, exc.message_key)
            return
        self.scene_before_run = self.scene.copy()
        self.app_state.mode = "run"
        self.app_state.error = None
        self.app_state.message = tr(self.app_state.language, "message_started")

    def _reset_scene(self) -> None:
        if self.scene_before_run is not None:
            self.scene = self.scene_before_run.copy()
        self.controller.reset()
        self.app_state.mode = "edit"
        self.app_state.error = None
        self.app_state.message = tr(self.app_state.language, "message_reset")

    def _cycle_speed(self) -> None:
        current_index = constants.SPEED_MULTIPLIERS.index(self.app_state.speed_multiplier)
        next_index = (current_index + 1) % len(constants.SPEED_MULTIPLIERS)
        self.app_state.speed_multiplier = constants.SPEED_MULTIPLIERS[next_index]
        self.controller.set_speed_multiplier(self.app_state.speed_multiplier)
        self.app_state.error = None
        self.app_state.message = tr(
            self.app_state.language,
            "message_speed_set",
            speed=self.app_state.speed_multiplier,
        )

    def _cycle_language(self) -> None:
        self.app_state.language = cycle_language(self.app_state.language)
        self._refresh_window_caption()
        self.app_state.error = None
        self.app_state.message = tr(self.app_state.language, "message_language_switched")

    def _refresh_window_caption(self) -> None:
        pygame.display.set_caption(tr(self.app_state.language, "window_title"))

    def _resolve_scenarios_dir(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent / "scenarios"
        return Path(__file__).resolve().parents[2] / "scenarios"
