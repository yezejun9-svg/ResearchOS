"""Independent Main23 v3 Source review; no Root operation or product process."""
import ast
import contextlib
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import types
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
S=B/'fresh_main23_root_caller_registration_source_codex/main23root-20261009-03'
PR=B/'fresh_main23_root_caller_registration_independent_source_review_codex/review-20261009-01'
ACTOR='codex:/root/attach_fixture_source_review';ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,obj):
 with (N/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def mod(p):
 m=types.ModuleType('review_'+Path(p).stem);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
def main():
 h=read(S/'HDF.json');mf=read(h['manifest_ref']['path']);contract=read(h['contract_ref']['path']);m=mod(h['caller_ref']['path']);source=Path(h['caller_ref']['path']).read_bytes();tree=ast.parse(source)
 old=read(PR/'HDF.json');builder=m.builder_chain();inputs=read(h['source_inputs_ref']['path']);base=read(h['base_hdf_ref']['path'])
 refs=[pin(__file__),pin(S/'HDF.json'),h['manifest_ref'],*mf['members'],*inputs['references'],h['base_hdf_ref'],h['base_mf_ref'],base['caller_ref'],pin(PR/'HDF.json'),old['decision_ref'],old['findings_ref'],m.GUARD_REF,m.TP_REF,*builder['refs'],*[pin(p) for p in m.CANON]]
 for pair in h['actual_source_hostpairs']:refs.extend((pair['raw_ref'],pair['binding_ref']))
 refs.extend(inputs['real_identity_mapping_receipt_refs'])
 refs=m.local_refs(refs);guard=m.guard_primitives().SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 before=[pin(p) for p in m.CANON];guard.acquire(refs)
 try:
  check('exact task52 HDF MF caller pins',pin(S/'HDF.json')['sha256']=='6ea62e31e8a8b50ac1685bee9e19b639e7df1417a1a18421fc755a0bd4b0525b' and h['manifest_ref']['sha256']=='6ede7ac360b4f71f086872a8e1ee2e7097187dd16dd6618ddc17c8ea0d296872' and h['caller_ref']['sha256']=='c72ba84cde5cbbc6cc55cd25322d2faa49b34981f5fd88ce7b746275d2af336b')
  check('reviewer independent caller builder authors',ACTOR not in (m.ROOT,m.CALLER_AUTHOR,m.BUILDER_AUTHOR) and h['source_author']==m.CALLER_AUTHOR and h['builder_source_author']==m.BUILDER_AUTHOR)
  check('contract actual caller pin',m.same_ref(contract['caller_ref'],h['caller_ref']) and m.same_ref(contract['registrar_ref'],h['registrar_ref']) and m.same_ref(contract['source_inputs_ref'],h['source_inputs_ref']))
  check('current Source old findings R1 R2 preserved',[f['id'] for f in read(old['findings_ref']['path'])['findings']]==['R1','R2'])
  inv=read(h['inverse_ref']['path']);prior=Path(inv['base_caller_ref']['path']).read_bytes()
  check('v3 exact identity-only delta and inverse',source.count(inv['new_utf8'].encode())==1 and source.replace(inv['new_utf8'].encode(),inv['old_utf8'].encode(),1)==prior and source[:inv['offset_bytes']]==prior[:inv['offset_bytes']])
  # Independently run the current v3 22 controls, omitting publication only.
  p=S/'source_controls.py';ctl=ast.parse(p.read_bytes());stop=next(i for i,n in enumerate(ctl.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='result' for t in n.targets))
  env={'__file__':str(p),'__name__':'independent_finite_controls'};exec(compile(ast.Module(body=ctl.body[:stop+1],type_ignores=[]),str(p),'exec'),env)
  check('current v3 original22 finite controls',len(env['rows'])==22 and all(r['pass'] and r.get('result',True) is not False for r in env['rows']))
  # Current v3 targeted controls retain exact caller but write their disposable
  # synthetic fixtures and report solely in this new review namespace.
  targeted=mod(S/'source_controls_v3.py');targeted.Q=N;targeted.CALLER=Path(h['caller_ref']['path'])
  sink=io.StringIO()
  with contextlib.redirect_stdout(sink):targeted.main()
  tr=read(N/'source-controls.v3.final.json')
  check('current v3 45 provenance controls',tr['passed']==45 and tr['failed']==0 and tr['synthetic_audit_resources_deleted'])
  # Actual backend rows are never synthesized. Pin/check their original Root
  # audit offsets; evaluate the exact production envelope predicate.
  real=read(h['real_Root_peer_mapping_ref']['path']);raw=Path(real['original_receipt_raw_ref']['path']).read_bytes();lines=raw.splitlines(keepends=True)
  bind=dict(schema='researchos.root-actual-peer-capture-binding.v2',issued_by=m.ROOT,root_thread_id=m.ROOT_THREAD,original_capture_ref=real['original_receipt_raw_ref'],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],source_line_bytes=[len(x) for x in lines],source_line_offsets=real['source_line_offsets'],source_prefix_size_observed=real['source_prefix_size_observed'],source_audit_path=m.ROOT_AUDIT_LOG)
  first,last=m.original_capture_rows(bind,raw,peer=True)
  fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='validate_peer_delivery')
  expr=next(n.args[0] for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='need' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='ACTUAL_PEER_DELIVERY_REQUIRED')
  gate=compile(ast.Expression(expr),'real-peer-source-predicate','eval')
  admit=lambda f,l,actor:eval(gate,m.__dict__,dict(first=f,last=l,payload=l['payload'],peer_actor=actor))
  check('actual Root original peer envelope matches production predicate',admit(first,last,real['canonical_peer_actor']))
  check('actual backend /root actor mapped canonically',last['payload']['author']==real['canonical_peer_actor'].removeprefix('codex:'))
  check('wrong actual peer rejected',not admit(first,last,ACTOR))
  forged=copy.deepcopy(last);forged['metadata']['client_authored']=True;check('client authored injection rejected',not admit(first,forged,real['canonical_peer_actor']))
  try:m.original_capture_rows(dict(bind,root_thread_id='wrong-root-thread'),raw,peer=True)
  except ValueError as e:check('wrong Root thread rejected',str(e)=='EXTERNAL_ROOT_CAPTURE_IDENTITY')
  else:check('wrong Root thread rejected',False)
  try:m.validate_peer_delivery(None,[],m.BUILDER_AUTHOR,'SOURCE_REVIEW_WITNESS')
  except ValueError as e:check('builder author remains excluded',str(e)=='ACTUAL_NONAUTHOR_PEER_REQUIRED')
  else:check('builder author remains excluded',False)
  for pair in h['actual_source_hostpairs']:
   b=read(pair['binding_ref']['path']);rows=Path(pair['raw_ref']['path']).read_bytes().splitlines(keepends=True)
   with Path(b['source_audit_path']).open('rb') as f:
    actual=[]
    for offset,size in zip(b['source_line_offsets'],b['source_line_bytes']):f.seek(offset);actual.append(f.read(size))
   check('Source author exact original hostpair '+Path(pair['raw_ref']['path']).name,rows==actual and [hashlib.sha256(x).hexdigest() for x in rows]==b['source_line_sha256'])
   sh=json.loads(rows[0])['payload'];check('Source author actual identity '+Path(pair['raw_ref']['path']).name,sh['id']==h['source_thread_id'] and sh['source']['subagent']['thread_spawn']['agent_path']=='/root/backup_regression_resources')
  # Verify strong typed provenance is production-wired before resource loading.
  functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
  text={k:ast.unparse(v) for k,v in functions.items()}
  check('R1 no digest substring acceptance', 'EXTERNAL_PAIR_DOES_NOT_BIND_REVIEW_REFS' in text['validate_root_capture'] and 'exact_ref_set(observed.get' in text['validate_root_capture'] and 'structured_documents' in text['validate_root_capture'])
  check('R1 real audit checked in Root and peer parsers','original_capture_rows' in text['validate_root_capture'] and 'original_capture_rows' in text['validate_peer_delivery'])
  check('R2 provenance before native module loading',text['runtime_closure'].index('runtime_review_chain')<text['runtime_closure'].index('load(contract'))
  check('R2 both independent peer and Root issuance required','validate_peer_delivery' in text['runtime_review_chain'] and 'validate_root_capture' in text['runtime_review_chain'] and 'QUALIFICATION_PAYLOAD_EXACT_BINDING' in text['runtime_review_chain'])
  check('runtime closure required registration and execute','runtime_closure' in text['register'] and 'runtime_closure' in text['execute'])
  check('registration TP callback no IO', {n.func.id for fn in ast.walk(functions['register']) if isinstance(fn,ast.FunctionDef) and fn.name=='transform' for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}=={'need','projection'})
  check('v3_source_Runtime_still_unissued',h['actual_future_qualification_ref'] is None and h['actual_request_ref'] is None and h['actual_registration_ref'] is None and h['formal_acceptance'] is False)
  for r in refs:check('held exact '+r['path'],m.same_ref(pin(r['path']),r))
  check('full current Canon unchanged',before==[pin(p) for p in m.CANON])
 finally:closed=guard.close()
 check('Source guard closed 0 errors',closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[] and closed['verification']=='PASSED')
 gr=save('source-guard.closed.json',closed);failed=[c for c in checks if not c['passed']]
 cr=save('finitechecks.json',dict(checks=checks,failed=failed,author22_independently_reproduced=22,targeted45_independently_reproduced=45,actual_mapping_controls=6,synthetic_runtime_qualification_only=True,actual_runtime_qualification=False,actual_registration=False,product_processes=0,Source_guard_ref=gr,diagnostics=[dict(original=1046,chunk='8e1773',outer_exit=0,python_exit=None,native_exit=None,diagnostic='read-only old decision filename missing; corrected via old HDF actual decision_ref')]))
 dr=save('decision.json',dict(schema='researchos.main23-root-independent-source-decision.v3',review_author=ACTOR,source_author=h['source_author'],builder_source_author=h['builder_source_author'],root_thread_id=ROOT_THREAD,independent_non_author=True,verdict='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION' if not failed else 'CHANGES_REQUIRED',source_hdf_ref=pin(S/'HDF.json'),source_mf_ref=h['manifest_ref'],caller_ref=h['caller_ref'],registrar_ref=h['registrar_ref'],calling_contract_ref=h['contract_ref'],source_inputs_ref=h['source_inputs_ref'],prior_changes_required_ref=old['decision_ref'],R1='RESOLVED_TYPED_COMPLETE_REFS_AND_ACTUAL_ROOT_AUDIT',R2='RESOLVED_PINNED_REVIEW_CHAIN_ACTUAL_PEER_AND_ROOT_ISSUANCE',v3_backend_actor_mapping='VERIFIED_AGAINST_REAL_BACKEND_ENVELOPE',finitechecks_ref=cr,Source_guard_ref=gr,blocking_findings=failed,actual_runtime_qualification_ref=None,actual_request_ref=None,execution_grant=False,formal_acceptance=False,parent_acceptance=False))
 mr=save('MF.json',dict(schema='researchos.main23-independent-source-review-manifest.v3',members=[pin(__file__),dr,cr,gr,pin(N/'source-controls.v3.final.json')],input_refs=refs))
 hr=save('HDF.json',dict(schema='researchos.main23-root-independent-source-hdf.v3',status='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION' if not failed else 'SOURCE_CHANGES_REQUIRED',review_author=ACTOR,source_author=h['source_author'],builder_source_author=h['builder_source_author'],root_thread_id=ROOT_THREAD,independent_non_author=True,reviewed_utc=datetime.now(timezone.utc).isoformat(),source_hdf_ref=pin(S/'HDF.json'),source_mf_ref=h['manifest_ref'],caller_ref=h['caller_ref'],registrar_ref=h['registrar_ref'],calling_contract_ref=h['contract_ref'],manifest_ref=mr,source_decision_ref=dr,finitechecks_ref=cr,Source_guard_ref=gr,checks=len(checks),held_refs=len(refs),blocking_findings=len(failed),actual_runtime_qualification_ref=None,execution_grant=False,formal_acceptance=False,parent_acceptance=False))
 print(json.dumps(dict(HDF=hr,MF=mr,decision=dr,checks=len(checks),held_refs=len(refs),failed=failed),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
