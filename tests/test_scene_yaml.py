from pathlib import Path

import pytest

from factory_gui.io.scene_yaml import SceneFileError, SceneYamlStore
from factory_gui.model.scene import SceneModel


def test_scene_round_trip(tmp_path: Path):
    store = SceneYamlStore()
    scene = SceneModel(
        obstacles={(2, 2), (1, 3)},
        start=(1, 1),
        pickup=(3, 3),
        dropoff=(5, 5),
    )
    path = tmp_path / "scene.yaml"
    store.save(path, scene)
    loaded = store.load(path)
    assert loaded == scene


def test_load_rejects_wrong_grid_size(tmp_path: Path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
version: 1
scene:
  name: bad
  grid:
    width: 10
    height: 10
    cell_size_px: 40
  start: [1, 1]
  pickup: [2, 2]
  dropoff: [3, 3]
  obstacles: []
""".strip(),
        encoding="utf-8",
    )
    store = SceneYamlStore()
    with pytest.raises(SceneFileError):
        store.load(path)


def test_load_rejects_duplicate_markers(tmp_path: Path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
version: 1
scene:
  name: bad
  grid:
    width: 20
    height: 12
    cell_size_px: 40
  start: [1, 1]
  pickup: [1, 1]
  dropoff: [3, 3]
  obstacles: []
""".strip(),
        encoding="utf-8",
    )
    store = SceneYamlStore()
    with pytest.raises(SceneFileError):
        store.load(path)
