import pathlib,json,hashlib,gzip,collections,concurrent.futures,datetime
H=pathlib.Path(__file__).resolve().parent
M=pathlib.Path('D:/作品集/ResearchOS/research-os')
I=M/'.local/independent-provider-typed-route-r288-d4fd01da69224e05a135e0b01794826c'
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
def ref(p):
 p=pathlib.Path(p);d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):d.update(b)
 return {'path':str(p),'sha256':d.hexdigest(),'bytes':p.stat().st_size}
def write(n,v):
 with (H/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def vec(p):return json.loads(gzip.decompress(pathlib.Path(p).read_bytes()))
def rows(v,t):
 r=v['tables'][t]['rows'];return [dict(zip(r['columns'],[None if x[0]=='null' else x[1] for x in json.loads(line)])) for line in r['typed_row_multiset']]
def rowset(v,t):return collections.Counter(v['tables'][t]['rows']['typed_row_multiset'])
def diffrows(b,a,t):
 c=rowset(a,t)-rowset(b,t);cols=a['tables'][t]['rows']['columns'];return [dict(zip(cols,[None if x[0]=='null' else x[1] for x in json.loads(line)])) for line,n in c.items() for _ in range(n)]
def budget(v):return {t:[r for r in rows(v,t) if r['kind'] in ['BudgetPolicy','BudgetLedgerEntry']] for t in ['domain_objects','domain_versions']}
P=H/'public-positive-1-evidence'
b=vec(P/'semantic-before.json.gz');a=vec(P/'semantic-after.json.gz');decoded=vec(P/'archive-proof/decoded-semantic.json.gz');restored=vec(P/'restored-before-open.json.gz')
assert b==a
newrefs=diffrows(decoded,restored,'domain_refs');removedrefs=list((rowset(decoded,'domain_refs')-rowset(restored,'domain_refs')).elements());assert not removedrefs
vs={(r['project'],r['kind'],r['id'],r['revision']):r for r in rows(restored,'domain_versions')}
objects={(r['project'],r['kind'],r['id']):r for r in rows(restored,'domain_objects')}
resolved=[];arrays=[]
for r in newrefs:
 owner=vs[(r['project'],r['kind'],r['id'],r['revision'])];value=json.loads(owner['body'])
 for part in r['field'].lstrip('/').split('/'):
  value=value[int(part)] if isinstance(value,list) else value[part]
 target=vs.get((r['target_project'],r['target_kind'],r['target_id'],r['target_revision']))
 record={'row':r,'owner_field_value':value,'target_historical_version_exists':target is not None}
 if isinstance(value,list):
  group=[x for x in newrefs if all(x[k]==r[k] for k in ['project','kind','id','revision','field'])]
  record['array_field_members_equal_target_multiset']=collections.Counter(value)==collections.Counter(x['target_id'] for x in group)
  record['target_current_revision_matches']=objects[(r['target_project'],r['target_kind'],r['target_id'])]['revision']==r['target_revision']
  arrays.append(record)
 resolved.append(record)
assert len(arrays)==1 and arrays[0]['row']['field']=='/active_goal_ids' and arrays[0]['array_field_members_equal_target_multiset']
changed=[t for t in sorted(set(decoded['tables'])|set(restored['tables'])) if decoded['tables'].get(t)!=restored['tables'].get(t)]
effects=diffrows(decoded,restored,'resource_effects');effect_proof=[]
for r in effects:
 body=json.loads(r['body']);orig=[x for x in rows(decoded,'resource_effects') if all(x[k]==r[k] for k in ['project','run','effect_key'])];latest=max(orig,key=lambda x:int(x['sequence']));lb=json.loads(latest['body'])
 effect_proof.append({'row':r,'original_latest':latest,'appended_UNKNOWN':body.get('state')=='UNKNOWN' or body.get('status')=='UNKNOWN','original_payload_equal':body.get('payload')==lb.get('payload'),'original_upper_bound_equal':body.get('upper_bound')==lb.get('upper_bound'),'original_identity_equal':all(body.get(k)==lb.get(k) for k in ['key','run_id','task_id','goal_id','epoch']),'sequence_plus_one':int(r['sequence'])==int(latest['sequence'])+1})
write('readonly-causal-row-audit.json',{'method':'Only parse already sealed gzip vectors; no new SQL/DB open/validator/case','source':ref(I/'internal/domain/store.go'),'producer_lines':'refs 237-296, ref INSERT 338; idTargets active_goal_ids Goal at172','before':ref(P/'archive-proof/decoded-semantic.json.gz'),'after':ref(P/'restored-before-open.json.gz'),'new_refs':resolved,'array_relations':arrays,'old_refs_multiset_preserved':True,'all_changed_tables':changed,'budget_ledger_policy_full_history_equal':budget(decoded)==budget(restored),'new_effect_rows':effect_proof,'complete_restore_delta_acceptance':False,'reason':'Overlay stopped during refs checks; this read-only diagnosis is not a replacement full public test pass.'})
plan=read(H/'case-plan.json');done=[]
for c in plan:
 result=H/(c['label']+'.result.json')
 if not result.exists():continue
 ev=[json.loads(l) for l in (H/(c['label']+'.stdout.raw')).read_text('utf-8').splitlines() if l.strip()]
 done.append({'label':c['label'],'exit':read(result)['exit'],'counts':{k:sum(1 for x in ev if x.get('Test') and x.get('Action')==k) for k in ['run','pass','fail','skip']},'invocation':ref(H/(c['label']+'.invocation.json')),'result':ref(result),'stdout':ref(H/(c['label']+'.stdout.raw')),'stderr':ref(H/(c['label']+'.stderr.raw'))})
assert len(done)==1 and done[0]['exit']==1 and done[0]['counts']=={'run':1,'pass':0,'fail':1,'skip':0}
actual=read(P/'actual.json');assert actual['restore_report']['status']=='RESTORED_RECONCILIATION_REQUIRED'
write('actual-case-audit.json',{'cases':done,'this_cohort_actual':1,'this_cohort_PASS':0,'this_cohort_FAIL':1,'this_cohort_SKIP':0,'not_run':[c['label'] for c in plan[1:]],'prior_internal64_PASS_retained_not_repeated':64,'prior_public_harnessFAIL_retained':1,'cumulative_actual':66,'cumulative_PASS':64,'cumulative_FAIL':2,'not_one_executable_76_PASS':True,'public_CreateBackup_calls':1,'public_RestoreBackup_calls':1,'rebackup_calls':0,'public_negative_calls':0,'first_unexpected_stopped':True})
write('public-partial-resource-chain.json',{'stage':'CREATE_DECODE_RESTORE_SUCCEEDED_OVERLAY_RELATION_CHECK_FAILED_BEFORE_REBACKUP','actual':ref(P/'actual.json'),'archive_manifest':ref(P/'archive/manifest.json'),'archive_files':[ref(x) for x in sorted((P/'archive').iterdir()) if x.is_file()],'decoded_chain':ref(P/'archive-proof/decoded-chain.json'),'decoded_files':[ref(x) for x in sorted((P/'archive-proof/decoded').iterdir()) if x.is_file()],'restored_closed_DB':ref(P/'restored/state.sqlite'),'restore_report':ref(P/'restored/restore-report.json'),'source_copied_DB':ref(P/'case.sqlite'),'source_full_semantic_before_after_equal':True,'no_original_workspace_binding':actual['original_all_workspace_binding_count']==0,'witness_callback_calls':0,'rebackup_not_invoked':True,'model_HTTP_Node_worker_paid':0})
write('public-overlay-relation-correction-proposal.json',{'status':'PROPOSED_NOT_APPLIED_NOT_AUTHORIZED','exact_edit':'Only new owned copy of independentRestoreDelta domain_refs branch; retain current immutable overlay and raw','original_overlay':ref(H/'independent_provider_public_boundary_windows_test.go'),'production_source':ref(I/'internal/domain/store.go'),'causal_evidence':ref(H/'readonly-causal-row-audit.json'),'cause':'Production refs expands relation-valued string arrays at the same field path; overlay compares resolved []any directly to scalar target_id. Actual one appended ProjectState /active_goal_ids ref is valid.','required_rule':['Generate the exact expected reference multiset from each producer-bound appended Run/ProjectState/EventEnvelope version, following actual relationKind and VersionRef recursion semantics, not a coarse relation-kind whitelist or contains-only test.','For relation-valued arrays, require every element string and compare complete per-owner/version/field target-ID multiplicity; reject missing/extra/duplicate refs inconsistent with original array. Empty arrays imply no refs. Require target_project/kind and actual target version selected at event production; preserve VersionRef exact ID/kind/revision/content_hash checks.','Retain all original domain_refs rows unchanged; no owner outside already validated producer-bound appended versions; no removal/update/foreign target. Retain all other restore event/project/run/ledger/queue/UNKNOWN checks.','Resolve scalar relation type from actual relationKind, including its special cases; retain current scalar and nested array VersionRef checks, add exact closure rather than skipping arrays.','Build new overlay/program and freeze complete actual inputs/binary before any new case; never claim old internal64 used this executable.'],'public_retry_request_if_authorized':{'positive_order':[1,0,2,3,4,5],'negative_count':6,'total_new_cases':12,'prior_internal64_not_repeated':True,'cumulative_if_all12_executed':78,'retained_failed_public_cases':2,'first_unexpected_stop':True},'source9_SQL_original7_changes':0,'model_HTTP_Node_worker_paid':0,'formal_increment':0})
originals=read(H/'original7.before.json')
for e in originals:
 for key in ['original','copy']:assert ref(e[key]['path'])==e[key]
scope=read(M/'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-independent-scope-r288/scope_registration.json');source9=[]
for e in scope['source9']:
 r=ref(e['actual']['path']);assert r==e['actual'];source9.append(r)
write('protected-source9-original7.after.json',{'source9':source9,'original7':originals,'drift':[]})
before=read(H/'before-first-case.json')['files'];current={}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
 for r in ex.map(ref,before):current[r['path']]=r
drift=[p for p,v in before.items() if current[p]!=v]
write('after-current-inputs.json',{'files':current,'count':len(current),'drift':drift,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
write('failure_origins.json',{'origins':[{'origin_id':'r292-public-positive1-overlay-array-relation-79e9ab97','kind':'INDEPENDENT_PUBLIC_TEST_HARNESS_FAILURE','invocation':done[0]['invocation'],'result':done[0]['result'],'stdout':done[0]['stdout'],'stderr':done[0]['stderr'],'native_exit':1,'driver_outer_exit':1,'outer_tool_chunk':'1364ee','count_once':True,'actual_case_count':1,'cause':'Terminal relation-valued []any compared to scalar target ID by independentRestoreDelta, after actual successful public Restore','product_P1':False}],'prior_failures_not_recounted':True,'old_model_history5_held':True,'old_P1three_retained':True,'expected_pending_file_rg_no_match_not_failure':True})
write('review.json',{'decision':'PUBLIC_COHORT_STOPPED_BY_INDEPENDENT_ARRAY_RELATION_HARNESS','candidate':'6fb5263681c17f0e50920c354dc07ed440a23714','source_composition_schema':22,'source2_accepted':False,'whole_original9_accepted':False,'Main23_verified':False,'formal_increment':0,'this_cohort_actual':1,'this_cohort_fail':1,'remaining_NOT_RUN':11,'prior_internal64_PASS_not_repeated':64,'prior_public_failure_retained':1,'cumulative_actual':66,'CreateBackup_decode_Restore_success_partial_only':True,'rebackup_and_complete_public_roundtrip_NOT_RUN':True,'frozen_inputs':len(before),'input_drift':drift,'binary':ref(H/'independent.domain.test.exe'),'refs':[ref(H/n) for n in ['actual-case-audit.json','readonly-causal-row-audit.json','public-partial-resource-chain.json','protected-source9-original7.after.json','after-current-inputs.json','failure_origins.json','public-overlay-relation-correction-proposal.json']],'old_author_history5_and_P1three_held':True,'private_MODEL_HTTP_Node_worker_paid':0})
files=[ref(x) for x in sorted(H.rglob('*')) if x.is_file()];write('manifest.json',{'files':files,'listed':len(files),'excludes':['manifest.json','handoff.json']})
write('handoff.json',{'decision':'STOPPED_HARNESS_CAUSE_NO_SOURCE_ACCEPTANCE','review':ref(H/'review.json'),'manifest':ref(H/'manifest.json'),'proposal':ref(H/'public-overlay-relation-correction-proposal.json'),'failure_origins':ref(H/'failure_origins.json'),'actual_cases_this_cohort':1,'cumulative_actual':66,'source_changes':0,'formal_increment':0})
print(json.dumps({n:ref(H/n) for n in ['review.json','manifest.json','handoff.json','public-overlay-relation-correction-proposal.json','failure_origins.json','readonly-causal-row-audit.json']},ensure_ascii=False,indent=2))
