from pathlib import Path
import hashlib,json,subprocess,os,time,re
ROOT=Path('D:/作品集/ResearchOS/research-os');WT=ROOT/'.local/worktrees/codex-w0599-model-stream-worker';OUT=Path(__file__).resolve().parent
C='6eb611b11364ba25a9560ba54c1b54f3a549eb32';P='execution/v2.4/receipts/W05/W05-99/model_stream_worker_executor_codex/implementation-6f05ada907be4eb8b01ac21fe0e10455';D=WT/P
sh=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,o):(OUT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
h=json.loads((D/'handoff.json').read_bytes());m=json.loads((D/'manifest.json').read_bytes());run=WT/h['final_run']['directory'];v=json.loads((run/'source.before.json').read_bytes());v2=json.loads((run/'source.after.json').read_bytes())
changed=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',C],cwd=WT).decode().splitlines()
proc=subprocess.Popen(['git','cat-file','--batch'],cwd=WT,stdin=subprocess.PIPE,stdout=subprocess.PIPE);data,_=proc.communicate(('\n'.join(C+':'+p for p in changed)+'\n').encode());offset=0;blobs=[]
for p in changed:
 end=data.index(b'\n',offset);head=data[offset:end].split();length=int(head[2]);offset=end+1;b=data[offset:offset+length];offset+=length+1;blobs.append({'path':p,'sha256':hashlib.sha256(b).hexdigest(),'same_worktree':b==(WT/p).read_bytes()})
manifest=[{**x,'actual_sha256':sh(WT/x['path'])} for x in m['files']]
current=[{**x,'actual_sha256':sh(Path(x['path']))} for x in v]
inputsok=v==v2 and all(x['sha256']==x['actual_sha256'] for x in current)
raws=[]
for r in sorted(D.glob('run-*')):
 rr={'path':str(r)}
 for name in ['build','test']:
  f=r/(name+'.invocation.json')
  if not f.exists():continue
  i=json.loads(f.read_bytes());rr[name]={'exit_code':i['exit_code'],'timeout':i['timeout'],'stdout_match':sh(r/(name+'.stdout'))==i['stdout_sha256'],'stderr_match':sh(r/(name+'.stderr'))==i['stderr_sha256']}
 rr['source_snapshot_present']=(r/'worker.mjs').exists()
 raws.append(rr)
inv=json.loads((run/'test.invocation.json').read_bytes());env=os.environ.copy();env.pop('NODE_OPTIONS',None);env.update({k:value for k,value in inv['environment'].items() if value is not None});start=time.time_ns();q=subprocess.run(inv['argv'],cwd=WT,env=env,capture_output=True,timeout=50)
(OUT/'replay.stdout').write_bytes(q.stdout);(OUT/'replay.stderr').write_bytes(q.stderr);dump('replay.invocation.json',{'argv':inv['argv'],'cwd':str(WT),'environment':inv['environment'],'started_ns':start,'finished_ns':time.time_ns(),'exit_code':q.returncode,'stdout_sha256':sh(OUT/'replay.stdout'),'stderr_sha256':sh(OUT/'replay.stderr'),'measurement_mode':'FIXTURE_TRANSPORT_ONLY_NOT_SQLITE_OR_LIVE'})
text=q.stdout.decode('utf8');counts={k:int(re.search(r'(?:ℹ|#) '+k+r' (\d+)',text).group(1)) for k in ['tests','pass','fail','cancelled','skipped']}
final=[{**x,'actual_sha256':sh(Path(x['path']))} for x in v]
refs=[]
for f in [D/'handoff.json',D/'manifest.json',D/'run.py',D/'freeze.py',D/'failure_origins.json',D/'finite_state_design.json',WT/'adapters/runtime/mu/worker.mjs',WT/'adapters/runtime/mu/worker-stream.test.mjs',WT/'adapters/runtime/mu/worker-control.test.mjs',WT/'adapters/runtime/mu/build.mjs',ROOT/'third_party/mu/packages/agent/src/agent.ts',ROOT/'third_party/mu/packages/agent/src/agent-loop.ts',ROOT/'third_party/mu/packages/ai/src/utils/event-stream.ts',ROOT/'third_party/mu/packages/ai/src/api/openai-completions.ts',ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/model-stream-wire-freeze-d6a45a6308994f4c9d84a280d08f5eb1/interface.original.json']:
 refs.append({'path':str(f),'sha256':sh(f)})
a={'candidate':C,'changed_count':len(changed),'blobs':blobs,'manifest_count':len(manifest),'manifest':manifest,'exact_set':set(changed)=={x['path'] for x in manifest}|{P+'/manifest.json'}|{x['path'] for x in h['source']},'source_input_count':len(v),'before_after_current_match':inputsok,'after_independent_replay_match':all(x['sha256']==x['actual_sha256'] for x in final),'qualified_inputs':current,'original_runs':raws,'bundle_actual_sha256':sh(Path(h['build']['bundle'])),'actual_read_refs':refs,'independent_counts':counts,'independent_exit':q.returncode}
dump('audit.json',a)
assert a['exact_set'] and all(x['same_worktree'] for x in blobs) and all(x['sha256']==x['actual_sha256'] for x in manifest)
assert inputsok and a['after_independent_replay_match'] and len(v)==30152 and q.returncode==0 and counts=={'tests':20,'pass':20,'fail':0,'cancelled':0,'skipped':0}
assert a['bundle_actual_sha256']==h['build']['bundle_sha256']
print(json.dumps({'audit_sha256':sh(OUT/'audit.json'),'blobs':len(changed),'manifest_count':len(manifest),'inputs':len(v),'replay':counts}))
