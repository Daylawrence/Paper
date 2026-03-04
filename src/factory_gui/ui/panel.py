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
    """Render the right-side button panel and info text."""

    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        self.font = font
        self.small_font = small_font
        self.buttons: list[Button] = []

    def draw(self, surface: pygame.Surface, app_state, controller) -> None:
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
            text_color = constants.TEXT_COLOR if button.enabled else constants.MUTED_TEXT_COLOR
            rendered = self.small_font.render(button.label, True, text_color)
            rendered_rect = rendered.get_rect(center=button.rect.center)
            surface.blit(rendered, rendered_rect)

        language = app_state.language
        info_top = constants.PANEL_TOP + 438
        self._draw_line(
            surface,
            f"{tr(language, 'label_mode')}: {tr(language, f'mode_{app_state.mode}')}",
            info_top,
        )
        self._draw_line(
            surface,
            f"{tr(language, 'label_robot')}: {tr(language, controller.status_key())}",
            info_top + 20,
        )
        carry_text = tr(language, "yes" if controller.robot.has_item else "no")
        self._draw_line(
            surface,
            f"{tr(language, 'label_carrying')}: {carry_text}",
            info_top + 40,
        )

    def action_at(self, pos: tuple[int, int]) -> str | None:
        for button in self.buttons:
            if button.enabled and button.rect.collidepoint(pos):
                return button.action
        return None

    def _build_buttons(self, app_state) -> list[Button]:
        language = app_state.language
        x = constants.PANEL_LEFT + 16
        y = constants.PANEL_TOP + 20
        width = constants.PANEL_WIDTH - 32
        height = 28
        gap = 4
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
        for action, label in (
            ("new", tr(language, "action_new")),
            ("load", tr(language, "action_load")),
            ("save", tr(language, "action_save")),
            ("start", tr(language, "action_start")),
            ("reset", tr(language, "action_reset")),
            ("speed", tr(language, "action_speed", speed=app_state.speed_multiplier)),
            ("language", tr(language, "action_language")),
        ):
            enabled = True
            if app_state.mode == "run" and action in {"new", "load", "save", "start"}:
                enabled = False
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

    def _draw_line(self, surface: pygame.Surface, text: str, top: int) -> None:
        rendered = self.small_font.render(text, True, constants.TEXT_COLOR)
        surface.blit(rendered, (constants.PANEL_LEFT + 16, top))
