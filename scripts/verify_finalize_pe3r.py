#!/usr/bin/env python3
"""Verify immutable uploaded PE3R expanded files, then mark complete and remove old ZIP."""
import pathlib,requests,json,hashlib,time,os,base64
ROOT=pathlib.Path(__file__).resolve().parents[1]
R=ROOT/'reading-packs'
D=R/'2026-09-21_CVPR2026_PE3R'
repo='Daylawrence/Paper'
token=os.environ['GH_TOKEN']
sess=requests.Session()
sess.headers.update({'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'PE3R-repaired-pack-verification'})
manifest=json.loads((D/'manifest.json').read_text('utf-8'))
files={f['path']:f for f in manifest['files']}
assert len(files)>=30,len(files)
prefix='reading-packs/2026-09-21_CVPR2026_PE3R/'
tree={}
for attempt in range(6):
    r=sess.get(f'https://api.github.com/repos/{repo}/git/trees/main',params={'recursive':1},timeout=60)
    r.raise_for_status()
    t=r.json()
    tree={i['path'][len(prefix):]:i for i in t['tree'] if i.get('type')=='blob' and i['path'].startswith(prefix)}
    if all(p in tree and tree[p]['sha']==v['git_blob_sha'] for p,v in files.items()):
        break
    time.sleep(3)
issues=[]
for path,item in files.items():
    t=tree.get(path)
    if not t or t.get('size')!=item['bytes'] or t.get('sha')!=item['git_blob_sha']:
        issues.append(f'{path}: Git main tree missing/size/SHA mismatch')
        continue
    r=sess.get(f"https://api.github.com/repos/{repo}/git/blobs/{t['sha']}",timeout=100)
    r.raise_for_status()
    blob=r.json()
    b=base64.b64decode(blob['content'])
    if len(b)!=item['bytes'] or hashlib.sha256(b).hexdigest()!=item['sha256']:
        issues.append(f'{path}: remote fetched actual byte/SHA256 mismatch')
report={'paper':'PE3R','check_date':'2026-11-10','main_pages':11,'official_supplement_pages':2,
        'files_requested':len(files),'files_verified':len(files)-len(issues),'issues':issues,
        'verification':'main branch git-tree blob SHA + actual fetched blob size & SHA256',
        'translation':'CVPR2026 formal main non-reference full text plus official supplemental sections 6 and 7, formulas 8-17 and tables 8-11',
        'browser_audit':'offline-browser-audit-2026-11-10.json',
        'status':'passed' if not issues else 'failed'}
(D/'remote-verification-2026-11-10.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps(report,ensure_ascii=False))
if issues:raise RuntimeError('Remote verification failed; do not mark completed.')
assert (D/'translation.md').stat().st_size>12000
assert '7.4 迭代细化' in (D/'translation.md').read_text('utf-8')
assert len(list((D/'pages').glob('page-*.jpg')))==11
assert len(list((D/'supplement-pages').glob('page-*.jpg')))==2
assert (D/'offline-browser-audit-2026-11-10.json').is_file()
queue=R/'repair-queue.json'
q=json.loads(queue.read_text('utf-8'))
e=next(i for i in q['entries'] if i['paper']=='PE3R')
assert not e.get('new_standard_completed')
e.update({'legacy_status':'completed',
 'repair_status':'2026-11-10_completed_main_plus_official_supplement_full_translation_offline_html_no_zip',
 'new_standard_completed':True,'last_repair_date':'2026-11-10','completed_date':'2026-11-10','pending_items':[],
 'completion_basis':'CVPR2026 11-page main + 2-page official supplemental PDF, non-reference full Chinese translation including tables 1-11 and equations 1-17; HTML/MD, offline browser, remote per-blob bytes/SHA256',
 'completion_path':str(D.relative_to(ROOT)),
 'completion_report_path':str((D/'remote-verification-2026-11-10.json').relative_to(ROOT))})
q['updated_date']='2026-11-10'
q['pending']=sum(not x.get('new_standard_completed',False) for x in q['entries'])
queue.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n','utf-8')
catalog=R/'catalog.json'
c=json.loads(catalog.read_text('utf-8'))
ce=next(x for x in c if x.get('paper')=='PE3R')
for key in list(ce):
    if 'zip' in key.lower():ce.pop(key)
ce.update({'directory':str(D.relative_to(ROOT)),'repair_date':'2026-11-10','completed_date':'2026-11-10',
 'delivery_status':'completed','delivery_format':'fully_expanded_no_zip','new_standard_completed':True,
 'source_version':'CVPR2026 official main 11 pages + official supplementary 2 pages',
 'original_pdf_path':str((D/'paper.pdf').relative_to(ROOT)),
 'supplement_pdf_path':str((D/'supplement.pdf').relative_to(ROOT)),
 'main_translation_path':str((D/'translation.md').relative_to(ROOT)),
 'translation_html_path':str((D/'translation.html').relative_to(ROOT)),
 'index_html_path':str((D/'index.html').relative_to(ROOT)),
 'algorithm_md_path':str((D/'algorithms.md').relative_to(ROOT)),
 'algorithm_html_path':str((D/'algorithms.html').relative_to(ROOT)),
 'coverage_path':str((D/'coverage.html').relative_to(ROOT)),
 'manifest_path':str((D/'manifest.json').relative_to(ROOT)),
 'audit_path':str((D/'remote-verification-2026-11-10.json').relative_to(ROOT)),
 'expanded_files_verified':len(files)})
catalog.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n','utf-8')
readme=R/'README.md'
old=readme.read_text('utf-8')
old=old.replace('2026-09-21_CVPR2026_PE3R_阅读包.zip','PE3R 已改为完整展开目录')
intro=('## 2026-11-10：PE3R 全文译文与官方补充材料已修复\n\n'
 '[主文及补充材料完整中文译文](2026-09-21_CVPR2026_PE3R/translation.md) · '
 '[关键解释](2026-09-21_CVPR2026_PE3R/algorithms.md) · '
 '[11 页主文 PDF](2026-09-21_CVPR2026_PE3R/paper.pdf) · '
 '[2 页补充 PDF](2026-09-21_CVPR2026_PE3R/supplement.pdf) · '
 '[HTML 展开目录](2026-09-21_CVPR2026_PE3R/) · '
 '[独立远端审计](2026-09-21_CVPR2026_PE3R/remote-verification-2026-11-10.json)。\n\n'
 '原文、译文、关键解释三个阅读选项；参考文献列表不翻译；在线直接读 Markdown，克隆后本地打开 index.html。此篇已删除旧 ZIP。\n\n---\n\n')
if intro not in old:old=old.replace('\n', '\n\n'+intro,1)
readme.write_text(old,'utf-8')
oldzip=D/'2026-09-21_CVPR2026_PE3R_阅读包.zip'
assert oldzip.exists()
oldzip.unlink()
print(json.dumps({'completed':'PE3R','pending':q['pending'],'legacy_zip_deleted':True}))
