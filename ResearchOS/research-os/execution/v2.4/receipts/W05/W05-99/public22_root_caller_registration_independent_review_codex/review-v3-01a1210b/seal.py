import json
from pathlib import Path
import runpy
N=Path(__file__).resolve().parent
x=runpy.run_path(str(N/'review.py'),run_name='seal_definitions');pin,read,save=x['pin'],x['read'],x['save']
previous=x['mod'](x['R']/'execution/v2.4/receipts/W09/W09-99/cp370_actual_registration_independent_review_codex/actualr4-01a120ab/review.py');previous.N=N
audit=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
cap=previous.capture(audit,40928429,'88a15e','review-complete');assert cap['result']['exit_code']==0
lines=cap['result']['output'].splitlines();published=json.loads(lines[0]);assert lines[-1]=='ROOT_SOURCE_PYTHON_EXIT=0'
refs=[pin(N/k) for k in ('HDF.json','MF.json','source-decision.json','findings.json','independent-controls.json','sourceguard.closed.json','review.py','seal.py')]
for k,n in [('HDF','HDF.json'),('MF','MF.json'),('decision','source-decision.json'),('findings','findings.json')]:assert published[k]==pin(N/n)
refs.extend((cap['cap_ref'],cap['binding_ref']))
guardmod=x['mod'](x['B']/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py');guard=guardmod.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs)
try:
 binding=read(cap['binding_ref']['path']);raw=Path(cap['cap_ref']['path']).read_bytes().splitlines(keepends=True)
 assert len(raw)==3
 with audit.open('rb') as f:
  for offset,b in zip(binding['source_line_offsets'],raw):f.seek(offset);assert f.read(len(b))==b
 d=read(N/'source-decision.json');g=read(N/'sourceguard.closed.json');c=read(N/'independent-controls.json')
 assert all(pin(r['path'])==r for r in d['current_canonical_refs'])
 assert g['closed'] and g['retained_handles_count']==0 and g['errors']==[]
 assert all(z['passed'] for z in c['checks'])
 for r in refs:assert pin(r['path'])==r
finally:closed=guard.close()
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('seal-sourceguard.closed.json',closed)
sr=save('complete-hostpair-seal.json',dict(decision='REQUEST_CHANGES_SOURCE_ONLY',review_refs={k:published[k] for k in ('HDF','MF','decision','findings')},actual_review_host_capture_ref=cap['cap_ref'],actual_review_host_binding_ref=cap['binding_ref'],actual_outer_exit=0,actual_python_exit=0,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,source_guard_ref=gr,checks=c['count'],read_refs_held=d['held_read_refs'],blocking_findings=1,new_original_failures=[],Root_next_observed=1017,canonical_unchanged=True,formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(seal=sr,HDF=published['HDF'],MF=published['MF'],decision=published['decision'],host_capture=cap['cap_ref'],host_binding=cap['binding_ref']),ensure_ascii=False),flush=True)
