import pathlib,json,hashlib,subprocess,tarfile,shutil,sys,time,os
B=pathlib.Path(__file__).parent;R=pathlib.Path(r'D:/作品集/ResearchOS/research-os')
A=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp547/C57-independent-phase2-exact57-amendment.json'
sha=lambda d:hashlib.sha256(d).hexdigest()
araw=A.read_bytes();assert sha(araw)=='15fc725cd3c61a165949718775c163d41bf9f9ddc7f8dfadf9f2467185d76bba'
a=json.loads(araw); commit=a['candidate_commit']
I=B/'PHASE2-fixed-inputs';I.mkdir(exist_ok=False);(I/A.name).write_bytes(araw)
objs={}
for key,ref in a.items():
 if key.endswith('_ref') and isinstance(ref,dict):
  data=(R/ref['path']).read_bytes();assert sha(data)==ref['sha256'] and len(data)==ref['bytes'],key
  (I/pathlib.Path(ref['path']).name).write_bytes(data);objs[key]=json.loads(data)
def git(*args):
 p=subprocess.run(['git',*args],cwd=R,capture_output=True)
 assert p.returncode==0,(args,p.stderr.decode(errors='replace'))
 return p.stdout
meta=git('show','-s','--format=%H%n%T%n%P',commit).decode().strip().splitlines()
assert meta==[commit,a['candidate_tree'],a['candidate_parent']],meta
m=objs['source57_manifest_ref'];scope=objs['source_scope_ref']
assert len(m['files'])==57 and set(i['path'] for i in m['files'])==set(scope['source_allowlist'])
changed=git('diff-tree','--no-commit-id','--name-only','-r',commit).decode().splitlines()
assert len(changed)==52 and set(changed)<=set(scope['source_allowlist'])
for i in m['files']:
 data=git('show',commit+':'+i['path']);assert len(data)==i['bytes'] and sha(data)==i['sha256'],i['path']
pins=scope['inherited43_other_paths_must_remain_exact'];assert len(pins)==40
for i in pins:
 data=git('show',commit+':'+i['path']);assert len(data)==i['bytes'] and sha(data)==i['sha256'],i['path']
native=pathlib.Path(a['owned_ascii_native_fixture_root']);native.mkdir(parents=True,exist_ok=True)
snapshot=pathlib.Path(a['isolated_snapshot']);assert snapshot.parent==native and not snapshot.exists()
archive=native/'exact-08d63ed86356.tar'
assert not archive.exists()
with archive.open('xb') as f:
 p=subprocess.run(['git','archive','--format=tar',commit],cwd=R,stdout=f,stderr=subprocess.PIPE)
assert p.returncode==0,p.stderr.decode(errors='replace')
h=hashlib.sha256()
with archive.open('rb') as f:
 for block in iter(lambda:f.read(8<<20),b''):h.update(block)
archive_sha=h.hexdigest();archive_bytes=archive.stat().st_size
snapshot.mkdir(exist_ok=False)
count=0
with tarfile.open(archive,'r:') as tar:
 for member in tar:
  parts=pathlib.PurePosixPath(member.name).parts
  assert not member.name.startswith('/') and '..' not in parts,member.name
  dest=snapshot.joinpath(*parts)
  if member.isdir():dest.mkdir(parents=True,exist_ok=True);continue
  assert member.isfile(),('unsupported archive member',member.name)
  dest.parent.mkdir(parents=True,exist_ok=True)
  source=tar.extractfile(member)
  with dest.open('xb') as out:shutil.copyfileobj(source,out,1<<20)
  count+=1
for i in m['files']+pins:
 data=(snapshot/i['path']).read_bytes();assert len(data)==i['bytes'] and sha(data)==i['sha256'],i['path']
# Remove only this exact owned archive after its extraction and hash are recorded.
assert archive.parent.resolve()==native.resolve() and archive.name=='exact-08d63ed86356.tar'
archive.unlink()
out={'schema':'researchos.c57.independent-phase2-snapshot.v1','amendment_sha256':sha(araw),'commit':commit,'tree':a['candidate_tree'],'parent':a['candidate_parent'],'snapshot':str(snapshot),'source57_verified':True,'inherited40_verified':True,'changed52_allowlisted':True,'extracted_files':count,'archive_sha256':archive_sha,'archive_bytes':archive_bytes,'archive_removed_after_verified_extraction':True,'candidate_source_files':m['files'],'inherited40':pins}
with (B/'PHASE2-exact-snapshot-verification.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['candidate_source_files','inherited40']},ensure_ascii=False,indent=2))
print('GO_TOOL_EXISTS', (R/'.local/tools/go1.27.1/go/bin/go.exe').is_file())
