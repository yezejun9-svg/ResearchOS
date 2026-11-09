from pathlib import Path
import json,hashlib,subprocess,re
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-product-coding-profile-core-20261012'
AUTHOR=OUT.parents[1]/'product_coding_profile_core_codex/20261012-current-chat'
CANDIDATE='860a8935c8fffe4a1671eafa177e7fc5a053158a';BASE='d3a0fcaf506f1a3dd88f3f5d0a46f7bc1f0b56c1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def native(s):return re.sub(r'\\u([0-9a-fA-F]{4})',lambda m:chr(int(m[1],16)),s)
checks=[]
def check(kind,p,digest,size=None):
 actual=sha(p) if p.is_file() else None
 checks.append(dict(kind=kind,path=str(p),expected=digest,actual=actual,passed=actual==digest and (size is None or p.stat().st_size==size)))
bundle=AUTHOR/'source-bundle-final.json';check('frozen-bundle',bundle,'ab1dfa48850183a28a9a9220b5d8fdb565b2443379abba607e6b7bd05d052208')
b=read(bundle);assert b['candidate']==CANDIDATE and b['base']==BASE
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()==CANDIDATE
status=subprocess.check_output(['git','status','--porcelain'],cwd=WT);assert not status.strip()
(OUT/'candidate-tracked-status.txt').write_bytes(status)
changed=subprocess.check_output(['git','diff','--name-only',BASE,CANDIDATE],cwd=WT,text=True).splitlines()
assert len(changed)==24 and set(changed)=={x['path'] for x in b['source']['source_files']}
allowed=set()
for row in b['source']['scope_refs']:
 p=ROOT/row['path'];check('scope',p,row['sha256'],row['bytes']);v=read(p);allowed.update(v.get('paths',v.get('new_paths',[])))
assert len(allowed)==30 and set(changed)<=allowed
for row in b['source']['source_files']:
 name=row['path'];check('worktree-source',WT/name,row['sha256'],row['bytes'])
 raw=subprocess.check_output(['git','show',f'{CANDIDATE}:{name}'],cwd=WT)
 assert hashlib.sha256(raw).hexdigest()==row['sha256']
 target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
for row in b['receipts']:check('author-raw-evidence',AUTHOR/row['path'],row['sha256'],row['bytes'])
go=ROOT/'.local/tools/go1.27.1/go/bin/go.exe'
for row in b['builds']:
 p=Path(native(row['path']));check('frozen-binary',p,row['sha256'],row['bytes'])
 raw=subprocess.check_output([str(go),'version','-m',str(p)])
 assert ('vcs.revision='+CANDIDATE).encode() in raw and b'vcs.modified=false' in raw
 (OUT/(p.name+'.buildinfo.txt')).write_bytes(raw)
totals=[]
for test in b['final_tests']:
 prefix=test['attempt'];inv=read(AUTHOR/(prefix+'.invocation.json'));events=[]
 for line in (AUTHOR/(prefix+'.stdout')).read_bytes().splitlines():
  try:events.append(json.loads(line))
  except ValueError:pass
 terminal=[e for e in events if e.get('Action') in ['pass','fail','skip']]
 assert terminal==read(AUTHOR/(prefix+'.summary.json'))
 counts=dict(attempt=prefix,parent_passes=sum(e.get('Action')=='pass' and 'Test' in e and '/' not in e['Test'] for e in terminal),subtest_passes=sum(e.get('Action')=='pass' and '/' in e.get('Test','') for e in terminal),failures=sum(e.get('Action')=='fail' for e in terminal),skips=sum(e.get('Action')=='skip' for e in terminal),exit_code=inv['exit_code'])
 for key in ['parent_passes','subtest_passes','failures','skips','exit_code']:assert counts[key]==test[key]
 totals.append(counts)
(OUT/'candidate-full.diff').write_bytes(subprocess.check_output(['git','diff',BASE,CANDIDATE],cwd=WT))
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
 p=ROOT/'execution/v2.4'/name;canon[name]=dict(sha256=sha(p),facts={k:v for k,v in read(p).items() if k in ['revision','head','status']})
(OUT/'main-canon-baseline.json').write_text(json.dumps(dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon),indent=2)+'\n',encoding='utf-8')
result=dict(candidate=CANDIDATE,checks=len(checks),passed=sum(x['passed'] for x in checks),failures=[x for x in checks if not x['passed']],registered_paths=30,source_paths=24,author_final_counts=totals,checks_detail=checks)
(OUT/'input-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checks_detail'}));raise SystemExit(bool(result['failures']))
