import hashlib, json, subprocess
from pathlib import Path
from datetime import datetime, timezone

OUT=Path(__file__).resolve().parent
REPO=next(p for p in OUT.parents if (p/'execution/project_identity.json').is_file())
BASE=REPO/'execution/v2.4/receipts/W05/W05-99/queue_integration_codex/historical-resource-proposal-41e7b6ba-8465-45d4-914e-c503f6af4602'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p): return {'path':p.relative_to(REPO).as_posix(),'sha256':sha(p)}
def write(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
proposal=read(BASE/'proposal.json')
assert sha(BASE/'proposal.json')=='b8fb7c6b3800c2ff486a8aba0df363ce66cd44cd978eec62796c7c24190d9840'
checks=[]
for r in [proposal[k] for k in ['resource_audit','schema20_source_identity','exact_source_spans']]:
 checks.append({'ref':r,'matches':sha(REPO/r['path'])==r['sha256']})
audit=read(BASE/'resource_audit.json')
for r in audit['inputs']:
 checks.append({'ref':r,'matches':sha(REPO/r['path'])==r['sha256']})
spans=read(BASE/'exact_spans.json')
p=REPO/spans['source']['path']; raw=p.read_bytes(); lines=raw.splitlines(keepends=True)
assert sha(p)==spans['source']['sha256']
spanchecks=[dict(r,actual_sha256=hashlib.sha256(b''.join(lines[r['start_line']-1:r['end_line']])).hexdigest()) for r in spans['spans']]
assert all(r['sha256']==r['actual_sha256'] for r in spanchecks)
protected={'prefix_through_line974':hashlib.sha256(b''.join(lines[:974])).hexdigest(),
 'suffix_from_line982_to_EOF':hashlib.sha256(b''.join(lines[981:])).hexdigest(),
 'raw_bytes_not_normalized':True}
identity=read(BASE/'schema20-source-identity.json')
root20=Path(identity['source_root'])
rows20=[]
for r in identity['source_files']:
 actual=sha(root20/r['path'])
 rows20.append({'path':r['path'],'sha256':actual,'matches_recorded':actual==r['expected'].removeprefix('sha256:')})
locked=read(REPO/'execution/toolchains/locked.json')['tools']
commands=[]
def git(name,args):
 proc=subprocess.run([locked['git']['path'],*args],cwd=REPO,capture_output=True)
 (OUT/(name+'.stdout.raw')).write_bytes(proc.stdout); (OUT/(name+'.stderr.raw')).write_bytes(proc.stderr)
 commands.append({'argv':[locked['git']['path'],*args],'cwd':str(REPO),'exit_code':proc.returncode,
 'stdout_ref':ref(OUT/(name+'.stdout.raw')),'stderr_ref':ref(OUT/(name+'.stderr.raw'))})
 assert proc.returncode==0
 return proc.stdout
commit14='09a6a5ecfba40c1596a3ec46be25c34ba1f2fce0'
root14=REPO/'.local/releases/schema14-09a6a5e'
tree=git('historical14-tree',['ls-tree','-rz',commit14,'--','apps','internal','adapters','evaluation','ops','migrations/sqlite','spec/v2.0/contracts','go.mod','go.sum'])
rows14=[]
for entry in tree.split(b'\0'):
 if not entry: continue
 metadata,name=entry.split(b'\t',1); mode,kind,oid=metadata.decode().split(); name=name.decode('utf-8')
 if kind!='blob' or not(name.endswith(('.go','.sql')) or name in ['go.mod','go.sum'] or '/contracts/' in name or name=='adapters/protectedstore/frozen_development.json'): continue
 p=root14/name; data=p.read_bytes() if p.is_file() else None
 blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() if data is not None else None
 rows14.append({'path':name,'git_blob':oid,'actual_git_blob':blob,'sha256':sha(p) if p.is_file() else None,'matches_commit':blob==oid})
test20=root20/'internal/domain/evolution_control_test.go'
old20=git('historical20-test',['show','104b83f0f4a6634a1367938da2bbf7b496483da2:internal/domain/evolution_control_test.go'])
artifactchecks=[]
for name,digest in [('.local/bin/researchos-remote.exe','aeda2d5eff0028529eaa53e9f5cc91fbcd668842577315eb744bd5f066834032'),('.local/current-control-attempt10/control.exe','203fe4d5208de7c571392b345ec580e007ec3713799a8d2042e921393dcae14c')]:
 artifactchecks.append({'ref':ref(REPO/name),'matches':sha(REPO/name)==digest})
result={'schema':'researchos.historical-resource-independent-audit.v1','reviewer':'codex:/root/queue_upgrade_impl','created_at':datetime.now(timezone.utc).isoformat(),
 'proposal_ref':ref(BASE/'proposal.json'),'hash_checks':checks,'main_source_ref':ref(REPO/'internal/domain/backup_upgrade_test.go'),
 'span_checks':spanchecks,'protected_exterior':protected,'schema14_tree':{'commit':commit14,'root':str(root14),'files':rows14},
 'schema20_recorded206':rows20,'schema20_test_matches_104b83f':test20.read_bytes()==old20,'schema20_test_ref':ref(test20),
 'artifact_checks':artifactchecks,'commands':commands,'product_executions':0,'formal_acceptance_increment':0,
 'limitations':['Git tree check is only listed source/test/contracts/SQL inputs; final disposable tree needs full embed/dependency/extras census and before/after manifest.',
 'Schema14 binary vcs.modified=true; fixed artifact SHA plus historical receipt identity is authoritative, not claimed reproducible from clean09a.',
 '206 schema20 production inventory does not alone bind all tests/build helpers/assets; final snapshot manifest must include them.',
 'No previous private holdout/authority database or product executable opened/executed by reviewer.']}
write('audit.json',result)
print(json.dumps({'proposal_sha256':sha(BASE/'proposal.json'),'main_sha256':sha(REPO/'internal/domain/backup_upgrade_test.go'),
 'hash_mismatches':sum(not r['matches'] for r in checks),'schema14_files':len(rows14),'schema14_differences':[r['path'] for r in rows14 if not r['matches_commit']],
 'schema20_rows':len(rows20),'schema20_mismatches':[r['path'] for r in rows20 if not r['matches_recorded']],
 'schema20_test_matches':result['schema20_test_matches_104b83f'],'artifact_checks':artifactchecks,'audit_sha256':sha(OUT/'audit.json')},ensure_ascii=False))
assert all(r['matches'] for r in checks+artifactchecks) and all(r['matches_recorded'] for r in rows20) and result['schema20_test_matches_104b83f']
