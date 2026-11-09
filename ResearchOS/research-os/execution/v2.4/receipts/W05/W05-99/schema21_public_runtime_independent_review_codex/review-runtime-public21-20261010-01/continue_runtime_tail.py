"""Only the diagnosed spelling predicate and previously unreached tail."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,ntpath,sys,traceback,types
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent;N=B/'schema21_public_root_caller_source_codex/s21public-caller-20261010-02';S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009';Q=S/'public21-current-resource-root-20261010-02'
p=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py';s=types.ModuleType('bounded_review_support');s.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),s.__dict__);s.D=D
def key(p):return ntpath.normcase(ntpath.normpath(str(p)))
def read(r):
 b=Path(r['path']).read_bytes()
 if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('TAIL_INPUT_PIN')
 return json.loads(b)
def when(v):return datetime.fromisoformat(v.replace('Z','+00:00'))
prefix=json.loads((D/'runtime-resource-review.result.json').read_bytes());diagnosis=json.loads((D/'original-1154.diagnosis.json').read_bytes());manifest=read(prefix['runtime_manifest_ref']);request=read(prefix['prepare_request_ref']);resources=manifest['resource_refs'];bykey={key(r['path']):r for r in resources}
caller=s.inert(manifest['caller_ref']['path']);base=caller.base();contract=read(manifest['runner_contract_ref'])
import sqlite3,_sqlite3
job=s.inert(contract['owned_job']['path']);loaded=[s.pin(x) for x in job.runtime_resource_paths()]
sqlite_refs=[s.pin(sqlite3.__file__),s.pin(_sqlite3.__file__),s.pin(Path(sys.executable).parent/'DLLs/sqlite3.dll')]
tail=[prefix['runtime_manifest_ref'],prefix['qualification_scope_ref'],prefix['prepare_request_ref'],s.pin(D/'runtime-resource-review.result.json'),s.pin(D/'runtime-resources.guard.closed.json'),s.pin(D/'original-1154.diagnosis.json'),manifest['source_hdf_ref'],manifest['source_mf_ref'],manifest['caller_ref'],manifest['runner_contract_ref'],caller.OC3_REF,base.GUARD_REF,base.TP_REF,caller.PROGRAMME_REF,contract['owned_job'],*loaded,*sqlite_refs]
for row in diagnosis['missing_actual_pairs']:tail.extend(row['prepared_current_resource_ref'])
witnesses=[]
for name,refs,actor in [('SOURCE_REVIEW_WITNESS',[request[k] for k in ('review_hdf_ref','review_mf_ref','review_decision_ref')],'codex:/root/full_w09_source_review'),('RUNNER_SOURCE_REVIEW_WITNESS',list(request['runner_review_refs'].values()),'codex:/root/attach_restore_independent_review')]:
 witness_ref=request['review_hostpair_witness_ref' if name=='SOURCE_REVIEW_WITNESS' else 'runner_review_witness_ref'];witness=read(witness_ref);binding_ref=witness['capture_binding_ref'];binding=read(binding_ref);peer=read(binding['peer_delivery_binding_ref'])
 tail += [witness_ref,binding_ref,binding['original_capture_ref'],binding['peer_delivery_binding_ref'],peer['original_capture_ref'],*refs]
 witnesses.append((name,witness_ref,refs,actor))
pre=read(request['preparation_host_binding_ref']);tail += [request['preparation_host_binding_ref'],pre['original_capture_ref']]
unique={}
for r in tail:
 k=key(r['path'])
 if k in unique and unique[k]!=r:raise ValueError('TAIL_PIN_CONFLICT')
 unique[k]=r
held=s.guard();checks=[];failure=None;details={}
def check(name,ok,evidence=None):
 checks.append(dict(name=name,passed=bool(ok),evidence=evidence))
 if not ok:raise ValueError(name)
def raw(r):return held.get_buffer(r['path'])
def doc(r):return json.loads(raw(r))
def required(refs,label):
 missing=[r for r in refs if key(r['path']) not in bykey or not base.same_ref(r,bykey[key(r['path'])])]
 check(label,not missing,dict(required_count=len(refs),missing=missing))
try:
 held.acquire(list(unique.values()))
 check('reuse_exact_original_34_successes_and_511_closed_guard',prefix['successful_check_count']==34 and sum(x['passed'] for x in prefix['checks'])==34 and prefix['checks'][-1]['name']=='existing_actual_programme_qualified_closure_pins' and doc(prefix['guard_ref'])['verification']=='PASSED' and doc(prefix['guard_ref'])['closed'] is True and doc(prefix['guard_ref'])['retained_handles_count']==0,dict(original_report_ref=s.pin(D/'runtime-resource-review.result.json'),original_guard_ref=prefix['guard_ref'],full_resource_ref_checks_replayed=False))
 pair=diagnosis['missing_actual_pairs'][0];historical=pair['historical_programme_member_ref'];current=pair['prepared_current_resource_ref'][0]
 check('historical_programme_member_same_ref_current_pin',len(diagnosis['missing_actual_pairs'])==1 and len(pair['prepared_current_resource_ref'])==1 and base.same_ref(historical,current) and bykey[key(historical['path'])]==current,dict(historical_ref=historical,current_resource_ref=current,Source_comparison='OC3.same_ref canonical path plus exact sha256/int bytes',current_manifest_array_unmodified=True))
 programme=doc(caller.PROGRAMME_REF)
 check('real_qualified_old21_programmes_reused_not_reexecuted',programme['status']=='QUALIFIED_OLD21_BUILD' and programme['independent_non_author'] is True and programme['all_owned_jobs_idle_and_closed'] is True and programme['formal_acceptance'] is False and programme['execution_grant'] is False and contract['old21_control']==programme['program_refs']['control'] and contract['old21_backup']==programme['program_refs']['backup'],dict(programme_ref=caller.PROGRAMME_REF,control_ref=contract['old21_control'],backup_ref=contract['old21_backup']))
 scope=doc(prefix['qualification_scope_ref']);start=when(scope['created_utc'])
 for operation,witness_ref,expected,actor in witnesses:
  witness=doc(witness_ref);binding_ref=witness['capture_binding_ref'];binding=doc(binding_ref)
  caller.validate_root_capture(binding,raw(binding['original_capture_ref']),expected,operation,actor)
  check('fresh_actual_'+operation+'_identity_refs_offsets',witness['issued_by']==caller.ROOT and witness['root_thread_id']==caller.ROOT_THREAD and when(binding['tool_result_timestamp'])<=when(witness['created_utc'])<=start,dict(binding_ref=binding_ref,review_refs=expected))
 pre=doc(request['preparation_host_binding_ref']);expected=[prefix['qualification_scope_ref'],manifest['source_hdf_ref'],manifest['source_mf_ref'],*request['runner_review_refs'].values(),*request['before_canonical_refs']]
 caller.validate_root_capture(pre,raw(pre['original_capture_ref']),expected,'RUNTIME_MANIFEST_PREREQUISITES')
 check('fresh_actual_runtime_prerequisite_capture_full_refs',start<=when(pre['tool_call_timestamp'])<=when(pre['tool_result_timestamp'])<when('2026-10-09T22:50:57.012Z'),dict(binding_ref=request['preparation_host_binding_ref'],live_refs_not_reread_or_held=True))
 required(loaded,'actual_loaded_python_windows_SQLite_DLL_runtime_resources')
 required(sqlite_refs,'mandatory_actual_SQLite_extension_DLL_stdlib')
 # Runtime checks cover pinned Root/Caller imports, not reviewer-only __main__.
 expected_stdlib=[r for r in resources if Path(r['path']).is_relative_to(Path(sys.executable).parent) and Path(r['path']).suffix.lower() in ('.py','.pyc')]
 check('Root_prepared_stdlib_and_existing_cache_all_verified',bool(expected_stdlib) and all(any(e['path']==r['path'] and e['sha256']==r['sha256'] and e['bytes']==r['bytes'] and e['verified'] and e['final_path_match'] and e['closed'] for e in doc(prefix['guard_ref'])['entries']) for r in expected_stdlib),dict(ref_count=len(expected_stdlib),reused_current_full_guard_ref=prefix['guard_ref'],no_reviewer_main_required_as_Root_entry=True))
 check('review_time_within_real_scope_no_future_issuance',start<=datetime.now(timezone.utc)<when(scope['lease_expires_at']),dict(reviewed_now=datetime.now(timezone.utc).isoformat(),lease_expires_at=scope['lease_expires_at'],Root_wrapper_payload_or_peer_witness_issued=False))
 counts={}
 for r in resources:counts[Path(r['path']).suffix.lower()]=counts.get(Path(r['path']).suffix.lower(),0)+1
 details=dict(resource_refs=resources,resource_suffix_counts=counts,expected_common_fields={k:manifest[k] for k in ('source_hdf_ref','source_mf_ref','caller_ref','runner_contract_ref','qualification_scope_ref')},python_ref=contract['locked_python_ref'],control_ref=contract['old21_control'],loaded_runtime_refs=loaded,SQLite_refs=sqlite_refs,stdlib_and_cache_ref_count=len(expected_stdlib),earlier_error_is_reviewer_foreign_ref_comparison=True,old_Source_controls_replayed=False,full_current_resource_guard_replayed=False,actual_product_calls=0,Root_qualification_still_requires_true_Final_later_peer_capture_payload_and_wrapper=True)
except BaseException as e:failure=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
finally:
 closed=held.close();guard_ref=s.write('runtime-tail.guard.closed.json',closed)
 report=s.write('runtime-tail-review.result.json',dict(schema='researchos.public21-runtime-bounded-tail-review-result.v1',review_author='codex:/root/full_w09_source_review',created_utc=datetime.now(timezone.utc).isoformat(),checks=checks,successful_check_count=sum(x['passed'] for x in checks),failure=failure,guard_ref=guard_ref,original_prefix_report_ref=s.pin(D/'runtime-resource-review.result.json'),original_guard_ref=prefix['guard_ref'],original_failure_1154_diagnosis_ref=s.pin(D/'original-1154.diagnosis.json'),details=details,formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(report_ref=report,guard_ref=guard_ref,successful_checks=sum(x['passed'] for x in checks),failure=failure,tail_guard_refs=len(unique),closed=closed['closed'],retained_handles_count=closed['retained_handles_count'],formal_acceptance=False,execution_grant=False),ensure_ascii=False))
if failure or not closed['closed'] or closed['retained_handles_count'] or closed['errors']:sys.exit(1)
