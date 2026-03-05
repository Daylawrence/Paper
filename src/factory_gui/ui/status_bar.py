"""Bottom status bar renderer."""

from __future__ import annotations

import pygame

from factory_gui import constants
from factory_gui.i18n import tr


class StatusBarRenderer:
    """Render the application status bar."""

    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        self.font = font
        self.small_font = small_font

    def draw(self, surface: pygame.Surface, app_state, controller) -> None:
        rect = pygame.Rect(
            constants.STATUS_LEFT,
            constants.STATUS_TOP,
            constants.STATUS_WIDTH,
            constants.STATUS_HEIGHT,
        )
        pygame.draw.rect(surface, constants.PANEL_BG_COLOR, rect, border_radius=8)
        pygame.draw.rect(surface, constants.BUTTON_BORDER_COLOR, rect, width=1, border_radius=8)

        message = app_state.error or app_state.message or tr(app_state.language, "status_ready")
        color = constants.ERROR_COLOR if app_state.error else constants.TEXT_COLOR
        if controller.status_key() == "sim_completed" and not app_state.error:
            color = constants.SUCCESS_COLOR

        summary = controller.summary()
        line1 = self.font.render(message, True, color)
        line2 = self.small_font.render(
            (
                f"{tr(app_state.language, 'label_phase')}: {tr(app_state.language, controller.status_key())} | "
                f"{tr(app_state.language, 'label_time')}: {summary.time_s:.1f}s | "
                f"{tr(app_state.language, 'label_completed')}: {summary.completed_tasks}/{summary.total_tasks} | "
                f"{tr(app_state.language, 'label_speed')}: {app_state.speed_multiplier}x"
            ),
            True,
            constants.MUTED_TEXT_COLOR,
        )
        surface.blit(line1, (rect.x + 16, rect.y + 10))
        surface.blit(line2, (rect.x + 16, rect.y + 40))
