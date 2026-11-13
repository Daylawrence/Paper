# 2026-11-13｜DriveWAM｜自动驾驶世界-动作模型

**论文**：DriveWAM: Video Generative Priors Enable Scalable World-Action Modeling for Autonomous Driving  
**作者**：Chen Shi、Jinrui Xu、Shaoshuai Shi、Kehua Sheng、Bo Zhang、Li Jiang。  
**版本/会议**：arXiv:2605.28544（2026-05-27 首次提交）；作者 [官方仓库](https://github.com/chenshi3/DriveWAM) 在 2026-09-25 宣布 NeurIPS 2026 接收，README 标为 “Preliminary accepted”。本次采用 arXiv 原稿，不冒称已取得最终会议出版 PDF。  

## 1. 原文 PDF

- [arXiv 官方原文 PDF](https://arxiv.org/pdf/2605.28544) ｜ [论文详情](https://arxiv.org/abs/2605.28544)
- 此次**仅链接官方 PDF，未把 PDF 二进制上传到本仓库**；没有翻译、HTML 或 ZIP。

## 2. 推荐理由

DriveWAM 与以 VLM 为规划主干的 AutoVLA 等路线不同：将预训练**视频生成模型作为驾驶策略主干**，在统一时序序列里同时预测未来视频潜变量和自车动作，训练采用视频与动作的联合 flow-matching。它先预测场景如何演化，再以未来世界表征为条件生成动作；用冻结的 VLM 产生**随时间块变化的驾驶语义指导**，并用 **Selective KV Memory** 控制长序列推理显存。论文/作者报告 NAVSIM PDMS 90.1、PhysicalAI-AV ADE@4s 0.83m（非本次复现）。

**推荐的具体原因**：适合把已有的 VGGT/Depth Pro 感知、驾驶 VLM 理解拓展到视频世界模型和连续动作学习；还可研究 Qwen-VL 生成的驾驶语义如何通过 chunk-level cross-attention 影响动作，以及 KV 缓存对长时序规划的影响。作者仓库还记录了 8×H20 的训练修复与实验配置，但不代表单卡可直接复现。

## 3. 官方代码与固定版本

- **作者官方仓库**：[chenshi3/DriveWAM](https://github.com/chenshi3/DriveWAM)
- **本次实际静态阅读的固定 commit**：[14d16d2412dc4d70af59a921cc450299f5207f10](https://github.com/chenshi3/DriveWAM/commit/14d16d2412dc4d70af59a921cc450299f5207f10)
- 作者公开源码与权重（[Hugging Face 链接见 README](https://github.com/chenshi3/DriveWAM)）；**本次未运行训练、推理或模型复现**。

## 4. 关键代码解释（建议依次阅读）

### A. 世界潜变量 + 动作的共同预测

[physicalai_model.py：`_input_embed` / `forward_train`](https://github.com/chenshi3/DriveWAM/blob/14d16d2412dc4d70af59a921cc450299f5207f10/src/modules/physicalai_model.py#L630-L823) 将视频潜变量按 3D patch 展平并投影为 tokens；动作流另外用 MLP 投影。训练时拼接“带噪视频、条件视频、带噪动作、条件动作”四段 token，在一个 Transformer 内交互，输出视频和动作预测。另看 [train.py：`compute_loss` / `_train_step`](https://github.com/chenshi3/DriveWAM/blob/14d16d2412dc4d70af59a921cc450299f5207f10/src/physicalai/train.py#L424-L501)：对两路 flow target 分别计算带权、带 mask 的 MSE，损失相加反传；VAE 和 text encoder 在 Trainer 初始化时被冻结（[见代码](https://github.com/chenshi3/DriveWAM/blob/14d16d2412dc4d70af59a921cc450299f5207f10/src/physicalai/train.py#L51-L99)）。重点理解视频生成如何被改造为可输出连续动作的训练目标。

### B. Scene-evolving guidance：VLM 指导具体时间块

[generate_scene_evolving_guidance.py](https://github.com/chenshi3/DriveWAM/blob/14d16d2412dc4d70af59a921cc450299f5207f10/src/physicalai/vlm_preprocess/generate_scene_evolving_guidance.py#L147-L269) 按 clip 和 chunk 准备当前图像、路线及可用 BEV 历史，调用 VLM 批量生成 `clip_id → chunk_idx → caption`；预处理脚本默认 VLM 名称是 `Qwen3-VL-8B-Instruct`。[vlm_captioner.py](https://github.com/chenshi3/DriveWAM/blob/14d16d2412dc4d70af59a921cc450299f5207f10/src/physicalai/vlm_preprocess/vlm_captioner.py#L195-L250) 可见构建提示词和图像输入方式。[physicalai_model.py 的 text mask](https://github.com/chenshi3/DriveWAM/blob/14d16d2412dc4d70af59a921cc450299f5207f10/src/modules/physicalai_model.py#L166-L179) 同时约束 query 与文本键值必须属于同一 batch、同一 chunk，避免跨时间块直接看到未来语义。

### C. Selective KV：控制长时序缓存

[compress_kv.py：`selectiveKV_score_tokens`](https://github.com/chenshi3/DriveWAM/blob/14d16d2412dc4d70af59a921cc450299f5207f10/src/modules/compress_kv.py#L6-L113) 输入 `query_states:[Q,H_q,D]`、`key_states:[K,H_{kv},D]`，计算注意力相关度及 Key 的余弦相似冗余，合成为 `score = λ·relevance − (1−λ)·redundancy`；[model.py：`allocate_slots`](https://github.com/chenshi3/DriveWAM/blob/14d16d2412dc4d70af59a921cc450299f5207f10/src/modules/model.py#L1087-L1159) 在缓存不够时优先淘汰最低分 token，保护 pinned 首帧锚点；条件不足时回退到按最旧 ID 淘汰。它是**推理期的缓存管理**，不能误写成训练时重新学习注意力权重。

---

**去重与证据**：检查了本仓库 `reading-packs/` 现有目录、旧 `catalog.json` 和 2026-11-11 AutoVLA 笔记；未见 DriveWAM 同一论文推荐。会议接收依据作者仓库公告；实验结果依据作者论文/README；代码部分仅为上述 commit 的静态阅读。无历史阅读包改动、无 Gmail。
