from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';N=P/'integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4';O=Path(__file__).parent
def path(x):
 p=Path(x);return p if p.is_absolute() else R/p
def ref(x):
 p=path(x);r=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(r).hexdigest(),'bytes':len(r)}
def doc(x):return json.loads(path(x).read_bytes())
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
a=doc(O/'audit.json');p=doc(N/'prepared_refs.json');b=p['binding'];assert len(a['checks'])==24453 and not a['failed_checks']
for original,copied in zip(p['canonical_before'],a['copied_canonical_before_refs']):
 actual=ref(original['path']);assert actual['sha256']==original['sha256'] and actual['bytes']==original['bytes'];assert path(copied['path']).parent==O and path(copied['path']).read_bytes()==path(original['path']).read_bytes()
save('audit.execution.json',{'auditor_derivation_tool':'c655de','audit_tool':'19bec1','actual_outer_exit':0,'actual_native_python_exit':0,'explicit_exit_LASTEXITCODE':True,'stdout_ref':ref(O/'audit.stdout.raw'),'stderr_ref':ref(O/'audit.stderr.raw'),'check_count':24453,'failed_checks':0,'target_executions':0,'new_failure_origins':[]})
review={'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','requested_changes':[],'actual_registration_executed':False,
 'expected_before':[328,156,469],'expected_after':[329,157,481],
 'register_sha256':ref(N/'register.py')['sha256'],'wrapper_sha256':ref(N/'run.py')['sha256'],'prepared_refs_sha256':ref(N/'prepared_refs.json')['sha256'],'audit_sha256':ref(N/'audit.json')['sha256'],'sealer_sha256':ref(N/'seal.py')['sha256'],
 'canonical_before':p['canonical_before'],'copied_canonical_before_refs':a['copied_canonical_before_refs'],
 'scope_ref':p['scope_ref'],'binding_ref':ref(N/'binding.json'),'registration_draft_manifest_ref':ref(N/'registration-draft.manifest.json'),'independent_audit_ref':ref(O/'audit.json'),'audit_execution_ref':ref(O/'audit.execution.json'),'reused_bound_scope_review_ref':b['controller_review_ref'],
 'metadata_module_ref':next(x for x in b['metadata_code_refs'] if 'metadata_pipeline.v7.proposed.py' in x['path']),
 'findings':[
  'All62 actual draft manifest members match bytes. Final binding differs only by inserting actual independent controller review efcef49; prepared binding and ROOT-relative scope ref match the exact producer/consumer schema.',
  'Four current canonical files equal original snapshots and ordered immutable copies inside this review directory. Desired329/157/481 changes only CP revision/previous revision/stamp/actor/failure append and three parsed WIP keys, plus OW revision/stamp/actor. Every other CP/OW field is preserved; ST/CM exact bytes unchanged.',
  'Complete old469 failure prefix plus the exact12 original payloads is preserved. Three mapped leaf records equal their original container new_origins indexed rows and retain original native NULL or numeric exits. Propagated r328 launcher/inner failure remains one underlying event. Later pending events are outside this fixed cut.',
  'Three saved owned Git invocations have native0, complete assignment/resume/primary exit/Job idle/handle closure and empty cleanup errors. Actual saved HEADa510, status894B/13rows/11oldD and empty index agree. Direct current HEAD is unchanged; no reviewer Git invocation occurred.',
  'Successful Python point-time records match pinned runtime/controller refs, strict successful-observation marker remains true and lifecycle proof false. This metadata observation proves no future compiler/tool/CLI lifecycle closure.',
  'Prepared verified refs were compared with approved compiler/runtime/source catalog metadata; other refs were independently hashed. No complete backing-tree rehash is claimed. Prior289 scope checks, f690 helper correction,2685967 failed-run closure and unchanged v7 full producer/consumer review are explicitly reused.',
  'The actual v7 source retains immutable original/desired intent, all-four guard immediately before each replace after resource/source checks, cache invalidation, final all-four verification, and forward-only recovery requiring separate Root decision. Review schema/actor/four SHA fields and same-parent ordered canonical copies exactly match registration_review.',
  'All five future execution/authorization/preflight/export leaves are absent; registration intent/invocation have not begun. Only Root may execute this reviewed registration once; seal and unique grant remain required before finite cases.'
 ],
 'audit_statistics':a['facts'],'limitations':['No register/run/seal/grant, product, Go, SQL, HTTP or helper was executed by reviewer.','Future current43 graph/generated artifacts/actual module closure/case qualification/time fit remain open.','This review does not qualify old r328 HTTP evidence, accept source/Main/Desktop15, or increment formal cases.'],
 'formal_increment':0,'source_acceptance':False,'target_executions':0,'new_failure_origins':[],'status':'STOPPED'}
save('review.json',review)
save('handoff.json',{'schema':'researchos.independent-review-handoff.v1','reviewer':review['reviewer'],'decision':review['decision'],'review_ref':ref(O/'review.json'),'audit_ref':ref(O/'audit.json'),'expected_before':review['expected_before'],'expected_after':review['expected_after'],'actual_registration_executed':False,'new_failure_origins':[],'status':'STOPPED'})
entries=[ref(x) for x in sorted(O.iterdir()) if x.is_file() and x.name!='manifest.json'];save('manifest.json',{'schema':'researchos.independent-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True})
print(json.dumps({x:ref(O/x) for x in ['review.json','manifest.json','handoff.json']},ensure_ascii=False))
