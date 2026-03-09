"""Pygame desktop application."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Literal

import pygame

from factory_gui import constants
from factory_gui.algorithms.registry import create_task_planner
from factory_gui.fonts import load_ui_fonts
from factory_gui.i18n import Language, cycle_language, tr
from factory_gui.io.scene_yaml import SceneFileError, SceneYamlStore
from factory_gui.model.scene import SceneModel, SceneValidationError
from factory_gui.planner.registry import create_path_planner
from factory_gui.sim.controller import SimulationController, SimulationError
from factory_gui.ui.canvas import GridCanvas
from factory_gui.ui.dialogs import ask_open_path, ask_save_path
from factory_gui.ui.panel import PanelRenderer
from factory_gui.ui.status_bar import StatusBarRenderer


@dataclass(slots=True)
class AppState:
    mode: Literal["edit", "run"] = "edit"
    selected_tool: str = constants.TOOLS[0]
    selected_task_algorithm: str = constants.TASK_ALGORITHMS[0]
    selected_path_algorithm: str = constants.PATH_ALGORITHMS[0]
    selected_insert_task_type: str = constants.RUNTIME_INSERT_TASK_TYPES[0]
    selected_insert_task_count: int = constants.RUNTIME_INSERT_TASK_COUNT_OPTIONS[0]
    speed_multiplier: int = 1
    language: Language = "zh"
    paused: bool = False
    inserted_once: bool = False
    selected_insert_cells: list[tuple[int, int]] = field(default_factory=list)
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
        self.app_state = AppState()
        self.controller = self._create_controller()
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
            if not self.app_state.paused:
                self.controller.update(dt_ms)
            if self.controller.status_key() == "sim_completed" and self.app_state.error is None:
                output_dir = self.controller.training_output_dir()
                if output_dir:
                    self.app_state.message = tr(
                        self.app_state.language,
                        "message_done_with_export",
                        path=output_dir,
                    )
                else:
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

        cell = self.canvas.cell_from_pos(pos, self.scene)
        if cell is None:
            return

        if self.app_state.mode == "run":
            self._handle_runtime_insert_cell(cell)
            return

        if self.app_state.mode != "edit":
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
        elif action == "task_algorithm":
            self._cycle_task_algorithm()
        elif action == "path_algorithm":
            self._cycle_path_algorithm()
        elif action == "start":
            self._start_simulation()
        elif action == "pause":
            self._toggle_pause()
        elif action == "insert_task_type":
            self._cycle_insert_task_type()
        elif action == "insert_task_count":
            self._cycle_insert_task_count()
        elif action == "insert_task":
            self._insert_tasks_mid_run()
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
        self.app_state.paused = False
        self.app_state.inserted_once = False
        self.app_state.selected_insert_cells.clear()
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
        self.app_state.paused = False
        self.app_state.inserted_once = False
        self.app_state.selected_insert_cells.clear()
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

    def _cycle_task_algorithm(self) -> None:
        current_index = constants.TASK_ALGORITHMS.index(self.app_state.selected_task_algorithm)
        next_index = (current_index + 1) % len(constants.TASK_ALGORITHMS)
        self.app_state.selected_task_algorithm = constants.TASK_ALGORITHMS[next_index]
        self.controller = self._create_controller()
        self.controller.set_speed_multiplier(self.app_state.speed_multiplier)
        self.app_state.error = None
        self.app_state.message = tr(
            self.app_state.language,
            "message_task_algorithm_set",
            algorithm=tr(
                self.app_state.language,
                f"algorithm_{self.app_state.selected_task_algorithm}",
            ),
        )

    def _cycle_path_algorithm(self) -> None:
        current_index = constants.PATH_ALGORITHMS.index(self.app_state.selected_path_algorithm)
        next_index = (current_index + 1) % len(constants.PATH_ALGORITHMS)
        self.app_state.selected_path_algorithm = constants.PATH_ALGORITHMS[next_index]
        self.controller = self._create_controller()
        self.controller.set_speed_multiplier(self.app_state.speed_multiplier)
        self.app_state.error = None
        self.app_state.message = tr(
            self.app_state.language,
            "message_path_algorithm_set",
            algorithm=tr(
                self.app_state.language,
                f"path_{self.app_state.selected_path_algorithm}",
            ),
        )

    def _start_simulation(self) -> None:
        self.controller.set_speed_multiplier(self.app_state.speed_multiplier)
        try:
            self.controller.start(self.scene)
        except SimulationError as exc:
            self.app_state.error = tr(self.app_state.language, exc.message_key)
            return
        self.scene_before_run = self.scene.copy()
        self.app_state.mode = "run"
        self.app_state.paused = False
        self.app_state.inserted_once = False
        self.app_state.selected_insert_cells.clear()
        self.app_state.error = None
        output_dir = self.controller.training_output_dir()
        if output_dir:
            self.app_state.message = tr(
                self.app_state.language,
                "message_started_with_export",
                path=output_dir,
            )
        else:
            self.app_state.message = tr(self.app_state.language, "message_started")

    def _toggle_pause(self) -> None:
        if self.app_state.mode != "run":
            return
        self.app_state.paused = not self.app_state.paused
        if not self.app_state.paused:
            self.app_state.selected_insert_cells.clear()
        self.app_state.error = None
        if self.app_state.paused:
            self.app_state.message = tr(self.app_state.language, "message_paused")
        else:
            self.app_state.message = tr(self.app_state.language, "message_resumed")

    def _insert_tasks_mid_run(self) -> None:
        if self.app_state.mode != "run":
            return
        if not self.app_state.paused:
            self.app_state.error = tr(self.app_state.language, "error_insert_requires_pause")
            return
        if self.app_state.inserted_once:
            self.app_state.error = tr(self.app_state.language, "error_insert_limit")
            return
        required = self.app_state.selected_insert_task_count
        if len(self.app_state.selected_insert_cells) < required:
            self.app_state.error = self._insert_selection_required_text(required)
            return
        target_cells = list(self.app_state.selected_insert_cells[:required])
        try:
            inserted = self.controller.insert_tasks_at_cells(
                task_type=self.app_state.selected_insert_task_type,
                cells=target_cells,
            )
        except SimulationError as exc:
            self.app_state.error = tr(self.app_state.language, exc.message_key)
            return
        self.app_state.inserted_once = True
        self.app_state.selected_insert_cells.clear()
        if self.controller.scene is not None:
            self.scene = self.controller.scene.copy()
        self.app_state.error = None
        self.app_state.message = tr(
            self.app_state.language,
            "message_inserted_tasks",
            count=inserted,
            task=tr(
                self.app_state.language,
                f"tool_task_{self.app_state.selected_insert_task_type}",
            ),
        )

    def _cycle_insert_task_type(self) -> None:
        if self.app_state.mode != "run" or not self.app_state.paused or self.app_state.inserted_once:
            return
        options = constants.RUNTIME_INSERT_TASK_TYPES
        idx = options.index(self.app_state.selected_insert_task_type)
        self.app_state.selected_insert_task_type = options[(idx + 1) % len(options)]
        self.app_state.error = None
        self.app_state.message = tr(
            self.app_state.language,
            "message_insert_task_type_set",
            task=tr(
                self.app_state.language,
                f"tool_task_{self.app_state.selected_insert_task_type}",
            ),
        )

    def _cycle_insert_task_count(self) -> None:
        if self.app_state.mode != "run" or not self.app_state.paused or self.app_state.inserted_once:
            return
        options = constants.RUNTIME_INSERT_TASK_COUNT_OPTIONS
        idx = options.index(self.app_state.selected_insert_task_count)
        self.app_state.selected_insert_task_count = options[(idx + 1) % len(options)]
        selected = self.app_state.selected_insert_cells
        if len(selected) > self.app_state.selected_insert_task_count:
            del selected[self.app_state.selected_insert_task_count :]
        self.app_state.error = None
        self.app_state.message = tr(
            self.app_state.language,
            "message_insert_task_count_set",
            count=self.app_state.selected_insert_task_count,
        )

    def _reset_scene(self) -> None:
        if self.scene_before_run is not None:
            self.scene = self.scene_before_run.copy()
        self.controller.reset()
        self.app_state.mode = "edit"
        self.app_state.paused = False
        self.app_state.inserted_once = False
        self.app_state.selected_insert_cells.clear()
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

    def _handle_runtime_insert_cell(self, cell: tuple[int, int]) -> None:
        if self.app_state.mode != "run" or not self.app_state.paused or self.app_state.inserted_once:
            return
        selected = self.app_state.selected_insert_cells
        if cell in selected:
            selected.remove(cell)
            self.app_state.error = None
            self.app_state.message = self._insert_selection_text(
                selected_count=len(selected),
                required_count=self.app_state.selected_insert_task_count,
                cell=cell,
                removed=True,
            )
            return

        if len(selected) >= self.app_state.selected_insert_task_count:
            self.app_state.error = self._insert_selection_full_text(
                self.app_state.selected_insert_task_count
            )
            return
        if not self.controller.can_insert_task_at(cell):
            self.app_state.error = tr(self.app_state.language, "error_insert_cell_blocked")
            return
        selected.append(cell)
        self.app_state.error = None
        self.app_state.message = self._insert_selection_text(
            selected_count=len(selected),
            required_count=self.app_state.selected_insert_task_count,
            cell=cell,
            removed=False,
        )

    def _insert_selection_text(
        self,
        selected_count: int,
        required_count: int,
        cell: tuple[int, int],
        removed: bool,
    ) -> str:
        if self.app_state.language == "zh":
            if removed:
                return f"已取消插入位置 {cell}，当前 {selected_count}/{required_count}。"
            return f"已选择插入位置 {cell}，当前 {selected_count}/{required_count}。"
        if removed:
            return f"Deselected insert cell {cell}. {selected_count}/{required_count} selected."
        return f"Selected insert cell {cell}. {selected_count}/{required_count} selected."

    def _insert_selection_required_text(self, required_count: int) -> str:
        if self.app_state.language == "zh":
            return f"请先在地图上选择 {required_count} 个可插入格子。"
        return f"Select {required_count} insert cell(s) on the grid first."

    def _insert_selection_full_text(self, required_count: int) -> str:
        if self.app_state.language == "zh":
            return f"已选满 {required_count} 个格子，先取消后再选。"
        return f"You already selected {required_count} cell(s). Deselect one before adding more."

    def _create_controller(self) -> SimulationController:
        planner = create_task_planner(self.app_state.selected_task_algorithm)
        path_planner = create_path_planner(self.app_state.selected_path_algorithm)
        return SimulationController(planner=planner, path_planner=path_planner)
