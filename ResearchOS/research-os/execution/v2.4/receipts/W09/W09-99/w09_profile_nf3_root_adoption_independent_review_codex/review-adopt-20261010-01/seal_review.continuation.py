"""Seal Task78 Source-only review and verify published exact review prefix."""
import ast,copy,hashlib,json,types
from datetime import datetime,timezone
from pathlib import Path
D=Path(__file__).resolve().parent
S=D.parent.parent/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-01'
ACTOR='codex:/root/full_w09_source_review';THREAD='01a1215b-7210-7613-b033-756b9d553b83'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
LOG=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T23-50-03-01a1215b-7210-7613-b033-756b9d553b83.jsonl')
def pin(path):
 p=Path(path);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(path):return json.loads(Path(path).read_bytes())
def verify(ref):
 assert pin(ref['path'])==ref;return Path(ref['path']).read_bytes()
def save(name,value):
 with (D/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(D/name)
def module(path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(Path(path).read_bytes(),str(path),'exec'),m.__dict__);return m
def docs(value):
 result=[]
 if type(value) is dict:
  result.append(value)
  for x in value.values():result.extend(docs(x))
 elif type(value) is list:
  for x in value:result.extend(docs(x))
 elif type(value) is str:
  try:result.extend(docs(json.loads(value)))
  except (ValueError,TypeError):pass
 return result
def source_hosts(h):
 index=doc(h['actual_source_host_pairs_ref']['path']);result=[]
 for entry in index['captures']:
  raw=verify(entry['raw_ref']);b=doc(entry['binding_ref']['path']);verify(entry['binding_ref'])
  assert b['original_capture_ref']==entry['raw_ref']
  lengths=b['source_line_lengths'];offsets=b['source_line_offsets'];hashes=b['source_line_sha256']
  lines=raw.splitlines(keepends=True);assert len(lines)==3 and [len(x) for x in lines]==lengths and [hashlib.sha256(x).hexdigest() for x in lines]==hashes
  with Path(b['source_audit_path']).open('rb') as f:
   for offset,line in zip(offsets,lines):f.seek(offset);assert f.read(len(line))==line
  header,call,returned=[json.loads(x) for x in lines]
  assert header['payload']['id']==h['source_thread_id'] and call['payload']['call_id']==returned['payload']['call_id']==b['original_call_id']
  if b['chunk_id'] is not None:
   values=[x for x in docs(returned['payload']['output']) if x.get('chunk_id')==b['chunk_id']]
   assert len(values)==1 and values[0]['exit_code']==b['outer_exit']==0
   assert "pythoncore-3.14-64/python.exe' -I -S -B -X utf8" in call['payload']['input']
  else:assert entry['key']=='original1090' and b['outer_exit'] is None and b['Python_exit'] is None
  assert b['actual_Go_exit'] is None and b['actual_Native_exit'] is None and b['actual_SQL_exit'] is None
  result.append(dict(key=entry['key'],raw_ref=entry['raw_ref'],binding_ref=entry['binding_ref'],actual_three_original_lines_verified=True,outer_exit=b['outer_exit'],Source_binding_claimed_Python_exit=b['Python_exit'],independent_observed_Python_exit=None,inner_exit_marker_present=False))
 return result
def own_host(chunk):
 size=LOG.stat().st_size;calls={};found=[]
 with LOG.open('rb') as f:
  header=f.readline();assert json.loads(header)['payload']['id']==THREAD
  start=max(0,size-64*1024*1024);f.seek(start)
  if start:f.readline()
  while f.tell()<size:
   offset=f.tell();raw=f.readline();row=json.loads(raw);payload=row.get('payload',{})
   if payload.get('type')=='custom_tool_call':calls[payload['call_id']]=(offset,raw,row)
   if payload.get('type')=='custom_tool_call_output':
    matches=[x for x in docs(payload.get('output')) if x.get('chunk_id')==chunk]
    if matches:found.append((calls[payload['call_id']],(offset,raw,row),matches))
 assert len(found)==1 and len(found[0][2])==1
 call,result,values=found[0];assert values[0]['exit_code']==0 and 'Python_exit=0' in values[0]['output']
 lines=[header,call[1],result[1]];offsets=[0,call[0],result[0]]
 with LOG.open('rb') as f:
  for offset,line in zip(offsets,lines):f.seek(offset);assert f.read(len(line))==line
 raw_path=D/('actual-independent-'+chunk+'.raw.jsonl')
 with raw_path.open('xb') as f:f.write(b''.join(lines))
 raw_ref=pin(raw_path)
 binding_ref=save('actual-independent-'+chunk+'.binding.json',dict(schema='researchos.independent-source-host-binding.v1',actor_id=ACTOR,actor_thread_id=THREAD,
  source_audit_path=str(LOG),source_prefix_size_observed=size,source_line_offsets=offsets,source_line_bytes=[len(x) for x in lines],source_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],
  actual_call_id=call[2]['payload']['call_id'],actual_chunk_id=chunk,raw_ref=raw_ref,outer_tool_exit=0,python_exit=0,native_process_exit=None,go_process_exit=None,sqlite_process_exit=None,dispatcher_exit=None,model_call_exit=None,
  actual_product_calls=0,execution_grant=False,formal_acceptance=False))
 return dict(raw_ref=raw_ref,binding_ref=binding_ref)
def rejected(core,decision,href,mref,bindings,changes):
 candidate=copy.deepcopy(decision);candidate.update(changes)
 try:core.validate_own_review(candidate,href,mref,bindings)
 except ValueError as exc:return 'OWN_NONAUTHOR_REVIEW_NO_GRANT' in str(exc)
 return False
def main():
 h=doc(S/'HDF.json');mf=doc(S/'MF.json');p=doc(h['input_pins_ref']['path']);pins=p['refs']
 reg=module(h['caller_ref']['path'],'Task78_seal_registrar_readonly');core=module(h['core_ref']['path'],'Task78_seal_core_values');gm=module(pins['guard']['path'],'Task78_seal_guard')
 href=reg.pin(S/'HDF.json');mref=h['manifest_ref'];assert mref==reg.pin(S/'MF.json')
 bindings={k:h[k] for k in ('caller_ref','core_ref','main_pair_ref','contract_ref')}
 assert all(reg.pin(S/name)==bindings[k] for k,name in {'caller_ref':'register_w09_adoption.source.py','core_ref':'adoption_core.source.py','main_pair_ref':'main_pair_bytes.source.py','contract_ref':'root-calling-contract.source.json'}.items())
 resolved=doc(D/'finite-Source-checks.resolved.json');assert resolved['continuation_failed']==0 and resolved['prior_success_count']==32 and resolved['continuation_passed']==4
 prior_guards=[pin(D/x) for x in ('independent-Source-guard.closed.json','continuation-Source-guard.closed.json','seal-Source-guard.closed.json')]
 for ref in prior_guards+h['source_guard_refs']:
  g=doc(ref['path']);assert g['closed'] and g['retained_handles_count']==0 and not g['errors']
 guard=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 source_refs=[href,mref,*mf['members']];own_refs=[pin(x) for x in D.iterdir() if x.is_file()]
 unique={str(Path(ref['path'])).casefold():dict(ref,path=str(Path(ref['path']))) for ref in source_refs+own_refs}
 assert not set(unique)&{str(x).casefold() for x in reg.CANON}
 try:
  guard.acquire(list(unique.values()))
  hosts=source_hosts(h);continuation_pair=own_host('c206e7');preservation_pair=own_host('91e740')
  source_host_ref=save('Source-host-originals.verified.json',dict(schema='researchos.independent-source-host-verification.v1',actor_id=ACTOR,Source_author=h['actor_id'],Source_thread=h['source_thread_id'],hosts=hosts,
   full_original_bytes=True,source_offset_hash_length_verified=True,original1090_preserved=True,actual_product_calls=0,execution_grant=False,formal_acceptance=False))
  own_host_ref=save('independent-host-evidence.json',dict(schema='researchos.independent-source-host-pairs.v1',actor_id=ACTOR,actor_thread_id=THREAD,continuation=continuation_pair,preservation=preservation_pair,
   original_failures={str(n):dict(raw_ref=pin(D/('original-'+str(n)+'.raw.jsonl')),binding_ref=pin(D/('original-'+str(n)+'.binding.json'))) for n in (1092,1093,1096)},execution_grant=False,formal_acceptance=False))
 finally:
  closed=guard.close();seal_guard_ref=save('seal-continuation-Source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
 limitation=dict(id='PINNED_NF3_PEER_TIMESTAMP_EQUALITY',current_adoption_input_blocker=False,
  current_Task75_actual_author='Root metadata62875 and FINAL62876 both2026-10-09T19:00:30.428Z satisfy exact accepted helper.',
  real_comparison='Task76 old21 metadata62777 .566Z and FINAL62778 .567Z fail the same unchanged helper; this record is not an adoption dependency.',
  own_future_Root_received_Final='UNOBSERVED_ROOT_MUST_CAPTURE_AFTER_THIS_DELIVERY',
  if_actual_own_Final_rejected='New adoption Source-only minimum adapter may validate nondecreasing parsed aware platform times; keep real identities, recipient, adjacency, client_authoredfalse, original offsets/hash/bytes and artifact digest. Accepted old NF3 remains immutable.',
  evidence_ref=pin(D/'actual-Task76-platform-time-limit.observation.json'))
 next_fields=doc(h['contract_ref']['path'])['root_request']['exact_fields']
 decision=dict(schema='researchos.w09-root-adoption-independent-source-decision.v1',decision='SOURCE_ACCEPTED_FOR_ROOT_W09_ADOPTION',verdict='SOURCE_ACCEPTED_FOR_ROOT_ADOPTION',status='SOURCE_ACCEPTED_FOR_ROOT_ADOPTION',
  actor_role='INDEPENDENT_NON_AUTHOR',actor_id=ACTOR,actor_thread_id=THREAD,source_author_id=h['actor_id'],source_handoff_ref=href,source_manifest_ref=mref,**bindings,
  created_utc=datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z'),independent_non_author=True,actual_executed=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,programme_qualification=False,formal_case_accepted_delta=0,
  finite_Source_checks_ref=pin(D/'finite-Source-checks.resolved.json'),original_checks_progress_ref=pin(D/'checks.progress.jsonl'),Source_host_originals_ref=source_host_ref,independent_host_evidence_ref=own_host_ref,
  source_author_real_observation_ref=pin(D/'actual-Task75-Source-author.observation.json'),source_author_real_raw_ref=pin(D/'actual-Task75-Source-author.raw.jsonl'),
  Source_guards_closed_refs=prior_guards+[seal_guard_ref]+h['source_guard_refs'],all_Source_guards_closed=True,retained_handles_count=0,live_Canon_held=0,
  author68_reexecuted=False,Q_NF3_previous_controls_reexecuted=False,known_limitations=[limitation],blocking_findings=[],
  reviewed_conditions=[
   'Dynamic whole CP/OW named operations and complete inverse retain untouched histories; nullable SS is never revised or written.',
   'Pending suffix is bound to actual Current4, exact contiguous nondecreasing integers exclude bool; actual22 original required fields and binding triples recover exactly; immutable full pending_ref retained.',
   'Bound Main23 is context only. Actual Root request completed full hostpair and independent author/review Source audits precede every stage; Source carries no execution grant.',
   'Unchanged mandatory share0 TP owns CP/OW while live CP/OW are excluded from Source guards; returned partial state requires Root reconciliation.',
   'Fixed Main profile and commands open together share0/readwrite/open-existing; exact CAS, durable full before/after archives and intent precede first write; readback precedes commit; partial failures retain state without automatic inverse or retry.',
   'CM40 has32 commands, only retrieval/security changed, four new routes and two preserved C19 routes; Q proposal differs only by actual Root issuance time.',
   'Three distinct contained finite Native leases, actual committed profile before new request, and postactivation scope SHA plus activation SHA plus ROOT_SCOPE_REGISTERED hostpair are mandatory before request finalization.',
   'Selector identities/rosters/packages/Native one-shot UUIDs/locked Python/list+test budget are copied from accepted NF3; registrar only calls validate_authority and never prepare/run.'
  ],
  required_next=dict(authority='Root must capture this real FINAL, bind full decision SHA and original author/reviewer audit bytes, then create its own fresh Current4/pending/leases/request and completed request toolpair.',root_request_schema='researchos.root-w09-profile-nf3-registration-request.v1',exact_request_fields=next_fields,
   profile_stage='PROFILE_ADOPTION request then actual propose/check/activate/apply-profile; no Source qualification substituted.',native_stage='After real profile commit, new NATIVE_SCOPES request/current4/pending/three leases, real registration activation and per-selector actual scope audits before finalize and unchanged NF3 prepare/run.',
   product_status='OPEN',formal_acceptance=False,parent_acceptance=False,execution_grant=False))
 assert core.validate_own_review(decision,href,mref,bindings)==ACTOR
 negatives=[{'actor_id':core.AUTHOR},{'actor_id':core.ROOT},{'execution_grant':True},{'actual_executed':True},{'formal_acceptance':True},{'source_manifest_ref':dict(mref,bytes=mref['bytes']+1)}]
 assert all(rejected(core,decision,href,mref,bindings,x) for x in negatives)
 decision['Source_interface_controls']=dict(positive_exact_review=1,rejected_author_Root_grant_actual_formal_wrong_manifest=6,Source_only=True,Root_witness_created=False)
 dref=save('Source-decision.json',decision)
 members=[pin(x) for x in sorted(D.iterdir(),key=lambda x:x.name) if x.is_file() and x.name not in ('HDF.json','MF.json')]
 mfref=save('MF.json',dict(schema='researchos.w09-root-adoption-independent-source-manifest.v1',actor_id=ACTOR,status='SOURCE_ACCEPTED_FOR_ROOT_ADOPTION',members=members,
  excluded_self=['HDF.json','MF.json'],postseal_publication_proof='Published prefix proof is independently emitted after these immutable files are sealed; it grants no Root authority.',execution_grant=False,formal_acceptance=False))
 hdf=dict(schema='researchos.w09-root-adoption-independent-source-handoff.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',actor_thread_id=THREAD,status='SOURCE_ACCEPTED_FOR_ROOT_ADOPTION',
  manifest_ref=mfref,source_decision_ref=dref,source_handoff_ref=href,source_manifest_ref=mref,source_author_id=h['actor_id'],**bindings,
  actual_executed=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,programme_qualification=False,formal_case_accepted_delta=0,
  controls_summary=dict(prior_independent_passed=32,prior_failed_assertion_preserved=1,continuation_passed=4,continuation_failed=0,decision_interface_positive=1,decision_interface_negative=6,author68_reexecuted=False,Q_NF3_reexecuted=False),
  finite_Source_checks_ref=pin(D/'finite-Source-checks.resolved.json'),independent_host_evidence_ref=own_host_ref,Source_host_originals_ref=source_host_ref,
  Source_guards_closed_refs=prior_guards+[seal_guard_ref]+h['source_guard_refs'],all_Source_guards_closed=True,retained_handles_count=0,live_Canon_held=0,
  original_failure_refs=[dict(ordinal=n,raw_ref=pin(D/('original-'+str(n)+'.raw.jsonl')),binding_ref=pin(D/('original-'+str(n)+'.binding.json'))) for n in (1092,1093,1096)],
  original_Source1090_refs=h['original_failure_refs'],known_limitations=[limitation],required_next=decision['required_next'])
 href_review=save('HDF.json',hdf)
 # Run only the actual own_source prefix through the Source review validation.
 # This fixture has no request issuer, time, Scope, lease or Root witness.
 tree=ast.parse(Path(h['caller_ref']['path']).read_bytes());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='own_source')
 fn=copy.deepcopy(fn);end=next(i for i,x in enumerate(fn.body) if isinstance(x,ast.For));fn.body=fn.body[:end]
 fn.body.append(ast.Return(value=ast.Constant(value=True)));fn.name='published_own_source_prefix'
 ast.fix_missing_locations(fn);env=reg.__dict__.copy();exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual Source own_source prefix; no audit grant>','exec'),env)
 fixture=dict(source_handoff_ref=href,source_manifest_ref=mref,source_review_handoff_ref=href_review,source_review_manifest_ref=mfref,source_review_decision_ref=dref)
 pg=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 try:
  pg.acquire([href,mref,href_review,mfref,dref,*bindings.values()])
  assert env['published_own_source_prefix'](fixture,None,core) is True
  assert pin(D/'HDF.json')==href_review and pin(D/'MF.json')==mfref and pin(D/'Source-decision.json')==dref
 finally:
  pclosed=pg.close();pguard=save('published-prefix-Source-guard.closed.json',pclosed)
 assert pclosed['closed'] and pclosed['retained_handles_count']==0 and not pclosed['errors']
 proof=save('published-own-source-prefix.verified.json',dict(schema='researchos.w09-adoption-published-Source-interface-review.v1',review_refs=dict(HDF=href_review,MF=mfref,decision=dref),
  actual_exact_foreign_refs_preserved=True,actual_published_own_source_prefix=True,Source_only_interface_fixture=True,completed_Root_audit_loops_executed=False,Root_request_lease_Scope_grant_created=False,
  guard_ref=pguard,retained_handles_count=0,live_Canon_held=0,actual_product_calls=0,execution_grant=False,formal_acceptance=False))
 print(json.dumps(dict(status='SOURCE_ACCEPTED_FOR_ROOT_ADOPTION',decision='SOURCE_ACCEPTED_FOR_ROOT_W09_ADOPTION',review_refs=dict(HDF=href_review,MF=mfref,decision=dref),publication_proof_ref=proof,
  all_Source_guards_closed=True,retained_handles_count=0,actual_product_calls=0,execution_grant=False,formal_acceptance=False),ensure_ascii=False))
if __name__=='__main__':main()
