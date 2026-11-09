"""Resolve eight review assertion schema assumptions; no product execution."""
import copy
from datetime import datetime,timezone
import runpy
from pathlib import Path
import json
N=Path(__file__).resolve().parent
x=runpy.run_path(str(N/'review.py'),run_name='definitions_only')
pin,read,save,mod=x['pin'],x['read'],x['save'],x['mod'];D=x['D'];C=x['C'];P=x['P'];PR=x['PR']
prior=read(N/'review.json');h=read(N/'HDF.json');mf=read(N/'MF.json');decision=read(N/'decision.json')
refs=[pin(__file__),pin(N/'review.py'),pin(N/'review.json'),pin(N/'HDF.json'),pin(N/'MF.json'),pin(N/'decision.json'),*mf['input_refs'],*mf['members']]
refs=list({str(Path(r['path']).resolve()):r for r in refs}.values())
g=mod(read(P/'HDF.json')['registrar_ref']['path']);guard=mod(g.GUARD).SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
guard.acquire(refs);resolutions=[]
try:
 for mode in ('build','check','activate','actual'):
  binding=read(D/f'public22.v4.{mode}.actual-host.binding.root.json');events=[json.loads(v) for v in Path(binding['original_capture_ref']['path']).read_bytes().splitlines()];call,result=events[1:]
  ok=call['payload']['call_id']==result['payload']['call_id']==binding['original_call_id'] and call['payload']['name']=='exec'
  resolutions.append(dict(prior_check='Root '+mode+' actual paired invocation',passed=ok,reason='Actual audit records normalized tool name exec. Paired call IDs exactly match.',capture_ref=binding['original_capture_ref']))
  if mode!='actual':
   ok=('register_public22.source.py\' '+mode+' \'') in call['payload']['input']
   resolutions.append(dict(prior_check='Root '+mode+' intended producer selected',passed=ok,reason='Pinned registrar receives the mode as a positional argument.',capture_ref=binding['original_capture_ref']))
 state=read(C/'runner-returned-state.root.json')
 ok=state['formal_acceptance'] is False and state['full20to24']=='OPEN' and state['schema21']=='OPEN_NO_PROGRAMME_BOUND' and state['next23to24']['code']=='MAIN_PUBLIC_23_TO_24_NOT_ADOPTED' and all(not state['publication'][k] for k in ('snapshot23','candidate23','backup23','verify23'))
 resolutions.append(dict(prior_check='formal remains false no23or24 product',passed=ok,reason='Unexecuted scopes are explicitly OPEN; next23to24 carries a non-adoption code. They are not boolean fields.',state_ref=pin(C/'runner-returned-state.root.json')))
 assert {r['prior_check'] for r in resolutions}=={r['name'] for r in prior['failed']}
 assert all(r['passed'] for r in resolutions)
 assert all(pin(r['path'])==r for r in refs)
finally:closed=guard.close()
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('resolution.source-guard.closed.json',closed)
rr=save('review-resolution.json',dict(prior_review_ref=pin(N/'review.json'),prior_decision_ref=pin(N/'decision.json'),resolutions=resolutions,all6860_checks_resolved=True,prior_artifacts_preserved=True,source_guard_ref=gr,additional_diagnostics=[dict(chunk_id='794d07',outer_exit=1,python_exit=1,native_exit=None,diagnostic='Reviewer recursively followed unrelated historical model_stream invocation ref. Narrowed to exact Canon and TP bytes; no product ran.'),dict(chunk_id='2a8f99',outer_exit=0,python_exit=0,native_exit=None,diagnostic='Eight incorrect review schema assertions; resolved by exact actual audit/state fields in this supplement.')],formal_acceptance=False,parent_acceptance=False,execution_grant=False))
decision.update(decision='QUALIFIED_REGISTRATION_AND_PUBLIC22_STOPPED_SOURCE_ORACLE_MISMATCH',registration_qualified=True,resolution_ref=rr,initial_review_preserved_ref=pin(N/'review.json'),current_main23_qualification=False,full20to24=False)
dr=save('decision.resolved.json',decision)
mr=save('MF.resolved.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(__file__),pin(N/'HDF.json'),pin(N/'MF.json'),pin(N/'decision.json'),rr,dr,gr],input_refs=refs))
h.update(reviewed_utc=datetime.now(timezone.utc).isoformat(),decision_ref=dr,manifest_ref=mr,resolution_ref=rr,source_guard_ref=gr,failed=0,checks=6860,prior_hdf_ref=pin(N/'HDF.json'),original_root_next_at_handoff=1030)
hr=save('HDF.resolved.json',h)
print(json.dumps(dict(HDF=hr,MF=mr,decision=dr,resolution=rr,checks_resolved=6860,held_refs=len(refs),failed=0,formal_acceptance=False,parent_acceptance=False),ensure_ascii=False),flush=True)
