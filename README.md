# Factory GUI MVP

This project provides a desktop GUI MVP for a single robot in a grid factory scene.
You can place a robot start cell, one pickup point, one dropoff point, and obstacles.
When the run starts, the robot plans with A* and moves cell by cell to pick up the item
and deliver it to the destination.
The GUI includes a `语言 / EN` or `Language / 中文` button so the packaged desktop app can
switch between Chinese and English labels.

## Requirements

- Python 3.12

## Install

```bash
py -3.12 -m pip install -e .[dev]
```

## Run

```bash
py -3.12 -m factory_gui
```

or:

```bash
factory-gui
```

## Tests

```bash
py -3.12 -m pytest
```

## Build EXE

```bash
py -3.12 -m pip install -e .[dev]
py -3.12 -m PyInstaller factory-gui.spec --noconfirm
```

The packaged desktop application will be generated at `dist/factory-gui.exe`.
