from pathlib import Path
import hashlib,json,subprocess
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-desktop-parent-image-observation-repair-20261012'
AUTHOR=OUT.parents[1]/'product_parent_image_observation_repair_codex/20261012-current-chat'
CANDIDATE='040d297627e2cfc5de2d6b9e770acc7bdf4f9ab7';BASE='860a8935c8fffe4a1671eafa177e7fc5a053158a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def check(kind,p,digest,size=None):
 got=sha(p) if p.is_file() else None;passed=got==digest and (size is None or p.stat().st_size==size)
 checks.append(dict(kind=kind,path=str(p),sha256=got,expected=digest,passed=passed))
check('frozen-bundle',AUTHOR/'source-bundle-final.json','3ac0eb9ef64c8e1790ae27f6c9dee4b3244a1d79a1c1b353a9de0ab3fe449df4')
b=read(AUTHOR/'source-bundle-final.json');s=b['source'];assert s['candidate']==CANDIDATE and s['base']==BASE and Path(s['worktree']).samefile(WT)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()==CANDIDATE
status=subprocess.check_output(['git','status','--porcelain'],cwd=WT);assert not status.strip();(OUT/'candidate-tracked-status.txt').write_bytes(status)
scope=Path(s['scope_path']);check('scope',scope,'ad8f5eaa6e9570b11bfeb638e64be7974094c4f0e3e8e17f42cdc28fc959c2d6')
scopeobj=read(scope)
for key in ['core_source_bundle_ref','actual_failed_boot_ref']:
 row=scopeobj[key];check(key,ROOT/row['path'],row['sha256'],row['bytes'])
row=scopeobj['original_electron'];check('original-electron',Path(row['path']),row['sha256'],row['bytes'])
check('base-core-bundle',Path(b['base_core_bundle']['path']),b['base_core_bundle']['sha256'])
prior=OUT.parents[1]/'product_coding_profile_core_review_codex/20261012-current-chat'
check('prior-independent-manifest',prior/'receipt_manifest.json','54a8857d5831bf7c374d826c1d011446dac2c3290f3fa1babf8d0070dd5f4b6f')
changed=subprocess.check_output(['git','diff','--name-only',BASE,CANDIDATE],cwd=WT,text=True).splitlines()
assert len(changed)==2 and set(changed)==set(scopeobj['paths'])=={r['path'] for r in s['files']}
for row in s['files']:
 check('source',WT/row['path'],row['sha256'],row['bytes'])
 raw=subprocess.check_output(['git','show',CANDIDATE+':'+row['path']],cwd=WT);assert hashlib.sha256(raw).hexdigest()==row['sha256']
 p=OUT/'source'/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
for row in b['files']:check('author-receipt',AUTHOR/row['path'],row['sha256'],row['bytes'])
go=ROOT/'.local/tools/go1.27.1/go/bin/go.exe'
for row in b['builds']:
 p=Path(row['path']);check('binary',p,row['sha256'],row['bytes'])
 raw=subprocess.check_output([str(go),'version','-m',str(p)]);assert ('vcs.revision='+CANDIDATE).encode() in raw and b'vcs.modified=false' in raw
 (OUT/(p.name+'.buildinfo.txt')).write_bytes(raw)
old=subprocess.check_output(['git','show',BASE+':ops/supervisor/release_process_windows.go'],cwd=WT).decode('utf-8')
new=(WT/'ops/supervisor/release_process_windows.go').read_text(encoding='utf-8')
def body(s):return s[s.index('func exactImage('):s.index('\nfunc processCreated(')]
assert body(old)==body(new)
write('unchanged-release-policy.json',dict(exactImage_body_equal=True,sha256=hashlib.sha256(body(old).encode()).hexdigest(),limit_bytes=128*1024*1024,observation_limit_bytes=256*1024*1024))
totals=[]
for test in b['final_tests']:
 label=test['attempt'];events=[]
 for line in (AUTHOR/(label+'.stdout')).read_bytes().splitlines():
  try:events.append(json.loads(line))
  except ValueError:pass
 terminal=[x for x in events if x.get('Action') in ['pass','fail','skip']];assert terminal==read(AUTHOR/(label+'.summary.json'))
 result=dict(attempt=label,parent_passes=sum(x['Action']=='pass' and 'Test'in x and '/'not in x['Test'] for x in terminal),subtest_passes=sum(x['Action']=='pass' and '/'in x.get('Test','') for x in terminal),failures=sum(x['Action']=='fail' for x in terminal),skips=sum(x['Action']=='skip' for x in terminal),exit_code=read(AUTHOR/(label+'.invocation.json'))['exit_code'])
 assert result==test;totals.append(result)
(OUT/'candidate-full.diff').write_bytes(subprocess.check_output(['git','diff',BASE,CANDIDATE],cwd=WT))
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
 p=ROOT/'execution/v2.4'/name;canon[name]=dict(sha256=sha(p),facts={k:v for k,v in read(p).items() if k in ['revision','head','status']})
write('main-canon-baseline.json',dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon))
result=dict(candidate=CANDIDATE,checks=len(checks),passed=sum(x['passed'] for x in checks),failures=[x for x in checks if not x['passed']],author_receipts=len(b['files']),source_paths=2,author_tests=totals,checks_detail=checks)
write('input-verification.json',result);print(json.dumps({k:v for k,v in result.items() if k!='checks_detail'}));assert not result['failures']
