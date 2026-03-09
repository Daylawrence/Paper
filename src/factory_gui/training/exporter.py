"""Export training history and objective plots."""

from __future__ import annotations

from datetime import datetime
import csv
import json
from pathlib import Path
import sys
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt


class TrainingResultExporter:
    """Persist optimization history for each dispatch and simulation run."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or _resolve_default_result_dir()
        self.run_dir: Path | None = None
        self._dispatch_rows: list[dict[str, float | int]] = []
        self._overall_rows: list[dict[str, float | int]] = []

    def start_run(
        self,
        scene_name: str,
        planner_name: str,
        path_planner_name: str,
        agent_count: int,
        task_count: int,
    ) -> Path:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scene_part = _safe_slug(scene_name) or "scene"
        run_dir = self.base_dir / f"{stamp}_{planner_name}_{path_planner_name}_{scene_part}"
        suffix = 1
        while run_dir.exists():
            run_dir = self.base_dir / (
                f"{stamp}_{planner_name}_{path_planner_name}_{scene_part}_{suffix}"
            )
            suffix += 1

        run_dir.mkdir(parents=True, exist_ok=True)
        self.run_dir = run_dir
        self._dispatch_rows = []
        self._overall_rows = []

        self._write_json(
            run_dir / "run_meta.json",
            {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "scene_name": scene_name,
                "planner_name": planner_name,
                "path_planner_name": path_planner_name,
                "agent_count": agent_count,
                "task_count": task_count,
            },
        )
        return run_dir

    def export_dispatch(
        self,
        dispatch_index: int,
        history: Iterable[dict[str, float | int]],
        best_objective: float,
        assigned_tasks: int,
    ) -> None:
        if self.run_dir is None:
            return

        rows = list(history)
        if not rows:
            return
        dispatch_dir = self.run_dir / "dispatch"
        dispatch_dir.mkdir(parents=True, exist_ok=True)

        csv_path = dispatch_dir / f"dispatch_{dispatch_index:03d}.csv"
        self._write_csv(csv_path, rows)
        png_path = dispatch_dir / f"dispatch_{dispatch_index:03d}.png"
        self._plot_objective_curve(rows, png_path, f"Dispatch {dispatch_index:03d} objective")

        self._dispatch_rows.append(
            {
                "dispatch_index": dispatch_index,
                "best_objective": float(best_objective),
                "assigned_tasks": int(assigned_tasks),
            }
        )
        generation_offset = len(self._overall_rows)
        for local_index, row in enumerate(rows):
            merged = dict(row)
            merged["dispatch_index"] = dispatch_index
            merged["generation_in_dispatch"] = int(row["generation"])
            merged["generation"] = generation_offset + local_index
            self._overall_rows.append(merged)

    def finalize_run(self, summary: dict[str, object]) -> None:
        if self.run_dir is None:
            return

        if self._overall_rows:
            overall_csv = self.run_dir / "overall_objective.csv"
            self._write_csv(overall_csv, self._overall_rows)
            overall_png = self.run_dir / "overall_objective.png"
            self._plot_objective_curve(self._overall_rows, overall_png, "Overall objective trend")

            # Backward-compatible names used by GUI/EXE users.
            summary_csv = self.run_dir / "dispatch_summary.csv"
            self._write_csv(summary_csv, self._overall_rows)
            summary_png = self.run_dir / "dispatch_summary.png"
            self._plot_objective_curve(self._overall_rows, summary_png, "Overall objective trend")

        if self._dispatch_rows:
            overview_csv = self.run_dir / "dispatch_overview.csv"
            self._write_csv(overview_csv, self._dispatch_rows)
            overview_png = self.run_dir / "dispatch_overview.png"
            self._plot_dispatch_overview(self._dispatch_rows, overview_png)

        payload = {
            "finished_at": datetime.now().isoformat(timespec="seconds"),
            "dispatch_count": len(self._dispatch_rows),
            "summary": summary,
        }
        self._write_json(self.run_dir / "simulation_summary.json", payload)

    def _write_csv(self, path: Path, rows: list[dict[str, object]]) -> None:
        if not rows:
            return
        fieldnames = list(rows[0].keys())
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _write_json(self, path: Path, payload: dict[str, object]) -> None:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _plot_objective_curve(
        self,
        rows: list[dict[str, float | int]],
        path: Path,
        title: str,
    ) -> None:
        x = [int(row["generation"]) for row in rows]
        best = [float(row["best_objective"]) for row in rows]
        avg = [float(row["avg_objective"]) for row in rows]

        plt.figure(figsize=(8.0, 4.4))
        plt.plot(x, best, label="Best objective", linewidth=2.0)
        plt.plot(x, avg, label="Average objective", linewidth=1.5, alpha=0.9)
        plt.xlabel("Generation")
        plt.ylabel("Objective (lower is better)")
        plt.title(title)
        plt.grid(alpha=0.25)
        plt.legend()
        plt.tight_layout()
        plt.savefig(path, dpi=140)
        plt.close()

    def _plot_dispatch_overview(self, rows: list[dict[str, float | int]], path: Path) -> None:
        x = [int(row["dispatch_index"]) for row in rows]
        y = [float(row["best_objective"]) for row in rows]
        assigned = [int(row["assigned_tasks"]) for row in rows]

        plt.figure(figsize=(8.0, 4.4))
        plt.plot(x, y, marker="o", linewidth=2.0, label="Best objective per dispatch")
        plt.xlabel("Dispatch index")
        plt.ylabel("Objective")
        plt.title("Dispatch-level objective trend")
        plt.grid(alpha=0.25)
        for idx, y_value, tasks in zip(x, y, assigned):
            plt.text(idx, y_value, f"tasks={tasks}", fontsize=8, ha="center", va="bottom")
        plt.tight_layout()
        plt.savefig(path, dpi=140)
        plt.close()


def _safe_slug(value: str) -> str:
    chars: list[str] = []
    for ch in value:
        if ch.isalnum() or ch in {"-", "_"}:
            chars.append(ch)
        elif ch in {" ", "."}:
            chars.append("_")
    return "".join(chars).strip("_")


def _resolve_default_result_dir() -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if exe_dir.name.lower() == "dist":
            return exe_dir.parent / "result"
        return exe_dir / "result"
    project_root = Path(__file__).resolve().parents[3]
    return project_root / "result"
