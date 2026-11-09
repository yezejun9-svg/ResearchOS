from pathlib import Path
import json,hashlib
O=Path(__file__).parent
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
a=json.loads((O/'audit.json').read_bytes());assert len(a['checks'])==549 and not a['failed_checks']
save('audit.execution.json',{'auditor_derivation_tool':'180928','tool_chunk':'845b37','actual_outer_exit':0,'actual_native_python_exit':0,'basis':'explicit PowerShell exit LASTEXITCODE','stdout_ref':ref(O/'audit.stdout.raw'),'stderr_ref':ref(O/'audit.stderr.raw'),'candidate_calls':0,'new_failure_origins':[]})
r={'schema':'researchos.cli43-root-caller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_ONCE_ONLY_PINNED_LAUNCHER_CALL','requested_changes':[],'actual_caller_executed':False,'actual_launcher_executed':False,
 'scope_ref':a['scope_ref'],'grant_ref':a['grant_ref'],'caller_ref':a['caller_ref'],'caller_sha256':a['caller_ref']['sha256'],'scope_sha256':a['scope_ref']['sha256'],'grant_sha256':a['grant_ref']['sha256'],'audit_ref':ref(O/'audit.json'),'audit_execution_ref':ref(O/'audit.execution.json'),'reused_previous_caller_review_ref':a['reused_previous_caller_review_ref'],'checks_passed':549,'registered_tuple':[329,157,481],
 'conclusions':[
  'Full caller inverse bytes and AST equal reviewed r328 caller after only SCOPE_SHA and GRANT_SHA replacement. There is one subprocess call, no retry, and original nullable exit/first-cause/raw-reference/secondary-error retention is unchanged.',
  'Actual grant55efa0 scope/binding/authority refs and registration/grant manifest members byte-verified. Four ordered live canonical files equal grant copies and registered desired bytes; complete old469 plus fixed12 preserved.',
  'Grant-final saved three owned Git records are native0 with complete Job cleanup. HEADa510/status894B13rows11oldD/indexempty verified; direct current .git HEAD also matches. No new Git invocation occurred.',
  'Executor, launcher and export leaves plus four Root launch outputs are absent. Authorization/preflight leaves already exist due to actual sealed grant, unique to the r329 UUID.',
  'Caller invokes fixed Python -I -S -X utf8, pinned launcher0a958, scope90aec and grant55efa0 with the same five public environment keys. Caller3900 does not extend launcher3600/inner3300/cleanup5 or original case/HTTP/resource caps.',
  'Scope instrumentation helper37a3 and plana626 bind the independently reviewed immediate bytes.Clone ownership correction; original test37220, runner529/debughelper9c and strict raw/SHA assertions remain pinned unchanged.',
  'Caller does not claim WindowsJob or full OS lifecycle qualification. Any pre-try validation failure still relies on actual outer tool observations; unavailable child native exit remains NULL, never fake0.',
  'Previous complete caller/scope/v7 chain and f690 correction reviews are reused transparently. No complete compiler/OS tree rehash, new Go graph, target execution or source/product/formal acceptance is claimed.'
 ],
 'pending_origin_note':'Preparation registered481/observed484 remains its historical snapshot: two sealed late refs verified, third sealed_ref was NULL then with native/outerNULL and no process launch. Root reports a later sealed third ref; this narrow audit does not rewrite the snapshot or count. All late events stay outside fixed481.',
 'source_acceptance':False,'formal_increment':0,'new_failure_origins':[],'status':'STOPPED'}
save('review.json',r)
save('handoff.json',{'schema':'researchos.independent-review-handoff.v1','reviewer':r['reviewer'],'decision':r['decision'],'review_ref':ref(O/'review.json'),'audit_ref':ref(O/'audit.json'),'actual_caller_executed':False,'new_failure_origins':[],'status':'STOPPED'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json'];save('manifest.json',{'schema':'researchos.independent-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True})
print(json.dumps({n:ref(O/n) for n in ['review.json','manifest.json','handoff.json']},ensure_ascii=False))
