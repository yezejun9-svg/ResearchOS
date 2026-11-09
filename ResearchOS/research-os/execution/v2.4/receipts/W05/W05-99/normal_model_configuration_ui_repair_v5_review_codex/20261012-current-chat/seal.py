from pathlib import Path
import hashlib,json,subprocess,datetime
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v5-20261012'
AUTHOR=OUT.parents[1]/'normal_model_configuration_ui_repair_v5_codex/20261012-current-chat'
V4=OUT.parents[1]/'normal_model_configuration_ui_repair_v4_review_codex/20261012-current-chat'
CANDIDATE='1c761174cabdd5be6fc95218eeaa502cd8c6c3f1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()==CANDIDATE
status=subprocess.check_output(['git','status','--short','-uno'],cwd=WT)
assert not status.strip()
(OUT/'candidate-tracked-status.txt').write_bytes(status)
assert sha(AUTHOR/'receipt_manifest.json')=='0a9143a104ab913ed2c759c1f3ec5ff6d9662083a20fd751570f67e41ef35e13'
assert read(OUT/'independent-review.json')['decision']=='ACCEPT'
assert sha(V4/'receipt_manifest.json')=='883c77020ca482a6ece9eaab46f1cddaba7862d719063eda3cd4532966aa83c1'
prior=next(row for row in read(V4/'receipt_manifest.json')['files'] if row['path']=='surface-comparison.json')
assert sha(V4/prior['path'])==prior['sha256']
(OUT/'prior-v4-surface-comparison.json').write_bytes((V4/prior['path']).read_bytes())
assert len(read(OUT/'status-race-results.json')['facts'])==3
assert all(f['repaired'] and not f['pageErrors'] for f in read(OUT/'status-race-results.json')['facts'])
assert len(read(OUT/'status-barrier-results.json')['facts'])==2
assert all(f['passed'] for f in read(OUT/'status-barrier-results.json')['facts'])
descriptor=read(OUT/'bound-descriptor.json')
assets={row['sha256'] for row in descriptor['compiled_React_asset_inventory']}
assert all(row['sha256'] in assets for row in read(OUT/'status-race-results.json')['servedAssets'])
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
    p=ROOT/'execution/v2.4'/name;canon[name]=dict(sha256=sha(p),facts={k:v for k,v in read(p).items() if k in ['revision','head','status','plan_sha256','spec_manifest_sha256','manifest_sha256']})
(OUT/'main-canon-end-observation.json').write_text(json.dumps(dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon,note='Read-only observation; concurrent parent integration is outside this reviewer write scope'),indent=2)+'\n',encoding='utf-8')
files=[]
excluded={'vite-cache','status-race-cache'}
for p in sorted(OUT.rglob('*')):
    rel=p.relative_to(OUT)
    if p.is_file() and p.name not in ('receipt_manifest.json','review-seal.json') and rel.parts[0] not in excluded:
        files.append(dict(path=rel.as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
manifest=dict(schema='researchos.independent-review-manifest/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='ACCEPT',acceptance_scope='SOURCE_AND_FIXTURE_ONLY',candidate=CANDIDATE,model_calls=0,external_calls=0,excluded_retained_cache_roots=sorted(excluded),files=files)
(OUT/'receipt_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for row in files:assert sha(OUT/row['path'])==row['sha256']
seal=dict(decision='ACCEPT',acceptance_scope='SOURCE_AND_FIXTURE_ONLY',files=len(files),decision_sha256=sha(OUT/'independent-review.json'),manifest_sha256=sha(OUT/'receipt_manifest.json'))
(OUT/'review-seal.json').write_text(json.dumps(seal,indent=2)+'\n',encoding='utf-8')
print(json.dumps(seal))
