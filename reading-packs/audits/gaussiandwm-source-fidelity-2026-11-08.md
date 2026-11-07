# GaussianDWM 原文—中文逐段忠实性审计：2026-11-08

- **原制作日**：2026-10-28；**本次审计日**：2026-11-08；**状态**：`repairing`，不满足 `completed`。
- **原文**：[arXiv 2512.23180v3 HTML（主文逐段）](https://arxiv.org/html/2512.23180v3)、[CVPR 2026 正式论文记录](https://openaccess.thecvf.com/content/CVPR2026/html/Deng_GaussianDWM_3D_Gaussian_Driving_World_Model_for_Unified_Scene_Understanding_CVPR_2026_paper.html)，补充材料与现有合并 PDF 的 [原始文字提取](../2026-10-28_CVPR2026_GaussianDWM/supplement-source-extracted-2026-11-07.txt)。
- **核对目标**：[现有中文 Markdown](../2026-10-28_CVPR2026_GaussianDWM/translation.md)。这次直接对照上述主文 HTML 及补充提取文本，**没有重新做 PDF 逐页视觉或离线浏览器验收**。此前完整性/Chromium 结果属于 2026-11-07 版本，不能推定今后更新仍自动通过。

## 已实际检查的主文区间与发现

| 英文原文位置 | 核对情况 | 当前发现/必须修复项 |
| --- | --- | --- |
| Abstract（HTML 摘要 4 个段落） | 中国译文的四段保留了现有 DWM 局限、语言 Gaussian、查询相关采样、双条件生成和两个数据集，未在本次抽查发现数值更改 | 最终仍需按版本 PDF 核对图注、标点与逐句细节 |
| §1 Introduction | arXiv HTML 可见 8 个连续正文段落，当前 Markdown 在贡献列表前为 6 个中文段落 | 已发现把英文 HERMES/BEV 瓶颈段与后续 3DGS 提议段合并、把查询选择与双条件总结合并；必须拆回对应原段落，不能用“信息大致覆盖”代替严格 1:1 |
| §2 Related Work | HTML 中 11 个连续相关工作段落，译文三个小节合计 8 个中文正文段落 | 已合并多段先前工作（如 NeRF 与 3DGS 进展，GAIA/DriveDreamer 等），需要按原始段落边界重新排布并复核引用号 |
| §3.1 World Tokenizer | 检查 (1) alpha 合成、(2) Fourier 位置编码及 `D=512,d=3,L=10`；译文基本保留术语及符号 | 说明性“请注意，这里的 f_i 可能是……”是译者额外解释，应单独标“译注”，不能混入作者正文 |
| §3.2 Scene Understanding | 检查 (3) LLM 输入输出、4096 个全局 Gaussian、两阶段 5k/30k 和 (4) 自回归损失 | 存在原文相邻语义段的合并（世界知识→Qwen3；grounding 方法→能力结论）；需要逐段映射并保留公式前后段落顺序 |
| §3.3 Scene Generation | 检查复制深度通道、RGB/深度 VAE、投影稀疏条件、(5) v-prediction、1m/2m 和 1s/2s | 译者对 `d_t` 的解释与代码 EDM 参数化须留在明确“译注/关键解释”，不要伪装为原作者推导 |
| §4.1–4.3 | 对照 nuScenes 六相机、NuInteract 约 150 万标注、16×A100、224×400→424×800、59.23 与 52.12 | 核心数值和方法存在；“不同指标需逐列理解”等非作者评论须放独立译注；其余表格仍需逐单元最终复核 |
| §4.4 Scene Generation | 对照 2Hz→12Hz、FID/FVD 及表3：±4m 时 DiST-S = 17.57/105.29，Ours = 18.81/116.40 | 原文“优于所有方法”与表3不完全一致，现有译文已有辨析，但这属于译注，应显式标记；图3/4 小字号标签仍未完全证实 |
| §4.5 Ablation | 对照表2、表4、混合采样、世界知识条件；表4原始标题与数值照录 | “不能仅由模型命名推断其贡献”等额外解读须标“译注”或移入关键解释 |
| §5 Conclusion + Acknowledgement | 检查结论两段及基金编号 `2024YFB4708900`、`62225309`、`U24A20278`、`62361166632` | 有相应中文；致谢英文姓名及排版需最终字级检查 |

## 补充材料已对照的可复核项目

- **B 数据与轨迹**：英文源第 13–14 页提取文本含 800 个 nuScenes 场景、LiDAR 初始化与 PSNR 过滤、512→3 的场景语言自编码器、4 帧历史和 6 帧预测；现有译文包含对应术语与数值。原始提取的多栏断行和 JSON 不能替代页图逐字段核对。已留存 [11 月 7 日视觉记录](../2026-10-28_CVPR2026_GaussianDWM/source-visual-audit-2026-11-07.md)。
- **C 实现细节**：英文源第 14–15 页分别描述三阶段训练、两种 Gaussian 视角加载、0.45%/0.79% 可训练参数和文本级 `E_enc=[E_img;E_text]+E_type`；中文版均涉及，但多段压缩为一个中文段落，不满足严格一一对应。
- **D/E**：英文源第 16–17 页含 128/512/4096 token 的采样消融，OmniDrive 的 CIDEr（GaussianDWM 0.712、Separated unification 0.745）和 30 场景知识消融；当前译文保留这些数据并注明原文 SOTA 表述与表格的不一致。**第 17–18 页定性图的所有小字号框、相机标签与坐标本轮尚未视觉逐字符再核。**

## 本轮结论与下一步的完成门槛

**明确不通过全文逐段一一对应验收**：已经发现 §1、§2、§3.2 及补充 C 中的多段合并，以及正文里数处未标注的译者评论。不是文件损坏，而是内容组织/作者与译注边界问题。须先对所选版全部非参考文献段落建立稳定原文 ID→译文 ID 清单，再逐段拆分、忠实性复核和标记译注；随后同步 `translation.md`、`translation.html`、`index.html`，核对算法/简报依赖，重新生成 `manifest.json` 及可选 ZIP，并执行 GitHub 默认分支逐文件字节数、Git blob SHA、PDF 与离线 KaTeX/浏览器验收。未完成前，不得将 catalog 或修复队列的 `repairing` 改成 `completed`。

此记录只提供主文 HTML/现有中文及已有补充文字的**局部实际审核结果**，不宣称全文已翻译合格，也不冒充新版本远端内容校验。
