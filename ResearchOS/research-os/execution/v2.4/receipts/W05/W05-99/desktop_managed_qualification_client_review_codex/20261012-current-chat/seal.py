from pathlib import Path
import hashlib,json,subprocess,datetime

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-desktop-managed-qualification-client-20261012'
AUTHOR=OUT.parents[1]/'desktop_managed_qualification_client_codex/20261012-current-chat'
CANDIDATE='fc350c97cddbf7d54e37b88ece25b0e8be8f1d87'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))

assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()==CANDIDATE
status=subprocess.check_output(['git','status','--short','-uno'],cwd=WT)
assert not status.strip()
(OUT/'candidate-tracked-status.txt').write_bytes(status)
assert sha(AUTHOR/'source-bundle-final.json')=='f8024bfb5d835d5cf9b9584970988e6c818b413e5362d592166c518faea81617'
assert sha(AUTHOR/'receipt-manifest-final.json')=='31579e9e4c48d9e16719c3d78ea1eca8f9a161156ee64d6856f5bf8083ca2620'
review=read(OUT/'independent-review.json')
assert review['decision']=='REQUEST_CHANGES' and len(review['findings'])==2
assert review['actual_model_calls']==0 and review['external_calls']==0
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
    p=ROOT/'execution/v2.4'/name
    canon[name]=dict(sha256=sha(p),facts={k:v for k,v in read(p).items() if k in ['revision','head','status','plan_sha256','spec_manifest_sha256','manifest_sha256']})
(OUT/'main-canon-end-observation.json').write_text(json.dumps(dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon,note='Read-only observation; concurrent parent integration is outside this reviewer write scope'),indent=2)+'\n',encoding='utf-8')
excluded={
    'vite-qualification-cache':'Retained temporary bundler cache; scoped deletion was blocked by policy.',
    'smoke-user-data':'Local Electron runtime profile; private runtime state excluded from review package.',
    'smoke-data':'Local smoke runtime data; private runtime state excluded from review package.',
    'real-core-fixture-review1':'Owned zero-model Core runtime data; private credentials excluded from review package. Public protocol results are retained at receipt root.',
    'test-temp':'Temporary test runtime data excluded from review package.'
}
files=[]
for p in sorted(OUT.rglob('*')):
    rel=p.relative_to(OUT)
    if p.is_file() and p.name not in ('receipt_manifest.json','review-seal.json') and rel.parts[0] not in excluded:
        files.append(dict(path=rel.as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
manifest=dict(schema='researchos.independent-review-manifest/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='REQUEST_CHANGES',acceptance_scope='SOURCE_AND_FIXTURE_ONLY',candidate=CANDIDATE,model_calls=0,external_calls=0,excluded_retained_runtime_roots=excluded,files=files)
(OUT/'receipt_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for row in files: assert sha(OUT/row['path'])==row['sha256']
seal=dict(decision='REQUEST_CHANGES',acceptance_scope='SOURCE_AND_FIXTURE_ONLY',files=len(files),decision_sha256=sha(OUT/'independent-review.json'),manifest_sha256=sha(OUT/'receipt_manifest.json'))
(OUT/'review-seal.json').write_text(json.dumps(seal,indent=2)+'\n',encoding='utf-8')
print(json.dumps(seal))
