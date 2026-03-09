"""Grid canvas renderer with zoom and pan support."""

from __future__ import annotations

import pygame

from factory_gui import constants
from factory_gui.i18n import tr
from factory_gui.model.grid import Coord


class GridCanvas:
    """Draw the grid, obstacles, tasks, agents, and paths."""

    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        self.font = font
        self.small_font = small_font
        self.rect = pygame.Rect(
            constants.CANVAS_LEFT,
            constants.CANVAS_TOP,
            constants.CANVAS_WIDTH,
            constants.CANVAS_HEIGHT,
        )
        self.cell_size_px = constants.DEFAULT_CELL_SIZE_PX
        self.offset_x = 0.0
        self.offset_y = 0.0

    def reset_view(self, scene) -> None:
        fit = min(
            self.rect.width / max(1, scene.width),
            self.rect.height / max(1, scene.height),
        )
        level = constants.ZOOM_LEVELS[0]
        for candidate in constants.ZOOM_LEVELS:
            if candidate <= fit:
                level = candidate
        self.cell_size_px = level
        total_width = scene.width * self.cell_size_px
        total_height = scene.height * self.cell_size_px
        self.offset_x = self.rect.x + (self.rect.width - total_width) / 2
        self.offset_y = self.rect.y + (self.rect.height - total_height) / 2

    def draw(self, surface: pygame.Surface, scene, controller, app_state) -> None:
        pygame.draw.rect(surface, constants.GRID_BG_COLOR, self.rect)
        pygame.draw.rect(surface, constants.BUTTON_BORDER_COLOR, self.rect, width=1)

        self._draw_grid(surface, scene)
        self._draw_obstacles(surface, scene)
        self._draw_tasks(surface, scene, controller)
        self._draw_insert_selection(surface, app_state)
        self._draw_homes(surface, scene)
        self._draw_paths(surface, controller)
        self._draw_agents(surface, scene, controller)

        hint = self.small_font.render(
            tr(app_state.language, "hint_edit_grid"),
            True,
            constants.MUTED_TEXT_COLOR,
        )
        surface.blit(hint, (self.rect.x, self.rect.y - 18))

    def _draw_insert_selection(self, surface: pygame.Surface, app_state) -> None:
        if app_state.mode != "run" or not app_state.paused or app_state.inserted_once:
            return
        for idx, cell in enumerate(app_state.selected_insert_cells, start=1):
            rect = self._cell_rect(cell).inflate(-4, -4)
            if not self.rect.colliderect(rect):
                continue
            pygame.draw.rect(surface, (255, 198, 73), rect, width=3, border_radius=4)
            text = self.small_font.render(str(idx), True, (88, 56, 0))
            surface.blit(text, text.get_rect(center=rect.center))

    def cell_from_pos(self, pos: tuple[int, int], scene) -> Coord | None:
        if not self.rect.collidepoint(pos):
            return None
        x = int((pos[0] - self.offset_x) // self.cell_size_px)
        y = int((pos[1] - self.offset_y) // self.cell_size_px)
        if 0 <= x < scene.width and 0 <= y < scene.height:
            return (x, y)
        return None

    def pan(self, dx: float, dy: float) -> None:
        self.offset_x += dx
        self.offset_y += dy

    def zoom(self, delta: int, focus_pos: tuple[int, int]) -> None:
        current_index = constants.ZOOM_LEVELS.index(self.cell_size_px)
        target_index = max(0, min(len(constants.ZOOM_LEVELS) - 1, current_index + delta))
        new_size = constants.ZOOM_LEVELS[target_index]
        if new_size == self.cell_size_px:
            return

        focus_grid_x = (focus_pos[0] - self.offset_x) / self.cell_size_px
        focus_grid_y = (focus_pos[1] - self.offset_y) / self.cell_size_px
        self.cell_size_px = new_size
        self.offset_x = focus_pos[0] - focus_grid_x * self.cell_size_px
        self.offset_y = focus_pos[1] - focus_grid_y * self.cell_size_px

    def _draw_grid(self, surface: pygame.Surface, scene) -> None:
        for x in range(scene.width + 1):
            start = (int(self.offset_x + x * self.cell_size_px), self.rect.y)
            end = (start[0], self.rect.bottom)
            pygame.draw.line(surface, constants.GRID_LINE_COLOR, start, end, width=1)
        for y in range(scene.height + 1):
            start = (self.rect.x, int(self.offset_y + y * self.cell_size_px))
            end = (self.rect.right, start[1])
            pygame.draw.line(surface, constants.GRID_LINE_COLOR, start, end, width=1)

    def _draw_obstacles(self, surface: pygame.Surface, scene) -> None:
        for cell in scene.obstacles:
            rect = self._cell_rect(cell)
            if self.rect.colliderect(rect):
                pygame.draw.rect(surface, constants.OBSTACLE_COLOR, rect)

    def _draw_homes(self, surface: pygame.Surface, scene) -> None:
        for agent in scene.agents:
            rect = self._cell_rect(agent.home).inflate(-4, -4)
            color = constants.AGENT_TYPE_COLORS.get(agent.type, constants.TEXT_COLOR)
            pygame.draw.rect(surface, color, rect, width=2, border_radius=4)

    def _draw_agents(self, surface: pygame.Surface, scene, controller) -> None:
        runtime_positions = {
            agent_id: state.position for agent_id, state in controller.agent_states.items()
        }
        for agent in scene.agents:
            coord = runtime_positions.get(agent.id, agent.home)
            rect = self._cell_rect(coord)
            if not self.rect.colliderect(rect):
                continue
            center = rect.center
            color = constants.AGENT_TYPE_COLORS.get(agent.type, constants.TEXT_COLOR)
            pygame.draw.circle(surface, color, center, max(6, int(self.cell_size_px * 0.35)))
            label = agent.id.split("_")[-1]
            text = self.small_font.render(label, True, (255, 255, 255))
            surface.blit(text, text.get_rect(center=center))

    def _draw_tasks(self, surface: pygame.Surface, scene, controller) -> None:
        status_lookup = controller.task_states if controller.task_states else {}
        for task in scene.tasks:
            margin = max(2, int(self.cell_size_px * 0.22))
            rect = self._cell_rect(task.location).inflate(-2 * margin, -2 * margin)
            if not self.rect.colliderect(rect):
                continue
            runtime = status_lookup.get(task.id)
            if runtime is None:
                color = constants.TASK_TYPE_COLORS.get(task.type, constants.TEXT_COLOR)
            elif runtime.status == "completed":
                color = constants.COMPLETED_TASK_COLOR
            elif runtime.status in {"assigned", "in_service"}:
                color = constants.ASSIGNED_TASK_COLOR
            else:
                color = constants.TASK_TYPE_COLORS.get(task.type, constants.TEXT_COLOR)
            pygame.draw.rect(surface, color, rect, border_radius=4)
            if rect.width >= 14 and rect.height >= 14:
                task_label = task.id.split("_")[-1]
                label_text = self.small_font.render(task_label, True, (255, 255, 255))
                label_pos = label_text.get_rect(center=(rect.centerx, rect.centery - 4))
                surface.blit(label_text, label_pos)

                demand_text = self.small_font.render(
                    f"{task.min_agents}/{task.max_agents}",
                    True,
                    (255, 255, 255),
                )
                badge_padding_x = 4
                badge_height = demand_text.get_height() + 2
                badge_width = demand_text.get_width() + badge_padding_x * 2
                badge = pygame.Rect(0, 0, badge_width, badge_height)
                badge.centerx = rect.centerx
                badge.bottom = rect.bottom - 1
                pygame.draw.rect(surface, (44, 48, 54), badge, border_radius=3)
                surface.blit(demand_text, demand_text.get_rect(center=badge.center))

    def _draw_paths(self, surface: pygame.Surface, controller) -> None:
        for agent_id, path in controller.current_paths().items():
            agent_state = controller.agent_states[agent_id]
            overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            points = [self._cell_center_relative(cell) for cell in path]
            if len(points) > 1:
                color = constants.PATH_COLORS.get(agent_state.spec.type, (0, 0, 0, 128))
                pygame.draw.lines(overlay, color, False, points, width=3)
            surface.blit(overlay, self.rect.topleft)

    def _cell_rect(self, coord: Coord) -> pygame.Rect:
        x, y = coord
        return pygame.Rect(
            int(self.offset_x + x * self.cell_size_px),
            int(self.offset_y + y * self.cell_size_px),
            int(self.cell_size_px),
            int(self.cell_size_px),
        )

    def _cell_center_relative(self, coord: Coord) -> tuple[int, int]:
        rect = self._cell_rect(coord)
        return (rect.centerx - self.rect.x, rect.centery - self.rect.y)
