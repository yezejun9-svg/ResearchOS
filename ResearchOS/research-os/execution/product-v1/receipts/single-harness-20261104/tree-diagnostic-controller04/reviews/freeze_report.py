from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;T=R.parent.parent
A=T/'product-v1-real-electron-tree-diagnostic-revision-04';O=T/'product-v1-real-electron-tree-diagnostic-revision-03'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):
 p=R/n;assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(A/'FROZEN.json')=='9ea24e6c15ca1d39ab0328a4c0db3c45ec064449b88b52f2692eefedb5ff84ce'
assert sha(A/'MANIFEST.json')=='88f49cbbba0d6a79770354d1fc6da5fbc409d835b394f0e3a415e9a90e8e2884'
m=json.loads((A/'MANIFEST.json').read_text());f=json.loads((A/'FROZEN.json').read_text())
for row in m['files']:
 p=A/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
for name,pin in f['source_sha256'].items():assert sha(A/name)==pin
assert sha(A/'real-electron-flow.mjs')==sha(O/'real-electron-flow.mjs')=='def290342be6417bff524cac2e0a3c0779429851e3c87160381600c268ca3eb6'
old=(O/'choose-owned-folder.ps1').read_bytes().decode('utf-8');new=(A/'choose-owned-folder.ps1').read_bytes().decode('utf-8')
start='function Project-TreeDiagnostic(';end='# These functions are pure string/evidence predicates.'
a,z=new.index(start),new.index(end,new.index(start));oa,oz=old.index(start),old.index(end,old.index(start))
reverse=(new[:a]+old[oa:oz]+new[z:]).replace('Project-TreeDiagnostic $element 0 $coreId','Project-TreeDiagnostic $element 0').replace('Project-TreeDiagnostic $selected[$i] $i $coreId','Project-TreeDiagnostic $selected[$i] $i')
assert reverse.encode('utf-8')==(O/'choose-owned-folder.ps1').read_bytes()
r=json.loads((R/'result.json').read_text());assert r['exit_code']==0 and sha(R/'stdout.raw')==r['stdout_sha256'] and sha(R/'stderr.raw')==r['stderr_sha256']
tests=json.loads((R/'stdout.raw').read_text());assert tests['passed']==3 and tests['foreign_name_reads']==tests['foreign_id_reads']==0 and tests['selected_owner_change_refused']
prior=R.parent/'revision03/report.json';assert sha(prior)=='4381f47ea3713acedcff385f5dc8733ef7473be2d7204a3e9688709e2dfc8ec9'
assert sha(A/'prior-review/report.json')==sha(prior)
put('report.json',{
 'schema':'researchos.independent-source-review.v1','decision':'APPROVED_SOURCE_FIXTURE_ONLY','formal_increment':0,'product_increment':0,'pending_blockers':[],
 'source_sha256':f['source_sha256'],'freeze_ref':str(A/'FROZEN.json'),'freeze_sha256':sha(A/'FROZEN.json'),'manifest_ref':str(A/'MANIFEST.json'),'manifest_sha256':sha(A/'MANIFEST.json'),'manifest_files_verified':len(m['files']),'no_drift':True,
 'resolved_findings':[{'origin_key':'direct-native-provider-metadata-before-owner-check','severity':'P2','status':'RESOLVED_SOURCE_FIXTURE_ONLY','prior_report_ref':str(prior),'prior_report_sha256':sha(prior),'fix':'Project-TreeDiagnostic itself requires positive owner, takes one Current snapshot and caches ProcessId before any other getter. Foreign owner emits fixed status/PID only; both root and selected calls pass coreId.','evidence_ref':str(R/'stdout.raw'),'evidence_sha256':sha(R/'stdout.raw')}],
 'independent_checks':{'case_groups':3,'exit_code':0,'ref':str(R/'result.json'),'command_ref':str(R/'command.json'),'raw_tool_chunk':'52cfe7','stdout_ref':str(R/'stdout.raw'),'stdout_sha256':sha(R/'stdout.raw'),'stderr_ref':str(R/'stderr.raw'),'stderr_sha256':sha(R/'stderr.raw'),'source_AST_syntax_exit':0,'method':'Actual AST projection/helper definitions only, using the original counted foreign getter counterexample plus selected-owner-change and owned positive snapshots. No helper entrypoint or native APIs.','foreign_Name_and_AutomationId_reads':0,'selected_owner_change_foreign_reads':0,'owned_Current_and_PID_reads_each':1,'powershell_sha256':'362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139'},
 'source_delta_proof':{'runner_byte_identical':True,'reverse_projector_and_two_calls_restores_entire_previous_helper_bytes':True,'old_CRLF_preserved':True,'old_noOK_zero_budget_ownership_UTC_env_cwd_Job_code_unchanged':True},
 'review_scope':'Close the confirmed P2 and preserve prior direct-HWND diagnostic-only source findings; no new selector, navigation, permission or production feature.',
 'reused_review':{'ref':str(prior),'reason':'Prior unique fresh owned Tree/IsChild/visibility/limited selected values and no-navigation/no-OK static findings unchanged. Previously blocked result and raw remain intact; no old path/date/env suites rerun or recounted.'},
 'qualification_limits':['Source/fixture approval is not actual UIA/provider path availability, folder authorization or product acceptance.','Direct values and absolute candidates remain nonauthorizing; a path printed by provider is not a validated selected workspace.','No SDK, helper entrypoint, Add-Type, UIA, GUI, Native, model, user auth/config or DB ran here.','Root must use one fresh exact-source zero-model diagnostic scope and original outer Job accounting. Unknown provider/cancel/close remains blocked; no arbitrary selector/path guess is permitted.'],
 'diagnostic_events':[{'origin_key':'direct-native-provider-metadata-before-owner-check','classification':'SOURCE_P2_FIXED_WITH_INDEPENDENT_AST_REGRESSION','status':'RESOLVED_SOURCE_FIXTURE_ONLY','old_counterexample_ref':str(R.parent/'revision03/owner-stdout.raw'),'new_ref':str(R/'stdout.raw'),'failure_history_retained':True}],
 'counter_reset':False,'pending_operations':[],'uncertain_outcomes':[]
})
files=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ['EVIDENCE-MANIFEST.json','archive-file-list.json']]
put('EVIDENCE-MANIFEST.json',{'schema':'researchos.independent-review-evidence.v1','files':files})
put('archive-file-list.json',[v['path'] for v in files]+[str(R/'EVIDENCE-MANIFEST.json')])
print(json.dumps({n:sha(R/n) for n in ['report.json','EVIDENCE-MANIFEST.json','archive-file-list.json']}))
