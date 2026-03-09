# Factory Multi-Agent GUI

智能工厂多智能体调度实验项目，包含：
- 桌面 GUI（Pygame）演示
- 可插拔任务分配算法（含遗传算法）
- 可插拔路径算法（A* / Greedy Best-First）
- 离线训练脚本（支持大规模随机场景）

## 当前能力

- 默认 GUI 场景：15 个智能体、5 个任务
- 约束：
  - 能力匹配 `required_capabilities`
  - 智能体总任务上限 `max_tasks_total`
  - 任务适配阈值 `required_proficiency`
  - 智能体-任务冲突 `agent_task_conflicts`
- 训练导出：
  - 代际目标函数曲线（CSV/PNG）
  - 分配结果、能力矩阵、冲突矩阵
  - 统一导出到项目目录 `result/`

## 安装

```bash
py -3.12 -m pip install -e .[dev]
```

或：

```bash
py -3.12 -m pip install -r requirements.txt
```

## 运行 GUI

```bash
py -3.12 -m factory_gui
```

## 离线训练（推荐）

120 智能体 + 30 任务示例：

```bash
py -3.12 -m factory_gui.train --agents 120 --tasks 30 --generations 200 --population 120 --seed 42
```

训练结果目录示例：

```text
result/20260310_xxxxxx_genetic_assignment_astar_train_a120_t30_seed42/
```

其中包含：
- `run_meta.json`
- `scenario_snapshot.yaml`
- `proficiency_matrix.csv`
- `conflict_matrix.csv`
- `dispatch/dispatch_001.csv`
- `dispatch/dispatch_001.png`
- `dispatch_summary.csv`
- `dispatch_summary.png`
- `best_assignment.csv`
- `simulation_summary.json`

## 测试

```bash
py -3.12 -m pytest
```

## 打包 EXE

```bash
py -3.12 -m PyInstaller factory-gui.spec --noconfirm --clean
```

输出：

```text
dist/factory-gui.exe
```
