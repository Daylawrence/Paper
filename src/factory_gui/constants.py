"""Shared application constants."""

from __future__ import annotations

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 820

DEFAULT_GRID_WIDTH = 60
DEFAULT_GRID_HEIGHT = 36
DEFAULT_CELL_SIZE_PX = 16
MIN_GRID_WIDTH = 20
MAX_GRID_WIDTH = 120
MIN_GRID_HEIGHT = 12
MAX_GRID_HEIGHT = 80

CANVAS_LEFT = 10
CANVAS_TOP = 30
CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 680

PANEL_LEFT = 1030
PANEL_TOP = 30
PANEL_WIDTH = 350
PANEL_HEIGHT = 680

STATUS_LEFT = 10
STATUS_TOP = 730
STATUS_WIDTH = 1370
STATUS_HEIGHT = 70

FPS = 60
SPEED_MULTIPLIERS = (1, 2, 4)
ZOOM_LEVELS = (8, 12, 16, 20, 24, 28)
RUNTIME_INSERT_TASK_TYPES = ("transport", "heavy", "precision")
RUNTIME_INSERT_TASK_COUNT_OPTIONS = (1, 3, 5)

TOOLS = (
    "obstacle",
    "agent_agv",
    "agent_forklift",
    "agent_picker",
    "task_transport",
    "task_heavy",
    "task_precision",
    "erase",
)

TASK_ALGORITHMS = ("genetic_assignment", "greedy_nearest", "earliest_due_date")
PATH_ALGORITHMS = ("astar", "greedy_best_first")

BG_COLOR = (242, 243, 245)
GRID_BG_COLOR = (252, 252, 252)
GRID_LINE_COLOR = (214, 218, 224)
OBSTACLE_COLOR = (72, 76, 84)
TEXT_COLOR = (33, 37, 41)
MUTED_TEXT_COLOR = (92, 99, 110)
ERROR_COLOR = (193, 55, 69)
SUCCESS_COLOR = (30, 132, 73)
PANEL_BG_COLOR = (232, 236, 241)
BUTTON_COLOR = (249, 250, 251)
BUTTON_DISABLED_COLOR = (220, 223, 229)
BUTTON_SELECTED_COLOR = (204, 223, 255)
BUTTON_BORDER_COLOR = (163, 171, 181)
ASSIGNED_TASK_COLOR = (79, 129, 189)
COMPLETED_TASK_COLOR = (77, 160, 96)

AGENT_TYPE_COLORS = {
    "agv": (44, 111, 214),
    "forklift": (188, 87, 36),
    "picker": (101, 120, 43),
}

TASK_TYPE_COLORS = {
    "transport": (242, 138, 33),
    "heavy": (168, 87, 43),
    "precision": (117, 83, 171),
}

PATH_COLORS = {
    "agv": (60, 122, 227, 130),
    "forklift": (205, 118, 57, 130),
    "picker": (115, 152, 73, 130),
}
