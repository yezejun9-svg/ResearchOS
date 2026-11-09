import hashlib,json,subprocess
from pathlib import Path
R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'.local/worktrees/desktop-installed-delivery-20261025'
O=R/'execution/v2.4/receipts/W05/W05-99/product_host_independent_20261028/frozen-5ee2c694-review'
S=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp558/Product-host-exact14-source-scope.json'
commit='5ee2c694ee275a72f40e8aa1d6c377d719fb8631'
base='ecc28dd3c91a0f68dcddb41b53325aa7f0e81419'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
commands=[]
def git(*args):
 p=subprocess.run(['git',*args],cwd=W,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
 n=len(commands); prefix=O/f'git-{n:02}'
 Path(str(prefix)+'.stdout.raw').write_bytes(p.stdout);Path(str(prefix)+'.stderr.raw').write_bytes(p.stderr)
 commands.append({'argv':['git',*args],'cwd':str(W),'exit':p.returncode,'stdout_sha256':sha(p.stdout),'stderr_sha256':sha(p.stderr)})
 if p.returncode:raise RuntimeError(f'git {args}: {p.stderr.decode("utf8","replace")}')
 return p.stdout
head=git('rev-parse','HEAD').decode().strip()
tree=git('rev-parse',commit+'^{tree}').decode().strip()
parent=git('rev-parse',commit+'^').decode().strip()
rawcommit=git('cat-file','-p',commit)
status=git('status','--porcelain=v1','-z')
diffnames=git('diff','--name-only','-z',base,commit).decode().strip('\0').split('\0')
git('diff','--check',base,commit)
diff=git('diff','--binary',base,commit)
(O/'exact14.diff').write_bytes(diff)
scope=json.loads(S.read_bytes());allowed=scope['allowed_source_paths']
assert head==commit and parent==base and tree=='43e71226bbcb5d413bfa0ca2b11a767d255b2aec'
assert not status and set(diffnames)==set(allowed) and len(diffnames)==14
rows=[]
for rel in allowed:
 p=W/rel;raw=p.read_bytes();target=O/'source'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 blob=git('show',commit+':'+rel)
 after=p.read_bytes()
 assert raw==after and target.read_bytes()==raw
 rows.append({'path':rel,'bytes':len(raw),'sha256':sha(raw),'git_blob_sha256':sha(blob),'git_blob_equals_worktree_bytes':raw==blob,'copy_stable':True})
assert git('status','--porcelain=v1','-z')==status and git('rev-parse','HEAD').decode().strip()==head
put(O/'GIT-COMMANDS.json',commands)
put(O/'SOURCE-INPUTS.json',{'head':head,'tree':tree,'parent':parent,'scope_path':str(S),'scope_sha256':sha(S.read_bytes()),'changed':diffnames,'clean':True,'source_acceptance':False,'final_build_and_exact7_pending':True,'files':rows})
put(O/'REVIEWER-COMMAND-DIAGNOSTIC.json',{'status':'RETAINED_REVIEWER_SHELL_SYNTAX_ERROR_CORRECTED_READ_ONLY','action':'Initial PowerShell batch passed unquoted commit^{tree}; braces parsed as scriptblock and encodedCommand args appeared. Later single quoted rev expression succeeded.','observed_output_excerpt':"fatal: ambiguous argument 'dAByAGUAZQA=': unknown revision or path not in the working tree.",'native_product_runs':0,'not_the_builder_gc_error':True})
print(json.dumps({'head':head,'tree':tree,'parent':parent,'clean':True,'exact_paths':len(rows),'raw_blob_equal':sum(r['git_blob_equals_worktree_bytes'] for r in rows),'acceptance':False}))