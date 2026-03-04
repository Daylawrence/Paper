"""File dialogs."""

from __future__ import annotations

from pathlib import Path
from tkinter import Tk, filedialog

from factory_gui.i18n import Language, tr


def ask_open_path(initial_dir: Path, language: Language) -> Path | None:
    root = Tk()
    root.withdraw()
    root.update()
    path = filedialog.askopenfilename(
        title=tr(language, "dialog_load_title"),
        initialdir=str(initial_dir),
        filetypes=[(tr(language, "dialog_yaml_files"), "*.yaml"), (tr(language, "dialog_yaml_files"), "*.yml")],
    )
    root.destroy()
    return Path(path) if path else None


def ask_save_path(initial_dir: Path, language: Language) -> Path | None:
    root = Tk()
    root.withdraw()
    root.update()
    path = filedialog.asksaveasfilename(
        title=tr(language, "dialog_save_title"),
        initialdir=str(initial_dir),
        defaultextension=".yaml",
        filetypes=[(tr(language, "dialog_yaml_files"), "*.yaml")],
    )
    root.destroy()
    return Path(path) if path else None
