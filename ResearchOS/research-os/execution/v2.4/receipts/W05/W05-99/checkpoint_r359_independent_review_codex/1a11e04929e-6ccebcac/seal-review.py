from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def write(n,v):
 with (H/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
v=json.loads((H/'verified-input-pins.json').read_bytes());r=json.loads((H/'review.json').read_bytes())
assert v['count']==192 and r['new_mechanical_errors']==0
for p in v['references']:assert pin(p['path'])==p
members={p.name:pin(p) for p in sorted(H.iterdir()) if p.is_file()}
write('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=members,base_refs=v['references'],drift_count=0))
h=dict(schema='researchos.independent-review-handoff.v1',decision=r['decision'],manifest_ref=pin(H/'MF.json'),review_ref=pin(H/'review.json'),report_ref=pin(H/'report.md'),
 counts=dict(members=len(members),files=len(members)+2,base_refs=v['count']),checkpoint_ref=r['checkpoint_ref'],
 old823prefix_preserved=True,registered_failures=829,highest_observed_ordinal=831,guard_entries_closed=159,Main_pinned_sources_unchanged=14,
 T7_compile_and_prelaunch_Source_only=True,native_case_started=0,signatures_created=0,attach_restore_fence_Source_rejected=True,legacy_Source_unaccepted=True,
 diagnostic828_full_original_input_persisted=False,diagnostic830_bootstrap_close_observed=False,diagnostic831_observed_Python_exit=None,
 new_mechanical_errors=0,counter_reset=False,authority='NONE',formal_acceptance=False,Owner_or_original_business_acceptance=False,stop=True)
write('HDF.json',h)
for p in members.values():assert pin(p['path'])==p
print(json.dumps(dict(HDF=pin(H/'HDF.json'),MF=pin(H/'MF.json'),counts=h['counts'],decision=r['decision']),ensure_ascii=True))

