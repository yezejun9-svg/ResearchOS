import hashlib, json, pathlib, subprocess
out=pathlib.Path(__file__).resolve().parent
root=out.parents[6]
receipts=out.parent
handoff=receipts/'handoff-5375496dd2b24206b5db17fc9bc358c3'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(args):
    r=subprocess.run(['git',*args],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if r.returncode: raise RuntimeError((args,r.returncode,r.stdout.decode('utf8',errors='replace'),r.stderr.decode('utf8',errors='replace')))
    return r.stdout
assert not git(['diff','--cached','--name-only']).strip(), 'Unexpected pre-existing staged changes'
sources=json.loads((handoff/'source.before_after.json').read_text('utf8'))
assert len(sources)==10
for row in sources: assert digest(root/row['path'])==row['after_sha256'], row['path']
files=sorted(p for p in receipts.rglob('*') if p.is_file())
manifest=out/'commit_manifest.json'
assert not manifest.exists()
manifest.write_text(json.dumps({'schema':'researchos.executor.commit-manifest.v1','scope':'Exact10 source plus complete owned executor receipts. Excludes only this manifest itself. Previous sealed manifests remain historical immutable snapshots.', 'source':[{'path':r['path'],'sha256':r['after_sha256']} for r in sources],'files':[{'path':p.relative_to(root).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size} for p in files]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
files.append(manifest)
stage=[r['path'] for r in sources]+[p.relative_to(root).as_posix() for p in files]
for start in range(0,len(stage),35): git(['add','-f','--',*stage[start:start+35]])
staged=git(['diff','--cached','--name-only','-z']).decode('utf8').split('\0')
assert set(filter(None,staged))==set(stage)
stdout=git(['commit','-m','feat(domain): add fixed schema22 to23 configuration upgrade guards'])
print(stdout.decode('utf8',errors='replace')[:400])
print(json.dumps({'candidate_commit':git(['rev-parse','HEAD']).decode().strip(),'source_count':10,'receipt_count':len(files),'manifest':{'path':manifest.relative_to(root).as_posix(),'sha256':digest(manifest)},'status':git(['status','--porcelain=v1']).decode('utf8',errors='replace')},ensure_ascii=False))
