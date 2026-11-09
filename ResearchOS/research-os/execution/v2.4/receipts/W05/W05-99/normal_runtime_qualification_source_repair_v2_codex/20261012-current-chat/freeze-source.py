import hashlib,json,pathlib,re,subprocess

repo=pathlib.Path('D:/作品集/ResearchOS/research-os')
wt=repo/'.local/worktrees/w05-runtime-qualification-repair-v2-20261012'
out=pathlib.Path(__file__).parent
build=repo/'.local/builds/runtime-qualification-repair-v2-20261012'
commit='68a34150abab24c4e7edc49d166bf540c47cc42d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=wt,text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD')==commit and git('status','--porcelain')==''
base=git('rev-parse','HEAD^')
phase1=git('rev-parse','c9e47c6c^')
old=repo/'execution/v2.4/receipts/W05/W05-99/normal_runtime_qualification_source_codex/20261012-current-chat/source-bundle-final.json'
review=repo/'execution/v2.4/receipts/W05/W05-99/normal_runtime_qualification_source_review_codex/20261012-current-chat/final-decision-v2.json'
assert sha(old)=='4614b44b8ff3657cc14cac4efa2642e2b87bdbf46a76ea276a9fb37a9344a023'
assert sha(review)=='f475716b0ee1b74a0e7360ce80dfe419fdbbf330b677a634df4856dea313f1b2'
def sources(start):return [{'path':p,'sha256':sha(wt/p),'bytes':(wt/p).stat().st_size} for p in git('diff','--name-only',start,commit).splitlines()]
tests=[]
for name in ['attempt06-frozen-domain-regression.txt','attempt07-frozen-actual-service-root-revocation.txt']:
    text=(out/name).read_text(encoding='utf-8-sig').replace('\r','')
    assert '\nFAIL' not in text and '--- FAIL:' not in text and '\nPASS\n' in text
    tests.append({'path':name,'sha256':sha(out/name),'parent_passes':len(re.findall(r'^--- PASS:',text,re.M)),'subtest_passes':len(re.findall(r'^    --- PASS:',text,re.M)),'skips':len(re.findall(r'--- SKIP:',text))})
binaries=[];provenance=''
for name in ['runtime-verifier.exe','researchos-control.exe']:
    path=build/name
    info=subprocess.check_output([str(repo/'.local/tools/go1.27.1/go/bin/go.exe'),'version','-m',str(path)],cwd=wt,text=True,encoding='utf-8')
    assert 'vcs.revision='+commit in info and 'vcs.modified=false' in info
    provenance+=info+'\n'
    binaries.append({'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'source_commit':commit,'vcs_modified':False})
(out/'build-provenance.txt').write_text(provenance,encoding='utf-8')
manifest={'schema':'researchos.source-repair-candidate.v1','candidate_commit':commit,'parent_commit':base,'worktree':str(wt),'status':'SOURCE_REPAIR_PENDING_INDEPENDENT_REVIEW','finding':'W05-QUALIFICATION-ROOT-REVOCATION-001','review_input':{'path':str(review.relative_to(repo)),'sha256':sha(review),'original_decision':'REQUEST_CHANGES'},'original_frozen_input':{'path':str(old.relative_to(repo)),'sha256':sha(old)},'source_delta':sources(base),'cumulative_phase2_source':sources(phase1),'binaries':binaries,'tests':tests,'real_model_calls':0,'paid_model_calls':0,'external_model_calls':0,'protected_holdout':False,'live_product_qualification':False,'formal_acceptance_delta':0,'parent_acceptance_delta':0,'final_host_fixture':{'normal_synthetic_calls':2,'root_revocation_cases':4,'synthetic_calls_per_revoke_case':1,'retained_original_UNKNOWN_null':True,'verifier_tokens_revoked':True,'new_dispatch_after_root_revocation':False},'evidence':[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file() and p.name!='source-bundle-final.json']}
(out/'source-bundle-final.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'commit':commit,'source_delta':len(manifest['source_delta']),'cumulative_source':len(manifest['cumulative_phase2_source']),'manifest_sha256':sha(out/'source-bundle-final.json'),'tests':tests},ensure_ascii=False))
