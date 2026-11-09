#!/usr/bin/env python3
"""Build a complete, uncompressed, offline DiffusionDrive reader from verified source material.
Does not generate a ZIP; no downloaded code from the old ZIP is executed.
"""
from __future__ import annotations
import hashlib, html, json, pathlib, re, shutil, sys
import fitz
import html2text
import markdown
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKS = ROOT / "reading-packs"
DST = PACKS / "2026-09-18_CVPR2025_DiffusionDrive"
TEMPLATE = PACKS / "2026-09-16_ICLR2026_DriveVLA-W0_阅读包"
REPAIRED_DATE = "2026-11-09"
BASE = "https://github.com/Daylawrence/Paper/tree/main/reading-packs/2026-09-18_CVPR2025_DiffusionDrive"
TITLE = "DiffusionDrive: Truncated Diffusion Model for End-to-End Autonomous Driving"
CODE = "https://github.com/hustvl/DiffusionDrive/tree/9b52ed0ec06b073d82d6f392ab084c7b301c8681"
PAPER = "https://openaccess.thecvf.com/content/CVPR2025/html/Liao_DiffusionDrive_Truncated_Diffusion_Model_for_End-to-End_Autonomous_Driving_CVPR_2025_paper.html"
SUPP = "https://openaccess.thecvf.com/content/CVPR2025/supplemental/Liao_DiffusionDrive_Truncated_Diffusion_CVPR_2025_supplemental.pdf"

def digest(payload: bytes) -> dict:
    return {
        "bytes": len(payload),
        "git_blob_sha": hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest(),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }

def write(filename, text):
    (DST / filename).write_text(text, encoding="utf-8")

def convert(md):
    return markdown.markdown(md, extensions=["tables", "fenced_code", "toc", "sane_lists"], output_format="html5")

assert TEMPLATE.is_dir(), "DriveVLA-W0 real source template not present"
for name in ("index.html", "style.css", "app.js", "translation.html", "algorithms.html", "coverage.html"):
    assert (TEMPLATE/name).is_file(), name

source = (DST/"translation.md").read_text(encoding="utf-8")
need = [
    "## 摘要", "## 1. 引言", "## 2. 相关工作", "## 3. 方法", "## 4. 实验",
    "### 4.1", "### 4.2", "### 4.3", "### 4.4", "### 4.5", "### 4.6", "### 4.7",
    "## 5. 结论", "## 致谢", "## A.", "## B.", "## C."
]
assert len(source)>19000, "Translation is too short for full main+supplement"
for n in need:
    assert n in source, f"Missing translation section: {n}"
for n in range(1,8):
    assert f"主文表 {n}：" in source, f"Missing full original Table {n}"
for n in range(1,7):
    assert f"\\tag{{{n}}}" in source, f"Missing original formula ({n})"
for n in range(1,4):
    assert f"补充图 {n}：" in source, f"Missing supplement figure {n}"
assert source.count("|---")>=9, "Tables need tabular cells, not just summaries"
assert "参考文献列表不翻译" in source

# Keep the original two PDFs as distinct, explicitly versioned sources.
main = fitz.open(DST/"paper.pdf")
extra = fitz.open(DST/"supplement.pdf")
assert len(main)==11 and len(extra)==5, (len(main),len(extra))
for i in range(1,17):
    img=DST/"pages"/f"page-{i:02d}.jpg"
    assert img.is_file() and img.stat().st_size>30000, img

# Copies of the complete source pages put the original figures beside the translated captions.
figure_pages={
    "main-figure-1.jpg":1, "main-figure-2.jpg":3,
    "main-figure-3.jpg":4, "main-figure-4.jpg":5,
    "supp-figure-1.jpg":14, "supp-figure-2.jpg":15,
    "supp-figure-3.jpg":16,
}
(DST/"images").mkdir(exist_ok=True)
for filename,page in figure_pages.items():
    shutil.copy2(DST/"pages"/f"page-{page:02d}.jpg",DST/"images"/filename)

# Reuse actual checked-in template CSS and its offline KaTeX resources.
css=(TEMPLATE/"style.css").read_text("utf-8")
css += """
.panel#translation,.panel#explanation{background:var(--paper);padding:28px 38px;border:1px solid var(--line);border-radius:9px}
.panel#translation img,.panel#explanation img{display:block;max-width:100%;max-height:700px;object-fit:contain;margin:20px auto}
.panel#translation table,.panel#explanation table{display:block;overflow-x:auto}
.panel .reading{background:transparent}
.panel .reading section{margin:18px 0}
.panel .reading h1{font-size:29px}
@media(max-width:720px){.panel#translation,.panel#explanation{padding:16px 12px}}
"""
write("style.css",css)

# Preserve the real app.js reader implementation, adding only file://-safe localStorage fallback.
app=(TEMPLATE/"app.js").read_text("utf-8")
assert "paper-reader:" in app and "data-tab" in app and "original" in app
app=app.replace("localStorage.getItem", "safeStore.getItem").replace("localStorage.setItem", "safeStore.setItem")
assert app.startswith("(()=>{"), "Template script changed; review before migration"
fallback="""(()=>{const storageMemory={};const safeStore={getItem(key){try{return window.localStorage.getItem(key)}catch(_){return storageMemory[key]??null}},setItem(key,val){try{window.localStorage.setItem(key,String(val))}catch(_){storageMemory[key]=String(val)}}};"""
app=fallback+app[len("(()=>{"):]
write("app.js",app)

if not (DST/"vendor/katex.min.js").exists():
    if (DST/"vendor").exists():
        shutil.rmtree(DST/"vendor")
    shutil.copytree(TEMPLATE/"vendor",DST/"vendor")
else:
    # Ensure files and font resources match the known functioning template.
    shutil.rmtree(DST/"vendor")
    shutil.copytree(TEMPLATE/"vendor",DST/"vendor")
assert (DST/"vendor/katex.min.css").is_file()
assert (DST/"vendor/auto-render.min.js").is_file()
assert (DST/"vendor/fonts/KaTeX_Main-Regular.woff2").is_file()

# Reuse the old algorithms study material, not a freshly invented summary.
old_algo=(DST/"algorithms.html").read_text("utf-8")
soup=BeautifulSoup(old_algo,"html.parser")
alg_article=soup.select_one("article.reading.algorithms")
assert alg_article is not None, "Historical algorithms source not found"
alg_markup=str(alg_article)
alg_md=html2text.HTML2Text()
alg_md.ignore_links=False
alg_md.ignore_images=False
alg_md.body_width=0
alg_md.unicode_snob=True
algorithms_md=alg_md.handle(alg_markup)
assert len(algorithms_md)>4000, "Algorithm explanation unexpectedly short"
write("algorithms.md","# DiffusionDrive：关键解释与学习简报\n\n"+algorithms_md)

translation_html=convert(source)
assert translation_html.count("<table")>=9 and "## 1. 引言" not in translation_html
assert "DiffusionDrive" in translation_html and "补充材料" in translation_html
write("translation.html",f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DiffusionDrive · 完整中文译文</title>
<link rel="stylesheet" href="style.css"><link rel="stylesheet" href="vendor/katex.min.css"></head>
<body class="standalone"><article>{translation_html}</article>
<script src="vendor/katex.min.js"></script><script src="vendor/auto-render.min.js"></script>
<script>if(window.renderMathInElement)renderMathInElement(document.body,{{delimiters:[{{left:"$$",right:"$$",display:true}},{{left:"$",right:"$",display:false}}],throwOnError:false}})</script>
</body></html>""")

write("algorithms.html",f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DiffusionDrive · 关键解释</title><link rel="stylesheet" href="style.css">
<link rel="stylesheet" href="vendor/katex.min.css"></head><body class="standalone">
{alg_markup}<script src="vendor/katex.min.js"></script><script src="vendor/auto-render.min.js"></script>
<script>if(window.renderMathInElement)renderMathInElement(document.body,{{delimiters:[{{left:"$$",right:"$$",display:true}},{{left:"$",right:"$",display:false}}],throwOnError:false}})</script>
</body></html>""")

pages=[]
for i in range(1,17):
    which="主论文" if i<=11 else "官方补充材料"
    origin=i if i<=11 else i-11
    pages.append(f'<section class="paper-page" id="page-{i:02d}"><h2>{which} · 第 {origin} 页</h2><img loading="lazy" src="pages/page-{i:02d}.jpg" alt="{which}第{origin}页"></section>')
pages_html="\n".join(pages)
header=f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DiffusionDrive · 原文 / 译文 / 关键解释</title><link rel="stylesheet" href="style.css">
<link rel="stylesheet" href="vendor/katex.min.css"></head>
<body class="app" data-paper="DiffusionDrive"><header class="top">
<div class="brand"><h1>{html.escape(TITLE)}</h1><div class="meta">
2026-09-18 制作 · 2026-11-09 修复 · CVPR 2025 正式版 ·
<a href="paper.pdf">主文 PDF</a> · <a href="supplement.pdf">补充 PDF</a> ·
<a href="{PAPER}" target="_blank">论文官方入口</a> ·
<a href="{CODE}" target="_blank">官方固定源码</a>
</div></div><nav class="tabs"><button data-tab="original">原文</button>
<button data-tab="translation">译文</button><button data-tab="explanation">关键解释</button></nav>
</header><div class="layout"><aside><h2>目录</h2><nav id="toc"></nav></aside><main>"""
index=header+'<article id="original" class="panel"><section class="notice"><h2>原文版本与页数</h2><p>CVPR 2025 正式主文 11 页，加作者官方补充材料 5 页，共 16 页；以下逐页可离线查看。参考文献列在原文 PDF 中，中文译文不翻译参考文献列表。</p></section>'+pages_html+'</article><article id="translation" class="panel">'+translation_html+'</article><article id="explanation" class="panel">'+alg_markup+'</article></main></div><script src="vendor/katex.min.js"></script><script src="vendor/auto-render.min.js"></script><script src="app.js"></script></body></html>'
write("index.html",index)

# Section-level coverage ledger, not a false claim of publication-level word-for-word proof.
headings=re.findall(r"^(#{1,3})\s+(.+)$",source,re.M)
coverage={
  "paper":"DiffusionDrive","source_main":"CVPR 2025 OA (11 pages)","source_supplement":"CVF supplemental (5 pages)",
  "translated_range":"Main abstract + sections 1–5 + acknowledgement; supplemental A–C; bibliographies excluded",
  "reviewed_date":REPAIRED_DATE,
  "sections":[{"level":len(h),"name":name} for h,name in headings],
  "tables_main":7,"tables_supplement":2,
  "equations_main":6,"figure_sources":figure_pages,
  "known_scope":"Readable full Chinese section/paragraph translation. Source microtype not separately certified.",
}
write("coverage.json",json.dumps(coverage,ensure_ascii=False,indent=2)+"\n")
coverage_items="".join(f'<li>{html.escape(e["name"])}</li>' for e in coverage["sections"])
write("coverage.html",f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>DiffusionDrive · 完整翻译章节覆盖</title><link rel="stylesheet" href="style.css"></head><body class="standalone"><h1>全文翻译章节覆盖核对</h1><p>主文 11 页＋补充材料 5 页。参考文献列表不翻译；公式（1）–（6）、主文表 1–7、补充表 1–2 和全部图注均在译文中保留。下列为源章节和小节核对清单，不将标题数量冒充原文段落数量。</p><ol>{coverage_items}</ol><p>最终以 <a href="translation.md">translation.md</a>、<a href="paper.pdf">主文 PDF</a> 和 <a href="supplement.pdf">补充 PDF</a> 对照为准。</p></body></html>""")
brief=next(DST.glob("2026-09-18*DiffusionDrive-Truncated-Diffusion-Model.pdf"))
assert brief.stat().st_size>50000,"Missing independent Chinese study brief PDF"
readme=f"""# DiffusionDrive（CVPR 2025）中文全文阅读包

原制作 2026-09-18；修复 2026-11-09。仅展开文件夹，不提供 ZIP。

- [完整中文译文（Markdown）](translation.md)
- [关键解释（Markdown）](algorithms.md)
- [阅读主页（本地下载后打开）](index.html)
- [独立译文 HTML](translation.html) · [独立关键解释 HTML](algorithms.html)
- [正式论文 PDF（11 页）](paper.pdf) · [官方补充 PDF（5 页）](supplement.pdf)
- [主文与补充翻译章节覆盖核对](coverage.html)
- [独立中文学习简报 PDF]({brief.name})
- [源文件清单与哈希](manifest.json)

直接在 GitHub 查看 Markdown 和 PDF。GitHub 不运行 HTML；克隆该仓库后本地双击 index.html 即可在「原文 / 译文 / 关键解释」三项之间切换，无须服务器或在线依赖。原文共 16 页，前 11 页为 CVPR 正式论文，后 5 页为官方补充材料。

论文官方入口：{PAPER}
\n代码固定版本：{CODE}
"""
write("README.md",readme)
write("打开说明.txt",f"""DiffusionDrive 离线完整阅读包（2026-11-09 修复）
中文译文：translation.md / translation.html
关键解释：algorithms.md / algorithms.html
直接双击 index.html，切换 原文 / 译文 / 关键解释。
原文：paper.pdf（CVPR 2025 主文 11 页）+ supplement.pdf（官方补充 5 页）；pages/page-01.jpg 至 page-16.jpg。
GitHub 普通文件页面不能执行 HTML；要使用交互界面，请 git clone 后在本地打开 index.html。
所有核心页面依赖均是本地相对路径，公式渲染使用 vendor 内的 KaTeX 与字体。
本包不制作或提供 ZIP，参考文献列表不译。
""")

# Check actual embedded content and required local dependencies.
index_parsed=BeautifulSoup(index,"html.parser")
assert {p.get("id") for p in index_parsed.select(".panel")}=={"original","translation","explanation"}
assert [b.get("data-tab") for b in index_parsed.select(".tabs button")]==["original","translation","explanation"]
assert len(index_parsed.select("#original .paper-page img"))==16
assert len(index_parsed.select("#translation table"))>=9
assert len(index_parsed.select("#explanation h2"))>=10
assert "## A." not in index
for rel in re.findall(r"""(?:src|href)=["']([^"']+)""",index):
    if rel.startswith(("http:","https:","mailto:","#")):continue
    rel=rel.split("#",1)[0]
    if rel and not (DST/rel).is_file():raise RuntimeError(f"Broken relative dependency: {rel}")
for name in ("index.html","translation.html","algorithms.html"):
    page=BeautifulSoup((DST/name).read_text("utf-8"),"html.parser")
    for tag in page.select("script[src],link[href],img[src]"):
        rel=tag.get("src") or tag.get("href")
        if rel and not rel.startswith(("http:","https:","mailto:","#")):
            assert (DST/rel).is_file(),(name,rel)

# Never put the old ZIP in a deliverable manifest. Do not remove it before separate remote validation.
files={}
for f in sorted(DST.rglob("*")):
    if not f.is_file() or f.name=="manifest.json" or f.suffix.lower()==".zip" or f.name==".DS_Store":
        continue
    files[f.relative_to(DST).as_posix()]=digest(f.read_bytes())
manifest={
    "paper":"DiffusionDrive","original_date":"2026-09-18","repair_date":REPAIRED_DATE,
    "stage":"expanded_built_pending_independent_remote_audit_and_old_zip_removal",
    "delivery":"expanded GitHub tree only; no ZIP in final delivery",
    "main_pdf_pages":11,"supplement_pdf_pages":5,"page_images":16,
    "translation_md_chars":len(source),"algorithm_md_chars":len(algorithms_md),
    "files":files,"file_count":len(files),
}
write("manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"result":"built","manifest_files":len(files),"main_pdf_pages":len(main),"supplement_pages":len(extra),"main_translation_chars":len(source),"algorithms_chars":len(algorithms_md),"no_zip_generated":True},ensure_ascii=False))
