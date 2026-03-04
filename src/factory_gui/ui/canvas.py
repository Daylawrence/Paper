"""Grid canvas renderer."""

from __future__ import annotations

import pygame

from factory_gui import constants
from factory_gui.i18n import tr
from factory_gui.model.grid import Coord


class GridCanvas:
    """Draw the grid, markers, planned path, and robot state."""

    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        self.font = font
        self.small_font = small_font
        self.rect = pygame.Rect(
            constants.CANVAS_LEFT,
            constants.CANVAS_TOP,
            constants.CANVAS_WIDTH,
            constants.CANVAS_HEIGHT,
        )

    def draw(self, surface: pygame.Surface, scene, controller, app_state) -> None:
        pygame.draw.rect(surface, constants.GRID_BG_COLOR, self.rect)
        pygame.draw.rect(surface, constants.BUTTON_BORDER_COLOR, self.rect, width=1)

        self._draw_paths(surface, controller)
        self._draw_obstacles(surface, scene)
        self._draw_markers(surface, scene)
        self._draw_item(surface, controller)
        self._draw_robot(surface, controller)
        self._draw_grid_lines(surface)

        hint = self.small_font.render(
            tr(app_state.language, "hint_edit_grid"),
            True,
            constants.MUTED_TEXT_COLOR,
        )
        surface.blit(hint, (constants.CANVAS_LEFT, constants.CANVAS_TOP - 18))

    def cell_from_pos(self, pos: tuple[int, int]) -> Coord | None:
        if not self.rect.collidepoint(pos):
            return None
        rel_x = pos[0] - constants.CANVAS_LEFT
        rel_y = pos[1] - constants.CANVAS_TOP
        return rel_x // constants.CELL_SIZE_PX, rel_y // constants.CELL_SIZE_PX

    def _draw_obstacles(self, surface: pygame.Surface, scene) -> None:
        for cell in scene.obstacles:
            pygame.draw.rect(surface, constants.OBSTACLE_COLOR, self._cell_rect(cell))

    def _draw_markers(self, surface: pygame.Surface, scene) -> None:
        markers = (
            (scene.start, constants.START_COLOR, "S"),
            (scene.pickup, constants.PICKUP_COLOR, "P"),
            (scene.dropoff, constants.DROPOFF_COLOR, "D"),
        )
        for coord, color, label in markers:
            if coord is None:
                continue
            rect = self._cell_rect(coord).inflate(-8, -8)
            pygame.draw.rect(surface, color, rect, border_radius=6)
            text = self.font.render(label, True, (255, 255, 255))
            text_rect = text.get_rect(center=rect.center)
            surface.blit(text, text_rect)

    def _draw_item(self, surface: pygame.Surface, controller) -> None:
        if controller.item.delivered and controller.item.dropoff is not None:
            rect = self._cell_rect(controller.item.dropoff).inflate(-18, -18)
            pygame.draw.rect(surface, constants.PICKUP_COLOR, rect, border_radius=4)
            return
        if controller.item.at_pickup and controller.item.pickup is not None:
            rect = self._cell_rect(controller.item.pickup).inflate(-18, -18)
            pygame.draw.rect(surface, constants.PICKUP_COLOR, rect, border_radius=4)
            return
        if controller.item.carried and controller.robot.grid_pos is not None:
            rect = self._cell_rect(controller.robot.grid_pos).inflate(-26, -26)
            pygame.draw.rect(surface, constants.PICKUP_COLOR, rect, border_radius=3)

    def _draw_robot(self, surface: pygame.Surface, controller) -> None:
        if controller.robot.grid_pos is None:
            return
        center = self._cell_rect(controller.robot.grid_pos).center
        pygame.draw.circle(surface, constants.ROBOT_COLOR, center, 12)
        if controller.robot.has_item:
            carried_rect = pygame.Rect(0, 0, 10, 10)
            carried_rect.center = (center[0] + 9, center[1] - 9)
            pygame.draw.rect(surface, constants.PICKUP_COLOR, carried_rect, border_radius=2)

    def _draw_paths(self, surface: pygame.Surface, controller) -> None:
        if controller.planned_path:
            overlay = pygame.Surface((constants.CANVAS_WIDTH, constants.CANVAS_HEIGHT), pygame.SRCALPHA)
            points = [self._cell_center(cell) for cell in controller.planned_path]
            if len(points) > 1:
                pygame.draw.lines(overlay, constants.PATH_COLOR, False, points, width=4)
            surface.blit(overlay, (constants.CANVAS_LEFT, constants.CANVAS_TOP))

        for cell in controller.current_path():
            rect = self._cell_rect(cell).inflate(-12, -12)
            highlight = pygame.Surface(rect.size, pygame.SRCALPHA)
            highlight.fill(constants.ACTIVE_PATH_COLOR)
            surface.blit(highlight, rect.topleft)

    def _draw_grid_lines(self, surface: pygame.Surface) -> None:
        for x in range(constants.GRID_WIDTH + 1):
            start = (constants.CANVAS_LEFT + x * constants.CELL_SIZE_PX, constants.CANVAS_TOP)
            end = (start[0], constants.CANVAS_TOP + constants.CANVAS_HEIGHT)
            pygame.draw.line(surface, constants.GRID_LINE_COLOR, start, end, width=1)
        for y in range(constants.GRID_HEIGHT + 1):
            start = (constants.CANVAS_LEFT, constants.CANVAS_TOP + y * constants.CELL_SIZE_PX)
            end = (constants.CANVAS_LEFT + constants.CANVAS_WIDTH, start[1])
            pygame.draw.line(surface, constants.GRID_LINE_COLOR, start, end, width=1)

    def _cell_rect(self, coord: Coord) -> pygame.Rect:
        x, y = coord
        return pygame.Rect(
            constants.CANVAS_LEFT + x * constants.CELL_SIZE_PX,
            constants.CANVAS_TOP + y * constants.CELL_SIZE_PX,
            constants.CELL_SIZE_PX,
            constants.CELL_SIZE_PX,
        )

    def _cell_center(self, coord: Coord) -> tuple[int, int]:
        rect = self._cell_rect(coord)
        return rect.centerx - constants.CANVAS_LEFT, rect.centery - constants.CANVAS_TOP
