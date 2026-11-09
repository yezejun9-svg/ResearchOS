import pathlib,json,hashlib,subprocess,datetime
O=pathlib.Path(r'C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-v2-review-20261012');S=pathlib.Path(r'C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012');B=S/'.local/readlane-v2-wip-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def put(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raw=[]
for item in read(B/'raw-census-index.json'):
 root=pathlib.Path(item['root']);census=read(pathlib.Path(item['census']));drift=[]
 for row in census:
  p=root/row['path']
  if not p.is_file() or p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:drift.append(row['path'])
 assert not drift,drift
 raw.append({'root':str(root),'files':len(census),'bytes':sum(x['bytes'] for x in census),'drift':drift,'native_renderer_invocation':read(root/'electron.invocation.json')})
put('author-raw-verification.json',raw)
exe=S/'.local/qualification-build-output-v2-02/apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'
p=subprocess.run(['go','version','-m',str(exe)],cwd=O,capture_output=True);(O/'validator-build-metadata.stdout.raw').write_bytes(p.stdout);(O/'validator-build-metadata.stderr.raw').write_bytes(p.stderr);put('validator-build-metadata.invocation.json',{'argv':['go','version','-m',str(exe)],'cwd':str(O),'exit':p.returncode});assert p.returncode==0
print(p.stdout.decode());print(json.dumps({'author_raw_files':sum(x['files'] for x in raw),'drift':0}))
