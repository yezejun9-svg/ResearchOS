from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;A=R.parent.parent/'product-v1-real-electron-tree-diagnostic-revision-03'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):
 p=R/n;assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(A/'FROZEN.json')=='2eb264828fdbf0242abb59b5bc2b849265bd51266f974359f62f856e99e58495'
assert sha(A/'MANIFEST.json')=='61aeabd65fac0a002cd24a43f1f0213bca5c3f72c69bd1cccc684d261bb5bc6e'
m=json.loads((A/'MANIFEST.json').read_text());f=json.loads((A/'FROZEN.json').read_text())
for row in m['files']:
 p=A/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
r=json.loads((R/'owner-result.json').read_text());assert r['exit_code']==0 and sha(R/'owner-stdout.raw')==r['stdout_sha256']
assert sha(R/'owner-stdout.raw')=='43c2aded4bc391d7a74f2095acc16b940ec485100e88d2dfef4260183b73ffe1'
put('report.json',{
 'schema':'researchos.independent-source-review.v1','decision':'REQUIRES_CHANGES','formal_increment':0,'product_increment':0,
 'source_sha256':f['source_sha256'],'manifest_ref':str(A/'MANIFEST.json'),'manifest_sha256':sha(A/'MANIFEST.json'),'freeze_ref':str(A/'FROZEN.json'),'freeze_sha256':sha(A/'FROZEN.json'),'manifest_files_verified':len(m['files']),'no_drift':True,
 'pending_blockers':[{'id':'P2-OWNER-BEFORE-PUBLIC-METADATA','origin_key':'direct-native-provider-metadata-before-owner-check','severity':'P2','summary':'Foreign provider public Name/AutomationId values are read and emitted before checking Current.ProcessId.','source_refs':['choose-owned-folder.ps1:65','choose-owned-folder.ps1:90','choose-owned-folder.ps1:94','choose-owned-folder.ps1:411','choose-owned-folder.ps1:413','choose-owned-folder.ps1:442'],'evidence_ref':str(R/'owner-stdout.raw'),'evidence_sha256':sha(R/'owner-stdout.raw'),'minimum_fix':'Require expected owner inside Project-TreeDiagnostic itself. Obtain one Current snapshot, check its ProcessId before any Name/AutomationId/value read; on foreign PID emit only fixed unavailable state and necessary identity facts. Pass this protection through both root and selected metadata calls; an outer precheck followed by another unguarded Current fetch is insufficient.'}],
 'counterexample':{'method':'Extract actual AST definitions only, supply synthetic Current ProcessId99 and a counted Name getter; expected owner42. Actual metadata projection invokes getter once and records the returned Name before the later read-pattern owner gate.','exit_code':0,'foreign_name_reads':1,'raw_tool_chunk':'461cd0','ref':str(R/'owner-result.json'),'command_ref':str(R/'owner-command.json'),'stdout_ref':str(R/'owner-stdout.raw'),'stdout_sha256':sha(R/'owner-stdout.raw'),'stderr_sha256':sha(R/'owner-stderr.raw'),'powershell_sha256':'362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139'},
 'second_static_reader':{'agent':'prompt_flow_review','agrees_P2':True,'details':'Current metadata projection precedes Read-PublicPatterns owner gate; catch retains trees current with already-read Name. Selected path also re-fetches Current for metadata after an earlier guard, so same-snapshot check belongs inside projector.'},
 'other_narrow_findings':'Fresh child enumeration, single owned visible/enabled SysTreeView32 and IsChild revalidation, at most four selection records and nonauthorizing candidate flags remain. No new reachable navigation/IDOK path was found. These findings do not approve the blocked source.',
 'diagnostic_events':[{'origin_key':'direct-native-provider-metadata-before-owner-check','classification':'SOURCE_P2_CONFIRMED_WITH_PURE_AST_COUNTEREXAMPLE','status':'OPEN_REQUIRES_NEW_FREEZE','raw_tool_chunk':'461cd0','ref':str(R/'owner-stdout.raw'),'runtime_resource_calls':0}],
 'limits':['No helper entrypoint/Add-Type/UIA/SDK/GUI/Native/model, user auth/config or DB was executed/accessed.','Old date/env/cwd/Job and earlier diagnostic tests were not rerun or recounted.','This design is still diagnostic-only, zero task/model and normal owned Cancel. The P2 does not authorize navigation or product acceptance.'],
 'counter_reset':False,'pending_operations':[],'uncertain_outcomes':[]
})
files=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(R.iterdir()) if p.is_file() and p.name not in ['EVIDENCE-MANIFEST.json','archive-file-list.json']]
put('EVIDENCE-MANIFEST.json',{'schema':'researchos.independent-review-evidence.v1','files':files})
put('archive-file-list.json',[v['path'] for v in files]+[str(R/'EVIDENCE-MANIFEST.json')])
print(json.dumps({n:sha(R/n) for n in ['report.json','EVIDENCE-MANIFEST.json','archive-file-list.json']}))
