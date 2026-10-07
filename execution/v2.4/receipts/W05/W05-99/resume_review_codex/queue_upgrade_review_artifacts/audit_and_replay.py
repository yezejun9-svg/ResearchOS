import collections, datetime, hashlib, json, os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[7]
OWN = ROOT / '.local/worktrees/codex-w0599-queue-upgrade'
PEER = ROOT / '.local/worktrees/codex-w0599-command-queue'
OUT = pathlib.Path(__file__).parent
CANDIDATE = 'eff65eddf3eb55a54ff46aa315b16f5cf12e3ca3'
BASE = 'fbf661c142a98db72d273204615a9b20641b3cc3'
EVID = OWN / 'execution/v2.4/receipts/W05/W05-99/queue_upgrade_executor_codex'
SOURCES = ['internal/domain/backup_queue_upgrade.go', 'internal/domain/backup_queue_upgrade_test.go', 'internal/domain/backup_upgrade.go']

def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(name, value):
    p = OUT / name
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'path': str(p.relative_to(ROOT)).replace('\\','/'), 'sha256': sha(p.read_bytes())}
def git(*args): return subprocess.check_output(['git', '-C', str(OWN), *args])
def counts(raw):
    c = collections.Counter()
    for line in raw.splitlines():
        try: event = json.loads(line)
        except ValueError: continue
        if event.get('Test'): c[event.get('Action')] += 1
    return {k:c[k] for k in ['run','pass','fail','skip']}

assert git('rev-parse','HEAD').decode().strip() == CANDIDATE
assert not git('status','--porcelain').strip()
paths = git('diff-tree','--no-commit-id','--name-only','-r',CANDIDATE).decode().splitlines()
blobs = {}
for name in paths:
    raw = git('show', f'{CANDIDATE}:{name}')
    actual = (OWN / name).read_bytes()
    assert raw == actual, name
    blobs[name] = sha(raw)
assert sorted(p for p in paths if not p.startswith('execution/')) == sorted(SOURCES)
old = git('show', f'{BASE}:internal/domain/backup_upgrade.go')
new = (OWN / 'internal/domain/backup_upgrade.go').read_bytes()
route = b'\tif opt.Plan == QueueSchemaUpgradePlan {\n\t\treturn upgradeQueueLocal(ctx, opt, verifier)\n\t}\n'
assert new.count(route) == 1 and new.replace(route,b'',1) == old
report = json.loads((EVID/'execution_report.json').read_bytes())
runs=[]
for entry in report['all_runs']:
    p=OWN/entry['path']; result=json.loads(p.read_bytes()); assert sha(p.read_bytes())==entry['sha256']
    d=p.parent; hashes={}
    for name, field in [('inputs.json','inputs_sha256'),('stdout.raw','stdout_sha256'),('stderr.raw','stderr_sha256')]:
        raw=(d/name).read_bytes(); assert sha(raw)==result[field], str(d/name); hashes[name]=sha(raw)
    c=counts((d/'stdout.raw').read_bytes()); assert c==entry['test_counts']
    assert result['integer_exit']==entry['integer_exit']
    runs.append({'path':entry['path'],'result_sha256':entry['sha256'],'integer_exit':result['integer_exit'],'test_counts':c,'file_hashes':hashes,'reported_source_input_changes':result['source_input_changes']})
snap=json.loads((EVID/'snapshot-20261006T081512Z.json').read_bytes())
assert snap['source_hashes_before']==snap['source_hashes_after'] and not snap['source_drift']
inputs=json.loads((EVID/'runs/20261006T081619Z-9761314e/inputs.json').read_bytes())
for name,digest in inputs.items():
    key='migrations/sqlite/'+name.split('/',1)[1] if name.startswith('target-release/') else name
    assert snap['source_hashes_after'][key]==digest, name
for name in SOURCES: assert inputs[name]==blobs[name]
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
checkout=ROOT/'.local'/('queue-upgrade-independent-replay-'+stamp)
checkout.mkdir()
copied={}; changes={}
for name, previous in snap['source_hashes_after'].items():
    source=(OWN if name in SOURCES else PEER)/name
    raw=source.read_bytes(); copied[name]=sha(raw)
    target=checkout/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
    if copied[name]!=previous: changes[name]={'executor_snapshot':previous,'review_snapshot':copied[name]}
after={name:sha(((OWN if name in SOURCES else PEER)/name).read_bytes()) for name in copied}
assert after==copied, 'source drift while snapshotting'
go=ROOT/'.local/tools/go1.27.1/go/bin/go.exe'; gohash=sha(go.read_bytes())
assert gohash=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
manifest=save('replay_inputs.json',{'source_hashes':copied,'changed_from_executor_snapshot':changes,'copy_drift':[],'checkout':str(checkout),'go_sha256':gohash})
audit=save('executor_evidence_audit.json',{'candidate':CANDIDATE,'base':BASE,'commit_files':blobs,'commit_file_count':len(blobs),'source_paths':SOURCES,'historical_guard_bytes_unchanged_except_route':True,'runs':runs,'final_snapshot_sha256':sha((EVID/'snapshot-20261006T081512Z.json').read_bytes()),'final_snapshot_files':len(snap['source_hashes_after']),'final_inputs_files':len(inputs),'all_final_inputs_match_snapshot':True,'replay_inputs':manifest})
env=os.environ.copy(); env.update({'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(go.parent.parent),'GOCACHE':str(ROOT/'.local/gocache'),'GOPATH':str(ROOT/'.local/gopath'),'RESEARCHOS_QUEUE_UPGRADE_TARGET_ROOT':str(checkout)})
command=[str(go),'test','./internal/domain','-run','^TestQueueUpgrade','-count=1','-json']
with (OUT/'replay.stdout.raw').open('wb') as stdout, (OUT/'replay.stderr.raw').open('wb') as stderr:
    process=subprocess.run(command,cwd=checkout,env=env,stdout=stdout,stderr=stderr,timeout=300)
post={name:sha((checkout/name).read_bytes()) for name in copied}
result=save('replay_result.json',{'candidate':CANDIDATE,'cwd':str(checkout),'command':command,'integer_exit':process.returncode,'test_counts':counts((OUT/'replay.stdout.raw').read_bytes()),'stdout_sha256':sha((OUT/'replay.stdout.raw').read_bytes()),'stderr_sha256':sha((OUT/'replay.stderr.raw').read_bytes()),'inputs':manifest,'executor_audit':audit,'source_drift':[name for name in copied if copied[name]!=post[name]],'context':'independent isolated current S6 source snapshot plus exact three candidate blobs; public local fixture only; not final Q07 or parent acceptance'})
print(json.dumps({'result':result,'exit':process.returncode,'counts':counts((OUT/'replay.stdout.raw').read_bytes()),'dependency_changes':changes,'checkout':str(checkout)},ensure_ascii=False))
