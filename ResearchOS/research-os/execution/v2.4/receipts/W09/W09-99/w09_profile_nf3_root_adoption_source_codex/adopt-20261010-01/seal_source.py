"""Seal Task75 Source, new pure-delta results and original Source host evidence."""
import hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent
LOG=Path(r'C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-49-27-01a11e22-ecb2-7720-80d2-af63727d414d.jsonl')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=sha(raw),bytes=len(raw))
def save(name,obj):
 p=N/name
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
 return pin(p)
needles={'d74483':'d74483','ff2e70':'ff2e70','a5868c':'a5868c','original1090':'invalid hunk at line 124'}
size=LOG.stat().st_size
with LOG.open('rb') as f:
 first=f.readline();start=max(len(first),size-16000000);f.seek(start)
 if start>len(first):f.readline()
 offset=f.tell();tail=f.read(size-offset)
calls={};pairs={}
for line in tail.splitlines(keepends=True):
 try:item=json.loads(line)
 except ValueError:offset+=len(line);continue
 p=item.get('payload',{});kind=p.get('type');cid=p.get('call_id')
 if kind in ('function_call','custom_tool_call') and cid:calls[cid]=(offset,line,item)
 if kind in ('function_call_output','custom_tool_call_output') and cid in calls:
  for key,needle in needles.items():
   if needle in str(p.get('output','')) and key not in pairs:pairs[key]=(calls[cid],(offset,line,item))
 offset+=len(line)
assert set(pairs)==set(needles),{'missing':list(set(needles)-set(pairs))}
hostrefs=[];failure=None
for key in needles:
 call,result=pairs[key];path=N/('actual-source-'+key+'.raw.jsonl')
 with path.open('xb') as f:f.write(first+call[1]+result[1])
 rawref=pin(path);failed=key=='original1090'
 binding=save('actual-source-'+key+'.binding.json',dict(source_audit_path=str(LOG),source_prefix_size_observed=size,
  source_line_offsets=[0,call[0],result[0]],source_line_lengths=[len(first),len(call[1]),len(result[1])],
  source_line_sha256=[sha(first),sha(call[1]),sha(result[1])],original_capture_ref=rawref,
  original_call_id=call[2]['payload']['call_id'],chunk_id=None if failed else key,
  outer_exit=None if failed else 0,Python_exit=None if failed else 0,actual_Go_exit=None,actual_Native_exit=None,actual_SQL_exit=None))
 record=dict(key=key,raw_ref=rawref,binding_ref=binding);hostrefs.append(record)
 if failed:failure=dict(ordinal=1090,origin_ref=rawref,source_binding_ref=binding,origin_selector='$',
  classification='SOURCE_PATCH_FORMAT_TOOL_FAILURE',description='apply_patch missing plus prefix at hunk line 124; no subprocess was launched; checked runtime sources unchanged.',
  actual_outer_exit=None,actual_python_exit=None,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,
  actual_dispatcher_exit=None,actual_model_exit=None,counted_once_by_Root_only=True,automatic_retry=False)
failref=save('original-failure-1090.json',failure)
hostindex=save('actual-source-host-pairs.json',dict(captures=hostrefs,
 scope='Finite Source preparation, new pure/AST controls, contract construction and the original patch-format failure only',
 runtime_branch_called=False,existing_control_suites_rerun=False,new_original_failure_refs=[failref]))
inp=json.loads((N/'input-pins.json').read_bytes());gref=inp['refs']['guard'];graw=Path(gref['path']).read_bytes()
assert pin(gref['path'])==gref
gm=types.ModuleType('task75_final_source_guard');exec(compile(graw,gref['path'],'exec'),gm.__dict__)
members=[pin(p) for p in sorted(N.rglob('*')) if p.is_file()]
guard=gm.SourceReadGuard(total_cap=128*1024*1024)
try:
 guard.acquire(members)
 contract=json.loads(guard.get_buffer(str(N/'root-calling-contract.source.json')))
 controls=json.loads(guard.get_buffer(str(N/'source-controls.result.json')))
 assert controls['passed']==68 and controls['failed']==0
 assert controls['runtime_stage_called'] is False and controls['actual_exclusive_write_called'] is False and controls['actual_TP_called'] is False
 for key,ref in contract['source_bindings'].items():assert pin(ref['path'])==ref
 prior=[]
 for name in ('inputs.source-guard.closed.json','controls.source-guard.closed.json'):
  audit=json.loads(guard.get_buffer(str(N/name)))
  assert audit['closed'] is True and audit['retained_handles_count']==0 and audit['errors']==[];prior.append(pin(N/name))
finally:
 closed=guard.close();closedref=save('seal.source-guard.closed.json',closed)
 assert closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
delivery=save('Source-delivery.json',dict(schema='researchos.w09-root-adoption-source-delivery.v1',
 source_author='codex:/root/native_temp_independent_review',status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_ADOPTION',
 source_refs=contract['source_bindings'],contract_ref=pin(N/'root-calling-contract.source.json'),input_pins_ref=pin(N/'input-pins.json'),
 controls_ref=pin(N/'source-controls.result.json'),controls_passed=68,controls_failed=0,actual_source_host_pairs_ref=hostindex,
 source_guard_refs=[*prior,closedref],all_Source_guards_closed=True,retained_handles_count=0,
 existing_Q_QR_NF3_NF3R_modified=False,existing_control_suites_rerun=False,
 actual_Root_request_scope_or_lease_created=False,Main_written=False,Canon_written=False,actual_TP_called=False,
 actual_exclusive_write_called=False,actual_Go_Native_SQL_model_called=False,execution_grant=False,
 programme_qualification=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,
 role_registry_created=False,full_formal_capture_created=False,new_original_failure_refs=[failref],Root_last_reported_live_next=1091,STOP=True))
members=[pin(p) for p in sorted(N.rglob('*')) if p.is_file()]
mf=save('MF.json',dict(schema='researchos.w09-root-adoption-source-manifest.v1',members=members,excludes=['MF.json','HDF.json'],source_author='codex:/root/native_temp_independent_review'))
hdf=save('HDF.json',dict(schema='researchos.w09-root-adoption-source-handoff.v1',actor_id='codex:/root/native_temp_independent_review',
 source_thread_id='01a11e22-ecb2-7720-80d2-af63727d414d',status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_ADOPTION',
 manifest_ref=mf,source_delivery_ref=delivery,**contract['source_bindings'],contract_ref=pin(N/'root-calling-contract.source.json'),
 input_pins_ref=pin(N/'input-pins.json'),controls_ref=pin(N/'source-controls.result.json'),controls_passed=68,controls_failed=0,
 source_guard_refs=[*prior,closedref],all_Source_guards_closed=True,retained_handles_count=0,
 actual_source_host_pairs_ref=hostindex,original_failure_refs=[failref],actual_branch_called=False,actual_TP_called=False,actual_Main_exclusive_write_called=False,
 actual_NF3_prepare_run_called=False,Main_written=False,Canon_written=False,
 execution_grant=False,programme_qualification=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,
 required_next='Non-author Source review and actual peer capture; Root then issues a current request, completed host proof and finite leases before any runtime stage.'))
for ref in members:assert pin(ref['path'])==ref
print(json.dumps(dict(HDF=hdf,MF=mf,caller=contract['source_bindings']['caller_ref'],core=contract['source_bindings']['core_ref'],
 main_pair=contract['source_bindings']['main_pair_ref'],contract=pin(N/'root-calling-contract.source.json'),members=len(members),
 controls_passed=68,controls_failed=0,actual_branch_called=False,original_failure_ref=failref,
 original_failure_raw_ref=failure['origin_ref'],original_failure_binding_ref=failure['source_binding_ref']),ensure_ascii=False))
