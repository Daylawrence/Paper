from pathlib import Path
import json
import sys

import yaml

from factory_gui.train import main


def test_offline_train_writes_result_artifacts(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "factory_gui.train",
            "--agents",
            "12",
            "--tasks",
            "6",
            "--generations",
            "6",
            "--population",
            "14",
            "--seed",
            "23",
            "--result-dir",
            str(tmp_path),
        ],
    )
    assert main() == 0

    run_dirs = [path for path in tmp_path.iterdir() if path.is_dir()]
    assert run_dirs
    run_dir = sorted(run_dirs)[-1]

    assert (run_dir / "run_meta.json").exists()
    assert (run_dir / "scenario_snapshot.yaml").exists()
    assert (run_dir / "proficiency_matrix.csv").exists()
    assert (run_dir / "conflict_matrix.csv").exists()
    assert (run_dir / "best_assignment.csv").exists()
    assert (run_dir / "dispatch" / "dispatch_001.csv").exists()
    assert (run_dir / "dispatch" / "dispatch_001.png").exists()
    assert (run_dir / "dispatch_summary.png").exists()

    snapshot = yaml.safe_load((run_dir / "scenario_snapshot.yaml").read_text(encoding="utf-8"))
    releases = {int(task["release_time_s"]) for task in snapshot["scene"]["tasks"]}
    assert releases == {0}


def test_offline_train_can_insert_tasks_mid_run(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "factory_gui.train",
            "--agents",
            "24",
            "--tasks",
            "8",
            "--generations",
            "8",
            "--population",
            "18",
            "--seed",
            "29",
            "--insert-tasks",
            "5",
            "--insert-release-offset",
            "25",
            "--result-dir",
            str(tmp_path),
        ],
    )
    assert main() == 0

    run_dirs = [path for path in tmp_path.iterdir() if path.is_dir()]
    assert run_dirs
    run_dir = sorted(run_dirs)[-1]

    snapshot = yaml.safe_load((run_dir / "scenario_snapshot.yaml").read_text(encoding="utf-8"))
    tasks = snapshot["scene"]["tasks"]
    assert len(tasks) == 13
    releases = {int(task["release_time_s"]) for task in tasks}
    assert releases == {0, 25}

    summary_payload = json.loads((run_dir / "simulation_summary.json").read_text(encoding="utf-8"))
    summary = summary_payload["summary"]
    assert int(summary["inserted_tasks"]) == 5
    assert int(summary["base_tasks"]) == 8
