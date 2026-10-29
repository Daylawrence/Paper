# 论文阅读包（展开 Markdown / PDF 优先）

## 2026-10-30 修复进度：GaussianDWM 尚未完成

保留原制日期 **2026-10-28**，修复核查日期 **2026-10-30**。**历史旧包修复优先，新论文推荐与上传暂停。** [修复队列](repair-queue.json)。

- **已验证的部分**：原 ZIP 为 **7,048,829 字节**，本地 SHA256 为 `1aa852e5e6e66f92e959fd740e17592c01df1f4064c386a0ae028a4313aaa77e`，且本地 ZIP CRC 校验成功。GitHub `main` 上 ZIP blob 大小和 Git SHA-1 与本地完整 ZIP 一致（`9ecdd928324a0ef6662495f345b432ae5f18d979`）；34/34 个已展开文件的远端大小与 Git blob SHA 均匹配，9 个文本文件额外重新获取并核对内容字节数。此前的 524,288 字节截断状态不再符合当前 Git 树元数据。
- **仍不合格**：`paper.pdf` 是 19 页图片合成 PDF，其中 **第 18、19 页是纯白占位页**，没有恢复完整的原论文/补充材料内容；当前 `translation.md` / `translation.html` 是压缩的分节文本，**不能当作逐段完整译文**。本次不能将该包标为 `completed`，也不能把仅 ZIP CRC 成功等同于完整内容通过。
- **后续必须修复**：恢复官方 12 页主文 + 7 页补充材料的真实页面，制作完整逐段翻译并同步 `translation.md`、`translation.html` 和 `index.html`，重做 PDF/ZIP，最后从 GitHub 远端再次完整下载并验证。

目前能在 GitHub 直接查看的**未完工资料**：[译文 Markdown（待完整校对）](2026-10-28_CVPR2026_GaussianDWM/translation.md) · [关键算法 Markdown](2026-10-28_CVPR2026_GaussianDWM/algorithms.md) · [中文简报 PDF](2026-10-28_CVPR2026_GaussianDWM/2026-10-28_CVPR2026_GaussianDWM_%E4%B8%AD%E6%96%87%E5%AD%A6%E4%B9%A0%E7%AE%80%E6%8A%A5.pdf) · [原文图片 PDF（末两页有缺陷）](2026-10-28_CVPR2026_GaussianDWM/paper.pdf) · [展开文件目录](2026-10-28_CVPR2026_GaussianDWM/) · [逐文件清单](2026-10-28_CVPR2026_GaussianDWM/manifest.json) · [质量审计](2026-10-28_CVPR2026_GaussianDWM/quality-audit-2026-10-30.json)。需要核对完整英文材料，请使用[论文的 CVPR 官方页面](https://openaccess.thecvf.com/content/CVPR2026/html/Deng_GaussianDWM_3D_Gaussian_Driving_World_Model_for_Unified_Scene_Understanding_CVPR_2026_paper.html)所列的主文与补充材料。

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
