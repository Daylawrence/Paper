#!/usr/bin/env python3
"""GaussianDWM maintenance run: rebuild current PDF brief and optional ZIP, audit offline pack.
Only infrastructure/content synchronization is automated; NEVER claim complete Chinese translation.
"""
# 2026-11-07 translation source alignment: rebuild after B/4.2/4.4/4.5 fidelity corrections.
from __future__ import annotations
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile

import fitz
from bs4 import BeautifulSoup
from weasyprint import HTML

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"reading-packs"/"2026-10-28_CVPR2026_GaussianDWM"
QUEUE=ROOT/"reading-packs"/"repair-queue.json"
CAT=ROOT/"reading-packs"/"catalog.json"
ORIGINAL="2026-10-28"
TODAY="2026-11-07"
ZIP_NAME=ORIGINAL+"_CVPR2026_GaussianDWM_阅读包.zip"
BRIEF_NAME=ORIGINAL+"_CVPR2026_GaussianDWM_中文学习简报.pdf"
TEMPLATE=ROOT/"reading-packs"/"2026-09-16_ICLR2026_DriveVLA-W0_阅读包"
REPORT=P/"offline-quality-check-2026-11-07.json"
report={"paper":"GaussianDWM","audit_date":TODAY,"original_date":ORIGINAL,
        "quality_status":"repairing","translation_completeness":"not certified; source paragraph alignment remains pending",
        "checks":{},"warnings":[]}
def mark(k,v):report["checks"][k]=v;print(k,":",v,flush=True)
def sha(data):return hashlib.sha256(data).hexdigest()
def blob(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def read(path):return path.read_text(encoding="utf-8")
def save(path,s):path.write_text(s,encoding="utf-8")
def assert_relative_refs(src,location):
    s=BeautifulSoup(read(src),"html.parser")
    missing=[]
    for tag in s.find_all(True):
        for attr in ("src","href"):
            href=tag.get(attr,"")
            if not isinstance(href,str) or not href or href.startswith(("#","data:","mailto:","https:","http:","javascript:")):continue
            v=urllib.parse.unquote(href.split("#")[0].split("?")[0])
            p=(location/v).resolve()
            if not p.is_file():missing.append(href)
    return sorted(set(missing))
def wrap_article(name,source):
    html="""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{title}</title><link rel="stylesheet" href="style.css">
    <link rel="stylesheet" href="vendor/katex.min.css"></head>
    <body class="standalone">{content}
    <script src="vendor/katex.min.js"></script>
    <script>document.querySelectorAll('.formula[data-latex]').forEach(function(el){{
    var target=el.querySelector('.formula-rendered');
    if(target && window.katex) try{{katex.render(el.getAttribute('data-latex'),target,
    {{displayMode:true,throwOnError:false,strict:'ignore'}})}}catch(e){{el.dataset.mathError=String(e)}}}});</script>
    </body></html>""".format(title=name,content=source)
    return html
# HTML standalones: preserving full embedded text while making them truly readable offline.
index=read(P/"index.html")
trans=read(P/"translation.html")
alg=read(P/"algorithms.html")
si=BeautifulSoup(index,"html.parser")
def extract_article(doc,classname):
    marker='<article class="reading '+classname+'">'
    start=doc.find(marker)
    end=doc.rfind("</article>")
    if start<0 or end<start:
        raise AssertionError("Could not extract "+classname+" article from standalone HTML")
    return doc[start:end+len("</article>")]
trans=extract_article(trans,"translation-body")
alg=extract_article(alg,"algorithms-body")
st=BeautifulSoup(trans,"html.parser")
sa=BeautifulSoup(alg,"html.parser")
assert si.select_one("#translation") and si.select_one("#explanation")
assert si.select_one("#translation").get_text(" ",strip=True)==st.get_text(" ",strip=True),"Translation content differs between standalone and index"
assert si.select_one("#explanation").get_text(" ",strip=True)==sa.get_text(" ",strip=True),"Explanation content differs between standalone and index"
mark("index_standalone_translation_content_equal",True)
mark("index_standalone_algorithms_content_equal",True)
save(P/"translation.html",wrap_article("GaussianDWM 完整中文译文（验收中）",trans))
save(P/"algorithms.html",wrap_article("GaussianDWM 关键解释（算法与公式）",alg))
# Retain the source PDF, check every intended original page exists and can be decoded.
pdf=fitz.open(P/"paper.pdf")
assert len(pdf)==19,f"Expected 19 pages, found {len(pdf)}"
for i in range(1,20):
    file=P/"pages"/f"page-{i:02d}.jpg"
    assert file.is_file() and file.stat().st_size>20000,repr(file)
mark("source_pdf_pages",len(pdf))
mark("original_jpg_pages",19)
# Raw source extraction is kept for evidence; the manually checked JSON examples are now in translation.md/html.
selected=(12,13,14,15,16,17,18,19)
slices=[]
for i in selected:
    raw=pdf[i-1].get_text("text")
    slices.append(f"===== Original PDF page {i} (unverified machine extraction) =====\n{raw}")
save(P/"supplement-source-extracted-2026-11-07.txt",
     "Source: existing checked-in CVPR 2026 GaussianDWM merged main 12 + supplementary 7 PDF.\n"
     "This is RAW page text extracted from the PDF; reading order, JSON and figures require manual visual verification.\n"
     "NOT a Chinese translation; not evidence that the associated translation is complete.\n\n"+"\n\n".join(slices)+"\n")
mark("supplement_pdf_text_extraction_pages",list(selected))
# HTML equations use the template's locally vendored KaTeX and fonts.
font_files=list((P/"vendor"/"fonts").glob("*.woff2"))
assert len(font_files)>=20, f"Missing KaTeX fonts: {len(font_files)}"
for key in ("katex.min.css","katex.min.js","auto-render.min.js"):
    assert (P/"vendor"/key).stat().st_size>100
for f in ("index.html","translation.html","algorithms.html"):
    assert not assert_relative_refs(P/f,P),f"missing refs in {f}: {assert_relative_refs(P/f,P)}"
mark("local_katex_woff2_fonts",len(font_files))
mark("local_relative_resources",True)
# Render the Chinese brief from the current explanation, with present formulas, tables and source links.
# HTML is the source; screenshots/PDF are *not* used to manufacture missing translation content.
brief=read(P/"algorithms.html")
body=BeautifulSoup(brief,"html.parser").select_one("article")
assert body
print_css="""
@page { size:A4; margin:18mm 17mm; }
body { color:#18201f; font-family:'Noto Sans CJK SC','Noto Sans CJK',sans-serif; font-size:10.4pt; line-height:1.62;}
h1 {font-size:21pt; color:#143f37;} h2 {font-size:15pt; color:#143f37; margin-top:12mm; page-break-after:avoid;}
h3 {font-size:12pt; margin-top:7mm; page-break-after:avoid;}
table {border-collapse:collapse; width:100%; font-size:8pt; margin:6pt 0;}
td,th {border:1px solid #c7d3cd; padding:4px 5px; word-break:break-word;}
th{background:#e7eee9} pre,code{font-family:'DejaVu Sans Mono',monospace;font-size:8pt}
pre{white-space:pre-wrap;background:#f3f6f2;border:1px solid #d9d1c4;padding:8pt;line-height:1.35}
a{color:#176b59} p,li{overflow-wrap:anywhere}
.note{padding:8pt;background:#edf3ef;border-left:3px solid #143f37}
table,tr,figure{break-inside:avoid}
"""
html=f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>{print_css}</style></head><body><h1>GaussianDWM — 中文学习简报</h1>
<p><strong>原制作日期：</strong>{ORIGINAL} · <strong>本次同步日期：</strong>{TODAY}
· <strong>内容状态：</strong>算法解释已同步，论文逐段译文仍在精校中，非完整验收版。</p>
<p><strong>GitHub 阅读入口：</strong>https://github.com/Daylawrence/Paper/tree/main/reading-packs/2026-10-28_CVPR2026_GaussianDWM</p>
{str(body)}</body></html>"""
out=P/BRIEF_NAME
HTML(string=html,base_url=str(P)).write_pdf(out)
check=fitz.open(out)
assert len(check)>=2 and out.stat().st_size>25000
mark("brief_pdf_pages",len(check))
mark("brief_pdf_bytes",out.stat().st_size)
# Real browser validation with existing Chrome on the GitHub runner.
browser={"attempted":True,"success":False,"reason":None}
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pl:
        exe=shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
        options={"headless":True,"args":["--no-sandbox","--allow-file-access-from-files"]}
        if exe: options["executable_path"]=exe
        b=pl.chromium.launch(**options)
        page=b.new_page(viewport={"width":1280,"height":900})
        failures=[]
        page.on("pageerror",lambda e:failures.append(str(e)))
        page.goto((P/"index.html").resolve().as_uri(),wait_until="load")
        page.locator("[data-tab='translation']").click()
        page.wait_for_timeout(300)
        tc=page.locator("#translation .katex").count()
        assert tc>=5, f"Only {tc} KaTeX formulas rendered"
        page.locator("[data-tab='explanation']").click()
        assert page.locator("#explanation").is_visible()
        page.locator("[data-tab='original']").click()
        assert page.locator("#original").is_visible()
        main=page.locator(".layout main")
        # Simulate a real user scroll; assigning scrollTop while CSS smooth scrolling is
        # active is asynchronous and previously yielded a false negative (0 or 2 px).
        main.hover()
        page.mouse.wheel(0,850)
        page.wait_for_function("document.querySelector('.layout main').scrollTop >= 100",timeout=10000)
        actual_before=main.evaluate("(x)=>x.scrollTop")
        page.locator("[data-tab='translation']").click()
        page.locator("[data-tab='original']").click()
        page.wait_for_timeout(300)
        scroll=main.evaluate("(x)=>x.scrollTop")
        assert scroll>=100 and abs(scroll-actual_before)<200,(
            f"Scroll not restored: before={actual_before}, after={scroll}")
        page.set_viewport_size({"width":390,"height":830})
        page.wait_for_timeout(200)
        aside=page.locator("aside").bounding_box()
        assert aside and aside["width"]>90
        assets=page.evaluate("Array.from(document.images).filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src)")
        # Lazy original image loading should not be counted as broken here.
        true_failures=[x for x in assets if not x.includes('/pages/')]
        assert not true_failures,(true_failures[:5])
        assert not failures,failures
        browser={"attempted":True,"success":True,"katex_equations":tc,
                 "scroll_restored_px":scroll,"narrow_sidebar_width":round(aside["width"],1),
                 "javascript_errors":failures}
        b.close()
except Exception as e:
    browser["reason"]=type(e).__name__+": "+str(e)[:350]
    report["warnings"].append("Offline browser acceptance not fully passed: "+browser["reason"])
report["browser"]=browser
mark("real_offline_browser",browser)
# Generate honest report before hashing and archiving.
report["remaining"]=[
    "source-paragraph one-to-one audit for complete main text and non-reference supplement pages",
    "finish full-source paragraph alignment beyond the visually checked page-14 QA/trajectory JSON",
    "check remaining figure labels, table cells and target boxes against source pages",
    "synchronize full paragraph translation to corresponding HTML and Markdown",
    "re-run remote immutable-commit verification after this push"
]
save(REPORT,json.dumps(report,ensure_ascii=False,indent=2)+"\n")
# Build a local manifest from the actual bytes of each expanded file; output ZIP is optional backup.
files={}
for p in sorted(P.rglob("*")):
    if not p.is_file() or p.name in {"manifest.json",ZIP_NAME}:continue
    rel=p.relative_to(P).as_posix()
    data=p.read_bytes()
    files[rel]={"bytes":len(data),"git_blob_sha":blob(data),"sha256":sha(data)}
manifest={"paper":"GaussianDWM","original_created_date":ORIGINAL,
          "repair_date":TODAY,"status":"repairing","completed":False,
          "source_template":"2026-09-16_ICLR2026_DriveVLA-W0_阅读包",
          "files":files}
save(P/"manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
zpath=P/ZIP_NAME
with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
    for p in sorted(P.rglob("*")):
        if not p.is_file() or p==zpath:continue
        arc=ZIP_NAME[:-4]+"/"+p.relative_to(P).as_posix()
        z.write(p,arc)
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(files)+1
mark("zip_bytes",zpath.stat().st_size)
mark("zip_sha256",sha(zpath.read_bytes()))
# Persist queue/catalog truthfully: still repairing unless independent audit has genuinely passed.
q=json.loads(read(QUEUE))
item=next(x for x in q["entries"] if x["paper"]=="GaussianDWM")
item["legacy_status"]="repairing"
item["new_standard_completed"]=False
item["last_repair_date"]=TODAY
item["repair_status"]="2026-11-07_offline_katex_and_brief_sync_and_asset_manifest_rebuilt_full_translation_audit_pending"
item["pending_items"]=["source_paragraph_alignment","remaining_figure_and_table_labels",
                       "remote_immutable_commit_validation"]+([] if browser["success"] else ["offline_browser_validation"])
achievement=(f"{TODAY}: rebuilt KaTeX/brief/optional ZIP with source page 14 QA and trajectory examples, "
             f"source figures 1/2, and browser verification={browser['success']}; full paragraph fidelity pending")
if achievement not in item.setdefault("partial_achievements",[]):item["partial_achievements"].append(achievement)
q["updated_date"]=TODAY
q["pending"]=sum(not e.get("new_standard_completed",False) for e in q["entries"])
save(QUEUE,json.dumps(q,ensure_ascii=False,indent=2)+"\n")
c=json.loads(read(CAT))
row=next(x for x in c if x.get("paper")=="GaussianDWM")
row.update({"delivery_status":"repairing","repair_last_checked_date":TODAY,
"zip_bytes":zpath.stat().st_size,"zip_sha256":sha(zpath.read_bytes()),
"zip_git_blob_sha":blob(zpath.read_bytes()),
"pdf_bytes":out.stat().st_size,"pdf_sha256":sha(out.read_bytes()),
"pdf_git_blob_sha":blob(out.read_bytes()),
"pdf_brief_sync_status":"8-page brief regenerated from current algorithms.html; full translation audit still pending",
"last_content_repair_date":TODAY,
"optional_zip_status":"repackaged from current expanded content at the verified workflow commit; optional backup",
"latest_offline_audit_path":"reading-packs/2026-10-28_CVPR2026_GaussianDWM/"+REPORT.name,
"quality_note":"QA and trajectory JSON on source page14 and figures on pages17/18 visually checked; KaTeX/brief/ZIP rebuilt; remaining full 19-page paragraph fidelity audit pending."})
save(CAT,json.dumps(c,ensure_ascii=False,indent=2)+"\n")
print("repair run output prepared; never set completed without semantic quality acceptance")
