import sys
sys.dont_write_bytecode=True
import json,subprocess,hashlib,re
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';T=R/'.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371';O=Path(__file__).resolve().parent;C='3225a31fd25969c6a5e071a2fc686cb4a835e162'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,o):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def read(p):return json.loads(Path(p).read_bytes())
io=[];extra=[]
def git(label,args,success_codes=(0,)):
 p=subprocess.run(['git','-C',str(R),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 out=O/'git-raw'/(label+'.stdout.raw');err=O/'git-raw'/(label+'.stderr.raw');out.write_bytes(p.stdout);err.write_bytes(p.stderr)
 io.append(dict(argv=['git','-C',str(R),*args],actual_exit=p.returncode,stdout_ref=pin(out),stderr_ref=pin(err)))
 assert p.returncode in success_codes,label
 return p.stdout
entry=next(e for e in read(O/'full-tree.index.json') if e['path']=='adapters/protectedstore/frozen_development.json')
body=git('historical-required-embed',['cat-file','blob',entry['oid']]);dest=O/'historical-source'/entry['path'];dest.write_bytes(body)
assert hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==entry['oid'];extra.append(dict(tree_entry=entry,copy=pin(dest)))
matches=git('historical-session-install-calls',['grep','-n','-I','-e','next_v24_sessions','-e','CREATE TABLE.*client_sessions','-e','MapClientSession(',C,'--','apps','internal','ops','bootstrap','adapters'])
for rel in ('ops/backup/main.go','ops/supervisor/recovery_root/main_windows.go'):
 p=T/rel;d=O/'current-source'/rel;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(p.read_bytes());extra.append(dict(original=pin(p),copy=pin(d)))
packets=[B/'legacy_migration_fixture_source_revision_codex/fc052947b4d14f769bff1e735151c52d',B/'legacy_migration_fixture_revision_independent_review_codex/attach_restore_reviewer_02']
for base in packets:
 for n in ('HDF.json','MF.json'):
  p=base/n;d=O/'packet-evidence'/base.parent.name/n;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(p.read_bytes());extra.append(dict(original=pin(p),copy=pin(d)))
source=packets[0]/'candidate-root/internal/domain/legacy_migration_fixture_test.go';d=O/'packet-evidence/LEG2-legacy_migration_fixture_test.go';d.write_bytes(source.read_bytes());extra.append(dict(original=pin(source),copy=pin(d)))
modules=[];mod=(O/'historical-source/go.mod').read_text();cache=R/'.local/gopath/pkg/mod/cache/download';sums=(O/'historical-source/go.sum').read_text().splitlines()
for path,version in re.findall(r'^\s*([^\s()]+)\s+(v[^\s]+)',mod,re.M):
 escaped=''.join('!'+c.lower() if c.isupper() else c for c in path);vdir=cache/escaped/'@v';entry={'module':path,'version':version,'go_sum_lines':[s for s in sums if s.startswith(path+' '+version+' ') or s.startswith(path+' '+version+'/go.mod ')]}
 for suffix in ('.mod','.ziphash','.zip'):
  p=vdir/(version+suffix);entry[suffix]={'present':p.is_file(),'path':str(p)}
  if p.is_file():entry[suffix]['pin']=pin(p)
 modules.append(entry)
tool=read(O/'historical-source/execution/toolchains/locked.json')['tools']['go'];actualtool=pin(tool['path']);assert actualtool['sha256']==tool['sha256']
save('go-dependency-resource-presence.json',{'read_only':True,'module_count':len(modules),'modules':modules,'go_tool':actualtool,'go_module_target':'1.27.1','vendor_tree_present':any(e['path'].startswith('vendor/') for e in read(O/'full-tree.index.json')),'network_fetch':False,'compiler_run':False,'buildability_verified':False})
save('supplemental-source.pins.json',extra);save('augment.git-original-io.json',io)
print(json.dumps({'embed':entry if False else extra[0],'session_reference_matches':matches.decode('utf-8'),'modules':len(modules),'all_module_zip_present':all(x['.zip']['present'] for x in modules),'extra_source_files':len(extra)},ensure_ascii=False))
