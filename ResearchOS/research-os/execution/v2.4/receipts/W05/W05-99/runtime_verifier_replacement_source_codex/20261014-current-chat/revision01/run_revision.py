import datetime, hashlib, json, os, pathlib, subprocess, sys

base = pathlib.Path(__file__).resolve().parent
repo = pathlib.Path(r'D:\作品集\ResearchOS\research-os')
work = repo / '.local/worktrees/verifier-replacement-20261014'
def pin(p):
    raw = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
def write_new(p, data):
    with p.open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
if sys.argv[1] == 'baseline':
    scope = repo / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp487/verifier-replacement-revision01-scope.json'
    review = repo / 'execution/v2.4/receipts/W05/W05-99/runtime_verifier_replacement_independent_review_codex/20261014-current-chat/REVIEW.md'
    assert pin(scope)['sha256'] == '26871cdb92688e57db3975331f5aed3db0c71af3aa93d9e2ee83eb61b2c6881e'
    assert pin(review)['sha256'] == '02e9263dcac980d8bc4c2cfc30b15f498f2a786688b62419de2a645ab9782933'
    paths = [p for p in base.parent.rglob('*') if p.is_file() and base not in p.parents]
    paths += [p for p in review.parent.rglob('*') if p.is_file()]
    paths += [scope, base/'01-existing-focused.log', base/'01-existing-focused.json', base/'run_evidence.py']
    write_new(base/'02-baseline-pins.json', [pin(p) for p in sorted(set(paths))])
    write_new(base/'02-resume-diagnostics.json', {'preserved_diagnostics': ['Attempted parent AGENTS.md read: absent; repository AGENTS.md was then read.', 'Scope hash read used one excess parent segment: path absent; corrected to canonical absolute path and verified.'], 'product_execution': False})
    print('baseline pins verified and saved')
    sys.exit(0)
label, argv = sys.argv[1], sys.argv[2:]
env = {k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC','PATHEXT','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA','PROCESSOR_ARCHITECTURE','NUMBER_OF_PROCESSORS','HOMEDRIVE','HOMEPATH'}}
env.update(GOCACHE=str(repo/'.local/go-cache/verifier-replacement-20261014'), GOMODCACHE=str(repo/'.local/tools/gopath/pkg/mod'), GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off')
temp = repo / '.local/tmp/verifier-replacement-20261014'
temp.mkdir(parents=True, exist_ok=True)
env.update(TEMP=str(temp), TMP=str(temp))
record = {'label':label, 'argv':argv, 'cwd':str(work), 'environment':env, 'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
logpath = base / (label+'.log')
with logpath.open('xb') as log:
    result = subprocess.run(argv, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT)
record.update(exit_code=result.returncode, ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), log=pin(logpath))
write_new(base/(label+'.json'), record)
with (base/'attempt-ledger.jsonl').open('a', encoding='utf-8') as f:
    f.write(json.dumps(record, ensure_ascii=False)+'\n')
print(json.dumps({k:record[k] for k in ['label','exit_code','log']}, ensure_ascii=False))
print(logpath.read_text(encoding='utf-8', errors='replace')[-3500:])
sys.exit(result.returncode)
