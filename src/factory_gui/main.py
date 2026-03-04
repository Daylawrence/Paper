"""Application entrypoint."""

from __future__ import annotations

from factory_gui.app import FactoryGuiApp


def main() -> int:
    app = FactoryGuiApp()
    try:
        return app.run()
    finally:
        app.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
