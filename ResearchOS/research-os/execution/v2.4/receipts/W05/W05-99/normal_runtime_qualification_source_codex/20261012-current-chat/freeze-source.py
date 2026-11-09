import hashlib,json,pathlib,subprocess,re

root=pathlib.Path('D:/作品集/ResearchOS/research-os')
wt=root/'.local/worktrees/w05-runtime-qualification-source-20261012'
out=pathlib.Path(__file__).parent
build=root/'.local/builds/runtime-qualification-source-20261012'
commit='c9e47c6cd16946ac02a874422a894249f87c6c50'
def git(*args):return subprocess.check_output(['git',*args],cwd=wt,text=True,encoding='utf-8').strip()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert git('rev-parse','HEAD')==commit
assert not git('status','--porcelain')
base=git('rev-parse','HEAD^')
files=git('diff','--name-only',base,commit).splitlines()
source=[{'path':f,'sha256':sha(wt/f),'bytes':(wt/f).stat().st_size} for f in files]
go=root/'.local/tools/go1.27.1/go/bin/go.exe'
provenance=''
binaries=[]
for name in ['runtime-verifier.exe','researchos-control.exe']:
    path=build/name
    meta=subprocess.check_output([str(go),'version','-m',str(path)],cwd=wt,text=True,encoding='utf-8')
    assert 'vcs.revision='+commit in meta and 'vcs.modified=false' in meta
    provenance+=meta+'\n'
    binaries.append({'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'source_commit':commit,'vcs_modified':False})
(out/'build-provenance.txt').write_text(provenance,encoding='utf-8')
tests=[]
for name in ['attempt13-final-regression.txt','attempt14-frozen-source-synthetic.txt','attempt15-frozen-verifier.txt']:
    raw=(out/name).read_text(encoding='utf-8-sig')
    assert '\nFAIL' not in raw and '--- FAIL:' not in raw and '\nPASS\n' in raw.replace('\r','')
    tests.append({'path':name,'sha256':sha(out/name),'parent_passes':len(re.findall(r'^--- PASS:',raw,re.M)),'subtest_passes':len(re.findall(r'^    --- PASS:',raw,re.M)),'skips':len(re.findall(r'--- SKIP:',raw))})
evidence=[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file() and p.name!='source-bundle-final.json']
manifest={'schema':'researchos.source-candidate.v1','candidate_commit':commit,'parent_commit':base,'worktree':str(wt),'status':'SOURCE_CANDIDATE_PENDING_INDEPENDENT_REVIEW','real_model_calls':0,'live_qualification':False,'protected_holdout':False,'synthetic_transport_final_calls':2,'formal_parent_acceptance':False,'source':source,'binaries':binaries,'tests':tests,'evidence':evidence,'residuals':['Desktop privileged producer not implemented in this ownership','Actual Ollama qualification not run','Application separation does not prove protected holdout','Policy drift after Run admission fails closed; renewal is explicit']}
(out/'source-bundle-final.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'commit':commit,'source_files':len(source),'manifest_sha256':sha(out/'source-bundle-final.json'),'tests':tests},ensure_ascii=False))
