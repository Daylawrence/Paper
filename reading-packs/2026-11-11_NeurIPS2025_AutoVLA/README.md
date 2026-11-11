# 2026-11-11｜AutoVLA｜NeurIPS 2025

**论文全名**：AutoVLA: A Vision-Language-Action Model for End-to-End Autonomous Driving with Adaptive Reasoning and Reinforcement Fine-Tuning  
**作者**：Zewei Zhou、Tianhui Cai、Seth Zhao、Yun Zhang、Zhiyu Huang、Bolei Zhou、Jiaqi Ma  
**会议**：NeurIPS 2025 Main Conference（官方会议论文）；**arXiv**：2506.13757（与会议版可能有排版/版本差异）。  
**官方论文页面**：https://proceedings.neurips.cc/paper_files/paper/2025/hash/2843fccca5bedd369a4764848b9bd546-Abstract-Conference.html

## 1. 原文 PDF

- **NeurIPS 官方论文 PDF（直接打开）**：[AutoVLA PDF](https://proceedings.neurips.cc/paper_files/paper/2025/file/2843fccca5bedd369a4764848b9bd546-Paper-Conference.pdf)
- 备选：[arXiv 论文页面](https://arxiv.org/abs/2506.13757) / [arXiv PDF](https://arxiv.org/pdf/2506.13757)
- 本期交付原文官方链接，**未在此 GitHub 目录重复上传 PDF**；无需下载 ZIP，也无翻译或 HTML 阅读包。

## 2. 推荐理由

AutoVLA 研究如何让同一个 VLM 同时承担驾驶场景理解与轨迹决策，而不必把语言推理和轨迹规划拆成两个独立的生成模块。它把连续轨迹离散成可自回归预测的 action tokens；用 SFT 学到无需长推理的“快思考”和需要 CoT 的“慢思考”；再用 GRPO 风格强化微调结合规划质量与冗长推理惩罚，推动模型在简单场景更直接地输出轨迹。

**与已有学习方向的具体联系**：如果已经掌握 Qwen2.5-VL、SFT/GRPO 及车辆几何/深度估计，这篇值得重点阅读“从几何轨迹到 token”“推理文本与动作混合监督”“基于驾驶规划 reward 的 GRPO”三个接口。适合从原来的视觉感知任务过渡到 VLA Agent 的可训练端到端规划；论文报告了 nuPlan/nuScenes/Waymo/CARLA 实验，但这里未复现结果。

## 3. 官方代码与版本

- **作者官方 GitHub 仓库**：https://github.com/ucla-mobility/AutoVLA
- **本次静态阅读固定 commit**：[ba34eed74ce6729e7986592d0e66cbaca397b4fa](https://github.com/ucla-mobility/AutoVLA/commit/ba34eed74ce6729e7986592d0e66cbaca397b4fa)
- README 声称训练/标注代码于 2026-02 公开、checkpoint 于 2026-05 公开，**CoT reasoning data 尚未公开**；不应将代码公开等同于全部训练数据可复现。
- 原仓库以 **Qwen2.5-VL-3B-Instruct** 为 VLA 基座，Qwen2.5-VL-72B 系列用于 CoT 标注。

## 4. 关键代码解释（阅读顺序）

### A. 连续轨迹 ↔ 离散 Action Token

源码：[models/action_tokenizer.py：ActionTokenizer 与 rollout](https://github.com/ucla-mobility/AutoVLA/blob/ba34eed74ce6729e7986592d0e66cbaca397b4fa/models/action_tokenizer.py#L31-L121)。

- 初始化从 pickle 中读取每个 token 对应的局部运动模板，实际代码注释给出的 codebook 形状为 `[N_bins, 6, 4, 2]`（末维为二维坐标），并向 VLM tokenizer 添加 `<action_i>`。
- 解码流程：生成的 token ID → 查 codebook → 按自车前一步位置/航向将局部模板转到全局坐标 → 每个 token 汇总出下一时刻 `(x,y,heading)`；返回 `[1, N+1, 3]`（含原点初始状态）。
- 看点：语言模型输出的是**离散动作词表**，而不是直接回归每帧坐标；但误差也会受 codebook 的离散化和滚动累计影响。

### B. SFT 的快/慢思考数据组织

源码：[dataset_utils/sft_dataset.py：构造监督回答](https://github.com/ucla-mobility/AutoVLA/blob/ba34eed74ce6729e7986592d0e66cbaca397b4fa/dataset_utils/sft_dataset.py#L130-L245)。

- 无 CoT 时，助手直接在 `<answer>` 内输出 action token 序列；带 CoT 时，复杂场景的 `<think>` 中包含场景推理，后面仍用相同 `<answer>` 输出动作。
- 输入来自三路相机，每路 4 帧，加车辆速度、加速度和驾驶指令；参见 [数据构造](https://github.com/ucla-mobility/AutoVLA/blob/ba34eed74ce6729e7986592d0e66cbaca397b4fa/dataset_utils/sft_dataset.py#L92-L130) 与 [视频 prompt](https://github.com/ucla-mobility/AutoVLA/blob/ba34eed74ce6729e7986592d0e66cbaca397b4fa/dataset_utils/sft_dataset.py#L252-L334)。
- 看点：**同一模型、同一种动作表示**，但监督答案有短/长两类；因此“是否推理”不需要独立规划模型来完成。

### C. GRPO 风格强化微调与推理长度代价

源码：[models/autovla.py：training_step](https://github.com/ucla-mobility/AutoVLA/blob/ba34eed74ce6729e7986592d0e66cbaca397b4fa/models/autovla.py#L73-L133)、[reward_function](https://github.com/ucla-mobility/AutoVLA/blob/ba34eed74ce6729e7986592d0e66cbaca397b4fa/models/autovla.py#L162-L194)、[get_per_token_logps](https://github.com/ucla-mobility/AutoVLA/blob/ba34eed74ce6729e7986592d0e66cbaca397b4fa/models/autovla.py#L196-L208)。

- 当前策略自回归采样完成序列并解码轨迹，计算 **PDM planning score**；如果出现特定的复杂场景推理标记，会按生成文本长度通过 sigmoid 计算 CoT penalty；两者组合为 reward。
- 代码通过 `all_gather(reward)` 求均值和标准差进行 advantage 标准化，逐 token 取 `log π_θ` 和参考模型 `log π_ref`。loss 使用 `exp(logπ - stopgrad(logπ)) * advantage` 的策略梯度代理项，并加 KL 惩罚，再使用 completion mask 对生成区求平均。
- **实现注意点**：此版本没有典型 PPO/GRPO 的 clip-ratio 分支；advantage 是对 gather 得到的奖励整体标准化，不要误称“严格按每个 prompt 的 G 条响应分组”的标准 GRPO。上述结论来自源码静态阅读，未训练或运行模型。

---

**查验范围**：2026-11-11 查看作者仓库代码、README 与 NeurIPS 官方会议页面；按现有 GitHub 历史论文 catalog 与仓库代码搜索，未检索到这篇的已推荐记录。这里只提供原文 PDF 链接、推荐理由、官方代码及 3 处重点代码解释；不再提供翻译、HTML、ZIP 或旧包修复。
