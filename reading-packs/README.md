# 论文阅读包（展开 Markdown / PDF 优先）

## 2026-11-06：GaussianDWM 表1及图4原文视觉核验（继续修复）

根据仓库中的 [原文第6页](2026-10-28_CVPR2026_GaussianDWM/pages/page-06.jpg) 人工核对补齐 BEVFormer、PETR、CAPE 的3DVG检测指标；保留 BEVFormer F1=1.576（原文如此），跨任务不支持不按0分处理。根据 [原文第8页](2026-10-28_CVPR2026_GaussianDWM/pages/page-08.jpg) 恢复图4的RGB-D定性比较图注、六组方法标签，在译文HTML和Markdown中直接引用已有原文页图，无需在线图源。[详细视觉核验](2026-10-28_CVPR2026_GaussianDWM/source-visual-audit-2026-11-06.md)。 [11月6日远端逐文件校验报告](2026-10-28_CVPR2026_GaussianDWM/remote-verification-2026-11-06.json)：37/37 Git blob SHA 匹配、36/36 实际字节数匹配（原文 PDF 本轮仅复核 blob SHA，原字节数沿用此前验收）；已修正3个文件的 Unicode 字节数/SHA256。

已同步修改 [译文 Markdown](2026-10-28_CVPR2026_GaussianDWM/translation.md)、[HTML译文](2026-10-28_CVPR2026_GaussianDWM/translation.html)、[阅读主页源码](2026-10-28_CVPR2026_GaussianDWM/index.html) 和 [覆盖清单](2026-10-28_CVPR2026_GaussianDWM/coverage.md)。**仍为 repairing**：尚未完成补充材料 QA/轨迹全量核对、其他段落与图文字逐项比对、离线 KaTeX/浏览器验收及中文简报PDF同步。11月2日ZIP仍旧版备份，不视为最新交付。旧包修复优先，不推荐新论文。


## 2026-11-04：GaussianDWM 网页迁移及译文扩充（仍在修复）

已使用 [DriveVLA-W0 已上传真实模板](2026-09-16_ICLR2026_DriveVLA-W0_%E9%98%85%E8%AF%BB%E5%8C%85/) 中的实际 CSS/JS/HTML 为 GaussianDWM 迁移暖米色/深绿色/金色网页样式及三选项、左目录、右独立滚动、分选项记忆交互。翻译从先前概述扩展至主文引言、相关工作、完整方法（公式1–5）、实验与四张主表、结论及致谢，并补充附录A–E/公式S1–S5与三张补充实验表。**未完成严格逐段核验**：表1若干专用检测器行、图4、完整轨迹数据和图中文字仍有缺口；完整 KaTeX/离线视觉校验未通过，中文简报PDF及ZIP未同步本次文字内容。原有2026-11-02 ZIP仍是**过期备份**，不是最新HTML/Markdown完整包。GaussianDWM状态继续 repairing。

最新直接阅读：[完整目录](2026-10-28_CVPR2026_GaussianDWM/) · [翻译Markdown（仍待校对）](2026-10-28_CVPR2026_GaussianDWM/translation.md) · [关键解释Markdown](2026-10-28_CVPR2026_GaussianDWM/algorithms.md) · [逐节覆盖与缺口](2026-10-28_CVPR2026_GaussianDWM/coverage.md) · [原文PDF](2026-10-28_CVPR2026_GaussianDWM/paper.pdf)。未部署并核实GitHub Pages；普通GitHub网页不运行index.html，若需网页交互请clone后本地打开。保留优先处理本篇，历史问题包未验收完成前不推荐新论文。


## 2026-11-02 修复进度：GaussianDWM 原文与远端完整性已恢复

保留原制作日期 **2026-10-28**；实际修复与远端验收日期 **2026-11-02**。继续**先修复历史旧包，暂停新论文推荐与上传**。[修复队列](repair-queue.json)。

- **原文页修复通过**：按 CVPR 2026 官方文件 SHA256 核验，下载并合并 12 页主论文和 7 页补充材料，恢复 19 页可搜索文字的 [paper.pdf](2026-10-28_CVPR2026_GaussianDWM/paper.pdf)，重新生成 page-01.jpg 到 page-19.jpg；原第 18、19 页相同的空白占位图已替换。
- **GitHub 远端验收通过的部分**：完整展开目录的 34/34 个文件大小及 Git blob SHA 一致；重新下载远端 ZIP（20,861,399 字节，SHA256: f7c5289268b9372b26d41a7917dba5d784ee6421fd420fe6105167b8d9c61be8），通过 ZIP CRC 和内部逐文件 34 项字节数、SHA256、Git blob SHA；重新下载 paper.pdf，核验全部 19 页，末三页均有正文；静态相对资源链接无缺失。[远端验收明细](2026-10-28_CVPR2026_GaussianDWM/remote-verification-2026-11-02.json)。
- **仍待修复，不得标 completed**：[translation.md](2026-10-28_CVPR2026_GaussianDWM/translation.md)、translation.html 和 index.html 内嵌译文仍是压缩的分节文本，尚未达到整篇正文和补充材料逐节逐段完整翻译的标准。维持 repairing 状态，本篇优先级不变。

直接阅读入口：[完整展开目录](2026-10-28_CVPR2026_GaussianDWM/) · [原文 PDF](2026-10-28_CVPR2026_GaussianDWM/paper.pdf) · [现有译文 Markdown（未完成）](2026-10-28_CVPR2026_GaussianDWM/translation.md) · [关键算法 Markdown](2026-10-28_CVPR2026_GaussianDWM/algorithms.md) · [中文学习简报 PDF](2026-10-28_CVPR2026_GaussianDWM/2026-10-28_CVPR2026_GaussianDWM_%E4%B8%AD%E6%96%87%E5%AD%A6%E4%B9%A0%E7%AE%80%E6%8A%A5.pdf) · [逐文件清单](2026-10-28_CVPR2026_GaussianDWM/manifest.json)。

GitHub 文件页面**不执行 HTML**；可以直接阅读 Markdown/PDF，或 `git clone https://github.com/Daylawrence/Paper.git` 后本地打开对应 `index.html`。未部署且未验证 GitHub Pages，不提供虚构的网页阅读入口。ZIP 仅作备份，不作为取得展开资料的前提。

以下为早期未逐包重新核验的 ZIP 归档；请优先使用已修复的展开目录。下载 ZIP 后完整解压，双击 `index.html` 阅读「原文 / 译文 / 关键解释」。中文简报 PDF 可直接在 GitHub 打开。ZIP 中包含原文、译文、算法解释及离线资源。

以下为已生成历史成果的原文件归档，上传于 2026-10-10；保留原制作日期。本次校验了 ZIP 完整性与上传内容哈希，未重新审校全部译文。

| 制作日期 | 论文 | 阅读包 | 中文简报 |
|---|---|---|---|
| 2026-09-18 | DiffusionDrive | [下载 ZIP](2026-09-18_CVPR2025_DiffusionDrive/2026-09-18_CVPR2025_DiffusionDrive_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-09-18_CVPR2025_DiffusionDrive/2026-09-18_CVPR2025_DiffusionDrive-Truncated-Diffusion-Model.pdf) |
| 2026-09-21 | PE3R | [下载 ZIP](2026-09-21_CVPR2026_PE3R/2026-09-21_CVPR2026_PE3R_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-09-21_CVPR2026_PE3R/2026-09-21_CVPR2026_PE3R-Perception-Efficient-3D-Reconstruction.pdf) |
| 2026-09-23 | ACoT-VLA | [下载 ZIP](2026-09-23_CVPR2026_ACoT-VLA/2026-09-23_CVPR2026_ACoT-VLA_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-09-23_CVPR2026_ACoT-VLA/2026-09-23_CVPR2026_ACoT-VLA-Action-Chain-of-Thought.pdf) |
| 2026-09-28 | VLM-3R | [下载 ZIP](2026-09-28_CVPR2026_VLM-3R/2026-09-28_CVPR2026_VLM-3R_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-09-28_CVPR2026_VLM-3R/2026-09-28_CVPR2026_VLM-3R-Vision-Language-Models-Augmented-with-3D-Reconstruction.pdf) |
| 2026-09-30 | VGG-T3 | [下载 ZIP](2026-09-30_CVPR2026_VGG-T3/2026-09-30_CVPR2026_VGG-T3_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-09-30_CVPR2026_VGG-T3/2026-09-30_CVPR2026_VGG-T3-Offline-Feed-Forward-3D-Reconstruction-at-Scale.pdf) |
| 2026-10-05 | SRPO | [下载 ZIP](2026-10-05_CVPR2026_SRPO/2026-10-05_CVPR2026_SRPO_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-10-05_CVPR2026_SRPO/2026-10-05_CVPR2026_SRPO-Self-Referential-Policy-Optimization.pdf) |
| 2026-10-07 | G2VLM | [下载 ZIP](2026-10-07_CVPR2026_G2VLM/2026-10-07_CVPR2026_G2VLM_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-10-07_CVPR2026_G2VLM/2026-10-07_CVPR2026_G2VLM-Geometry-Grounded-Vision-Language-Model.pdf) |
| 2026-10-12 | WAM-Flow（历史论文按新提示词重制版，不是新推荐） | [下载 ZIP](2026-10-12_CVPR2026_WAM-Flow/2026-10-12_CVPR2026_WAM-Flow_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-10-12_CVPR2026_WAM-Flow/2026-10-12_CVPR2026_WAM-Flow-Parallel-Coarse-to-Fine-Motion-Planning.pdf) |
| 2026-10-14 | DrivePI（历史论文按新提示词重制版，不是新推荐） | [下载 ZIP](2026-10-14_CVPR2026_DrivePI/2026-10-14_CVPR2026_DrivePI_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-10-14_CVPR2026_DrivePI/2026-10-14_CVPR2026_DrivePI-Spatial-aware-4D-MLLM.pdf) |
| 2026-10-19 | UniVLA（历史论文按新提示词重制版，不是新推荐） | [下载 ZIP](2026-10-19_ICLR2026_UniVLA/2026-10-19_ICLR2026_UniVLA_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-10-19_ICLR2026_UniVLA/2026-10-19_ICLR2026_UniVLA-Unified-Vision-Language-Action-Model.pdf) |
| 2026-10-21 | GLUEMAP（新论文推荐） | [下载 ZIP](2026-10-21_CVPR2026_GLUEMAP/2026-10-21_CVPR2026_GLUEMAP_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-10-21_CVPR2026_GLUEMAP/2026-10-21_CVPR2026_GLUEMAP-Global-Structure-from-Motion-Meets-Feedforward-Reconstruction.pdf) |
| 2026-10-23 | MoRe（新论文推荐） | [下载 ZIP](2026-10-23_CVPR2026_MoRe/2026-10-23_CVPR2026_MoRe_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-10-23_CVPR2026_MoRe/2026-10-23_CVPR2026_MoRe-Motion-aware-Feed-forward-4D-Reconstruction-Transformer.pdf) |
| 2026-10-26 | VLA-World（新论文推荐，CVPR 2026 Findings） | [下载 ZIP](2026-10-26_CVPR2026F_VLA-World/2026-10-26_CVPR2026F_VLA-World_%E9%98%85%E8%AF%BB%E5%8C%85.zip?raw=true) | [查看 PDF](2026-10-26_CVPR2026F_VLA-World/2026-10-26_CVPR2026F_VLA-World-Learning-Vision-Language-Action-World-Models.pdf) |
