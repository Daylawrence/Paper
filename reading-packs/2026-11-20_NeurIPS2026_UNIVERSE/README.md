# UNIVERSE — NeurIPS 2026（2026-11-20 推荐）

**论文全名**：UNIVERSE: Unified Video Action Models for Autonomous Driving with Flexible Mask-Modulated Modality Generation  
**作者**：Mengmeng Liu et al.  
**会议**：NeurIPS 2026（arXiv 论文页面标注 Accepted；本次使用 arXiv 版本，并非声称会议出版 PDF）  
**论文版本**：arXiv:2607.05133v2，2026-11-16 更新（首次提交 2026-07-06）

## 1. 原文 PDF
- 官方原文：[arXiv PDF](https://arxiv.org/pdf/2607.05133)（v2 为目前最新列出版本）
- [论文详情及历史版本](https://arxiv.org/abs/2607.05133)
- **PDF 尚未上传到本仓库**：本次原始 PDF 下载未成功，因此仅提供官方直达链接，不以摘要或占位文件冒充原文。

## 2. 推荐理由
以往世界动作模型（WAM）借助未来视频生成学习场景动力学，但若规划时仍生成整段未来视频，推理成本很高。UNIVERSE 通过**共享一套 Diffusion Transformer（DiT）参数**联合训练未来视频与轨迹，同时利用 **Modality-Decoupling Visibility Mask** 阻断未来视频 Token 和未来轨迹 Token 之间的直接注意力依赖：二者只共享历史上下文，各自还能关注自身未来 Token。这样训练时视频监督仍能改善规划参数，而推理时可以只采样轨迹，无需生成未来视频。

论文报告 NAVSIM **91.0 PDMS**，相较耦合视频-动作推理，轨迹单独推理快约 **4.3 倍**（均为作者论文报告，未自行复现）。与之前 DriveWAM 论文对照，可重点学习“**共享参数 vs. 注意力可见性解耦**”如何减少推理延迟，对自动驾驶世界模型、DiT 和动作生成有直接参考价值。

## 3. 官方代码
- **作者目前维护的官方仓库**：[xiaomi-research/universe](https://github.com/xiaomi-research/universe)（2026-11-09 开源；作者原有 xiaomi-mlab/UNIVERSE 仓库说明代码已迁移）
- 本次静态阅读固定 commit：[`33aea49e5c62c614ac35b074e0b3a62ed9688ebd`](https://github.com/xiaomi-research/universe/commit/33aea49e5c62c614ac35b074e0b3a62ed9688ebd)
- 训练/推理入口分别位于 `examples/wanvideo/UNIVERSE_train/` 和 `examples/wanvideo/UNIVERSE_infer/`；作者提供检查点下载说明。

## 4. 关键代码解释（静态源码阅读，未运行）
**① 可见性掩码 — `mixed_visibility_attention`**  
[源码：`diffsynth/models/wan_video_dit.py:80-148`](https://github.com/xiaomi-research/universe/blob/33aea49e5c62c614ac35b074e0b3a62ed9688ebd/diffsynth/models/wan_video_dit.py#L80-L148)  
输入 Q/K/V 为 `[B, N, D]`，按“历史视频 / 未来视频 / 轨迹前缀 / 未来轨迹”四组切分。历史上下文仅关注历史上下文；未来视频关注历史和未来视频；未来轨迹关注历史和未来轨迹。分组 FlashAttention 后按原顺序拼接，因此两类未来 Token 不会互相泄漏。分组由 [`_build_mixed_sequence_partition`](https://github.com/xiaomi-research/universe/blob/33aea49e5c62c614ac35b074e0b3a62ed9688ebd/diffsynth/pipelines/wan_video_new.py#L119-L145) 构造。

**② 共享 DiT 的双任务训练 — `WanVideoPipeline.training_loss`**  
[源码：`diffsynth/pipelines/wan_video_new.py:503-665`](https://github.com/xiaomi-research/universe/blob/33aea49e5c62c614ac35b074e0b3a62ed9688ebd/diffsynth/pipelines/wan_video_new.py#L503-L665)  
对视频 latent 与未来轨迹 `[B,K,3]` 施加对应时间步噪声，模型在共享骨干上分别输出视频与轨迹预测。去掉轨迹历史/速度前缀后分别计算 MSE，再用可配置的 `video_loss_scale` / `trajectory_loss_scale` 和调度权重组合成训练损失。

**③ 不生成视频的规划推理 — `WanVideoPipeline.__call__`**  
[源码：`diffsynth/pipelines/wan_video_new.py:768-810`](https://github.com/xiaomi-research/universe/blob/33aea49e5c62c614ac35b074e0b3a62ed9688ebd/diffsynth/pipelines/wan_video_new.py#L768-L810)，[去噪与解码：`901-957`](https://github.com/xiaomi-research/universe/blob/33aea49e5c62c614ac35b074e0b3a62ed9688ebd/diffsynth/pipelines/wan_video_new.py#L901-L957)  
`output_mode="trajectory"` 时，满足历史 latent 与轨迹长度条件便仅保留历史视频 latent，未来轨迹从 `[B,K,3]` 高斯噪声开始逐步更新；停止未来视频去噪，并跳过 VAE 视频解码。最终轨迹去归一化，得到未来 `(x,y,yaw)`。注意这不等于删除历史视觉条件。

**核验范围**：已阅读官方 README、以上函数的固定 commit 源码，未训练或复现性能；GitHub 文件保存后另行核对远端。无需翻译、HTML、ZIP 或旧包修复。
