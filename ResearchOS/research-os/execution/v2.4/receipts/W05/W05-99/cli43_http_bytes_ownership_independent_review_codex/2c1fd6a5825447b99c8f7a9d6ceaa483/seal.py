from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,d):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
a=json.loads((O/'audit.json').read_bytes());assert a['failed_checks']==[] and len(a['checks'])==31
def named(s):return next(x for x in a['input_refs'] if x['path'].endswith(s))
save('audit.execution.json',{'tool':'3add4b','actual_outer_exit':0,'actual_python_native_exit':0,'explicit_exit_LASTEXITCODE':True,'stdout_ref':ref(O/'audit.stdout.raw'),'stderr_ref':ref(O/'audit.stderr.raw'),'target_execution_count':0,'separate_original_tool_payload_captured':False})
review={'schema':'researchos.cli43-http-byte-ownership-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_NEW_SCOPE_PREPARATION','requested_changes':[],
 'helper_ref':named('/cli43_receipt_instrumentation_test.go.proposed.txt'),'instrumentation_plan_ref':named('/instrumentation-plan.proposed.json'),'unchanged_instrumented_test_ref':named('/cli_sessions_test.instrumented.go.txt'),
 'candidate_handoff_ref':named('/310e0bf842a34df6813dad1126e2970a/handoff.json'),'candidate_manifest_ref':named('/310e0bf842a34df6813dad1126e2970a/manifest.json'),
 'audit_ref':ref(O/'audit.json'),'audit_execution_ref':ref(O/'audit.execution.json'),'checks':31,'failed_checks':0,
 'findings':[
  'All seven candidate manifest members match actual bytes and the complete candidate directory, excluding only its manifest.',
  'The entire new helper is exactly the old helper plus one 17-byte b=bytes.Clone(b); insertion at cli43Bytes entry. All other imports, functions, call sites, counters and assertion bytes are unchanged.',
  'The plan has the same key set and differs only at additional_file_ref. The complete instrumented CLI test remains SHA37220e2a574343f7e291b41745e556d23775711d79f01cc8deb47ee1c0b19966.',
  'The actual frozen Go bytes.go source matches the prior actual graph pin. Clone explicitly returns nil for nil; otherwise it appends into a nonnil empty slice. Nonempty data has independent backing storage before raw/length/SHA are constructed.',
  'Each existing cli43Bytes call now returns a self-owned snapshot at that call boundary. The wrapper still delegates the actual Write first and snapshots before returning; it does not acquire earlier socket-observation semantics.',
  'Strict Python length/digest checks and its existing null-plus-zero handling are unchanged. Original HTTP caps, timeouts, leaves and all other test/helper bytes are unchanged.'
 ],
 'clone_semantics':a['semantics'],'clone_source_ref':a['clone_source_ref'],'clone_function_lines':a['clone_function_lines'],'helper_call_sites':a['helper_call_sites'],
 'failure_context_ref':named('/684f0c8b739541fe8da3b2f06ca78d09/review.json'),
 'prior_failure_policy':'The four r328 nonempty requested digest discrepancies and all original evidence remain immutable and unqualified. This source correction does not retroactively qualify them.',
 'future_requirements':['Root must bind this exact helper and plan in a new scope, registration, seal and unique grant.','Fresh instrumented compiler/test artifacts and actual finite cases must complete all native, raw HTTP, fixture-after and qualification guards.','Nil, empty and caller-buffer mutation behavior is source-reviewed only; no new control has run.'],
 'actual_target_executions':0,'actual_template_imports':0,'actual_SQL_or_HTTP_calls':0,'actual_CAS':False,'actual_source_acceptance':False,'formal_acceptance':False,'execution_authorized_by_this_review':False,
 'reuse':'Existing r328 closed-execution review and prior controller/resource reviews provide context only; no complete resource-tree rehash or target replay was performed.',
 'new_failure_origins':[],'status':'STOPPED'}
save('review.json',review)
save('handoff.json',{'schema':'researchos.independent-review-handoff.v1','review_ref':ref(O/'review.json'),'audit_ref':ref(O/'audit.json'),'decision':review['decision'],'new_failure_origins':[],'target_executions':0,'status':'STOPPED'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'schema':'researchos.immutable-public-manifest.v1','entries':entries,'count':len(entries),'excluded_only_self':True})
print(json.dumps({n:ref(O/n) for n in ['review.json','manifest.json','handoff.json']},ensure_ascii=False))
