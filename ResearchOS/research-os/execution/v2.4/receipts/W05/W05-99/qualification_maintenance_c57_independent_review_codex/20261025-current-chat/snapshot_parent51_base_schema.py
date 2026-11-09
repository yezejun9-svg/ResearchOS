import pathlib,subprocess,hashlib,json
B=pathlib.Path(__file__).parent
R=pathlib.Path(r'D:/作品集/ResearchOS/research-os')
commit='085b4711afe0c1288448b174eef24ecd5af0551b'
names=['0002_domain.sql','0003_context.sql','0005_runtime.sql','0017_runtime_dispatch.sql','next_v24_sessions.sql']
D=B/'C51-frozen-base-schema';D.mkdir(exist_ok=False)
refs=[]
for name in names:
 p=subprocess.run(['git','show',commit+':migrations/sqlite/'+name],cwd=R,capture_output=True)
 assert p.returncode==0,(name,p.stderr.decode())
 (D/name).write_bytes(p.stdout)
 refs.append({'path':name,'sha256':hashlib.sha256(p.stdout).hexdigest(),'bytes':len(p.stdout)})
with (D/'manifest.json').open('x',encoding='utf-8') as f: json.dump({'base_commit':commit,'files':refs},f,indent=2)
print(json.dumps({'base_commit':commit,'files':refs},indent=2))
for name in names[:4]:
 for n,line in enumerate((D/name).read_text().splitlines(),1):
  if any(t in line for t in ['immutable INTEGER','objects_immutable','runtime_dispatch_manifest_frozen','BEFORE UPDATE OF project','worker TEXT','identity TEXT','prepared_at TEXT']): print(name+':'+str(n)+': '+line)
