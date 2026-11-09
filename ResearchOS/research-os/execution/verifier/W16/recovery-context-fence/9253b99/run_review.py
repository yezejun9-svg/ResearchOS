from pathlib import Path
import datetime,hashlib,json,os,subprocess
out=Path(__file__).parent
source=Path(r'D:/作品集/ResearchOS/research-os/.local/worktrees/recovery-context-fence-fix')
prior=out.parent/'613f65f'
receipt=source/'execution/receipts/W16/recovery-context-fence/correction-613f65f'
go=Path(r'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
git=lambda *a:subprocess.check_output(['git','-C',str(source),*a],text=True).strip()
declared=load(receipt/'sourcehash.json');checked=[]
for f in declared['files']:
 p=source/f['path'];blob=git('rev-parse',declared['source_commit']+':'+f['path'])
 checked.append(dict(f,actual_sha256=sha(p),hash_matches=sha(p)==f['sha256'],blob_matches=blob==f['git_blob']))
assert len(checked)==9 and all(f['hash_matches'] and f['blob_matches'] for f in checked)
changed=git('diff-tree','--no-commit-id','--name-only','-r',declared['source_commit']).splitlines()
assert changed==declared['changed_files']
evidence=[dict(f,hash_matches=sha(receipt/f['path'])==f['sha256']) for f in load(receipt/'evidencehash.json')['files']]
assert all(f['hash_matches'] for f in evidence)
stats={}
for name in ['affected.raw.jsonl','review-reproduction.raw.jsonl']:
 events=[json.loads(x) for x in (receipt/name).read_text(encoding='utf-8-sig').splitlines() if x.strip()]
 stats[name]={'pass':[x['Test'] for x in events if x.get('Action')=='pass' and x.get('Test')],'skip':[x['Test'] for x in events if x.get('Action')=='skip' and x.get('Test')],'fail':[x.get('Test',x.get('Package')) for x in events if x.get('Action')=='fail']}
binding={'source_commit':declared['source_commit'],'evidence_commit':git('rev-parse','HEAD'),'status':git('status','--short'),'changed_files':changed,'files':checked,'evidence':evidence,'author_stats':stats}
(out/'source-and-raw-binding.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
replacement={}
for name,pkg in [('journal','ops/supervisor'),('manifest','internal/domain'),('path','internal/domain')]:
 p=prior/f'independent_{name}_windows_test.go';target=out/p.name;target.write_bytes(p.read_bytes());replacement[str(source/pkg/f'zz_independent_{name}_windows_test.go')]=str(target)
replacement[str(source/'ops/supervisor/zz_independent_epoch_windows_test.go')]=str(out/'independent_epoch_windows_test.go')
(out/'overlay.json').write_text(json.dumps({'Replace':replacement},ensure_ascii=False,indent=2),encoding='utf-8')
env=os.environ.copy();env.update(GOENV='off',GOTOOLCHAIN='local',GOFLAGS='-mod=readonly',GOWORK='off',RESEARCHOS_GO=str(go),GOPROXY='off',GOSUMDB='off')
cmd=[str(go),'test','-overlay',str(out/'overlay.json'),'./ops/supervisor','./internal/domain','-run','^(TestIndependentRecoveryContext.*|TestIndependentRecoveryEpochRefresh|TestW16RecoveryContextCorrectionJournalOwnership|TestW16RecoveryContextCorrectionManifest.*)$','-count=1','-json']
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out/'independent.raw.jsonl').open('wb') as stdout,(out/'independent.stderr.log').open('wb') as stderr:
 r=subprocess.run(cmd,cwd=source,env=env,stdout=stdout,stderr=stderr,timeout=120)
events=[json.loads(x) for x in (out/'independent.raw.jsonl').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
record={'command':cmd,'cwd':str(source),'scope':'PUBLIC_SYNTHETIC_JOURNAL_AND_STORAGE_ONLY','started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':r.returncode,'raw_sha256':sha(out/'independent.raw.jsonl'),'stderr_sha256':sha(out/'independent.stderr.log'),'pass':[x['Test'] for x in events if x.get('Action')=='pass' and x.get('Test')],'skip':[x['Test'] for x in events if x.get('Action')=='skip' and x.get('Test')],'fail':[x.get('Test',x.get('Package')) for x in events if x.get('Action')=='fail'],'status_after':git('status','--short')}
(out/'independent-command.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(record,ensure_ascii=False))
