import hashlib
import json
from pathlib import Path
import subprocess

R=Path('D:/作品集/ResearchOS/research-os')
B=Path(__file__).parent
E=R/'execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision02_source_codex/20261015-current-chat'
O=B/'continuation-cp521-inputs'
O.mkdir(exist_ok=False)
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
    b=p.read_bytes()
    return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
assert ref(E/'FINAL-manifest.json')['sha256']=='1aca112dd1d8c963da7ea1cd7a9db6b012048426515aff439ccb420aca689bda'
m=read(E/'FINAL-manifest.json')
w=Path(m['worktree'])
g=['git','-c','maintenance.auto=false','-c','gc.auto=0']
assert subprocess.check_output(g+['rev-parse','HEAD'],cwd=w,text=True).strip()==m['commit']
assert subprocess.check_output(g+['rev-parse','HEAD^{tree}'],cwd=w,text=True).strip()==m['tree']
assert not subprocess.check_output(g+['status','--porcelain=v1','--untracked-files=all'],cwd=w)
assert set(subprocess.check_output(g+['diff','--name-only',m['base_commit'],m['commit']],cwd=w,text=True).splitlines())==set(m['source_allowlist'])
assert set(subprocess.check_output(g+['diff','--name-only',m['combined_base'],m['commit']],cwd=w,text=True).splitlines())==set(m['combined_source_paths'])
for path,v in m['source_hashes'].items():
    b=subprocess.check_output(g+['show',m['commit']+':'+path],cwd=w)
    assert hashlib.sha256(b).hexdigest()==v['sha256'] and len(b)==v['bytes'],path
    assert ref(w/path)['sha256']==v['sha256']
for v in m['patches'].values():
    a=ref(E/v['path'])
    assert a['sha256']==v['sha256'] and a['bytes']==v['bytes']
ci=read(E/m['command_index'])
assert ci['count']==len(ci['commands'])==134
refs={}
for row in ci['commands']:
    for key,hashkey in [('stdout_raw','stdout_sha256'),('stderr_raw','stderr_sha256')]:
        p=E/row[key]
        a=ref(p)
        assert a['sha256']==row[hashkey],row['tag']
        refs[str(p)]=a
    p=E/row['result']
    result=read(p)
    assert result['argv']==row['argv'] and result['cwd']==row['cwd'],row['tag']
    assert result['native_exit']==row['native_exit'],row['tag']
    refs[str(p)]=ref(p)
    # All author command recipes remain available for independent field/ordering review.
    candidates=[E/(row['tag']+'.recipe.json'),E/(row['tag']+'.command.json')]
    for p in candidates:
        if p.is_file(): refs[str(p)]=ref(p)
out={'schema':'researchos.root-B-r2-provenance-verification.v1','source_manifest':ref(E/'FINAL-manifest.json'),'candidate':m['commit'],'tree':m['tree'],'source_hashes':m['source_hashes'],'delta5_verified':True,'whole9_verified':True,'clean_worktree':True,'command_index':ref(E/m['command_index']),'commands_verified':134,'command_file_refs':list(refs.values()),'semantic_source_acceptance':False,'native_nonzero_or_unavailable':sum(x['native_exit']!=0 for x in ci['commands'])}
p=O/'B-r2-root-input-verification.json'
with p.open('x',encoding='utf8') as f: json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'output':ref(p),'commands_verified':134,'command_files':len(refs),'native_nonzero_or_unavailable':out['native_nonzero_or_unavailable']},ensure_ascii=False))
