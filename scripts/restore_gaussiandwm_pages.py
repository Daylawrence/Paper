#!/usr/bin/env python3
"""Restore checksum-pinned official GaussianDWM pages. Does NOT complete translation."""
import hashlib
import io
import json
import pathlib
import urllib.request
import zipfile
import fitz
from PIL import Image, ImageStat

ROOT=pathlib.Path(__file__).resolve().parents[1]
D=ROOT/"reading-packs/2026-10-28_CVPR2026_GaussianDWM"
TODAY="2026-11-02"
ZIP="2026-10-28_CVPR2026_GaussianDWM_阅读包.zip"
URLS={
    "main":("https://openaccess.thecvf.com/content/CVPR2026/papers/Deng_GaussianDWM_3D_Gaussian_Driving_World_Model_for_Unified_Scene_Understanding_CVPR_2026_paper.pdf","89faceab57ff03c0df3f803390a26f4f084432c9cff936cc69bf3d939643b87b",12),
    "supplement":("https://openaccess.thecvf.com/content/CVPR2026/supplemental/Deng_GaussianDWM_3D_Gaussian_CVPR_2026_supplemental.pdf","1af4fc2a67bffe58564df6911917c6b618f321b1b17ca8b69e43b8c0c089b74e",7),
}
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(("blob %d\0"%len(b)).encode()+b).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def download(name,url,expected,pages):
    request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(request,timeout=150) as r:data=r.read()
    assert sha(data)==expected,f"{name} official source SHA256 mismatch; refusing to replace"
    doc=fitz.open(stream=data,filetype="pdf")
    assert len(doc)==pages,(name,len(doc))
    assert all(len(p.get_text("text").strip())>100 for p in doc),f"{name}: blank official PDF page"
    return doc,dict(url=url,bytes=len(data),sha256=sha(data),pages=pages)
def render(page):
    pix=page.get_pixmap(matrix=fitz.Matrix(1.4,1.4),colorspace=fitz.csRGB,alpha=False)
    image=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
    assert max(ImageStat.Stat(image.resize((256,256))).stddev)>8,"blank raster page"
    f=io.BytesIO()
    image.save(f,"JPEG",quality=85,optimize=True,progressive=True)
    assert f.tell()>12000,"suspiciously short JPEG"
    return f.getvalue()
def run():
    assert D.is_dir()
    manifest_file=D/"manifest.json"
    manifest=json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["file_count"]==34
    sources={}
    docs={}
    for label,params in URLS.items():docs[label],sources[label]=download(label,*params)
    pages=[p for label in ("main","supplement") for p in docs[label]]
    assert len(pages)==19
    images=[render(p) for p in pages]
    assert sha(images[17])!=sha(images[18]),"pages 18 and 19 unexpectedly identical"
    merged=fitz.open()
    merged.insert_pdf(docs["main"])
    merged.insert_pdf(docs["supplement"])
    pdf=merged.tobytes(garbage=3,deflate=True)
    assert len(fitz.open(stream=pdf,filetype="pdf"))==19
    old_pdf_sha=sha((D/"paper.pdf").read_bytes())
    old_last={str(i):sha((D/"pages"/f"page-{i:02}.jpg").read_bytes()) for i in (18,19)}
    (D/"paper.pdf").write_bytes(pdf)
    for i,b in enumerate(images,1):(D/"pages"/f"page-{i:02}.jpg").write_bytes(b)
    (D/"images/supplement.jpg").write_bytes(images[12])
    for rel,obj in manifest["files"].items():
        f=D/rel
        assert f.is_file(),f"Missing original asset {rel}"
        b=f.read_bytes()
        obj.update(bytes=len(b),sha256=sha(b),git_blob_sha=blob(b))
    manifest["original_created_date"]="2026-10-28"
    manifest["last_content_repair_date"]=TODAY
    manifest["source_pdf"]="CVPR 2026 official 12-page main + 7-page supplement"
    manifest["official_source_sha256"]={k:v["sha256"] for k,v in sources.items()}
    manifest["quality_status"]="source pages restored; complete paragraph-level Chinese translation NOT passed"
    dump(manifest_file,manifest)
    zipfile_path=D/ZIP
    root_name=ZIP[:-4]
    with zipfile.ZipFile(zipfile_path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for rel in sorted([*manifest["files"],"manifest.json"]):
            z.write(D/rel,arcname=f"{root_name}/{rel}")
    with zipfile.ZipFile(zipfile_path) as z:
        assert z.testzip() is None
        assert len(z.namelist())==35
    zdata=zipfile_path.read_bytes()
    audit={
        "paper":"GaussianDWM","repair_date":TODAY,
        "original_created_date":"2026-10-28",
        "action":"restore exact official main+supplement PDF, JPEG pages 01-19, and optional ZIP",
        "sources":sources,"previous_packaged_pdf_sha256":old_pdf_sha,
        "previous_page_18_19_sha256":old_last,
        "source_pdf":{"pages":19,"bytes":len(pdf),"sha256":sha(pdf),"git_blob_sha":blob(pdf)},
        "new_page_18_sha256":sha(images[17]),"new_page_19_sha256":sha(images[18]),
        "manifest_files_updated":len(manifest["files"]),
        "zip":{"bytes":len(zdata),"sha256":sha(zdata),"git_blob_sha":blob(zdata),"crc":"passed"},
        "remote_default_branch_validation":"pending",
        "translation_quality":"not passed: paragraph-level complete translation still required",
        "delivery_status":"repairing","completed":False
    }
    dump(D/f"source-restoration-audit-{TODAY}.json",audit)
    catalog_file=ROOT/"reading-packs/catalog.json"
    catalog=json.loads(catalog_file.read_text(encoding="utf-8"))
    item=next(x for x in catalog if x.get("paper")=="GaussianDWM")
    item.update(zip_bytes=len(zdata),zip_sha256=sha(zdata),zip_git_blob_sha=blob(zdata),
        zip_remote_bytes_current_metadata=None,
        source_pdf_path=f"reading-packs/{D.name}/paper.pdf",
        source_pdf_bytes=len(pdf),source_pdf_sha256=sha(pdf),source_pdf_git_blob_sha=blob(pdf),
        repair_last_checked_date=TODAY,
        repair_status="source_pages_restored_remote_and_translation_pending",
        repair_audit_path=f"reading-packs/{D.name}/source-restoration-audit-{TODAY}.json",
        delivery_status="repairing",
        repair_note="Official pages 01-19 rebuilt from checksum-pinned CVF main and supplement. Full translation and independent remote download not yet passed.")
    dump(catalog_file,catalog)
    queue_file=ROOT/"reading-packs/repair-queue.json"
    queue=json.loads(queue_file.read_text(encoding="utf-8"))
    first=next(x for x in queue["entries"] if x["paper"]=="GaussianDWM")
    first["repair_status"]="source_pages_restored_remote_and_translation_pending"
    first["new_standard_completed"]=False
    queue["updated_date"]=TODAY
    dump(queue_file,queue)
    print(json.dumps({"restored_pages":19,"pdf_bytes":len(pdf),"zip_bytes":len(zdata),"zip_sha256":sha(zdata),"completed":False}))
if __name__=="__main__":run()
