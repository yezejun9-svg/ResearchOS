import json,hashlib,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path('D:/作品集/ResearchOS/research-os')
parent=root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
out=parent/'builder-stdout-fix';wt=root/'.local/worktrees/desktop-builder-stdout-20261104'
base='e0fc197321a92fcb5952e7d112f3f6c356bd309a'
def put(path,value):
    temp=path.with_name(path.name+'.new');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(temp,path)
def git(cwd,*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf-8')
cpfile=root/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw)
assert cp['revision']==583 and len(cp['failure_counters'])==2375
assert git(root,'rev-parse','HEAD').strip()==base and not wt.exists() and not out.exists()
failure=parent/'development-build/build-01/commands/client-wire-source-build/stderr.raw'
assert b'UnicodeDecodeError' in failure.read_bytes()
out.mkdir();(out/'author').mkdir();(out/'reviews').mkdir();(out/'tools').mkdir()
(out/'checkpoint.cp583.before.json').write_bytes(raw)
now=datetime.now(timezone.utc).isoformat()
scope={'scope_id':'DESKTOP_BUILDER_STDOUT_FIX_20261104','base_head':base,'owner':'codex:/root/workbench_builder','integrator':'codex:/root','worktree':str(wt),'source_paths':['apps/desktop/build-validator.py'],'purpose':'Preserve raw native mklink stdout without decoding it as UTF8; retain strict default decoding, invocation/raw evidence and exit/timeout refusal. No codepage changes or global replacement errors.','allowed_checks':'Pure mocked command outcomes against actual function source, py_compile, diff-check. No native/model/provider or mklink execution by author.','failure_origin':'compatibility-development-bundle-20261104','failed_build_attempt':1,'next_build_attempt':2,'first_failure_ref':str(failure.relative_to(root)),'first_failure_sha256':hashlib.sha256(failure.read_bytes()).hexdigest(),'formal_increment':0,'counter_reset':False,'at':now}
put(out/'scope.json',scope)
git(root,'worktree','add','--no-checkout','-b','codex/desktop-builder-stdout-20261104',str(wt),base)
git(wt,'sparse-checkout','set','--no-cone','/AGENTS.md','/apps/desktop/build-validator.py');git(wt,'checkout','HEAD')
assert not git(wt,'status','--porcelain=v1','-uno').strip()
cp['failure_counters'].append({'at':now,'origin_key':'20261104|compatibility-development-bundle|attempt1','attempts':1,'failure_origin':scope['failure_origin'],'attempt_index':1,'exit':1,'status':'DEVELOPMENT_BUILD_ENCODING_FAILURE','detail':'mklink itself exited0; OEM Chinese stdout strict-UTF8 decode raised UnicodeDecodeError in builder. Original failed partial r3 and logs retained; no product runtime, inference or native qualification.','source_ref':{'path':scope['first_failure_ref'],'sha256':scope['first_failure_sha256']},'counter_reset':False})
resume={'checkpoint_revision':584,'status':'IMPLEMENTING_DESKTOP_BUILDER_STDOUT_FIX','base_head':base,'worktree':str(wt),'scope_ref':str((out/'scope.json').relative_to(root)),'failed_r3_preserved':True,'old_r2_preserved':True,'next_build_attempt':2,'next_output':'development-ui-20261104-r4','formal_accepted':0,'formal_required':42,'counter_reset':False,'failure_records':len(cp['failure_counters']),'next':'Freeze and independently review one-file stdout fix, integrate source, build fresh r4 attempt2 under the same failure origin. Then build separate CLI binary; no native/model replay.'}
put(out/'RESUME.json',resume)
cp['expected_previous_revision']=583;cp['revision']=584;cp['updated_at']=now;cp['next_command']=resume['next']+' Read '+str((out/'RESUME.json').relative_to(root))
cp['current_implementation']={'status':resume['status'],'at':now,'resume_ref':str((out/'RESUME.json').relative_to(root)),'active_construction_owners':[scope['owner']],'formal_increment':0}
assert cpfile.read_bytes()==raw;put(cpfile,cp)
handoff=root/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(out/'handoff.cp583.before.md').write_bytes(before)
prefix=b'# Current resume CP584\n\nRead execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/builder-stdout-fix/RESUME.json. Desktop r3 attempt1 failed only after successful mklink emitted OEM Chinese decoded as UTF8. Logs/partial r3 and old r2 preserved. One-file source fix active; future r4 is same-origin attempt2, not counter reset. CLI source integrated e0fc1973, standalone binary pending. No native/model execution or formal acceptance.\n\n'
temp=handoff.with_name(handoff.name+'.cp584.new');temp.write_bytes(prefix+before);os.replace(temp,handoff)
print(json.dumps({'checkpoint':584,'failure_records':len(cp['failure_counters']),'worktree':str(wt),'next_build_attempt':2}))
