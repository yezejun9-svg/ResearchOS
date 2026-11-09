from pathlib import Path
import hashlib,json,subprocess,datetime
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v4-20261012'
AUTHOR=OUT.parents[1]/'normal_model_configuration_ui_repair_v4_codex/20261012-current-chat'
CANDIDATE='57ec9b4408835483bf0c4c30397968d7a11a0b2c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()==CANDIDATE
status=subprocess.check_output(['git','status','--short','-uno'],cwd=WT)
assert not status.strip()
(OUT/'candidate-tracked-status.txt').write_bytes(status)
assert sha(AUTHOR/'receipt_manifest.json')=='ece814f27447a2ec1e23acb2fcd2d18e214e858117b16206c51ee5aff448a0be'
decision=json.loads((OUT/'independent-review.json').read_text(encoding='utf-8'))
assert decision['decision']=='REQUEST_CHANGES'
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
    p=ROOT/'execution/v2.4'/name
    canon[name]=dict(sha256=sha(p),facts={k:v for k,v in json.loads(p.read_text(encoding='utf-8')).items() if k in ['revision','head','status','plan_sha256','spec_manifest_sha256','manifest_sha256']})
(OUT/'main-canon-end-observation.json').write_text(json.dumps(dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon,note='Read-only observation; concurrent parent integration is outside this reviewer write scope'),indent=2)+'\n',encoding='utf-8')
files=[]
excluded_cache_roots={'vite-cache','status-race-cache'}
for p in sorted(OUT.rglob('*')):
    rel=p.relative_to(OUT)
    if p.is_file() and p.name not in ('receipt_manifest.json','review-seal.json') and rel.parts[0] not in excluded_cache_roots:
        files.append(dict(path=rel.as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
manifest=dict(schema='researchos.independent-review-manifest/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='REQUEST_CHANGES',candidate=CANDIDATE,model_calls=0,external_calls=0,excluded_retained_cache_roots=sorted(excluded_cache_roots),files=files)
(OUT/'receipt_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for row in files:assert sha(OUT/row['path'])==row['sha256']
seal=dict(decision='REQUEST_CHANGES',files=len(files),decision_sha256=sha(OUT/'independent-review.json'),manifest_sha256=sha(OUT/'receipt_manifest.json'))
(OUT/'review-seal.json').write_text(json.dumps(seal,indent=2)+'\n',encoding='utf-8')
print(json.dumps(seal))
