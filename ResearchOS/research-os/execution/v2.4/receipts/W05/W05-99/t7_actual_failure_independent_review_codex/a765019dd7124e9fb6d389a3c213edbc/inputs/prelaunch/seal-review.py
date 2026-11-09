from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def write(name,v):
 with (H/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
v=json.loads((H/'verified-input-pins.json').read_bytes());review=json.loads((H/'review.json').read_bytes())
assert v['count']==4188 and review['copied_public_evidence_count']==16
for r in v['references']:assert pin(r['path'])==r
for pair in review['copies']:
 a=pin(pair['original_ref']['path']);b=pin(pair['copied_ref']['path'])
 assert a==pair['original_ref'] and b==pair['copied_ref'] and a['sha256']==b['sha256'] and a['bytes']==b['bytes']
members={p.relative_to(H).as_posix():pin(p) for p in sorted(H.rglob('*')) if p.is_file()}
write('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=members,base_refs=v['references'],copied_public_evidence_count=16,drift_count=0))
handoff=dict(schema='researchos.independent-review-handoff.v1',decision=review['decision'],
 manifest_ref=pin(H/'MF.json'),review_ref=pin(H/'review.json'),report_ref=pin(H/'report.md'),
 counts=dict(members=len(members),files=len(members)+2,base_refs=v['count'],copied_public_files=16),
 harness_config_ref=review['harness_config_ref'],controller_config_ref=review['controller_config_ref'],
 exact_server_API_inverse=True,frozen_input_count=4084,public_config_guard_closed=15,bootstrap_guard_closed=101,config_guard_closed=4084,
 Source_single_positive_prelaunch_can_proceed=True,future_actual_results_required_before_launch=False,
 diagnostic830_preserved=True,diagnostic830_bootstrap_closure_observed=False,diagnostic830_OS_exit_release_inference_only=True,
 new_mechanical_errors=0,counter_reset=False,authority='NONE',native_execution=False,native_acceptance=False,Owner_acceptance=False,formal_acceptance=False,stop=True)
write('HDF.json',handoff)
for r in members.values():assert pin(r['path'])==r
print(json.dumps(dict(HDF=pin(H/'HDF.json'),MF=pin(H/'MF.json'),counts=handoff['counts'],decision=review['decision']),ensure_ascii=True))

