from pathlib import Path
import json,hashlib
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';N=P/'integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4'
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
a=json.loads((O/'audit.json').read_bytes());s=json.loads((N/'scope_registration.json').read_bytes());assert len(a['checks'])==289 and not a['failed_checks']
origin=ref(O/'failure-origin.89547b.json')
save('audit.execution.json',{'tool_chunk':'0df523','actual_outer_exit':0,'actual_native_python_exit':0,'basis':'PowerShell explicitly propagated LASTEXITCODE; saved stdout reports 289 checks and zero failed checks','stdout_ref':ref(O/'audit.stdout.raw'),'stderr_ref':ref(O/'audit.stderr.raw'),'target_executions':0,'prior_locator_origin_ref':origin})
review={'schema':'researchos.cli43-compiler-controller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_CURRENT43_HELD2_ONCE','requested_changes':[],
 'scope_sha256':ref(N/'scope_registration.json')['sha256'],'runner_sha256':s['runner_ref']['sha256'],'launcher_sha256':s['launcher_ref']['sha256'],'gate_sha256':s['authorization_gate_ref']['sha256'],'debug_helper_sha256':s['debug_tree_helper_ref']['sha256'],
 'scope_ref':ref(N/'scope_registration.json'),'bound_manifest_ref':ref(N/'bound-scope.manifest.json'),'audit_ref':ref(O/'audit.json'),'audit_execution_ref':ref(O/'audit.execution.json'),
 'expected_before':[328,156,469],'expected_after':[329,157,481],'actual_registration_executed':False,'actual_integration_executed':False,'actual_candidate_executed':False,'actual_grant_issued_by_review':False,'formal_increment':0,'source_acceptance':False,'main_integration_authorized':False,'source_commit':s['source_commit'],
 'check_count':289,'failed_check_count':0,'canonical_before':a['facts']['canonical_before'],'new_failure_origins':[origin],'reused_review_refs':a['facts']['reused_review_refs'],
 'findings':[
  {'id':'B01','status':'CLOSED_STATIC','detail':'31 unique manifest members and supplied whole scope SHA verified. Current CP/OW/ST/CM byte-match saved snapshots and r328 desired references. Direct HEAD remains a510. Saved status13/11D/indexempty facts are unchanged; no new native Git query was run.'},
  {'id':'B02','status':'CLOSED_STATIC','detail':'Current original469 remains unchanged. Prospective fixed12 exactly matches the sealed cut capture. All12 original payloads match source JSON; three extracted mapping leaves equal their indexed original-container new_origins rows, including original native NULL or1 fields. The r328 qualification failure appears once, not once per propagated launcher exit. Later origins are outside this cut.'},
  {'id':'B03','status':'CLOSED_STATIC','detail':'Full scope delta is limited to new UUID/five roots/registration tuple/review path/runtime metadata overlay and instrumentation helper/plan refs. Template changes exactly those two instrumentation refs. Root outer driver whole bytes change only the scope SHA anchor and keep ROOT-relative serialized ScopeRef.'},
  {'id':'B04','status':'CLOSED_STATIC','detail':'Six v7 wrapper bytes are unchanged. Eight metadata refs verify in serialized relative form and project exactly to the final8 ABS runtime rows. Original1242 rows are unchanged;1250 total. V7 successful strict-observation marker, unknown rejection and point-time limits retain the prior independently reviewed producer/consumer semantics.'},
  {'id':'B05','status':'CLOSED_STATIC','detail':'New helper37a3 and plana626 match independent f690 ownership review: one17-byte clone insertion and a single plan reference change; original instrumented test37220 unchanged. Runner529/debughelper9c/launcher/gate remain byte-identical to r328, preserving strict raw/SHA and all caps. This changed input does not repair old r328 evidence.'},
  {'id':'B06','status':'CLOSED_STATIC','detail':'All five execution/authority leaves absent; binding.json and prepare.started.json absent. Actual metadata binder/scopebuilder exit0 and stdout/stderr pins verified. Scope execution_authorized=true is conditional configuration; actual CAS/seal/unique grant remain required.'},
  {'id':'B07','status':'OPEN_ACTUAL_EXECUTION','detail':'Source597/compiler22138/catalog metadata and prior reviews are reused. No complete historical resource backing-tree rehash occurred. Future fresh graph/generated files/exes/actual hFile closure, fixture-after vectors and time fit remain unproved.'}
 ],
 'scope_delta_keys':a['facts']['scope_delta_keys'],'template_delta_keys':a['facts']['template_delta_keys'],'mapped_origins':a['facts']['mapping'],
 'execution_conditions':[
  'Only Root actual r329 CAS and sealed registration plus unique matching grant can enable the single finite execution. This review grants nothing.',
  'Exactly real-existing-open-readonly and real-existing-self-send; preserve14 planned native calls<=16, images61+three built artifacts<=64, compiler600/case510/test480, inner3300/outer3600/cleanup5 and all process/Job caps.',
  'Preserve separate upstream32/proxy32 per-case budgets and128 complete-observation qualification limit. Unobserved client outbound hard cap remains NULL.',
  'SDK/MODEL/Node/external/paid/private calls0. No product/canonical/source/index mutations. New instrumentation is export-only and requires newly built artifacts.',
  'Unknown loaded module still stops; rejected-load diagnostics never become authorized successful modules.',
  'First unexpected failure stops dependent execution and preserves original raw records/nullable exits; no same-input retry or historical failure reset.',
  'Both cases require actual HTTP byte integrity, business/identity evidence, closed DB copy evidence and all native/fixture-after vectors before qualification. Native/build PASS alone does not qualify current43 or Desktop15.'
 ],
 'limitations':{'OS_lifecycle_complete':None,'future_Go_graph_complete':None,'time_fit_proved':False,'Python_resources':'POINT_IN_TIME_NOT_LIFECYCLE','r328_qualification':'WITHHELD; four nonempty requested digest mismatches and raw records preserved','whole43_product_acceptance':False,'Desktop15_acceptance':False,'formal_42_acceptance':False,'current_resource_tree_rehash_claim':False},
 'failure_accounting':'Own locator89547b is one outer1/nativeNULL event, outside fixed12. No canonical counter or scope cut was changed. The actual audit0df523 passed all289 checks.',
 'status':'STOPPED'}
save('review.json',review)
save('handoff.json',{'schema':'researchos.independent-review-handoff.v1','reviewer':review['reviewer'],'decision':review['decision'],'review_ref':ref(O/'review.json'),'audit_ref':ref(O/'audit.json'),'expected_before':review['expected_before'],'expected_after':review['expected_after'],'actual_candidate_executed':False,'new_failure_origins':[origin],'status':'STOPPED'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'schema':'researchos.independent-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True})
print(json.dumps({k:ref(O/k) for k in ['review.json','manifest.json','handoff.json','failure-origin.89547b.json']},ensure_ascii=False))
