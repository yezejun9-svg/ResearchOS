from pathlib import Path
import hashlib,json,datetime
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((R/name).read_bytes())
def pin(name):
 p=R/name;return{'ref':name,'sha256':sha(p),'bytes':p.stat().st_size}
def save(name,v):
 p=R/name;assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
i=read('inputs.json');focused=read('focused.result.json');vet=read('vet.result.json');nd=read('no-drift.json')
assert focused['exit_code']==0 and focused['counts']=={'run':38,'pass':38,'fail':0,'skip':0}
assert vet['exit_code']==0 and nd['C_author_and_current_exact3_match'] and nd['source_sha256']==i['source_sha256']
diag=read('author/diagnostics.json')
attempts=diag['diagnostic_events'];assert len(attempts)==2 and all(x['origin_key']=='source-context-baseline-sparse-closure' for x in attempts)
events=[{'origin_key':'source-context-baseline-sparse-closure','classification':'AUTHOR_BASELINE_SETUP_OR_FRESH_FIXTURE_CARRYFORWARD','failed_attempt_count':2,'attempts':attempts,'baseline_resolution':diag['baseline_resolution'],'raw_refs':['author/attempt-01/test.jsonl','author/attempt-01/test.result.json','author/attempt-02/test.jsonl','author/attempt-02/test.result.json'],'status':'RESOLVED_BASELINE_RESTORATION_BEFORE_FINAL_AUTHOR_AND_INDEPENDENT_TESTS','do_not_recount_existing_occurrences':True,'counter_reset':False}]
report={'schema':'researchos.source-context.independent-source-review.v1','reviewer':'codex:/root/implementation_review','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'decision':'APPROVED_SOURCE_FIXTURE_ONLY','formal_increment':0,'product_acceptance_increment':0,'pending_blockers':[],
 'scope_id':'PRODUCT_V1_REGISTERED_SOURCE_CONTEXT','scope_revision':2,'base_head':i['base_head'],'source_sha256':i['source_sha256'],'source_count':3,'production_count':1,'test_count':2,
 'manifest_sha256':i['author_pins']['final/source-manifest.json'],'source_manifest_sha256':i['author_pins']['final/source-manifest.json'],'freeze_sha256':i['author_pins']['final/freeze.json'],'summary_sha256':i['author_pins']['final/summary.json'],'author_diagnostics_sha256':i['author_pins']['diagnostics.json'],
 'manifest_ref':'author/final/source-manifest.json','freeze_ref':'author/final/freeze.json','source_readback':pin('no-drift.json'),'inputs':pin('inputs.json'),
 'independent_focused':{'exit_code':0,'run':38,'pass':38,'fail':0,'skip':0,'top_pass':8,'sub_pass':30,'existing_author_selected_case_events':33,'independent_case_events':5,'result':pin('focused.result.json'),'command':pin('focused.command.json'),'stdout':pin('focused.stdout.raw'),'stderr':pin('focused.stderr.raw'),'roster':focused['roster']},
 'independent_vet':{'exit_code':0,'tests_executed':0,'ref':'vet.result.json','sha256':sha(R/'vet.result.json'),'command':pin('vet.command.json'),'stdout':pin('vet.stdout.raw'),'stderr':pin('vet.stderr.raw')},
 'independent_boundaries':['Derived execution input overflow, canonical user prompt oversize and invalid Host path UTF8 reject before executable open/directory/pipe/Job/BeforeResume; no dispatch directory created','Actual owned Go fake child receives the JSON over actual stdin, echoes original Host source/owned process cwd and exact user_request; fake source-context text in user prompt never replaces Host fields','Child actual Getwd equals owned cwd while source_context.source_workspace remains authorized source; original owned source sentinel unchanged','Original 64KiB including escaped user bytes and independent1MiB derived limit covered without truncation','Original fake FAIL/WAIT/UNKNOWN, revocation/stale authority and atomic UNKNOWN terminal fault behaviors preserved by same focused set'],
 'source_review':{'static':pin('static-review.json'),'canonical_prompt_and_api_untouched':'Only driver production file changed. It derives execution-only JSON from existing Host Workspace/Directory and exact original Prompt; canonical request storage/hash/idempotency contract not changed.','native_arguments_permissions_cwd_unchanged':True,'domain_test_change':'Only embedded owned fake program changed; all following fixture/Coordinator/UNKNOWN/CAS/atomic fault assertions identical to previously approved source after line-ending normalization.','actual_pipe_write':'adapters/runtime/codex_driver_windows.go:317 writes executionInput, not the unannotated Prompt','budget_prelaunch':'adapters/runtime/codex_driver_windows.go:126-143 keeps original user validation and constructs bounded context before filesystem/process side effects'},
 'static_peer_review':{'reviewer':'codex:/root/implementation_review/prompt_flow_review','source_pin_check_tool':'3d9167','decision':'NO_P1_P2_FOUND_IN_SOURCE_CONTEXT_SCOPE','note':'No tests executed by static peer; dynamic fixtures here are separate.'},
 'diagnostic_events':events,'author_readonly_locator_notes':diag['readonly_discovery_notes'],'diagnostic_policy':'Carry both existing failed attempts under the same original sparse-baseline origin, preserving0tests/24adapterPASS+9fresh-setupFAIL raw and Root baseline-repair manifests. Do not recount existing occurrences or erase/reset historical counters. No independent failed command/test in this review.',
 'limitations':['This approves source and fixtures only. No real Codex/model or real context-following behavior was exercised; Root actualbuild05/freshflow02 remains separate.','Execution context is location metadata and explanatory instructions, not a privilege/permission bridge or proof that a model will follow instructions.','Owned Job stop/drain facts are not filesystem isolation proof; previous PLATFORM_POLICY and real readonly/cancel verification limits remain.','Actual child is the owned Go test executable under existing fixtureArgs/env; domain tests use fresh C temporary SQLite, not user databases/auth/profile state.','Input/source artifact cardinality, public rev2 DTO and ordinary Mu semantics are not expanded.'],
 'execution_class':'EXACT3_C_OVERLAY_WITH_READONLY_D_BASELINE_DEPENDENCIES_LOCKED_OFFLINE_GO_ACTUAL_OWNED_FAKE_PROCESSES_AND_FRESH_DB','real_Codex_or_model':False,'no_D_source_writes':True,
 'archive_file_list':'archive-file-list.json','evidence_manifest':'EVIDENCE-MANIFEST.json','pending_operations':[],'uncertain_outcomes':[],'counter_reset':False}
save('report.json',report)
files=[]
for p in sorted(R.rglob('*')):
 if p.is_file() and not any(x in ['private','__pycache__'] for x in p.relative_to(R).parts) and p.name not in ['archive-file-list.json','EVIDENCE-MANIFEST.json']:
  files.append({'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
save('EVIDENCE-MANIFEST.json',{'schema':'researchos.independent-source-evidence.v1','root':str(R),'files':files,'excluded':['private temp/profile','reused Go cache','module input cache'],'formal_increment':0})
save('archive-file-list.json',[v['path'] for v in files]+['EVIDENCE-MANIFEST.json'])
print(json.dumps({'decision':report['decision'],'report':str(R/'report.json'),'report_sha256':sha(R/'report.json'),'archive_file_list_sha256':sha(R/'archive-file-list.json'),'evidence_manifest_sha256':sha(R/'EVIDENCE-MANIFEST.json'),'files':len(files),'formal_increment':0}))
