from pathlib import Path
import datetime, hashlib, json, os, subprocess

out=Path(__file__).resolve().parent
source=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/recovery-context-fence')
go=Path('D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe')
receipt=source/'execution/receipts/W16/recovery-context-fence'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
declared=json.loads((receipt/'sourcehash.json').read_text(encoding='utf-8-sig'))
checked=[]
for f in declared['files']:
    actual=sha(source/f['path'])
    blob=subprocess.check_output(['git','-C',str(source),'rev-parse','613f65f:'+f['path']],text=True).strip()
    checked.append(dict(f,actual_sha256=actual,sha256_matches=actual==f['sha256'],git_blob_matches=blob==f['git_blob']))
assert all(x['sha256_matches'] and x['git_blob_matches'] for x in checked)
raw=receipt/'development/targeted-idle.raw.jsonl'
assert sha(raw)=='7df071c0e665140093239f421c6431befd3d039800c069585c615a3cfbc05430'
events=[json.loads(s) for s in raw.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
author_pass=[e for e in events if e.get('Action')=='pass' and e.get('Test')]
author_top=[e['Test'] for e in author_pass if '/' not in e['Test']]
binding={'source_commit':declared['source_commit'],'files':checked,'author_raw_sha256':sha(raw),'author_top_pass':author_top,'author_pass_test_events':len(author_pass),'author_fail_events':[e for e in events if e.get('Action')=='fail']}
(out/'source-and-raw-binding.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
overlay={'Replace':{
    str(source/'ops/supervisor/independent_recovery_context_windows_test.go'):str(out/'independent_journal_windows_test.go'),
    str(source/'internal/domain/independent_recovery_manifest_windows_test.go'):str(out/'independent_manifest_windows_test.go')}}
(out/'overlay.json').write_text(json.dumps(overlay,ensure_ascii=False,indent=2),encoding='utf-8')
env=os.environ.copy()
env.update(GOENV='off',GOTOOLCHAIN='local',GOFLAGS='-mod=readonly',GOWORK='off',RESEARCHOS_GO=str(go),GOPROXY='off')
cmd=[str(go),'test','-overlay',str(out/'overlay.json'),'./ops/supervisor','./internal/domain','-run','^TestIndependentRecoveryContext','-count=1','-json']
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out/'independent.raw.jsonl').open('wb') as stdout, (out/'independent.stderr.log').open('wb') as stderr:
    result=subprocess.run(cmd,cwd=source,env=env,stdout=stdout,stderr=stderr,timeout=120)
record={'command':cmd,'cwd':str(source),'purpose':'Only public synthetic pointer immutability and persisted manifest byte binding checks; no native control, private data, old helper or provider', 'started_utc':started,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':result.returncode,'raw_sha256':sha(out/'independent.raw.jsonl'),'stderr_sha256':sha(out/'independent.stderr.log')}
(out/'independent-command.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False))
