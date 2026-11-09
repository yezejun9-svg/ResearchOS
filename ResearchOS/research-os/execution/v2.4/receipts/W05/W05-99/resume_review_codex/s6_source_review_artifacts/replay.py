import hashlib, json, os, shutil, subprocess, sys
from datetime import datetime,timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WORK=ROOT/'.local/worktrees/codex-w0599-command-queue'
REC=WORK/'execution/v2.4/receipts/W05/W05-99/queue_executor_codex'
SNAP=ROOT/'.local/s6-independent-review-20261006'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
assert not SNAP.exists()
SNAP.mkdir()
names=subprocess.check_output(['git','-C',str(WORK),'ls-files','-z']).decode().split('\0')
selected=[]
for name in names:
    if not name: continue
    if name.startswith(('third_party/','execution/receipts/','execution/v2.4/receipts/','execution/verifier/')): continue
    source=WORK/name
    if not source.is_file(): continue
    target=SNAP/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    selected.append({'path':name,'sha256':sha(target)})
bundle=WORK/'.local/w1401-mu-worker/mu-worker.mjs'
target=SNAP/'.local/w1401-mu-worker/mu-worker.mjs';target.parent.mkdir(parents=True);shutil.copyfile(bundle,target)
shutil.copyfile(Path(str(bundle)+'.build.json'),Path(str(target)+'.build.json'))
command=read(REC/'final-current-matrix/command.json')
env=dict(os.environ,**command['environment'])
env['RESEARCHOS_MU_BUNDLE']=str(target)
env['RESEARCHOS_QUEUE_WORKER_BUNDLE']=str(target)
env['RESEARCHOS_QUEUE_FAILURE_DIR']=str(OUT/'failed-fixture')
env['GOPROXY']='off';env['GOSUMDB']='off'
env.pop('RESEARCHOS_W04_PACKAGE_INPUT',None)
result={'snapshot':str(SNAP),'candidate':'da7400e96aa1ce27ebb95a4b5c3a03d2b1d3d6f9','sources':selected,'bundle_sha256':sha(target),'calls':'loopback/injected only; no LIVE provider','runs':[]}
(OUT/'replay_inputs.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
runs=[('domain-runtime',[command['exe'],'test','-json','./internal/domain','./adapters/runtime','-run','^TestClientQueue|^TestRuntimeClientQueue|^TestQueueUpgradeActiveRecovery$|^TestQueueUpgradePopulatedBootstrapRoundTrip$|^TestQueueUpgradeHistoricalPlans$|^TestBridgeControl|^TestBridgeQueue','-count=1','-timeout=180s']),('sdk',[env['RESEARCHOS_NODE'],'--test','adapters/runtime/mu/worker-control.test.mjs']),('cli',[command['exe'],'test','-json','./apps/cli','-run','^TestCLIActualMuInteractive|^TestCLIActualGoalCancelBeforeRun$','-count=1','-timeout=180s'])]
for name,argv in runs:
    stdout=OUT/(name+'.stdout.raw');stderr=OUT/(name+'.stderr.raw')
    started=datetime.now(timezone.utc).isoformat()
    with stdout.open('wb') as out,stderr.open('wb') as err:
        done=subprocess.run(argv,cwd=SNAP,env=env,stdout=out,stderr=err,timeout=240)
    counts={'pass':[],'fail':[],'skip':[]}
    for line in stdout.read_text(encoding='utf-8-sig').splitlines():
        try: row=json.loads(line)
        except ValueError: continue
        if row.get('Test') and row.get('Action') in counts: counts[row['Action']].append(row['Test'])
    record={'name':name,'argv':argv,'cwd':str(SNAP),'started':started,'ended':datetime.now(timezone.utc).isoformat(),'actual_exit':done.returncode,'exe_sha256':sha(Path(argv[0])),'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr),'events':counts}
    result['runs'].append(record)
    (OUT/'replay_result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'run':name,'exit':done.returncode,'counts':{key:len(value) for key,value in counts.items()},'failed':counts['fail'],'skipped':counts['skip']}),flush=True)
    if done.returncode: sys.exit(done.returncode)
drift=[entry['path'] for entry in selected if sha(SNAP/entry['path'])!=entry['sha256']]
result['source_drift']=drift
assert not drift
(OUT/'replay_result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
