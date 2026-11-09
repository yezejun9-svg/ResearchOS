import pathlib,subprocess,json,hashlib,os
R=pathlib.Path('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/codex-w0599-host-configuration-handler';N=pathlib.Path(__file__).parent
C='22752a6a41732c8c158d7d7e1b8932ec958f8cb8';B='2cdb0d43d5a600eef13c8f1735946a9adf52d079';H=lambda b:hashlib.sha256(b).hexdigest()
E=os.environ.copy();E['GIT_NO_REPLACE_OBJECTS']='1';E.pop('GIT_DIR',None);E.pop('GIT_WORK_TREE',None)
def run(label,args):
 p=subprocess.run(['git','-C',str(W),*args],env=E,capture_output=True);(N/(label+'.stdout.raw')).write_bytes(p.stdout);(N/(label+'.stderr.raw')).write_bytes(p.stderr);(N/(label+'.invocation.json')).write_text(json.dumps({'argv':['git','-C',str(W),*args],'exit_code':p.returncode}),encoding='utf8');p.check_returncode();return p.stdout
def save(name,o):(N/name).write_bytes((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode())
pub=W/'execution/v2.4/receipts/W05/W05-99/host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec/candidate-review-2174dd5f0df043cd9f523945cc135cc2'
fraw=(pub/'source.freeze.json').read_bytes();(N/'author-source.freeze.json').write_bytes(fraw); f=json.loads(fraw)
head=run('head',['rev-parse','HEAD']).decode().strip();delta=run('delta',['diff','--name-only',B,C]).decode().splitlines();run('diff',['diff','--no-ext-diff','--no-textconv',B,C]);rows=[]
for i,x in enumerate(f['files']+f['protected']):
 rel=x['path']; raw=run('blob%02d'%i,['show',C+':'+rel]);p=N/'source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);actual=(W/rel).read_bytes();row={'path':rel,'sha256':H(raw),'bytes':len(raw),'author_expected':x['sha256'],'git_matches_author':H(raw)==x['sha256'],'worktree_matches_git':raw==actual,'protected':i>=38};rows.append(row)
 if i<38:
  out=run('diff%02d'%i,['diff','--no-ext-diff','--no-textconv',B,C,'--',rel]);q=N/'diffs'/((rel.replace('/','_'))+'.diff');q.parent.mkdir(exist_ok=True);q.write_bytes(out)
  if rel.endswith('_test.go') or rel.startswith('tests/'):
   import re
   row['test_selectors']=re.findall(r'^func (Test\w+)\(',raw.decode(),re.M)
save('source.audit.json',{'candidate':C,'base':B,'observed_head':head,'freeze_sha256':H(fraw),'delta':delta,'exact38':set(delta)==set(x['path'] for x in f['files']),'rows':rows})
for name in ['coverage.actual.json','coverage-plan.json','source-commit.json']:
 p=pub/name
 if p.exists():(N/('author-'+name)).write_bytes(p.read_bytes())
print(json.dumps({'namespace':str(N),'exact38':set(delta)==set(x['path'] for x in f['files']),'bad':[r['path'] for r in rows if not r['git_matches_author'] or not r['worktree_matches_git']],'production':[r['path'] for r in rows[:38] if not r['path'].endswith('_test.go') and not r['path'].startswith('tests/')],'tests':{r['path']:r.get('test_selectors',[]) for r in rows[:38] if 'test_selectors' in r}},ensure_ascii=True))