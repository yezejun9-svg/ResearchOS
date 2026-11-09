import hashlib,json,os,shutil,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path('D:/作品集/ResearchOS/research-os')
source=Path(__file__).resolve().parent
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def put(path,value):
    temporary=path.with_name(path.name+'.new');temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(temporary,path)
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=root).decode('utf-8')
cpfile=root/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw)
assert cp['revision']==586 and len(cp['failure_counters'])==2380
assert raw==(source/'checkpoint.baseline.json').read_bytes()
assert git('rev-parse','HEAD').strip()=='556cdc353f47167e5609f23291bf2746e3c8896f'
identity=json.loads((root/'execution/project_identity.json').read_bytes());assert identity['project_id']==cp['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
protected=json.loads((root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json').read_bytes())['protected_preserved']
for path,digest in protected.items():assert (sha(root/path) if (root/path).is_file() else 'ABSENT_BEFORE')==digest,path
assert not out.exists(),'Inspect uncertain state before replay'
out.mkdir();(out/'reviews').mkdir();(out/'tools').mkdir();(out/'resources').mkdir();(out/'sandbox-progress').mkdir()
(out/'checkpoint.cp586.before.json').write_bytes(raw)
(out/'git-tracked.before.txt').write_text(git('status','--porcelain=v1','-uno'),encoding='utf-8')
snapshot=[]
def copy_file(relative):
    original=source/relative;target=out/'sandbox-progress'/relative
    assert original.is_file() and not original.is_symlink()
    before=original.read_bytes();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(before)
    assert original.read_bytes()==target.read_bytes()
    snapshot.append({'path':relative,'sha256':hashlib.sha256(before).hexdigest(),'bytes':len(before)})
for relative in ['SESSION.json','RESUME.json','PENDING_HANDOFF.md','README.md','loopback-capability.json','review_staged_assets.py','check_loopback_capability.py','finalize_pending.py','start_repository_resume.py']:
    copy_file(relative)
for directory in ['w14-diagnosis','contract-design','reviews','pure-scalar/evidence','pure-scalar/reviews','pure-scalar/tools']:
    for file in sorted((source/directory).rglob('*')):
        if file.is_file():copy_file(file.relative_to(source).as_posix())
for relative in ['pure-scalar/go.mod','pure-scalar/validate.go','pure-scalar/validate_test.go','pure-scalar/README.md']:
    copy_file(relative)
for file in sorted((source/'owned-model-resource').iterdir()):
    if file.is_file():copy_file(file.relative_to(source).as_posix())
put(out/'sandbox-progress-manifest.json',{'status':'VERIFIED_METADATA_SOURCE_AND_EVIDENCE_SNAPSHOT','files':snapshot,'assets_binary_models_and_caches_not_duplicated':True,'assets_retained_at':str(source/'owned-model-resource'),'binding_schema_and_server_controller_still_C_work_in_progress':True})
now=datetime.now(timezone.utc).isoformat();initial=cp['failure_counters'][:]
pending=[
 {'origin_key':'20261104|cp586-native-git-transport','status':'EXEC_TRANSPORT_PRE_EXECUTION_FAILURE','tool_cell':'106','detail':'Elevated read-only Git check failed CreateProcess before execution. No D writes. Parent later supplied connected evidence; one retry fe959c/17ad56 succeeded.'},
 {'origin_key':'20261104|pure-scalar-missing-helper','status':'C_ONLY_TEST_COMPILATION_FAILURE_PRESERVED','failure_origin':'cli-pure-scalar-missing-test-helper-20261104','attempt_index':1,'exit':1,'detail':'Missing assertRejected helper prevented tests; original attempt01 retained. Same-origin attempt2 helper-only fix passed all10 author test functions; implementation itself unchanged.'},
 {'origin_key':'20261104|resource-service-metadata','status':'READONLY_OS_METADATA_DIAGNOSTIC','tool_chunk':'1b0233','exit':0,'detail':'Service Control Manager metadata denied; services UNKNOWN. No startup/request/inference.'},
 {'origin_key':'20261104|default-loopback-capability','status':'SANDBOX_CAPABILITY_DENIED','tool_chunk':'6f5138','exit':0,'winerror':10013,'detail':'One self-owned ephemeral loopback probe denied by default sandbox. No existing endpoint contacted, no Ollama process or request. Higher execution profile must be separately checked.'},
 {'origin_key':'20261104|w14-read-diagnostic-group','status':'READONLY_SOURCE_QUERY_DIAGNOSTIC_GROUP','detail':'W14 diagnosis retained earlier Windows rg wildcard/absent-path diagnostics; exact source and chunk refs archived under sandbox-progress/w14-diagnosis. No test/native failure inferred.'},
 {'origin_key':'20261104|contract-design-read-diagnostic-group','status':'READONLY_SOURCE_QUERY_DIAGNOSTIC_GROUP','detail':'Six source query diagnostics preserved in construction source-index (2dd000/29ce6b/8da081/7ab2b2/870f6e/8e3210). No product or primitive test failure inferred.'}
]
for item in pending:cp['failure_counters'].append(dict(at=now,attempts=1,counter_reset=False,**item))
assert cp['failure_counters'][:2380]==initial
put(out/'diagnostic-import.json',{'before':2380,'after':len(cp['failure_counters']),'prefix_preserved':True,'records':pending,'mixed_development_diagnostics_not_native_failure_count':True})
reconnection={'at':now,'native_chunks':['fe959c','17ad56'],'actual_head':cp['current_Main_HEAD'],'permanent_project_id':identity['project_id'],'checkpoint_before':586,'unconfirmed_D_writes':0,'server_starts_before_resume':0,'model_inference_before_resume':0,'related_process_metadata_chunk':'144289','related_processes_observed':[],'old_protected_paths_preserved':True,'old_CP575_consumed_scope_unchanged':True}
put(out/'reconnection.json',reconnection)
resume={'checkpoint_revision':587,'status':'NATIVE_RECONNECTED_C_CANDIDATES_ARCHIVED_CONTINUING_IMPLEMENTATION','main_head':cp['current_Main_HEAD'],'reconnection_ref':str((out/'reconnection.json').relative_to(root)),'sandbox_snapshot_ref':str((out/'sandbox-progress-manifest.json').relative_to(root)),'formal_accepted':0,'formal_required':42,'formal_increment':0,'failure_records':len(cp['failure_counters']),'counter_reset':False,'current_card':'W05-99','active_sandbox_scopes':['C binding-schema prototype with stable issuer-qualified anchor policy','C owned-server metadata controller preparation; no startup approved yet'],'next':'Finish/freeze/review binding schema candidate and bounded owned-server controller. Recheck higher-profile loopback capability. Register real D worktree scopes before integrating the validated pure source primitive or W14 handoff code. No old native/model replay; ordinary LIVE503 remains.'}
put(out/'RESUME.json',resume)
cp['expected_previous_revision']=586;cp['revision']=587;cp['updated_at']=now;cp['next_command']=resume['next']+' Read '+str((out/'RESUME.json').relative_to(root))
cp['current_implementation']={'status':resume['status'],'at':now,'resume_ref':str((out/'RESUME.json').relative_to(root)),'active_construction_owners':['codex:/root/workbench_builder C schema','codex:/root/runtime_readiness C server controller'],'formal_increment':0}
assert cpfile.read_bytes()==raw;put(cpfile,cp)
handoff=root/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(out/'handoff.cp586.before.md').write_bytes(before)
prefix=('# Current resume CP587\n\nRead '+str((out/'RESUME.json').relative_to(root))+'. Native connection reverified, same identity/HEAD, no uncertain prior D writes or model starts. Verified C pure-source primitive, model assets and W14/design evidence archived; product integration still pending. Stable-anchor policy corrected; ordinary LIVE503 retained. Counters preserved, formal0/42.\n\n').encode()
temp=handoff.with_name(handoff.name+'.cp587.new');temp.write_bytes(prefix+before);os.replace(temp,handoff)
print(json.dumps({'checkpoint':587,'head':cp['current_Main_HEAD'],'archived_files':len(snapshot),'failure_records':len(cp['failure_counters']),'formal_increment':0}))
