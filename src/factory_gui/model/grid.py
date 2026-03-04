"""Grid utility functions."""

from __future__ import annotations

Coord = tuple[int, int]


def in_bounds(coord: Coord, width: int, height: int) -> bool:
    x, y = coord
    return 0 <= x < width and 0 <= y < height


def neighbors(coord: Coord, width: int, height: int) -> list[Coord]:
    x, y = coord
    candidates = ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1))
    return [cell for cell in candidates if in_bounds(cell, width, height)]


def manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
