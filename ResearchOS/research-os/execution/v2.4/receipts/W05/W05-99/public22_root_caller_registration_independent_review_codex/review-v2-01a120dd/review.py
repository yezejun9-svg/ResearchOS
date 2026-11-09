"""Independent finite Source review. Never calls build/register/execute/update_pair."""
import ast
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import types

N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
S=B/'public22_root_caller_registration_source_codex/p22root-20261009-02'
PREV=R/'execution/v2.4/receipts/W09/W09-99/cp370_actual_registration_independent_review_codex/actualr4-01a120ab/review.py'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,value):
 with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def mod(p):
 m=types.ModuleType('independent_'+Path(p).stem);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def refs(x):
 if type(x) is dict:
  if set(x)=={'path','sha256','bytes'}:yield x
  else:
   for v in x.values():yield from refs(v)
 elif type(x) is list:
  for v in x:yield from refs(v)
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:raise AssertionError(name)

def main():
 previous=mod(PREV);previous.N=N
 failures=[]
 for chunk,ordinal,py in [('36367b',1013,None),('92b59f',1014,1),('328b81',1015,1)]:
  if (N/('failure-'+chunk+'.actual-host.raw.jsonl')).exists():
   raw=read_capture=[json.loads(z) for z in (N/('failure-'+chunk+'.actual-host.raw.jsonl')).read_bytes().splitlines()]
   values=[json.loads(b['text']) for b in raw[-1]['payload']['output'] if b.get('text','').startswith('{')]
   result=next(v for v in values if v.get('chunk_id')==chunk)
   cap=dict(result=result,cap_ref=pin(N/('failure-'+chunk+'.actual-host.raw.jsonl')),binding_ref=pin(N/('failure-'+chunk+'.actual-host.binding.json')))
  else:cap=previous.capture(AUDIT,40928429,chunk,'failure-'+chunk)
  check('original failure actual exit '+chunk,cap['result']['exit_code']==1)
  failures.append(dict(chunk_id=chunk,Root_assigned_ordinal=ordinal,actual_outer_exit=1,actual_python_exit=py,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,original_capture_ref=cap['cap_ref'],capture_binding_ref=cap['binding_ref']))
 h=read(S/'HDF.json');mf=read(h['manifest_ref']['path']);inputs=read(h['source_inputs_ref']['path'])
 leaf=read(h['runner_review_ref']['path']);leafmf=read(leaf['manifest_ref']['path']);leafsource=read(leaf['source_hdf_ref']['path'])
 leafinputs=read(leafsource['source_inputs_ref']['path'])
 reg=mod(h['registrar_ref']['path']);caller=mod(h['caller_ref']['path'])
 guardmod=mod(reg.GUARD)
 allrefs=[pin(__file__),pin(PREV),pin(S/'HDF.json'),h['manifest_ref'],*mf['members'],*inputs['references'],*leafmf['members'],leafsource['source_inputs_ref']]
 allrefs.extend(refs(h));allrefs.extend(refs(leafsource));allrefs.extend(refs(failures))
 allrefs.extend(pin(p) for p in N.glob('guarded-read-*.json'))
 current=[pin(p) for p in reg.CANON]
 unique={};path_attribution=[]
 for ref in allrefs:
  actual=pin(ref['path'])
  check('exact held input '+Path(ref['path']).name,Path(actual['path'])==Path(ref['path']) and (actual['sha256'],actual['bytes'])==(ref['sha256'],ref['bytes']))
  if actual!=ref:path_attribution.append(dict(original_logical_ref=ref,physical_ref=actual,only_windows_path_separator_changed=True))
  unique[actual['path'].casefold()]=actual
 heldrefs=list(unique.values());guard=guardmod.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 guard.acquire(heldrefs)
 try:
  check('handed Source HDF exact',(pin(S/'HDF.json')['sha256'],pin(S/'HDF.json')['bytes'])==('de905baaed55e65c32f4cb28d887c69a11a560d600ea7a3f129a1a97341e73da',4055))
  check('handed Source MF exact',(h['manifest_ref']['sha256'],h['manifest_ref']['bytes'])==('9113793df7089b55382e7b1438360c0d4fb485c4be289eb6c6acf7bf1e2cdb34',2643))
  check('original source controls15 scoped pure',read(h['source_controls_ref']['path'])['pass']==15 and h['actual_product_processes']==0)
  before,cp,ow=reg.before();check('current CP370OW174 full4 unchanged',before==current)
  live=reg.pending(dict(path=str(reg.BASE_PENDING[0]),sha256=reg.BASE_PENDING[1],bytes=reg.BASE_PENDING[2]))
  check('pending eight immutable NULL last',[r['ordinal'] for r in live['pending']]==list(range(1005,1013)) and live['pending'][-1]['actual_outer_exit'] is None)
  check('CP pair excluded from guard after exact validation',reg.held_without_canonical_pair(current,current[:2])==current[2:])
  check('leaf accepted exact v2',leaf['decision']=='ACCEPTED_SOURCE_ONLY' and leaf['runner_ref']['sha256']==caller.EXPECTED_RUNNER[0] and leaf['contract_ref']['sha256']==caller.EXPECTED_CONTRACT[0])
  # Pure source import probes only: modules declare code; no operational entrypoint.
  imported=[]
  for ref,name in [(pin(reg.GUARD),'guard'),(pin(reg.TP),'transaction'),(inputs['references'][21],'owned_job'),(leaf['runner_ref'],'runner')]:
   loaded=caller.module(ref,'source_import_probe_'+name)
   imported.append(dict(name=name,loaded=True,has_file=hasattr(loaded,'__file__')))
  check('current loader targets import without __file__',all(x['loaded'] for x in imported),imported)
  # This exact HDF is what execute calls runner_review. Its Source inputs belong
  # to source_hdf_ref instead; direct indexing at caller241 fails before held guard.
  try:leaf['source_inputs_ref']
  except KeyError as exc:missing=dict(type=type(exc).__name__,message=str(exc))
  else:raise AssertionError('expected independently observed missing Source inputs key')
  check('caller references absent runner-review field','source_inputs_ref' not in leaf and 'source_inputs_ref' in leafsource,missing)
  contract=read(leaf['contract_ref']['path'])
  try:caller.checked(contract['source_guard'])
  except ValueError as exc:path_failure=dict(type=type(exc).__name__,message=str(exc),exact_contract_ref=contract['source_guard'],physical_ref=pin(contract['source_guard']['path']))
  else:raise AssertionError('expected path separator mismatch absent')
  check('real accepted contract slash reference rejected',path_failure['message']=='REF_CHANGED',path_failure)
  # Synthetic docs are explicitly only the transform arguments. Real Main bytes
  # are kept read-only and held; no exclusive Canon handle or TP execution.
  ref=lambda n:dict(path='D:/Synthetic/'+n,sha256=n*64,bytes=1)
  sr,orr,wr=ref('1'),ref('2'),ref('3');out='D:/Synthetic/schema22-public-'+'a'*32
  common=dict(step_id='W05-99',slice_id=reg.SLICE,state=reg.STATE,scope_ref=sr,output_root=out,owner=reg.ROOT,lease_status='ACTIVE',lease_expires_at='2099-01-01T00:00:00Z')
  docs={sr['sha256']:dict(output_root=out),orr['sha256']:dict(common,owner_id=reg.ROOT,selected_worker_id=reg.ROOT),wr['sha256']:dict(common,worker_id=reg.ROOT,selected_owner_ref=orr)}
  facts=dict(before_canonical_refs=current,scope_ref=sr,owner_ref=orr,worker_ref=wr,source_hdf_ref=ref('4'),review_decision_ref=ref('5'),created_utc='2026-10-09T00:00:00Z')
  original_read,original_pin=reg.read,reg.pin
  denied=[]
  def exclusive_sim(p):
   if Path(p) in reg.CANON[:2]:
    denied.append(str(p));raise PermissionError('SIMULATED_TP_SHAREMODE0_REOPEN_DENIED')
   return original_pin(p)
  try:
   reg.read=lambda r:copy.deepcopy(docs[r['sha256']])
   a,b=reg.transform(cp,ow,facts,ref('6'),live)
   check('normal pure projection complete prefix plus8',a['failure_counters'][:1002]==cp['failure_counters'] and len(a['failure_counters'])==1010 and a['revision']==371 and b['revision']==175)
   reg.pin=exclusive_sim
   try:reg.transform(cp,ow,facts,ref('6'),live)
   except PermissionError as exc:exclusive_failure=dict(type=type(exc).__name__,message=str(exc),attempted_paths=denied)
   else:raise AssertionError('exclusive callback unexpectedly did not reopen Canon')
  finally:reg.read=original_read;reg.pin=original_pin
  check('pure callback under modeled exclusive handle reopens CP',denied==[str(reg.CANON[0])],exclusive_failure)
  tp=reg.TP.read_text();check('actual TP has share0 then transform before close',tp.index('0,None,3,0x80,None')<tp.index('result=transform(')<tp.index('for handle in reversed(handles)'))
  source=Path(h['caller_ref']['path']).read_text();regsource=Path(h['registrar_ref']['path']).read_text()
  check('scope requires fresh lease each phase','return live_lease(*self.args)[0]' in source and 'self._fresh()' in source)
  check('end23 refused and end22 bounded',caller.PHASES==('prepare','bootstrap22','keygen22','backup22','verify22') and 'MAIN23_NOT_QUALIFIED_FOR_THIS_END22_SCOPE' in source)
  check('fresh Root postreview witness gates','ROOT_POSTREVIEW_LIVE_REFRESH' in regsource and 'ACTIVATION_WITNESS_NOT_BOUND' in regsource and 'ROOT_EXTERNAL_REVIEW_HOSTPAIR' in regsource)
  check('returned state failure persisted outside case','runner-returned-state.root.json' in source and "'last_child_exit':None" in source)
  leafcanon=[r for r in refs(leafinputs) if Path(r['path']) in reg.CANON]
  check('inventory leaf logical Canon refs',True,leafcanon)
  check('no canonical write by review',[pin(p) for p in reg.CANON]==current)
  for ref in heldrefs:check('end same input '+Path(ref['path']).name,pin(ref['path'])==ref)
 finally:cleanup=guard.close()
 check('real finite guard closed zero',cleanup['closed'] and cleanup['retained_handles_count']==0 and cleanup['errors']==[])
 gr=save('sourceguard.closed.json',cleanup);cr=save('independent-controls.json',dict(scope='FINITE_PURE_SOURCE_NO_OPERATIONAL_ENTRYPOINT',checks=checks,count=len(checks),pass_count=len(checks),fail_count=0,modeled_exclusive_boundary=True,actual_exclusive_Canon_handles=False,product_calls=0,canonical_writes=0))
 findings=[dict(id='P22-01',priority='P1',file_ref=h['registrar_ref'],line=273,summary='activate callback reopens Canon while trusted update_pair owns both files with shareMode=0',evidence=exclusive_failure,required_change='Validate expected Canon before entering TP; inside callback compare passed objects or hashes derived from TP-held before bytes, never reopen CP/OW. Keep strict full-vector check and full inverse; add finite exclusive-boundary regression.'),dict(id='P22-02',priority='P1',file_ref=h['caller_ref'],line=241,summary='Pinned accepted runner review HDF has no source_inputs_ref; execute raises KeyError before acquiring runtime guard or starting runner',evidence=dict(actual_review_hdf=h['runner_review_ref'],actual_source_hdf=leaf['source_hdf_ref'],exception=missing),required_change='Resolve source_inputs_ref through the exact accepted leaf source_hdf_ref or accepted contract binding, verify that source HDF and inputs, and include them in held closure. Add pure real-schema execution-preflight validation without product calls.')]
 findings.append(dict(id='P22-03',priority='P1',file_ref=h['caller_ref'],line=56,summary='checked rejects exact accepted contract refs solely because Windows path separators differ; guard load at caller263 cannot proceed',evidence=path_failure,required_change='Preserve historical refs; compare SHA/bytes strictly and validate canonical Windows path identity, or derive explicitly verified physical refs before passing to loader/guard. Add pure actual-contract guard and owned-job ref compatibility controls. Do not weaken byte pinning.'))
 fr=save('findings.json',dict(decision='REQUEST_CHANGES_SOURCE_ONLY',blocking_source_findings=findings,nonblocking_loader_note='Current four pinned targets import successfully despite helpers not setting __file__; no demonstrated loader blocker in these exact bytes.',no_product_execution=True))
 now=datetime.now(timezone.utc).isoformat()
 common=dict(actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=reg.AUTHOR,decision='REQUEST_CHANGES_SOURCE_ONLY',reviewed_utc=now,source_hdf_ref=pin(S/'HDF.json'),source_mf_ref=h['manifest_ref'],caller_ref=h['caller_ref'],registrar_ref=h['registrar_ref'],formal_acceptance=False,execution_grant=False,parent_acceptance=False)
 dr=save('source-decision.json',dict(common,findings_ref=fr,review_controls_ref=cr,source_guard_ref=gr,held_read_refs=len(heldrefs),original_failures=failures,current_canonical_refs=current,Root_next_observed=1016,SourceOnly=True,Main_Canon_changes=0,Native_SQLite_dispatcher_model_calls=0,leaf_canonical_input_refs=leafcanon,path_attribution=path_attribution))
 mr=save('MF.json',dict(members=[pin(S/'HDF.json'),h['manifest_ref'],dr,fr,cr,gr,pin(__file__),*list(refs(failures))],source_input_refs=heldrefs,excludes=['HDF.json','MF.json']))
 hr=save('HDF.json',dict(common,manifest_ref=mr,source_decision_ref=dr,findings_ref=fr,review_controls_ref=cr,source_guard_ref=gr,blocking_source_findings=3,held_read_refs=len(heldrefs),guard_closed=True,product_processes_executed=0,Root_actual_registration=False,STOP=True,FINAL=True))
 print(json.dumps(dict(HDF=hr,MF=mr,decision=dr,findings=fr,failures=failures),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
