from pathlib import Path

import pytest

from factory_gui.io.scene_yaml import SceneFileError, SceneYamlStore
from factory_gui.model.scene import SceneModel
from factory_gui.planner.astar import AStarPlanner


def test_scene_round_trip(tmp_path: Path):
    store = SceneYamlStore()
    scene = SceneModel.default_scene()
    scene.generate_random_obstacles(seed=7, density=0.08)
    path = tmp_path / "scene.yaml"
    store.save(path, scene)
    loaded = store.load(path)
    assert loaded == scene


def test_load_rejects_old_version(tmp_path: Path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
version: 1
scene: {}
""".strip(),
        encoding="utf-8",
    )
    store = SceneYamlStore()
    with pytest.raises(SceneFileError):
        store.load(path)


def test_random_obstacles_keep_special_cells_reachable():
    scene = SceneModel.default_scene()
    assert scene.generate_random_obstacles(seed=3, density=0.1) is True
    planner = AStarPlanner()
    protected = sorted(scene.special_cells())
    start = protected[0]
    for goal in protected[1:]:
        path = planner.find_path(scene.width, scene.height, scene.obstacles, start, goal)
        assert path
    assert not scene.obstacles.intersection(scene.special_cells())
