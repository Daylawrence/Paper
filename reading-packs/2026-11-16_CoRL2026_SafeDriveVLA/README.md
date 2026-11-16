# SafeDriveVLA：导航指令冲突感知与世界模型预演

- **论文**：SafeDriveVLA: Navigation-Conditioned World Model Dreaming for Conflict-Aware End-to-End Autonomous Driving
- **会议**：CoRL 2026（论文及作者仓库标注已接收）；arXiv:2610.20609v1，2026-10-14
- **本期日期**：2026-11-16
- **源码阅读快照**：[`f38b4ad43931ceb56c36571724474b4152206ed8`](https://github.com/ASGuard-UCI/safedrive-vla/tree/f38b4ad43931ceb56c36571724474b4152206ed8)

## 1. 原文 PDF

[arXiv 原文 PDF](https://arxiv.org/pdf/2610.20609) ｜ [论文记录](https://arxiv.org/abs/2610.20609)

本期提供 arXiv 官方 PDF 直达链接；未将 PDF 二进制文件复制到本仓库，勿把笔记当作原论文。

## 2. 推荐理由

**问题**：自动驾驶 VLA 接收自然语言导航指令后，必须辨别“应该执行”与“当前场景不安全”。只会跟随指令，或只会模仿专家动作，都不保证能识别指令与道路场景的冲突。

**创新**：先预测三个导航服从模式：`<STRICT>`（执行）、`<CAUTIOUS>`（谨慎执行）、`<FALLBACK>`（覆盖危险指令），再生成动作；同时用冻结的 V-JEPA 2 潜在世界模型，沿**指令对应的动作锚点**预测未来隐空间状态，让 VLA 在做决定前看到“严格遵循指令可能发生什么”。作者还提供 CARLA-F、B2D-C 和 B2D-Adv 等评测。作者报告 B2D-C 成功率 67.3%，对照的 SimLingo-Safe 为 38.0%；这是基准实验结果，不是现实驾驶安全认证。

**学习价值**：比单纯让 VLM 输出轨迹更值得研究的是“导航冲突模式监督 → 世界模型条件预演 → VLA 动作预测”的闭环，可与自动驾驶世界模型、规划器和多模态 Agent 的决策约束对照。

## 3. 作者官方代码

[ASGuard-UCI/safedrive-vla](https://github.com/ASGuard-UCI/safedrive-vla)（作者发布的实现；包含 VLA 训练、世界模型与闭环评测代码）。

固定 commit：[`f38b4ad43931ceb56c36571724474b4152206ed8`](https://github.com/ASGuard-UCI/safedrive-vla/commit/f38b4ad43931ceb56c36571724474b4152206ed8)。下述文件链接都指向此快照，而非浮动的 main。

## 4. 三处关键源码

**① 导航模式标签构造：** [`safedrive_vla/data/driving_mode.py`，L34–104](https://github.com/ASGuard-UCI/safedrive-vla/blob/f38b4ad43931ceb56c36571724474b4152206ed8/safedrive_vla/data/driving_mode.py#L34-L104)

`classify_driving_mode(waypoints, meta_command, current_speed, speed_limit)` 根据专家未来轨迹 `[T,2]`（代码约定 4 Hz、2.5 s）、车速、限速与导航类型产生 `strict/cautious/fallback`。转弯比较轨迹弧长与可行前进距离，变道判断是否及何时越过横向阈值，直行则参考加速度与侧向偏移。这是**规则衍生的监督标签**，不是语言模型自由生成的安全判断。

**② 导航条件世界模型预演：** [`safedrive_vla/models/dreaming.py`，L22–136](https://github.com/ASGuard-UCI/safedrive-vla/blob/f38b4ad43931ceb56c36571724474b4152206ed8/safedrive_vla/models/dreaming.py#L22-L136)

`WorldModelDreamer.forward(tubelet, actions, state)` 接收连续两帧 `[B,2,3,H,W]`、动作序列 `[B,K,3]`（车体坐标 `dx,dy,dyaw`）和自车状态 `[B,4]`，用冻结的编码器/预测器自回归产生 `[B,K,HW,D_enc]` 未来隐状态；`WorldStateProjector` 通过 1×1 卷积、空间平均与线性层，将每步隐状态压成一个 `D_LM` 维世界 Token。默认 `K=5`，每步 0.5 秒；它**不直接生成未来 RGB 图像**。

**③ 与 VLA 对接和多项监督：** [`safedrive_vla/models/safedrive_vla.py`，L198–292](https://github.com/ASGuard-UCI/safedrive-vla/blob/f38b4ad43931ceb56c36571724474b4152206ed8/safedrive_vla/models/safedrive_vla.py#L198-L292)

`set_conditioning` 调用 Dreamer 和 Projector 准备 `[B,K,D_LM]` 世界 Token；`_override_embeddings` 用前向 Hook 替换输入中的 `<WM_LATENT>` 嵌入。随后 `compute_losses` 对动作 Token、模式 Token、普通文本分别计算交叉熵，并对 `<ACTIONS>` 位置预测的 `[N,P,2]` 路径计算 MSE，再加权求和。因此，**模式决策和动作预测虽分工明确，仍通过联合损失学习**。

**范围与限制**：以上根据固定 commit 静态阅读源码，未训练模型、复现实验，也未验证真实道路部署。PDF 为官方外链，本期仓库仅保存此 Markdown 笔记。
