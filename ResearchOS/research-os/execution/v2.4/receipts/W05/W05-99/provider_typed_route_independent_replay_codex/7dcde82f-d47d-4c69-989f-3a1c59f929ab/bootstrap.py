import pathlib,subprocess,json,hashlib,sys,os,datetime
MAIN=pathlib.Path('D:/作品集/ResearchOS/research-os'); HERE=pathlib.Path(__file__).resolve().parent
SCOPE=MAIN/'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-independent-scope-r288/scope_registration.json'
CANDIDATE='6fb5263681c17f0e50920c354dc07ed440a23714'; AUTHOR=MAIN/'.local/worktrees/codex-w0599-provider-binding'
AUTH=AUTHOR/'execution/v2.4/receipts/W05/W05-99/provider_binding_executor_codex/typed-route-final-6c47a88a198349b4bd2a3d3d223510b1'
ROOT=MAIN/'.local/independent-provider-typed-route-r288-d4fd01da69224e05a135e0b01794826c'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p),'bytes':pathlib.Path(p).stat().st_size}
def write(p,x):
 with pathlib.Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
assert sha(SCOPE)=='0d6c0121b1a267e124100f63872fc3f8eea3c84456c471ec2d4d11d1c007b277'
scope=json.loads(SCOPE.read_text(encoding='utf-8'));ROOT.mkdir();(HERE/'inputs').mkdir()
env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env['GIT_NO_REPLACE_OBJECTS']='1'
def git(*args):return subprocess.check_output(['git','-C',str(AUTHOR),*args],env=env)
entries=[]
for line in git('ls-tree','-r','-z',CANDIDATE).split(b'\0'):
 if not line:continue
 meta,name=line.split(b'\t');mode,kind,oid=meta.decode().split();name=name.decode()
 allow=name in ['go.mod','go.sum','AGENTS.md'] or name.startswith(('internal/','adapters/','apps/','migrations/','spec/','third_party/'))
 allow=allow or name in [x['path'] for x in scope['public_compile_files_explicit']]
 if allow and kind=='blob':entries.append((name,oid))
p=subprocess.Popen(['git','-C',str(AUTHOR),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,env=env)
export=[]
for name,oid in entries:
 p.stdin.write((oid+'\n').encode());p.stdin.flush();header=p.stdout.readline().decode().split();raw=p.stdout.read(int(header[2]));assert p.stdout.read(1)==b'\n'
 target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);export.append({'relative':name,'git_blob':oid,**ref(target)})
p.stdin.close();p.wait();assert p.returncode==0
for e in scope['public_compile_files_explicit']:assert sha(ROOT/e['path'])==e['sha256']
for e in scope['source9']:assert sha(ROOT/e['path'])==e['git_candidate_sha256']
originals=[]
for e in scope['original7_inputs']:
 for k in ['original','author_copy']:assert sha(e[k]['path'])==e[k]['sha256']
 dst=HERE/'inputs'/(e['id']+'.sqlite');dst.write_bytes(pathlib.Path(e['original']['path']).read_bytes());originals.append({'id':e['id'],'original':e['original'],'copy':ref(dst)})
w=scope['synthetic_workspace_boundary']['fixture_bytes'];assert sha(w['path'])==w['sha256'];(HERE/'synthetic_workspace_evidence.txt').write_bytes(pathlib.Path(w['path']).read_bytes())
write(HERE/'export.json',{'candidate':CANDIDATE,'files':export,'scope':ref(SCOPE),'generator_execution':False});write(HERE/'original7.before.json',originals)
write(HERE/'bootstrap.json',{'root':str(ROOT),'receipt':str(HERE),'source9':[ref(ROOT/e['path']) for e in scope['source9']],'export_count':len(export),'tests':0,'model':0})
print(json.dumps({'export_count':len(export),'root':str(ROOT),'receipt':str(HERE)}))
