from pathlib import Path
import json,hashlib
O=Path(__file__).parent
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
a=json.loads((O/'audit.json').read_bytes());assert len(a['checks'])==537 and a['failed_checks']==[]
save('audit.execution.json',{'tool_chunk':'70cc8e','actual_outer_exit':0,'actual_native_python_exit':0,'basis':'explicit PowerShell exit LASTEXITCODE','stdout_ref':ref(O/'audit.stdout.raw'),'stderr_ref':ref(O/'audit.stderr.raw'),'candidate_calls':0,'new_failure_origins':[]})
r={'schema':'researchos.cli43-root-caller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_ONCE_ONLY_PINNED_LAUNCHER_CALL','requested_changes':[],'actual_caller_executed':False,'actual_launcher_executed':False,'scope_ref':a['scope_ref'],'grant_ref':a['grant_ref'],'caller_ref':a['caller_ref'],'caller_sha256':a['caller_ref']['sha256'],'scope_sha256':a['scope_ref']['sha256'],'grant_sha256':a['grant_ref']['sha256'],'audit_ref':ref(O/'audit.json'),'audit_execution_ref':ref(O/'audit.execution.json'),'reused_previous_caller_review_ref':a['reused_previous_caller_review_ref'],'checks_passed':537,'registered_tuple':[328,156,469],
'conclusions':[
 'Full caller inverse bytes and AST equal reviewed r327 caller after replacing only SCOPE_SHA and GRANT_SHA. Exception/nullable exit/raw-reference/secondary-error behavior unchanged; one subprocess only.',
 'Actual sealed grant scope/binding/authority references and registration/grant manifest members byte-verified. Current ordered four canonical files equal grant copies and registered desired bytes; old459 plus fixed10 preserved. No new counter write.',
 'Grant-final actual three owned Git records native0 with complete Job cleanup. Saved HEADa510/status894B thirteen rows including eleven old deletions/indexempty verified. Direct current .git HEAD read also matches. No new Git process was invoked.',
 'Fresh executor, launcher and export roots absent, and four root-launch output files absent. Authorization/preflight exist because actual grant is already sealed; grant is unique to this scope UUID.',
 'Caller invokes exact pinned Python -I -S -X utf8, launcher0a958, scopeedec and grant26bd using fixed public environment without secrets. Caller3900 does not enlarge launcher3600/inner3300/cleanup5 or case/HTTP/resource bounds.',
 'Initial preflight failures before caller try still depend on actual outer tool trace; caller does not claim independent WindowsJob or full OS lifecycle qualification. Native launcher exit remains NULL when unavailable; errors and secondary receipt failures do not become fake0.',
 'Reuse bound scope282 checks and standalone529 runner/9c helper review; no full compiler/OS backing-tree rehash or new Go graph claimed. This permits only Root once-only call under existing grant, not source/product/Main/Desktop/formal acceptance.'
], 'pending_origin_note':'Caller preparation472 is preserved as its historical point-time snapshot. Root later reported two additional diagnostics outside fixed469; those do not alter reviewed scope/grant or count. Their source records are not represented as independently reverified by this narrow audit.', 'source_acceptance':False,'formal_increment':0,'new_failure_origins':[],'status':'STOPPED'}
save('review.json',r)
save('handoff.json',{'schema':'researchos.independent-review-handoff.v1','reviewer':r['reviewer'],'decision':r['decision'],'review_ref':ref(O/'review.json'),'audit_ref':ref(O/'audit.json'),'actual_caller_executed':False,'new_failure_origins':[],'status':'STOPPED'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json'];save('manifest.json',{'schema':'researchos.independent-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True})
print(json.dumps({n:ref(O/n) for n in ['review.json','manifest.json','handoff.json']},ensure_ascii=False))
