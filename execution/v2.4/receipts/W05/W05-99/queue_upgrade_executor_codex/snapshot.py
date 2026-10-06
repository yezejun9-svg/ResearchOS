import datetime, hashlib, json, pathlib, shutil

own=pathlib.Path(__file__).resolve().parents[6]
main=pathlib.Path('D:/作品集/ResearchOS/research-os')
peer=main/'.local/worktrees/codex-w0599-command-queue'
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
target=own/'.local'/('combined-'+stamp)
target.mkdir(parents=True,exist_ok=False)
paths=[]
for folder in ('internal','adapters','ops','migrations','spec/v2.0/contracts','evaluation'):
    paths.extend(p for p in (peer/folder).rglob('*') if p.is_file())
paths.extend(peer/name for name in ('go.mod','go.sum'))
overrides={'internal/domain/backup_queue_upgrade.go','internal/domain/backup_queue_upgrade_test.go','internal/domain/backup_upgrade.go'}
sources={p.relative_to(peer).as_posix():p for p in paths}
for path in overrides:sources[path]=own/path
before={}
for rel,p in sources.items():
    raw=p.read_bytes();before[rel]=hashlib.sha256(raw).hexdigest()
    dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
after={rel:hashlib.sha256(p.read_bytes()).hexdigest() for rel,p in sources.items()}
drift=[rel for rel in before if before[rel]!=after[rel]]
receipt={'context':'read-only current peer source snapshot, combined development candidate only; not frozen final Q07','peer':str(peer),'own':str(own),'target':str(target),'overrides':sorted(overrides),'source_hashes_before':before,'source_hashes_after':after,'source_drift':drift}
out=pathlib.Path(__file__).resolve().parent/('snapshot-'+stamp+'.json')
out.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(str(target));print('source drift:',drift)
if drift:raise SystemExit(1)
