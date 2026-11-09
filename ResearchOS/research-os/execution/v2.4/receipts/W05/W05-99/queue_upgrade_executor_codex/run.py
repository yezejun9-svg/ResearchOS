import datetime, hashlib, json, os, pathlib, subprocess, sys, uuid

ROOT = pathlib.Path(__file__).resolve().parents[6]
MAIN = pathlib.Path('D:/作品集/ResearchOS/research-os')
GO = MAIN / '.local/tools/go1.27.1/go/bin/go.exe'
RECEIPTS = pathlib.Path(__file__).resolve().parent
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs(root):
    paths=[]
    for folder in ('internal','adapters','ops','migrations','spec/v2.0/contracts','evaluation'):
        paths.extend(p for p in (root / folder).rglob('*') if p.is_file() and p.suffix in ('.go','.sql','.json'))
    paths.extend(root / name for name in ('go.mod','go.sum'))
    return {p.relative_to(root).as_posix():digest(p) for p in sorted(paths)}
env=os.environ.copy()
env.update(GOTOOLCHAIN='local',GOENV='off',GOROOT=str(GO.parent.parent),GOCACHE=str(MAIN/'.local/gocache'),GOPATH=str(MAIN/'.local/gopath'),RESEARCHOS_QUEUE_UPGRADE_TARGET_ROOT=str(MAIN/'.local/worktrees/codex-w0599-command-queue'))
root=pathlib.Path(env.get('QUEUE_UPGRADE_BUILD_ROOT',str(ROOT)))
if root!=ROOT:env['RESEARCHOS_QUEUE_UPGRADE_TARGET_ROOT']=str(root)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
out=RECEIPTS/'runs'/stamp;out.mkdir(parents=True)
assert digest(GO)=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
cmd=[str(GO),*sys.argv[1:]]
before=inputs(root)
external=pathlib.Path(env['RESEARCHOS_QUEUE_UPGRADE_TARGET_ROOT'])
for name in ('0021_research_pending_windows.sql','0022_client_command_queue.sql','next_v24_sessions.sql'):
    before['target-release/'+name]=digest(external/'migrations/sqlite'/name)
(out/'inputs.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
with (out/'stdout.raw').open('wb') as stdout,(out/'stderr.raw').open('wb') as stderr:
    process=subprocess.run(cmd,cwd=root,env=env,stdout=stdout,stderr=stderr)
after=inputs(root)
for name in ('0021_research_pending_windows.sql','0022_client_command_queue.sql','next_v24_sessions.sql'):
    after['target-release/'+name]=digest(external/'migrations/sqlite'/name)
result={'command':cmd,'cwd':str(root),'integer_exit':process.returncode,'time':stamp,'go_sha256':digest(GO),'source_input_changes':[k for k in set(before)|set(after) if before.get(k)!=after.get(k)],'inputs_sha256':digest(out/'inputs.json'),'stdout_sha256':digest(out/'stdout.raw'),'stderr_sha256':digest(out/'stderr.raw'),'context':'isolated development fixture; no final Q07 or parent acceptance','external_provider_calls':0,'environment':{k:env[k] for k in ('GOTOOLCHAIN','GOENV','GOROOT','GOCACHE','GOPATH','RESEARCHOS_QUEUE_UPGRADE_TARGET_ROOT')}}
(out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
print((out/'stdout.raw').read_text(encoding='utf-8',errors='replace')[-18000:])
print((out/'stderr.raw').read_text(encoding='utf-8',errors='replace')[-6000:])
sys.exit(process.returncode)
