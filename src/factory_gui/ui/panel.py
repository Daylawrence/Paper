"""Right-side control panel."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from factory_gui import constants
from factory_gui.i18n import tr


@dataclass(slots=True)
class Button:
    action: str
    label: str
    rect: pygame.Rect
    enabled: bool = True
    selected: bool = False


class PanelRenderer:
    """Render the right-side button panel and summary text."""

    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        self.font = font
        self.small_font = small_font
        self.buttons: list[Button] = []

    def draw(self, surface: pygame.Surface, app_state, controller, scene) -> None:
        panel_rect = pygame.Rect(
            constants.PANEL_LEFT,
            constants.PANEL_TOP,
            constants.PANEL_WIDTH,
            constants.PANEL_HEIGHT,
        )
        pygame.draw.rect(surface, constants.PANEL_BG_COLOR, panel_rect, border_radius=8)
        pygame.draw.rect(surface, constants.BUTTON_BORDER_COLOR, panel_rect, width=1, border_radius=8)

        self.buttons = self._build_buttons(app_state)
        for button in self.buttons:
            fill = constants.BUTTON_COLOR
            if not button.enabled:
                fill = constants.BUTTON_DISABLED_COLOR
            elif button.selected:
                fill = constants.BUTTON_SELECTED_COLOR
            pygame.draw.rect(surface, fill, button.rect, border_radius=6)
            pygame.draw.rect(surface, constants.BUTTON_BORDER_COLOR, button.rect, width=1, border_radius=6)
            color = constants.TEXT_COLOR if button.enabled else constants.MUTED_TEXT_COLOR
            rendered = self.small_font.render(button.label, True, color)
            surface.blit(rendered, rendered.get_rect(center=button.rect.center))

        language = app_state.language
        summary = controller.summary()
        info_top = constants.PANEL_TOP + 598
        lines = [
            f"{tr(language, 'label_mode')}: {tr(language, f'mode_{app_state.mode}')}",
            (
                f"{tr(language, 'label_task_algorithm')}: "
                f"{tr(language, f'algorithm_{app_state.selected_task_algorithm}')}"
            ),
            (
                f"{tr(language, 'label_path_algorithm')}: "
                f"{tr(language, f'path_{app_state.selected_path_algorithm}')}"
            ),
            f"{tr(language, 'label_map')}: {scene.width} x {scene.height}",
            f"{tr(language, 'label_agents')}: {len(scene.agents)}",
            (
                f"{tr(language, 'label_tasks')}: {summary.total_tasks} | "
                f"{tr(language, 'label_completed')}: {summary.completed_tasks}"
            ),
        ]
        for idx, line in enumerate(lines):
            rendered = self.small_font.render(line, True, constants.TEXT_COLOR)
            surface.blit(rendered, (constants.PANEL_LEFT + 16, info_top + idx * 18))

    def action_at(self, pos: tuple[int, int]) -> str | None:
        for button in self.buttons:
            if button.enabled and button.rect.collidepoint(pos):
                return button.action
        return None

    def _build_buttons(self, app_state) -> list[Button]:
        language = app_state.language
        x = constants.PANEL_LEFT + 16
        y = constants.PANEL_TOP + 16
        width = constants.PANEL_WIDTH - 32
        height = 24
        gap = 3
        buttons: list[Button] = []

        for tool in constants.TOOLS:
            buttons.append(
                Button(
                    action=f"tool:{tool}",
                    label=tr(language, f"tool_{tool}"),
                    rect=pygame.Rect(x, y, width, height),
                    enabled=app_state.mode == "edit",
                    selected=app_state.selected_tool == tool,
                )
            )
            y += height + gap

        y += 8
        selected_insert = len(app_state.selected_insert_cells)
        required_insert = app_state.selected_insert_task_count
        for action, label in (
            ("new", tr(language, "action_new")),
            ("load", tr(language, "action_load")),
            ("save", tr(language, "action_save")),
            ("preset_agents", tr(language, "action_preset_agents")),
            ("preset_tasks", tr(language, "action_preset_tasks")),
            ("random_obstacles", tr(language, "action_random_obstacles")),
            ("clear_obstacles", tr(language, "action_clear_obstacles")),
            (
                "task_algorithm",
                tr(
                    language,
                    "action_task_algorithm",
                    algorithm=tr(language, f"algorithm_{app_state.selected_task_algorithm}"),
                ),
            ),
            (
                "path_algorithm",
                tr(
                    language,
                    "action_path_algorithm",
                    algorithm=tr(language, f"path_{app_state.selected_path_algorithm}"),
                ),
            ),
            ("start", tr(language, "action_start")),
            (
                "pause",
                tr(language, "action_resume")
                if app_state.paused
                else tr(language, "action_pause"),
            ),
            (
                "insert_task_type",
                tr(
                    language,
                    "action_insert_task_type",
                    task=tr(language, f"tool_task_{app_state.selected_insert_task_type}"),
                ),
            ),
            (
                "insert_task_count",
                tr(
                    language,
                    "action_insert_task_count",
                    count=app_state.selected_insert_task_count,
                ),
            ),
            (
                "insert_task",
                f"{tr(language, 'action_insert_task')} ({selected_insert}/{required_insert})",
            ),
            ("reset", tr(language, "action_reset")),
            ("speed", tr(language, "action_speed", speed=app_state.speed_multiplier)),
            ("language", tr(language, "action_language")),
        ):
            enabled = True
            if app_state.mode == "run" and action in {
                "new",
                "load",
                "save",
                "preset_agents",
                "preset_tasks",
                "random_obstacles",
                "clear_obstacles",
                "task_algorithm",
                "path_algorithm",
                "start",
            }:
                enabled = False
            if app_state.mode != "run" and action in {"pause", "insert_task_type", "insert_task_count", "insert_task"}:
                enabled = False
            if app_state.mode == "run" and action in {"insert_task_type", "insert_task_count", "insert_task"}:
                enabled = app_state.paused and not app_state.inserted_once
            buttons.append(
                Button(
                    action=action,
                    label=label,
                    rect=pygame.Rect(x, y, width, height),
                    enabled=enabled,
                )
            )
            y += height + gap

        return buttons
