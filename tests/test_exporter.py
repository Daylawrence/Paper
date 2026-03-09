from pathlib import Path

from factory_gui.training import exporter


def test_exporter_uses_project_result_dir_when_frozen(monkeypatch):
    fake_exe = Path("C:/workspace/project/dist/factory-gui.exe")
    monkeypatch.setattr(exporter.sys, "frozen", True, raising=False)
    monkeypatch.setattr(exporter.sys, "executable", str(fake_exe), raising=False)

    result_dir = exporter._resolve_default_result_dir()

    assert result_dir == Path("C:/workspace/project/result")
