#!/usr/bin/env python3
"""Build PE3R expanded offline reader from actual GitHub DriveVLA-W0 template.
No ZIP generation. Historical PDF sources are kept. Non-reference translation is authoritative.
"""
from __future__ import annotations
import hashlib, json, pathlib, shutil, re
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import fitz

ROOT=pathlib.Path(__file__).resolve().parents[1]
D=ROOT/"reading-packs/2026-09-21_CVPR2026_PE3R"
TPL=ROOT/"reading-packs/2026-09-16_ICLR2026_DriveVLA-W0_阅读包"
assert D.is_dir() and TPL.is_dir()
assert (D/"supplement.pdf").is_file(), "Must include official PE3R supplemental PDF"
assert (D/"paper.pdf").is_file(), "Must include official PE3R main PDF"
assert len(fitz.open(D/"paper.pdf"))==11
assert len(fitz.open(D/"supplement.pdf"))==2
assert all((D/f"pages/page-{i:02d}.jpg").is_file() for i in range(1,12))
assert all((D/f"supplement-pages/page-{i:02d}.jpg").is_file() for i in range(1,3))
shutil.copy2(TPL/"style.css",D/"style.css")
shutil.copytree(TPL/"vendor",D/"vendor",dirs_exist_ok=True)
js=(TPL/"app.js").read_text("utf-8")
assert 'const main=' in js
js=js.replace('(()=>{const main=',"""(()=>{const storage=(()=>{try{const s=window.localStorage;const t='pe3r-access-test';s.setItem(t,'1');s.removeItem(t);return s}catch(e){const m={};return {getItem:k=>m[k]||null,setItem:(k,v)=>{m[k]=String(v)}}}})();const localStorage=storage;const main=""",1)
(D/"app.js").write_text(js,"utf-8")

trans=BeautifulSoup((D/"translation.html").read_text("utf-8"),"html.parser")
article=trans.select_one("article.translation")
assert article and len(article.select("section[id]"))>=7
old=article.find(id="tr-coverage")
if old:old.decompose()
note=article.select_one("p.note")
note.clear()
note.append("版本：CVPR 2026 Open Access 正式主文 11 页（第 1–8 页正文与致谢、第 9–11 页参考文献），另附官方 2 页 Supplementary Material（第 6–7 节）。下文为除参考文献列表之外的中文翻译，公式、数据、图表编号保留；补充材料的原作者证明存在的特殊等式在译注中单独提示。")
# Fix a factually incorrect sponsor line in the old historical translation.
conclusion=article.find(id="tr-conclusion")
if conclusion:
    for p in conclusion.find_all("p"):
        if "AISG Award" in p.get_text():
            p.clear()
            p.append(BeautifulSoup("<b>致谢。</b>","html.parser"))
            p.append("本项目由新加坡国家研究基金会资助，属于先进机器人技术创新中型研究中心项目。")

# Replace a single composite placeholder for figures 3–6 with distinct translated captions.
exp=article.find(id="tr-exp")
if exp:
    for figure in exp.find_all("figure"):
        if "图3-6" in figure.get_text():
            figure.decompose()
    figures=[
      (7,3,"图 3：多层级消歧的作用。移除此模块会使模型无法正确关联物体部件与整体，从而造成语义碎片化。"),
      (7,4,"图 4：跨视角消歧的作用。缺少跨视角对齐时，同一物体在不同视角下会被赋予不一致的标签。"),
      (7,5,"图 5：全局最小-最大归一化的作用。缺少全局归一化时，不同视角间的相似度分数无法得到统一标定，从而降低检索可靠性。"),
      (8,6,"图 6：语义点云重建模块的作用。移除此模块会增加空间噪声并降低重建点云在物体层面的一致性，体现它对几何和语义保真度的作用。"),
    ]
    for page,number,caption in figures:
        exp.append(BeautifulSoup(f'<figure><img src="pages/page-{page:02d}.jpg" alt="原文包含图{number}的页图"><figcaption>{caption}</figcaption></figure>',"html.parser"))

supp=BeautifulSoup((D/"supplement-translation-2026-11-10.html").read_text("utf-8"),"html.parser")
supp_sections=list(supp.find_all("section",recursive=False))
assert len(supp_sections)>=3
for section in supp_sections:
    article.append(section)
assert all(article.find(id=k) for k in ["tr-supp-intro","tr-supp-6","tr-supp-7"])
# Use template's built-in $ display-math renderer without adding a remote dependency.
for equation in article.select("div.equation"):
    raw=equation.get_text()
    equation.clear()
    equation.append(raw.replace(r"\[","$").replace(r"\]","$"))
assert len(article.select("table"))>=11  # main 7 tables + 4 official supplemental tables
assert "式（16）" in article.get_text()
(D/"translation.html").write_text(
    '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PE3R 完整中文译文（含官方补充材料）</title><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="vendor/katex.min.css"></head><body class="standalone">'+str(article)+'<script src="vendor/katex.min.js"></script><script src="vendor/auto-render.min.js"></script><script>if(window.renderMathInElement)renderMathInElement(document.body,{delimiters:[{left:"\\\\[",right:"\\\\]",display:true},{left:"$$",right:"$$",display:true},{left:"$",right:"$",display:false}],throwOnError:false});</script></body></html>',
    "utf-8")

# Preserve all translated paragraphs and every table in a GitHub-readable Markdown file.
def to_md(element):
    result=md(str(element),heading_style="ATX",bullets="-")
    result=re.sub(r'\n{3,}','\n\n',result)
    result=result.replace(r'\[',"\n$$\n").replace(r'\]',"\n$$\n")
    return result.strip()+"\n"
main_md=to_md(article)
assert "7.4 迭代细化" in main_md and "5. 结论" in main_md
assert "| 0.003 |" in main_md or "0.003" in main_md
(D/"translation.md").write_text(
    "# PE3R: Perception-Efficient 3D Reconstruction — 中文全文译文\n\n"
    "> 对应 CVPR 2026 正式主论文 11 页 + 官方补充材料 2 页；参考文献列表不翻译。原始论文及补充材料分别见 [paper.pdf](paper.pdf) 与 [supplement.pdf](supplement.pdf)。本译文为非官方中文翻译；译注与作者原文严格分开。\n\n"
    +main_md,"utf-8")

alg=BeautifulSoup((D/"algorithms.html").read_text("utf-8"),"html.parser")
alg_article=alg.select_one("article.algorithms")
assert alg_article is not None
(D/"algorithms.html").write_text(
    '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>PE3R 关键解释</title><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="vendor/katex.min.css"></head><body class="standalone">'
    +str(alg_article)+"</body></html>","utf-8")
(D/"algorithms.md").write_text("# PE3R 关键解释\n\n"+to_md(alg_article),"utf-8")

original=''.join(f'<section class="paper-page" id="page-{i:02d}"><img loading="lazy" src="pages/page-{i:02d}.jpg" alt="CVPR2026 正式原文第 {i} 页"></section>' for i in range(1,12))
original+= '<h2>官方补充材料原文（另附 2 页 PDF）</h2>'
original+=''.join(f'<section class="paper-page" id="supp-page-{i:02d}"><img loading="lazy" src="supplement-pages/page-{i:02d}.jpg" alt="官方补充材料原文第 {i} 页"></section>' for i in range(1,3))
index='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PE3R 论文阅读包</title><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="vendor/katex.min.css"></head>
<body class="app" data-paper="PE3R"><header class="top"><div class="brand"><h1>PE3R: Perception-Efficient 3D Reconstruction</h1><div class="meta">2026-09-21 历史包 · 2026-11-10 修复 · CVPR 2026 · <a href="paper.pdf">主文 PDF</a> · <a href="supplement.pdf">官方补充 PDF</a> · <a href="https://openaccess.thecvf.com/content/CVPR2026/html/Hu_PE3R_Perception-Efficient_3D_Reconstruction_CVPR_2026_paper.html" target="_blank">论文入口</a> · <a href="https://github.com/hujiecpp/PE3R/tree/a6c36830470de33fce43a843612d486217cb0f8b" target="_blank">固定源码</a></div></div><nav class="tabs"><button data-tab="original">原文</button><button data-tab="translation">译文</button><button data-tab="explanation">关键解释</button></nav></header>
<div class="layout"><aside><h2>目录</h2><nav id="toc"></nav></aside><main><article id="original" class="panel">'''
index+=original+'</article><article id="translation" class="panel">'+str(article)+'</article><article id="explanation" class="panel">'+str(alg_article)+'</article></main></div>'
index+='<script src="vendor/katex.min.js"></script><script src="vendor/auto-render.min.js"></script><script src="app.js"></script></body></html>'
(D/"index.html").write_text(index,"utf-8")

# Explicit coverage checklist only for sections actually present.
groups=[
("摘要、引言",["tr-abstract","tr-intro"]),
("相关工作、方法 3.1–3.5",["tr-related","tr-method"]),
("实验 4.1–4.3、表 1–7、结论与致谢",["tr-exp","tr-conclusion"]),
("官方补充 6：命题与公式 8–17",["tr-supp-6"]),
("官方补充 7.1：异常点选择、表 8",["tr-supp-7"]),
("官方补充 7.2–7.4：表 9–11",["tr-supp-7"]),
]
coverage_rows=''.join(f"<tr><td>{label}</td><td>{'、'.join(ids)}</td><td>{'是' if all(article.find(id=i) for i in ids) else '缺失'}</td></tr>" for label,ids in groups)
coverage='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>PE3R 章节覆盖核对</title><link rel="stylesheet" href="style.css"></head><body class="standalone"><h1>PE3R 译文覆盖清单</h1><p>主文：CVPR 2026 11 页，其中 1–8 页为正文、图表、结论，9–11 页主要为参考文献。补充材料官方 PDF：2 页，含公式（8）–（17）与表 8–11。参考文献不翻译。</p><table><tr><th>章节/材料</th><th>对应译文 ID</th><th>已存在</th></tr>'''+coverage_rows+'''</table><p>此表只证明结构和重要图表存在，不能代替每一英语句子的专业翻译校勘。公式（16）按原文保留并注明译注。</p></body></html>'''
(D/"coverage.html").write_text(coverage,"utf-8")
(D/"打开说明.txt").write_text("PE3R 历史论文阅读包（2026-11-10 修复）。\n从 GitHub 直接查看 translation.md、algorithms.md、paper.pdf、supplement.pdf；克隆仓库后双击 index.html 离线阅读原文、完整中文译文和关键解释。\n原文 11 页 + 官方补充材料 2 页；参考文献不翻译。无需 ZIP，不运行 HTML 外部 fetch。\n文件已采用 DriveVLA-W0 实际 CSS/JS/布局。若浏览器禁用 file:// localStorage，界面自动退回内存状态。\n","utf-8")

# No creation or reuse of ZIP: removal must follow validation in the workflow.
def blob_sha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
entries=[]
for path in sorted(D.rglob("*")):
    if not path.is_file() or path.suffix.lower()==".zip" or path.name=="manifest.json":
        continue
    data=path.read_bytes()
    entries.append({"path":str(path.relative_to(D)),"bytes":len(data),"git_blob_sha":blob_sha(data),"sha256":hashlib.sha256(data).hexdigest()})
(D/"manifest.json").write_text(json.dumps({"paper":"PE3R","version":"CVPR 2026 11-page main plus official 2-page supplement","repair_date":"2026-11-10","zip_is_not_an_output":True,"file_count_excluding_self_and_legacy_zip":len(entries),"files":entries},ensure_ascii=False,indent=2)+"\n","utf-8")
assert (D/"translation.md").stat().st_size>12000
assert (D/"algorithms.md").stat().st_size>5500
assert (D/"index.html").stat().st_size>22000
print(json.dumps({"status":"built_pending_remote_and_content_acceptance","files":len(entries),"main_pdf_pages":11,"supp_pdf_pages":2,"translation_chars":len(main_md),"algorithms_chars":len((D/"algorithms.md").read_text("utf-8")),"translation_sections":len(article.select("section[id]")),"translation_tables":len(article.select("table"))},ensure_ascii=False))
