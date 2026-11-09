"""Root exact-two integration after a separately pinned independent acceptance."""
import argparse,datetime,hashlib,json,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
BASE='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2';CANDIDATE='a070f16d06fee609691992ba57ee046431f8f55f'
W=R/'.local/worktrees/coding-profile-result-20261014'
FILES=['apps/desktop/main/lib/desktop-management.js','tests/ui/desktop/coding-authorization-boundary.test.mjs']
A=R/'execution/v2.4/receipts/W05/W05-99/coding_profile_result_source_codex/20261014-current-chat'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def query(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd).decode('utf8').strip()
def tracked_state():
 raw=subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=no'],cwd=R)
 rows=[]
 for entry in raw.split(b'\0'):
  if not entry:continue
  text=entry.decode('utf8');status,path=text[:2],text[3:];p=R/path
  assert 'R' not in status and 'C' not in status
  rows.append({'path':path,'status':status,'sha256':sha(p) if p.exists() else None})
 return rows
def run(name,argv):
 p=subprocess.run(argv,cwd=R,capture_output=True)
 for suffix,raw in [('stdout.raw',p.stdout),('stderr.raw',p.stderr)]:
  with (O/(name+'.'+suffix)).open('xb') as f:f.write(raw)
 write(O/(name+'.invocation.json'),{'argv':argv,'cwd':str(R),'actual_exit':p.returncode})
 if p.returncode:raise RuntimeError(name+' failed; retained original receipt, do not blindly retry')
 return p.stdout
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--review',required=True);parser.add_argument('--review-sha256',required=True);a=parser.parse_args()
 review=Path(a.review).resolve();assert review.is_relative_to(R/'execution/v2.4/receipts/W05/W05-99/coding_profile_result_independent_review_codex')
 assert sha(review)==a.review_sha256
 accepted=read(review)
 assert accepted['status']=='SOURCE_ACCEPTED' and accepted['findings']==[] and accepted['head']==CANDIDATE
 assert query('rev-parse','HEAD')==BASE and query('rev-parse','HEAD',cwd=W)==CANDIDATE
 assert query('rev-parse','--path-format=absolute','--git-dir').replace('\\','/').casefold()==str(R/'.git').replace('\\','/').casefold()
 assert query('rev-parse','--path-format=absolute','--git-common-dir').replace('\\','/').casefold()==str(R/'.git').replace('\\','/').casefold()
 assert sha(R/'.git/config')=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
 assert sha(R/'execution/project_identity.json')=='03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
 assert query('config','user.name')=='ResearchOS Codex' and query('config','user.email')=='researchos-codex@localhost'
 assert query('diff','--cached','--name-only')=='' and query('status','--porcelain=v1','--untracked-files=no',cwd=W)==''
 assert set(query('diff','--name-only',BASE,CANDIDATE,cwd=W).splitlines())==set(FILES)
 assert query('diff','--name-only','HEAD','--',*FILES)==''
 assert sha(A/'FINAL-report.json')=='3dae6f571e27e684785cee7f4e2149bfa0ee11746e46dce42f03c5aa0adfc1db'
 assert sha(A/'source.patch')=='7d72a74b6b34488c1953fe109fe802bf23a4e2eaa999088e9db8e9d61aef9a12'
 author=read(A/'FINAL-report.json')
 for name,digest in author['changed_source_sha256'].items():assert sha(W/name)==digest
 baseline=read(R/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')
 for row in baseline['protected_source']:assert sha(R/row['path'])==row['sha256']
 before=tracked_state();assert len(before)==20 and sum(x['status']==' D' for x in before)==11
 write(O/'preflight.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root_decision':'INTEGRATE_EXACT_TWO_AFTER_INDEPENDENT_ACCEPTANCE','base':BASE,'candidate':CANDIDATE,'review':ref(review),'author':ref(A/'FINAL-report.json'),'patch':ref(A/'source.patch'),'files':FILES,'tracked_dirty_before':before,'protected_source':baseline['protected_source'],'product_actions':0,'formal_increment':0})
 run('01-apply-check',['git','apply','--index','--check',str(A/'source.patch')])
 run('02-apply',['git','apply','--index',str(A/'source.patch')])
 assert set(query('diff','--cached','--name-only').splitlines())==set(FILES)
 run('03-diff-check',['git','diff','--cached','--check'])
 for name,digest in author['changed_source_sha256'].items():assert sha(R/name)==digest
 run('04-commit',['git','commit','-m','fix(desktop): validate coding profile artifact references'])
 head=query('rev-parse','HEAD');assert query('rev-parse','HEAD^')==BASE
 assert query('show','-s','--format=%T','HEAD')=='cd951533206a6a4545a6e55fec374e62289d2dd4'
 assert set(query('diff','--name-only',BASE,head).splitlines())==set(FILES)
 assert tracked_state()==before and query('diff','--cached','--name-only')==''
 for row in baseline['protected_source']:assert sha(R/row['path'])==row['sha256']
 write(O/'integration.json',{'status':'EXACT_TWO_INTEGRATED_SOURCE_ONLY','head':head,'tree':query('show','-s','--format=%T','HEAD'),'parent':BASE,'review':ref(review),'source_files':{name:sha(R/name) for name in FILES},'tracked_dirty_after':tracked_state(),'all_protected_source_unchanged':True,'package_rebuild_required':True,'model_calls':0,'product_database_writes':0,'formal_increment':0})
 print(json.dumps({'head':head,'tree':query('show','-s','--format=%T','HEAD'),'source_only':True,'protected_source':9,'historical_dirty':20}))
if __name__=='__main__':main()
