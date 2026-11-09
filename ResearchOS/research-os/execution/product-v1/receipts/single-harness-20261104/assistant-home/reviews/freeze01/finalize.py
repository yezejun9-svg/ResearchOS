from pathlib import Path
import datetime,hashlib,json,zipfile
R=Path(__file__).resolve().parent;RUN=R/'run-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def obj(name):return json.loads((R/name).read_bytes())
def pin(name):
 p=R/name;return{'ref':name,'sha256':sha(p),'bytes':p.stat().st_size}
def save(name,v):
 p=R/name;assert not p.exists(),str(p);p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
i=obj('run-01/inputs.json');nd=obj('run-01/no-drift.json');assert nd['exact8_match_current_worktree_author_and_C'] and nd['module_cache_unchanged']
assert i['source_sha256']==nd['source_sha256'] and len(i['source_sha256'])==8
assert sha(Path(i['node']))==i['node_sha256']=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
checks=[]
for name in ['required-tests','mu-first-use','independent-tests','main-full-syntax','vite-build']:
 result=obj('run-01/'+name+'.result.json');assert result['exit_code']==0
 command=obj('run-01/'+name+'.command.json');assert command['node_sha256']==i['node_sha256']
 refs={suffix:pin('run-01/'+name+'.'+suffix) for suffix in ['result.json','command.json','started.json','stdout.raw','stderr.raw','controller.py.txt']}
 assert refs['stdout.raw']['sha256']==result['stdout_sha256'] and refs['stderr.raw']['sha256']==result['stderr_sha256']
 checks.append({'name':name,**result,'evidence':refs})
assert checks[0]['tap_summary']['pass']==58 and checks[1]['tap_summary']['pass']==1 and checks[2]['tap_summary']['pass']==10
build=obj('run-01/vite/outputs.json');assert len(build['files'])==3 and build['cache_unchanged'] and build['source_unchanged']
author_diag=obj('run-01/author/final/diagnostics.json')
diagnostics=[{'origin_key':row['origin'],'source':'AUTHOR_DIAGNOSTICS_CARRYFORWARD_NOT_RECOUNTED',**row} for row in author_diag['events']]
diagnostics.append({'origin_key':'assistant-home-review-native-stdout-encoding-comparison','classification':'REVIEW_READONLY_COMPARE_ENCODING_FALSE_DIFFERENCE','raw_refs':['child:8fad72','child:48006a','child:5ddb9a'],'detail':'Initial PowerShell native git-output text comparison returned false despite command exit0. Explicit UTF8 comparison against base d9d correctly established unchanged Mu/Codex and route bodies. No product defect or source/test change from initial false comparison.'})
assert len(set(row['origin_key'] for row in diagnostics))==len(diagnostics)
static={'reviewer':'codex:/root/implementation_review/prompt_flow_review','decision':'NO_EVIDENCED_P1_P2_IN_FROZEN_EXACT8','manifest_sha256':i['author_pins']['final/source-manifest.json'],'source_pins_matched':8,'facts':['Accessible listProjects data remains authoritative; recent ID preference intersects actual accessible projects and never creates permission','Theme defaults dark with saved explicit light preserved and denied storage handled','Native directory success requires actual project and workspace reference; explicit open button enters encoded project route without model/provider prerequisite','Host health uses existing independent flat statusHealth monitor; no V2 presentation ticket race and no new Harness capability authority','NativeModelConfiguration and DesktopQualification-through-EOF including Mu/Codex controllers, draft/IME/UNKNOWN/send/poll unchanged from base after only line-ending normalization','screens Workbench-through-EOF routes preserved from base; new assistant CSS scoped and token-based'],'raw_tool_refs':['child:5ab671','child:48006a','child:5ddb9a'],'preference_observation':'rememberProject updates the current actually-opened project timestamp when profile refreshes. This does not fabricate unopened projects or expand visibility; not a blocker.','limits':['Actual visual, responsive and accessibility behavior needs separately scoped GUI observation','Static review did not execute GUI/Native/model or DB']}
save('STATIC_REVIEW.json',static)
report={
 'schema':'researchos.assistant-home.independent-source-review.v1','reviewer':'codex:/root/implementation_review','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'decision':'APPROVED_SOURCE_FIXTURE_ONLY','formal_increment':0,'product_acceptance_increment':0,'pending_blockers':[],
 'scope_id':'PRODUCT_V1_ASSISTANT_HOME_AND_TRUE_HOST_STATUS','base_head':i['base_head'],'scope_sha256':i['scope_sha256'],
 'source_sha256':i['source_sha256'],'source_count':8,'production_count':7,'test_count':1,
 'manifest_sha256':i['author_pins']['final/source-manifest.json'],'source_manifest_sha256':i['author_pins']['final/source-manifest.json'],'freeze_sha256':i['author_pins']['final/FROZEN.json'],'summary_sha256':i['author_pins']['final/summary.json'],'author_diagnostics_sha256':i['author_pins']['final/diagnostics.json'],
 'manifest_ref':'run-01/author/final/source-manifest.json','freeze_ref':'run-01/author/final/FROZEN.json','source_readback':pin('run-01/no-drift.json'),
 'independent_checks':checks,'independent_vite':{'exit_code':0,'ref':'run-01/vite-build.result.json','outputs':pin('run-01/vite/outputs.json'),'output_files':3,'cache_unchanged':True,'source_unchanged':True},
 'counts':{'required_pass':58,'selected_mu_first_use_pass':1,'independent_pass':10,'combined_distinct_case_events':69,'fail':0,'skip':0,'syntax_and_compiler_checks_are_not_test_case_acceptances':True},
 'independent_case_scope':['Dark default/explicit saved light/invalid preference and denied storage','Recents retain only closed ID/time prefs, intersect actual accessibility, strip prompt/path/token fields','Project locator requires actual workspace reference and encodes project ID','Header health is independent from project event availability; incomplete/wrong health shape never green','Disposed old health lifecycle cannot overwrite a newer healthy result','Timed-out old health reply cannot cancel/settle the next check deadline','Private Main probe rejects same HostID/data-root swap before sending HTTP','Private Main probe rejects same HostID/data-root swap during response','401 credential refresh never automatically retries the command','Directory uncertainty invokes selection once, preserves input, and does not navigate/retry'],
 'required_case_scope':['Actual Main private AUTHORITY_READ + renderer read both complete in either order while ordinary display supersession is preserved','Private Symbol cannot be selected by renderer string; project/session/revision/writer authority ABA remains stale','Changed native host and entry/late pending barriers/write sequences remain blocked','Original Harness readonly/idempotency/UNKNOWN/cancel/decimal cursor/IME/activity cases preserved','Existing selected Mu native-first-use fixture retains real project/workspace semantics'],
 'resolved_context_findings':[
  {'origin_key':'desktop-smoke-native-status-displaces-first-entry-read','status':'SOURCE_AND_PURE_FIXTURE_RECHECKED','source_ref':'apps/desktop/main/main.js:84-86,461-463','detail':'SMOKE uses private Main smokeNativeProbe -> AUTHORITY_READ, no longer renderer presentation probe. Existing IPC/preload byte pins unchanged. No claim that ordinary fresh homepage intrinsically sends two host.status reads.'},
  {'origin_key':'desktop-header-project-events-misreported-as-host-health','status':'SOURCE_AND_PURE_FIXTURE_RECHECKED','source_ref':'apps/web/src/main.jsx:27-29,68; startup.js:58-84; components/app-shell.jsx','detail':'Actual project-independent health requires ok/status ready/scope DEVELOPMENT_ONLY/database sqlite. Project events and original write guards remain distinct. No fake green from bridge existence or events.online.'}
 ],
 'static_review':pin('STATIC_REVIEW.json'),'build_inputs':{'inputs':pin('run-01/inputs.json'),'immutable_C_files':len(i['files']),'necessary_baseline_dependencies':len(i['files'])-8,'full_repository_archive':'NOT_CREATED_OR_ATTEMPTED','cache_descriptor':pin('run-01/INPUTS-02.json'),'cache_inventory':pin('run-01/cache-inventory.json'),'node_sha256':i['node_sha256'],'unchanged_boundary_sha256':i['unchanged_boundary_sha256']},
 'diagnostic_events':diagnostics,'diagnostic_merge_policy':'Preserve original raw author failures and exact origins; aliases are not additional failures. Initial sparse-spec/line-ending/preparation diagnostics remain distinct from product assertions. No failure counter reset.',
 'limitations':['This accepts exact8 source and development fixtures only, not product/real GUI or model qualification. Formal and product increments remain0.','No Electron/GUI/Host Native API/real CLI/model/old DB/user-auth access occurred in this QA. Vite uses preapproved existing compiler native addons only; these are not product Native qualification.','Actual new desktop screenshot, responsive layout, keyboard/accessibility and real directory/Codex execution remain Root separately scoped.','Health demonstrates observed service readiness, not Harness execution/model/cancel/filesystem qualification or write authority.','Actual local recent IDs are view preferences and remain filtered by current accessible projects; current project profile refresh may update its opened timestamp.','Main source merging, protected old changes and control-state guards are integrator responsibilities; this reviewer verified frozen source/unchanged boundaries and cache, without claiming product state acceptance.'],
 'author_prior_evidence':{'manifest':pin('run-01/author/EVIDENCE_MANIFEST.json'),'archive_file_list':pin('run-01/author/archive-file-list.json'),'diagnostics':pin('run-01/author/final/diagnostics.json')},
 'evidence_manifest':'EVIDENCE-MANIFEST.json','archive':'evidence.zip','pending_operations':[],'uncertain_outcomes':[],'failure_counter_reset':False,'no_d_writes':True
}
save('review.json',report)
files=[]
for p in sorted(R.rglob('*')):
 if p.is_file() and not any(part in ['private','__pycache__'] for part in p.relative_to(R).parts) and p.name not in ['EVIDENCE-MANIFEST.json','evidence.zip','HANDOFF.json']:
  files.append({'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
manifest={'schema':'researchos.independent-source-evidence-manifest.v1','root':str(R),'files':files,'file_count':len(files),'total_bytes':sum(v['bytes'] for v in files),'scope':'EXACT8_AND_NECESSARY_FRONTEND_OR_PURE_TEST_DEPENDENCIES_AND_RAW_REPORTS_NO_GIT_ARCHIVE','formal_increment':0}
save('EVIDENCE-MANIFEST.json',manifest)
archive=R/'evidence.zip';assert not archive.exists()
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for row in files:z.write(R/row['path'],row['path'])
 z.write(R/'EVIDENCE-MANIFEST.json','EVIDENCE-MANIFEST.json')
with zipfile.ZipFile(archive) as z:
 for row in files:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
handoff={'review':pin('review.json'),'manifest':pin('EVIDENCE-MANIFEST.json'),'archive':pin('evidence.zip'),'decision':report['decision'],'formal_increment':0,'pending_blockers':[]}
save('HANDOFF.json',handoff)
print(json.dumps(handoff))
