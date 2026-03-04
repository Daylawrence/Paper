"""Font helpers with Chinese-capable Windows fallbacks."""

from __future__ import annotations

import os
from pathlib import Path

import pygame


def load_ui_fonts() -> tuple[pygame.font.Font, pygame.font.Font]:
    font_path = _find_font_path()
    if font_path is not None:
        return pygame.font.Font(font_path, 20), pygame.font.Font(font_path, 16)
    return pygame.font.SysFont(None, 20), pygame.font.SysFont(None, 16)


def _find_font_path() -> str | None:
    windows_fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for file_name in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc", "arial.ttf"):
        candidate = windows_fonts / file_name
        if candidate.exists():
            return str(candidate)

    for font_name in (
        "microsoftyaheiui",
        "microsoftyahei",
        "simhei",
        "simsun",
        "arialunicode",
        "notosanscjksc",
        "arial",
    ):
        matched = pygame.font.match_font(font_name)
        if matched:
            return matched
    return None
