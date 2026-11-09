from pathlib import Path
import hashlib,json
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;P=R/'execution/v2.4/receipts/W13/W13-03'
B=P/'desktop15_root_scope_binding_executor_codex/8792799f829a23452ae5d89a59e1b0cf'
T=P/'desktop15_root_scope_binding_preparation_codex/5097ef19e4414a81b6457363a3b76060'
A=P/'desktop15_root_parameters_codex/8792799f829a23452ae5d89a59e1b0cf'
def path(v):
 p=Path(v);return p if p.is_absolute() else R/p
def pin(v):
 p=path(v);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def doc(v):return json.loads(path(v).read_bytes())
def verify(r):
 actual=pin(r['path']);assert actual['sha256']==r['sha256'] and actual['bytes']==r['bytes'];return path(r['path'])
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
 return pin(O/n)
checks=[]
def ck(v,label):checks.append({'check':label,'passed':bool(v)})
audit=doc(O/'audit.json');assert not audit['failed']
b=doc(B/'binding.prepared.json');s=doc(B/'scope.bound.proposed.json');act=doc(B/'scope.activation-plan.json')
annex=doc(A/'RESUME.bound.pending-review.manifest.json');ck(pin(A/'RESUME.bound.pending-review.manifest.json')['sha256']=='98a2ebf49795299df2d0f019f70e995cb5b8a4955d574f4710c51196a727936e','outer annex fixed MF')
ck(annex['count']==len(annex['entries'])==2,'annex two members')
for x in annex['entries']:verify(x)
outer=doc(A/'binding-tool-observations.closed.json');ck(outer['actual_outer_exit']==outer['actual_python_native_exit']==0 and outer['polls'][-1]['result']['exit_code']==0 and 'actualNativeExit=0' in outer['polls'][-1]['result']['output'],'actual outer bridge zero')
cut=doc(verify(b['origin_cut_ref']));ck(cut['confirmed_origins']==b['confirmed_pending_origins'],'cut exact rows')
oldcut=doc(verify(cut['historical_cut6_ref_preserved']));ck(oldcut['confirmed_origins']==cut['confirmed_origins'][:6],'old six complete payload prefix')
cp=doc(verify(b['canonical_before_refs'][0]));ow=doc(verify(b['canonical_before_refs'][1]));ck(not {x['origin'] for x in b['confirmed_pending_origins']} & {x.get('origin') for x in cp['failure_counters']},'new origin IDs not in old509')
ck(cp['current_effective_formal_status']['formal_cases_accepted']==0,'formal remains0')
ck((R/'.git/HEAD').read_bytes().strip()==b'ref: refs/heads/main' and (R/'.git/refs/heads/main').read_text().strip()==s['expected_cli43_head'],'direct HEAD branch bytes without Git')
def tree(name):
 d={}
 for row in (B/name).read_bytes().split(b'\0'):
  if row:
   header,name=row.split(b'\t',1);m,k,h=header.decode().split();d[name.decode('utf-8')]={'mode':m,'kind':k,'blob':h}
 return d
base=tree('tree2cdb.stdout.raw');live=tree('tree43.stdout.raw')
ck(live==doc(verify(s['logical43_tree_ref'])),'saved full tree equals logical43')
changed={x for x in set(base)|set(live) if base.get(x)!=live.get(x)}
ck(changed==set(s['shared38_paths'])|set(s['cli8_paths']) and len(changed)==43,'full tree exactly43 source-only')
protected=doc(B/'protected.actual-current43.json');expected=doc(verify(s['protected_source_paths_ref']))
ck(sorted(path(x['path']).relative_to(R).as_posix() for x in protected)==expected,'6983 complete declared public membership')
ck((R/'.gitattributes').read_bytes()==b'* -text\n','unchanged exact root attributes')
copies=[]
for name,rr in zip(['checkpoint','path_ownership','step_state','commands'],b['canonical_before_refs']):
 raw=verify(rr).read_bytes()
 with (O/(name+'.observed.json')).open('xb') as f:f.write(raw)
 copies.append(pin(O/(name+'.observed.json')))
ck(not path(s['registration_namespace']).exists() and not path(s['new_output_root']).exists(),'no registered scope or executor yet')
assert all(x['passed'] for x in checks),checks
sup=save('supplement.json',{'checks':checks,'count':len(checks),'failed':[],'outer_observation_ref':pin(A/'binding-tool-observations.closed.json'),'outer_annex_manifest_ref':pin(A/'RESUME.bound.pending-review.manifest.json'),'actual_target_executions':0,'new_failure_origins':[]})
chain=[
 {'producer':'build-metadata-templates.py:77-97','consumer':'metadata-engine desired / controller grant_check','fact':'Bound authorized=false is transformed only in serialized future payload; exactly authorized/status change, future scope hash62d704 verified; no scope file or grant now.'},
 {'producer':'build-metadata-templates.py:101-122','consumer':'current independent scope review','fact':'Requires exact W05 reviewer, future scope/controller/launcher/bound/builder/engine pins and sealed review member; no hash cycle because future scope contains no this-review SHA.'},
 {'producer':'metadata-engine.template.py desired','consumer':'register + future emitted metadata review','fact':'Deep copies before CP/OW; append exact7 origins after unchanged509; permitted WIP lease only; preserves HEAD/formal/otherownership; ST/CM emitted bytes identical. Actual desired4 not yet emitted or claimed verified.'},
 {'producer':'metadata-engine.template.py register','consumer':'controller grant_check lines295-324','fact':'Two CP/OW replacements only; original/desired refs and unchanged ST/CM in intent; all4 byte CAS before and immediately after each long source_guard, done hashes, final target4 verified; forward-only no auto rollback/retry.'},
 {'producer':'metadata-engine.template.py run/review_ok','consumer':'controller independent metadata review + invocation','fact':'Exact W05 reviewer, tuple and register/run/prepared/audit hashes, ordered four original bytecopies; owned child native nullable, raw stream hashes retained. Future emitted code/desired4 still requires separate independent review.'},
 {'producer':'metadata-engine.template.py seal','consumer':'grant + controller registration refs','fact':'Checks register/run absence of failure, actual runtime-after files, child0 and Job cleanup, intent/done/verified/desired4; only then materializes exact scope, audit before/after and original invocation refs; manifest emitted after runtime closure.'},
 {'producer':'metadata-engine.template.py grant','consumer':'controller grant_check lines253-324','fact':'Verifies full sealed registry and actual registration; exact scope_ref, review_ref, canonical_path/ref copies, registration_refs keys manifest/audit/invocation/intent/verified match consumer. Fresh UUID grant parent must be safely prepared by Root; source controller rechecks actual4 before mutation.'},
 {'producer':'controller7c863 and launcher3669','consumer':'future once-only source import','fact':'Same reviewed 1 apply/1 commit/80 Git; no receipt FF; full43/15 disjoint58 and protected6983, raw rootattrs, disabled hooks/filters, actual runtime unknown-reject and failure preservation retained. Point-in-time Python resources are not lifecycle proof.'}
]
mapping=save('producer-consumer-map.json',{'schema':'researchos.desktop15-metadata-static-interface-map.v1','entries':chain,'mode_imported':False,'template_executed':False,'actual_metadata_generated':False,'actual_CAS_executed':False})
oldreview=P/'desktop15_cli_qualification_gate_independent_review_codex/aff685f45a2a428cbdb90eb2f14d7977/review.json'
review={
 'schema':'researchos.desktop15-source-integration-controller-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_EXACT15_SOURCE_COMMIT_ONCE_WITH_OPEN_GATES','requested_changes':[],
 'actual_integration_executed':False,'source_acceptance':False,'formal_increment':0,
 'scope_sha256':act['future_scope_ref']['sha256'],'controller_sha256':s['controller_ref']['sha256'],'launcher_sha256':s['launcher_ref']['sha256'],'bound_proposal_sha256':b['scope_ref']['sha256'],'metadata_template_builder_sha256':pin(T/'build-metadata-templates.py')['sha256'],'metadata_engine_sha256':pin(T/'metadata-engine.template.py')['sha256'],
 'future_scope_ref':act['future_scope_ref'],'bound_proposal_ref':b['scope_ref'],'binding_ref':pin(B/'binding.prepared.json'),'binding_manifest_ref':pin(B/'manifest.json'),'activation_plan_ref':b['activation_plan_ref'],
 'controller_ref':s['controller_ref'],'launcher_ref':s['launcher_ref'],'metadata_template_builder_ref':pin(T/'build-metadata-templates.py'),'metadata_engine_ref':pin(T/'metadata-engine.template.py'),
 'expected_before':[331,159,509],'expected_after':[332,160,516],'current_source_head':s['expected_cli43_head'],'candidate':s['candidate'],'canonical_before':b['canonical_before_refs'],'copied_canonical_before_refs':copies,
 'audit_ref':pin(O/'audit.json'),'supplement_ref':sup,'producer_consumer_map_ref':mapping,'observed_inputs_ref':pin(O/'observed-inputs.json'),'origin_mapping_ref':pin(O/'origin-mapping.json'),
 'checks_passed':audit['count']+len(checks),'checks_failed':0,'distinct_actual_hashed_inputs':audit['distinct_hashed_refs'],'full_protected_paths_current_hash_checked':6983,'binding_manifest_actual_members_checked':42,
 'execution_evidence':{'Root_scope_builder_outer_exit':0,'Root_scope_builder_explicit_Python_exit':0,'owned_readonly_Git_calls':10,'all_actual_native_exit':0,'all_Job_idle_handles_closed_errors_empty':True,'raw_outer_evidence_ref':pin(A/'binding-tool-observations.closed.json'),'note':'Tool objects and explicit bridge, not an independently captured raw outer native stream. This reviewer executed no candidate or Git.'},
 'bounds':{'source_existing':9,'source_absent':6,'exact_paths':15,'existing_combined_paths':43,'resulting_unique_paths':58,'apply_cap':1,'commit_cap':1,'Git_cap':80,'controller_observed_seconds':900,'outer_job_seconds':1200,'cleanup_seconds':5,'runtime_catalog_entries':1212,'runtime_delta':'old1211 payload verbatim plus exact pinned Git cmd/git.exe only','candidate_runtime_tests':0},
 'origin_integrity':{'before_prefix':509,'new_unique_origin_count':7,'new_rows_equal_original_full_payloads':True,'old_cut6_prefix_preserved':True,'old_failed_binding_retained':True,'failed_binding_Python_exit':1,'failed_binding_child_native_exit':None,'counter_reset':False,'this_review_new_failures':0},
 'reused_reviews':[pin(oldreview),s['desktop_source_review_ref'],s['cli43_execution_review_ref'],s['main38_execution_review_ref'],s['cli43_bounded_qualification_refs']['review_ref']],
 'reuse_declaration':'Reuses sealed full gate inverse/original assertion review and prior actual bounded2/Go3/source review; current audit hashes actual fixed binding members, 8844 immutable inputs and protected6983. No recompilation, case replay, SQL inspection, or new lifecycle claim.',
 'remaining_gates':['Actual emitted register/run/seal/grant scripts and desired4 require separate independent registration review.','Only Root actual successful CAS332, closed seal and fresh exclusive grant may authorize the exact source15 import; this artifact is not a grant.','Root safely prepares required executor/grant parent directories; UUID leaf creation remains exclusive.','Actual Main58 source-import closure and post-head registration still pending.','Fresh combined58 compile, independent current Desktop169 replay, installedGUI, NVDA, BrowserContinuity, native frame, P02/SDK and formal42 remain OPEN.','No inherited author169 PASS as Root current replay; existing Go3 qualification remains DEBUG-only bounded evidence.','Python resource observation is point-in-time, not full OS lifecycle; future unknown resources stop execution.'],
 'new_failure_origins':[],'status':'STOPPED'
}
rr=save('review.json',review)
save('tool-observations.json',{'actual_audit_initial':{'chunk_id':'99b24b','session_id':31398},'actual_audit_completion':{'chunk_id':'7ec248','exit_code':0,'explicit_PythonNativeExit':0},'readonly_locator_tool_chunks_exit0':['c523fe','ad1b4d','c1c7de','9c6733','ba1e99','0e87d7','021074'],'new_failure_origins':[],'target_executions':0,'canonical_writes':0})
hr=save('handoff.json',{'schema':'researchos.public-review-handoff.v1','reviewer':'codex:/root/w05_merge_review','decision':review['decision'],'review_ref':rr,'manifest_path':str(O/'manifest.json'),'future_scope_ref':act['future_scope_ref'],'checks_passed':review['checks_passed'],'new_failure_origins':[],'actual_integration_executed':False,'status':'STOPPED'})
rows=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mr=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','count':len(rows),'entries':rows,'self_excluded':True})
print(json.dumps({'review':rr,'manifest':mr,'handoff':hr,'checks':review['checks_passed'],'new_failures':0},ensure_ascii=False))
