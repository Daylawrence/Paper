# MindDrive：在线强化学习驱动的自动驾驶 VLA

- **论文全名**：MindDrive: A Vision-Language-Action Model for Autonomous Driving via Online Reinforcement Learning
- **会议**：ECCV 2026（作者官方仓库公告已接收）；使用 arXiv:2512.13636 原稿，未把预印本冒充会议最终出版 PDF
- **本期日期**：2026-11-18
- **源码固定快照**：[1a4085dab1c20895a0c8d2b67b4f8e65712fa8de](https://github.com/xiaomi-mlab/MindDrive/tree/1a4085dab1c20895a0c8d2b67b4f8e65712fa8de)
- **去重**：已检查 Daylawrence/Paper 的 reading-packs 目录与 catalog，本篇未在先前交付清单中出现

## 1. 原文 PDF

[arXiv 官方论文 PDF](https://arxiv.org/pdf/2512.13636) · [arXiv 论文记录及版本](https://arxiv.org/abs/2512.13636)

官方 PDF 链接已核对，未把 PDF 二进制文件复制到本仓库（当前下载路径未能取得源文件）；请用上述官方链接查看完整原文。

## 2. 推荐理由

**解决的问题**：传统自动驾驶 VLA 大多利用专家演示做模仿学习，容易产生闭环分布偏移。直接在连续轨迹空间使用在线 RL，又存在高维探索困难。

**核心方法**：共享一个 LLM 主干、拆分两个 LoRA：Decision Expert 从多视角视觉与导航信息预测离散语言化驾驶元动作；Action Expert 将速度/路径语义转换成连续轨迹。先以模仿学习建立语言—轨迹映射，再在 CARLA/Bench2Drive 闭环中采样行驶、获取轨迹级奖励，**通过 PPO 优化决策侧**，动作侧继续提供轨迹生成能力。作者在仓库中报告 0.5B 模型 Driving Score 78.04、Success Rate 55.09%；3B 模型 80.59、58.26%。以上均为作者报告的仿真指标，不是实车安全证明。

**为什么值得学**：与之前的 AutoVLA/GRPO 推荐相比，这篇更适合理解真实环境交互产生的 reward、GAE 与 PPO clipping 怎样回传到 VLM 的语言决策侧；也便于对比你关注的 LoRA、SFT/强化学习多阶段训练以及端到端自动驾驶规划。

## 3. 作者官方源码

[官方 GitHub：xiaomi-mlab/MindDrive](https://github.com/xiaomi-mlab/MindDrive) · [固定 commit 1a4085dab1c20895a0c8d2b67b4f8e65712fa8de](https://github.com/xiaomi-mlab/MindDrive/commit/1a4085dab1c20895a0c8d2b67b4f8e65712fa8de)

作者仓库包含推理、训练、CARLA 闭环采集和 PPO 实现。下方链接均固定在上述快照，不使用可能变动的 main 行号。

## 4. 三处关键代码解释

**① 双 LoRA + 离散速度/路径动作。** [`mmcv/models/detectors/minddrive.py` L240–282](https://github.com/xiaomi-mlab/MindDrive/blob/1a4085dab1c20895a0c8d2b67b4f8e65712fa8de/mmcv/models/detectors/minddrive.py#L240-L282) 在一个 `lm_head` 上加载 `action_expert`、`decision_expert` 两套 adapter，注册驾驶元动作 Token，并把速度类型映射到 7 个动作、路径指令映射到 6 个方向类型。[L953–1028](https://github.com/xiaomi-mlab/MindDrive/blob/1a4085dab1c20895a0c8d2b67b4f8e65712fa8de/mmcv/models/detectors/minddrive.py#L953-L1028) 先用 `decision_expert` 预测元动作概率、抽取速度决策；随后切换到 `action_expert`，用条件信息生成供规划器使用的连续轨迹表示。这里**不是**对所有连续转向/加速度值做 RL 搜索。

**② 闭环采集与 GAE。** [`mmcv/runner/iter_based_runner.py` 的 `collect_rollouts_scenario`，L339–404](https://github.com/xiaomi-mlab/MindDrive/blob/1a4085dab1c20895a0c8d2b67b4f8e65712fa8de/mmcv/runner/iter_based_runner.py#L339-L404) 执行 `env.step`，将所选动作、奖励、旧策略对数概率、价值估计及语言条件信息写入 rollout buffer；终止时计算 returns/advantages。[`mmcv/runner/buffers.py` L237–277](https://github.com/xiaomi-mlab/MindDrive/blob/1a4085dab1c20895a0c8d2b67b4f8e65712fa8de/mmcv/runner/buffers.py#L237-L277) 使用逆序 GAE：`delta_t = r_t + gamma*V_{t+1} - V_t`（非终止时），`A_t = delta_t + gamma*lambda*A_{t+1}`。这是**在线环境数据采集 → PPO 样本**的关键连接，而非仅拿离线问答数据算奖励。

**③ PPO 优化 Decision Expert。** [`mmcv/models/detectors/minddrive.py` 的 `forward_ppo_train`，L770–783](https://github.com/xiaomi-mlab/MindDrive/blob/1a4085dab1c20895a0c8d2b67b4f8e65712fa8de/mmcv/models/detectors/minddrive.py#L770-L783) 显式启用 `decision_expert` 并计算该元动作策略的 log-prob 和价值预测。[`mmcv/runner/iter_based_runner.py` 的 `ppo_train`，L433–510](https://github.com/xiaomi-mlab/MindDrive/blob/1a4085dab1c20895a0c8d2b67b4f8e65712fa8de/mmcv/runner/iter_based_runner.py#L433-L510) 从缓存读取动作、旧 log-prob、优势与回报，按 `ratio = exp(new_logp - old_logp)` 计算 clipped surrogate policy loss，同时包含价值 MSE、可选 KL 正则及可选熵项。注意这段是 **PPO clipping**，不要混同于 GRPO 的组内相对优势算法。

**阅读范围**：实际读取作者仓库固定版本的上述函数，完成静态流程核对；未运行 CARLA、训练权重或复现实验。只交付本 Markdown 与官方原文链接，不生成翻译、HTML、ZIP 或历史修复内容。
