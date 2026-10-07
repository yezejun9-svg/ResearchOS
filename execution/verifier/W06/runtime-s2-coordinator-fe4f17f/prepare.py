from pathlib import Path
import subprocess,json,hashlib,os
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];REV='fe4f17f';SNAP=OUT/'source-checkout'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def command(args,cwd):
 r=subprocess.run(args,cwd=cwd,capture_output=True);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout
command(['git','clone','--shared','--no-checkout',str(ROOT),str(SNAP)],OUT)
command(['git','sparse-checkout','set','--no-cone','/adapters/','/apps/','/internal/','/ops/','/tests/','/bootstrap/','/evaluation/','/migrations/','/spec/','/contracts/','/qualification/','/release/','/execution/command_dispatcher/','/execution/commands.json','/execution/toolchains/locked.json','/go.mod','/go.sum','/.gitattributes','/.gitignore','/AGENTS.md'],SNAP)
command(['git','checkout','--detach',REV],SNAP)
assert not command(['git','status','--porcelain'],SNAP).strip()
source=OUT/'source';source.mkdir();overlay={}
name='internal/domain/runtime_coordinator_windows_test.go';raw=git('show',REV+':'+name).decode();(source/'original_runtime_coordinator_windows_test.go').write_text(raw,encoding='utf-8')
line='\tfmt.Printf("{\\"sequence\\":1,\\"type\\":\\"context.ready\\",\\"payload\\":{\\"input_hash\\":%q}}\\n", Digest(raw))\n'
assert line in raw
raw=raw.replace(line,'',1).replace('\tsequence := 2','\tsequence := 1\n\tif request["task_type"] == "runtime_qualification" {\n'+line+'\t\tsequence = 2\n\t}',1)
raw=raw.replace('\tc, route, r := coordinatorFixtureMode(t, effect)\n\tqualifyNativeCoordinator', '\tc, route, r := coordinatorFixtureMode(t, effect)\n\tt.Cleanup(func() { verifierSaveCoordinator(t, c) })\n\tqualifyNativeCoordinator',1)
(OUT/'malicious_coordinator_test.go').write_text(raw,encoding='utf-8');overlay[str(SNAP/name)]=str(OUT/'malicious_coordinator_test.go')
overlay[str(SNAP/'internal/domain/verifier_coordinator_test.go')]=str(OUT/'coordinator_observe_test.go')
overlay[str(SNAP/'adapters/runtime/verifier_bridge_test.go')]=str(OUT/'bridge_probe_test.go')
put(OUT/'overlay.json',{'Replace':overlay})
files=['adapters/runtime/bridge_windows.go','internal/domain/runtime_coordinator_windows.go','internal/domain/runtime_broker_windows.go','internal/domain/runtime_dispatch.go','internal/domain/acceptance.go','internal/domain/runtime.go']
rows=[]
for name in files:
 raw=git('show',REV+':'+name);p=source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);rows.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest()})
put(OUT/'source-audit.json',{'source_revision':git('rev-parse',REV).decode().strip(),'files':rows,'checkout_clean':True,'scope':'Synthetic offline fixture; only child protocol changed through test overlay.'})
