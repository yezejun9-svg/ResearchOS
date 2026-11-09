import pathlib,json,hashlib,gzip,collections,concurrent.futures,datetime
H=pathlib.Path(__file__).resolve().parent;M=pathlib.Path('D:/作品集/ResearchOS/research-os');O=H.parent/'79e9ab97-1451-4537-94db-e8259c9c67fa';INTERNAL=H.parent/'cc88ef8c-d066-4b10-b6c5-1d9bba89baad'
def read(p):return json.loads(pathlib.Path(p).read_text('utf8'))
def ref(p):
 p=pathlib.Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return {'path':str(p),'sha256':h.hexdigest(),'bytes':p.stat().st_size}
def write(n,v):
 with (H/n).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def vec(p):return json.loads(gzip.decompress(pathlib.Path(p).read_bytes()))
def rows(v,t):
 r=v['tables'][t]['rows'];return [dict(zip(r['columns'],[None if x[0]=='null' else x[1] for x in json.loads(s)])) for s in r['typed_row_multiset']]
def budget(v):return {t:[r for r in rows(v,t) if r['kind'] in ['BudgetPolicy','BudgetLedgerEntry']] for t in ['domain_objects','domain_versions']}
def full_delta(b,a):
 diff={}
 for name in sorted(set(b['tables'])|set(a['tables'])):
  bt=b['tables'].get(name);at=a['tables'].get(name)
  if bt==at:continue
  br=bt['rows'] if bt else {};ar=at['rows'] if at else {};bc=collections.Counter(br.get('typed_row_multiset',[]));ac=collections.Counter(ar.get('typed_row_multiset',[]))
  diff[name]={'before_columns':br.get('columns'),'after_columns':ar.get('columns'),'removed_complete_typed_rows':list((bc-ac).elements()),'added_complete_typed_rows':list((ac-bc).elements())}
 return {'schema_before':b['schema'],'schema_after':a['schema'],'all_tables':len(set(b['tables'])|set(a['tables'])),'tables_changed':diff,'unchanged_tables':[t for t in sorted(set(b['tables'])&set(a['tables'])) if b['tables'][t]==a['tables'][t]]}
summary=read(H/'execution-summary.json');assert summary['actual_cases']==12 and not summary['drift']
records=[];pairs=[];resource_chains=[];negative_causes=[];all_deltas={}
for case in read(H/'case-plan.json'):
 label=case['label'];d=H/(label+'-evidence');actual=read(d/'actual.json');spec=read(H/'specs'/(label+'.json'));r=read(H/(label+'.result.json'));ev=[json.loads(l) for l in (H/(label+'.stdout.raw')).read_text('utf8').splitlines() if l.strip()];counts={k:sum(1 for x in ev if x.get('Test') and x.get('Action')==k) for k in ['run','pass','fail','skip']}
 assert r['exit']==0 and counts=={'run':1,'pass':1,'fail':0,'skip':0} and actual['test_failed']==False
 assert actual['model_calls']==actual['HTTP']==actual['worker_starts']==0
 b=vec(d/'semantic-before.json.gz');a=vec(d/'semantic-after.json.gz');changed=[t for t in sorted(set(b['tables'])|set(a['tables'])) if b['tables'].get(t)!=a['tables'].get(t)];assert b['schema']==a['schema'];assert budget(b)==budget(a)
 record={'case':label,'exit':0,'counts':counts,'invocation':ref(H/(label+'.invocation.json')),'result':ref(H/(label+'.result.json')),'stdout':ref(H/(label+'.stdout.raw')),'stderr':ref(H/(label+'.stderr.raw')),'actual':ref(d/'actual.json')};records.append(record)
 pairing={'case':label,'input_sha256':actual['input_sha256'],'pre_open_sha256':actual['pre_open_sha256'],'closed_sha256':actual['closed_sha256'],'full_schema_equal':True,'changed_tables':changed,'budget_before':budget(b),'budget_after':budget(a),'input_copy':ref(spec['input']),'source_closed_DB':ref(d/'case.sqlite'),'before':ref(d/'semantic-before.json.gz'),'after':ref(d/'semantic-after.json.gz')}
 if spec['mode']=='positive':
  assert b==a and actual['public_roundtrip_proven']==True
  restored=vec(d/'restored-before-open.json.gz');closed=vec(d/'restored-closed.json.gz');assert restored==closed and budget(b)==budget(restored)
  chains=[]
  for archive,proof in [('archive','archive-proof'),('rebackup','rebackup-proof')]:
   manifest=read(d/archive/'manifest.json');decoded=vec(d/proof/'decoded-semantic.json.gz');resources=[]
   for entry in manifest['files']:
    item=ref(d/proof/'decoded'/entry['name']);assert 'sha256:'+item['sha256']==entry['hash'] and item['bytes']==entry['size'];resources.append(item)
   if spec['id']!='0':assert not any(x['name'].startswith('workspace-') for x in manifest['files'])
   chains.append({'archive_manifest':ref(d/archive/'manifest.json'),'encrypted_files':[ref(x) for x in sorted((d/archive).iterdir()) if x.is_file()],'decoded_chain':ref(d/proof/'decoded-chain.json'),'decoded_resources':resources,'decoded_full_semantic':ref(d/proof/'decoded-semantic.json.gz'),'decoded_semantic_equal_expected':decoded==(b if archive=='archive' else restored),'inventory':manifest['inventory']})
   assert decoded==(b if archive=='archive' else restored)
  all_deltas[label]=full_delta(b,restored)
  pairing['restored_before_open']=ref(d/'restored-before-open.json.gz');pairing['restored_closed']=ref(d/'restored-closed.json.gz');pairing['rebackup_left_restored_all_rows_unchanged']=True
  chain={'case':label,'public_CreateBackup':True,'actual_decode':True,'public_RestoreBackup':True,'public_rebackup':True,'chains':chains,'restore_report':ref(d/'restored/restore-report.json'),'restored_DB':ref(d/'restored/state.sqlite'),'recovery':actual['restore_report']['recovery'],'restore_delta':actual['restore_delta'],'original_inventory':actual['original_inventory'],'restored_inventory':actual['restored_inventory'],'synthetic_workspace':actual['synthetic_workspace']}
  assert actual['original_inventory']==actual['restored_inventory']
  if spec['id']=='0':
   assert len(actual['synthetic_backup_callbacks'])==len(actual['synthetic_rebackup_callbacks'])==len(actual['restore_pins'])==1
   for k,archive in [('synthetic_backup_callbacks','archive'),('synthetic_rebackup_callbacks','rebackup')]:
    cb=actual[k][0];assert pathlib.Path(cb['destination'])==d/archive and cb['principal']=='fixture-author' and cb['synthetic']==True and cb['original_filesystem_read']==False and cb['witness_bytes']==31 and cb['witness_hash']=='sha256:321924650b928275a3593273f011175b8f1d4b041976c35d74f41540ad611a54'
   witness=list((d/'restored/workspaces').rglob('evidence.txt'));assert len(witness)==1;wf=ref(witness[0]);assert wf['bytes']==31 and wf['sha256']=='321924650b928275a3593273f011175b8f1d4b041976c35d74f41540ad611a54';chain['actual_restored_witness']=wf
   chain['synthetic_backup_callbacks']=actual['synthetic_backup_callbacks'];chain['synthetic_rebackup_callbacks']=actual['synthetic_rebackup_callbacks'];chain['restore_pins']=actual['restore_pins'];chain['real_original_filesystem_restored_claim']=False
  else:assert actual['original_all_workspace_binding_count']==0
  resource_chains.append(chain)
 else:
  assert actual['public_refusal_proven']==True and not (d/'archive').exists() and set(changed)<= {'runtime_dispatches','resource_effects'}
  # Exact public-copy corruption: all original SQL schema/triggers restored, delete dispatch rows,
  # and strip only MODEL payload.provider_transport; never infer a more specific refusal than raw.
  assert rows(a,'runtime_dispatches')==[]
  before_effects=rows(b,'resource_effects');after_effects=rows(a,'resource_effects');assert len(before_effects)==len(after_effects)
  byid={x['rowid']:x for x in after_effects}
  for x in before_effects:
   y=byid[x['rowid']];assert {k:v for k,v in x.items() if k!='body'}=={k:v for k,v in y.items() if k!='body'}
   xb=json.loads(x['body']);yb=json.loads(y['body'])
   if xb.get('payload',{}).get('capability')=='MODEL':xb['payload'].pop('provider_transport',None)
   assert xb==yb
  negative_causes.append({'case':label,'mutations':actual['mutations'],'actual_public_refusal':actual['backup_error'],'public_archive_not_published':True,'raw':ref(H/(label+'.stdout.raw')),'actual':ref(d/'actual.json'),'boundary':'CreateBackup prepublication only; no corrupt archive Restore attempt','provider_inventory_stage_reached':spec['id']!='0','fixture0_earlier_queue_guard':spec['id']=='0'})
 pairs.append(pairing)
assert len(resource_chains)==len(negative_causes)==6
write('actual-cases-audit.json',{'cases':records,'this_exe_PASS':12,'this_exe_FAIL':0,'this_exe_SKIP':0,'prior_internal64_PASS':64,'prior_publicFAIL_retained':2,'cumulative_actual':78,'cumulative_PASS':76,'cumulative_FAIL':2,'not_single_executable_76_or78_PASS':True,'no_new_case_or_SQL_in_this_seal':True})
write('full-semantic-budget-pairs.json',{'pairs':pairs,'physical_byte_change_not_conflated_with_semantic_drift':True,'old_author_case02_still_historically_unproven':True})
(H/'restore-all-typed-row-deltas.json.gz').write_bytes(gzip.compress(json.dumps(all_deltas,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
write('public-resource-chains.json',{'positive6':resource_chains,'schema22_only':True,'fixture0_workspace':'SYNTHETIC fixed31byte boundary; never original filesystem capture or restoration','complete_row_delta_ref':ref(H/'restore-all-typed-row-deltas.json.gz')})
write('public-refusal-causes.json',{'negative6':negative_causes,'exact2_causal_inventory_stage_proof':'Five public fixtures fail at original MODEL dispatch/legacy provenance inventory; sameRun fixture0 stops earlier at BACKUP_QUEUE_REQUEST_OR_PROCESS_BINDING. Internal64 separate-exe proof carries its targeted inventory controls.','malformed_archive_Restore_tested':False})
originals=read(H/'original7.before.json')
for e in originals:
 for k in ['original','copy']:assert ref(e[k]['path'])==e[k]
source9=[]
for x in read(M/'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-independent-scope-r288/scope_registration.json')['source9']:
 assert ref(x['actual']['path'])==x['actual'];source9.append(x['actual'])
write('protected-source9-original7.after.json',{'source9':source9,'original7':originals,'drift':[]})
old=(O/'independent_provider_public_boundary_windows_test.go').read_text('utf8');new=(H/'independent_provider_public_boundary_windows_test.go').read_text('utf8');lo=old.index('\trefs := independentNewRows(t, before, after, "domain_refs")');hi=old.index('\t// Every original effect row remains.',lo);nlo=new.index('\t// Independent frozen producer reconstruction:');nhi=new.index('\t// Every original effect row remains.',nlo);assert old[:lo]==new[:nlo] and old[hi:]==new[nhi:]
write('actual-gofmt-boundary-proof.json',{'old_overlay':ref(O/'independent_provider_public_boundary_windows_test.go'),'new_overlay':ref(H/'independent_provider_public_boundary_windows_test.go'),'prefix_byte_equal':True,'suffix_byte_equal':True,'new_branch_lines':[new[:nlo].count('\n')+1,new[:nhi].count('\n')],'no_top_level_helper_added':True})
before=read(H/'before-first-case.json')['files'];after=read(H/'after-cases.json')['files'];assert before==after;current={}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
 for r in ex.map(ref,before):current[r['path']]=r
drift=[p for p,v in before.items() if current[p]!=v];assert not drift
write('final-current-inputs.json',{'files':current,'count':len(current),'drift':drift,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
write('failure_origins.json',{'new_origins':[],'prior_public_failure_refs':[ref(INTERNAL/'failure_origins.json'),ref(O/'failure_origins.json')],'prior_prepare_failures_retained':True,'old_history5_held':True,'old_P1three_retained':True,'failure_reset':False})
write('review.json',{'decision':'EXACT2_REPAIR_SOURCE_READY_WITH_SCHEMA22_PUBLIC_PROOF_AND_DECLARED_OPEN_GATES','reviewer':'codex:/root/w05_merge_review','candidate':'6fb5263681c17f0e50920c354dc07ed440a23714','source_acceptance_scope':['internal/domain/runtime_model_verification.go','internal/domain/runtime_provider_binding_windows_test.go'],'scope_relationship':'Exact2 repair evaluated in fixed original9 candidate composition; not whole-original9 source qualification','whole_original9_SOURCE_READY':False,'Main23_verified':False,'LIVE_runtime_provider_qualified':False,'formal_increment':0,'this_public_cohort':{'PASS':12,'FAIL':0,'SKIP':0,'inputs':len(before),'drift':[],'binary':ref(H/'independent.domain.test.exe')},'prior_nonself_internal64':{'review':ref(INTERNAL/'review.json'),'binary':ref(INTERNAL/'independent.domain.test.exe'),'PASS':64,'not_repeated':True},'cumulative':{'actual':78,'PASS':76,'FAIL_retained':2,'single_executable_PASS_claim':False},'public':{'complete_roundtrip':6,'corrupted_copy_CreateBackup_refusal':6,'public_provider_inventory_refusal_stage':5,'earlier_queue_refusal_stage':1,'corrupt_archive_Restore_not_tested':True},'proof_refs':[ref(H/n) for n in ['actual-cases-audit.json','full-semantic-budget-pairs.json','public-resource-chains.json','public-refusal-causes.json','protected-source9-original7.after.json','actual-gofmt-boundary-proof.json','final-current-inputs.json','failure_origins.json']],'limitations':['Original author model history5 and held positive qualification remain stopped; no new MODEL/HTTP/Node/worker/paid/private/vault calls.','Public source22 consumer proof; Main23 and handler composition not tested.','Fixture0 synthetic31byte workspace/source metadata and new restore pin only; no original user workspace restored.','Old incomplete case02 byte difference is not retroactively repaired by newly paired independent semantic vectors.','No full original9 or parent/A04/LIVE acceptance; Root owns integration/canonical decisions.'],'model_HTTP_Node_worker_paid_private':0})
fs=[ref(p) for p in sorted(H.rglob('*')) if p.is_file()];write('manifest.json',{'files':fs,'listed':len(fs),'excludes':['manifest.json','handoff.json']});write('handoff.json',{'decision':'EXACT2_REPAIR_SOURCE_READY_WITH_SCHEMA22_PUBLIC_PROOF_AND_DECLARED_OPEN_GATES','review':ref(H/'review.json'),'manifest':ref(H/'manifest.json'),'failure_origins':ref(H/'failure_origins.json'),'public_chains':ref(H/'public-resource-chains.json'),'public_causes':ref(H/'public-refusal-causes.json'),'current_vector':ref(H/'final-current-inputs.json'),'public12_PASS':12,'old_internal64_PASS_retained':64,'cumulative_actual':78,'retained_publicFAIL':2,'whole9_Main23_LIVE_formal':False})
print(json.dumps({n:ref(H/n) for n in ['review.json','manifest.json','handoff.json','failure_origins.json','public-resource-chains.json','public-refusal-causes.json','final-current-inputs.json']},ensure_ascii=True))
