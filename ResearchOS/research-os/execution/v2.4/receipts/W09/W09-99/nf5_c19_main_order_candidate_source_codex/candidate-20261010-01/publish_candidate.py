"""Publish only the Source candidate. Root alone may later adopt Main."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,sys,traceback,types
R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99';D=Path(__file__).resolve().parent
A=W/'nf5_c19_main_order_independent_review_codex/review-20261010-01'
p=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py';s=types.ModuleType('review_support');s.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),s.__dict__);s.D=D
def fresh(r):
 raw=Path(r['path']).read_bytes()
 if len(raw)!=r['bytes'] or hashlib.sha256(raw).hexdigest()!=r['sha256']:raise ValueError('ADVISORY_PIN_DRIFT')
 return json.loads(raw)
advisory_ref={'path':str(A/'source-advisory-decision.json'),'sha256':'8d510889cd395632affb2916c71822801489c4519b353dcc9daa95f7c4b62c46','bytes':5335}
advisory=fresh(advisory_ref);properties=fresh(advisory['properties_ref']);inputs=properties['details']['input_refs']
author='codex:/root/full_w09_source_review';author_thread='01a1215b-7210-7613-b033-756b9d553b83';root_thread='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
checks=[];failure=None;published={};g=s.guard()
def check(name,ok,evidence=None):
 checks.append(dict(name=name,passed=bool(ok),evidence=evidence))
 if not ok:raise ValueError(name)
def write_raw(name,raw):
 p=D/name
 with p.open('xb') as f:f.write(raw)
 return s.pin(p)
try:
 g.acquire(list(inputs.values()))
 before=g.get_buffer(inputs['retrieval']['path']);now_main=s.pin(inputs['retrieval']['path'])
 check('fresh_current_Main_exact_advisory_before_binding',now_main==inputs['retrieval']==advisory['actual_Main_ref'],dict(actual_current_Main_ref=now_main,not_from_memory=True))
 old=b'selected = GROUPS[check] if check else list(TESTS)';new=b'selected = GROUPS[check] if check else [name for name in CASES[case] if name in TESTS]'
 if before.count(old)!=1 or before.count(new):raise ValueError('SINGLE_KNOWN_REPLACEMENT')
 candidate=before.replace(old,new,1)
 published['before_source_ref']=write_raw('retrieval.before.source.py',before)
 published['candidate_ref']=write_raw('retrieval.source.py',candidate)
 diffraw=Path(advisory['candidate_diff_ref']['path']).read_bytes()
 if s.pin(advisory['candidate_diff_ref']['path'])!=advisory['candidate_diff_ref']:raise ValueError('ADVISORY_DIFF_PIN')
 published['diff_ref']=write_raw('retrieval.case-order.diff',diffraw)
 published['before_main_ref']=now_main
 check('new_published_before_snapshot_exact_held_Main_bytes',Path(published['before_source_ref']['path']).read_bytes()==before and published['before_source_ref']['sha256']==now_main['sha256'] and published['before_source_ref']['bytes']==now_main['bytes'])
 readback=Path(published['candidate_ref']['path']).read_bytes()
 check('new_published_candidate_exact_advisory_bytes',readback==candidate and published['candidate_ref']['sha256']==advisory['candidate_in_memory_sha256'] and published['candidate_ref']['bytes']==advisory['candidate_in_memory_bytes'])
 oldtree=ast.parse(before,filename=now_main['path']);newtree=ast.parse(readback,filename=published['candidate_ref']['path'])
 old_assign=next(n for n in ast.walk(oldtree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='selected' for t in n.targets) and isinstance(n.value,ast.IfExp))
 new_assign=next(n for n in ast.walk(newtree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='selected' for t in n.targets) and isinstance(n.value,ast.IfExp));new_assign.value.orelse=copy.deepcopy(old_assign.value.orelse)
 check('new_file_AST_only_expected_case_only_expression',ast.dump(newtree,include_attributes=False)==ast.dump(oldtree,include_attributes=False),dict(actual_candidate_Source_compiled_as_AST_only=True,entry_executed=False))
 check('new_file_exact_whole_byte_inverse',readback.replace(new,old,1)==before and readback.count(new)==1 and readback.count(old)==0)
 check('new_diff_file_exact_reused_advisory_not_retested_properties',Path(published['diff_ref']['path']).read_bytes()==diffraw and published['diff_ref']['sha256']==advisory['candidate_diff_ref']['sha256'] and published['diff_ref']['bytes']==advisory['candidate_diff_ref']['bytes'],dict(previous_18_properties_reused=True,previous_18_controls_rerun=False))
 input_ref=s.write('input-pins.json',dict(schema='researchos.w09-c19-main-order-candidate-input-pins.v1',source_author=author,source_author_thread=author_thread,root_thread_id=root_thread,advisory_decision_ref=advisory_ref,advisory_properties_ref=advisory['properties_ref'],advisory_diff_ref=advisory['candidate_diff_ref'],current_input_refs=inputs,actual_Main_before_ref=now_main,current_source21_refs=properties['details']['current_Source21_refs'],original_failure_ordinals_retained=[1158,1159],original_failure_evidence=advisory['original_failure_evidence'],old_18_properties_reused=True,old_18_controls_rerun=False,formal_acceptance=False,execution_grant=False))
 published['input_pins_ref']=input_ref
except BaseException as e:failure=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
finally:
 closed=g.close();guard_ref=s.write('input-eight.guard.closed.json',closed)
 result_ref=s.write('candidate-new-file-checks.json',dict(schema='researchos.w09-c19-main-order-candidate-new-file-checks.v1',source_author=author,source_author_thread=author_thread,created_utc=datetime.now(timezone.utc).isoformat(),checks=checks,new_checks_passed=sum(x['passed'] for x in checks),failure=failure,guard_ref=guard_ref,published_refs=published,old_18_controls_rerun=False,Main_Canon_NF5_Scope_written=False,actual_Go_Native_SQL_model_TP_calls=0,formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(status='CANDIDATE_FILES_PUBLISHED_PENDING_SEAL' if failure is None else 'FAILED_SOURCE_PUBLICATION',result_ref=result_ref,guard_ref=guard_ref,published_refs=published,new_checks_passed=sum(x['passed'] for x in checks),failure=failure,closed=closed['closed'],retained_handles_count=closed['retained_handles_count'],execution_grant=False,formal_acceptance=False),ensure_ascii=False))
if failure or not closed['closed'] or closed['retained_handles_count'] or closed['errors']:sys.exit(1)
