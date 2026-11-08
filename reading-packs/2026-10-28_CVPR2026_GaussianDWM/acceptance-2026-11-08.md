# GaussianDWM 2026-11-08 最低交付验收记录

## 验收结论

**completed：达到修订后的最小交付条件——参考文献列表之外，主文与补充材料均有连贯、可读的中文译文。** 不是论文复现证书或出版级逐字翻译认证。本次选定 arXiv:2512.23180v3 主文（12 页）与 CVPR 2026 官方补充（7 页），合计 19 页。原制作日期 2026-10-28，最低标准验收日期 2026-11-08。

## 依据

- 主文标题覆盖 Abstract、1 Introduction、2 Related Work、3.1–3.3 Method、4.1–4.5 Experiments、5 Conclusion 和 Acknowledgement。补充覆盖 A Overview、B Dataset Details、C Implementation Details、D Ablation Study、E Extensive Experiments。
- 已有中文译文保留五个主公式、补充公式 S1–S5、主表 1–4、补充表 1–3、原文图 1–4/补充图 1–2 的主要图注和中文标签解释。正文包含 QA 结构样例、4 帧历史＋6 帧预测轨迹样例，保留原始数值。
- 本轮对照 [arXiv 主文 HTML](https://arxiv.org/html/2512.23180v3) 和仓库 [补充原文提取](supplement-source-extracted-2026-11-07.txt)，核查章节及关键实验/训练内容均有中文对应；参考文献表没有翻译。原有多轮审校记录见 [2026-11-08 忠实性审计](../audits/gaussiandwm-source-fidelity-2026-11-08.md) 与 [11-07 源图核对](source-visual-audit-2026-11-07.md)。此前审计使用的是更严格的全段一一映射和图内小字逐字符门槛；现行用户最低标准允许多句合为自然中文段落，只要内容未被概括删减。
- 文件级远端验证既有证据：[2026-11-08 独立远端审计](../audits/gaussiandwm-remote-2026-11-08.json) 证实不可变快照 109 个展开文件字节数和 SHA；本次状态及覆盖说明是小范围文本改动，相关文件已在默认分支重新读取校验。未变的 PDF、页图、JS、CSS 复用其既有核验结果。
- 最近一次真实离线 Chromium、KaTeX 和阅读位置恢复测试来自 2026-11-07。本次改动限于文本及状态，不声称本轮执行了新的 Chromium 测试。

## 保留说明与交付

[完整译文 Markdown](translation.md) · [独立 HTML](translation.html) · [离线阅读主页](index.html) · [算法解释](algorithms.md) · [原文 PDF](paper.pdf)。

可选 ZIP 仍是未同步 11 月 8 日译文的旧版备份；本次以展开目录交付，不以 ZIP 可用性替代译文验收。附图小字号文本不声称逐字符完整核查，论文中有争议的数值均保留并通过“译注”区分。若后续发现影响语义的具体漏译，应重新开启该篇修复而不是掩盖。
