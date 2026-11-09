import hashlib,json,pathlib,subprocess
out=pathlib.Path(__file__).resolve().parent
repo=out.parents[6]
wt=repo/'.local/worktrees/w05-desktop-managed-qualification-core-repair-v2-20261012'
build=repo/'.local/builds/desktop-managed-qualification-core-repair-v2-20261012'
commit='0df32ed4eeeba3b9714477ccfae759ef90b633ee'
parent='63dec0f43b7a30d36e68a9826dc36e633936318f'
base='dfefe326dd7f4ae528caaf311ae388f40b8f0841'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=wt,text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD')==commit and git('rev-parse','HEAD^')==parent and not git('status','--porcelain')
refs=[]
for name,digest in [
('desktop_managed_qualification_core_codex/20261012-current-chat/source-bundle-final.json','091465245b17a69c03a05144418a35561db69cbf965985abd951bbb6ecefcb28'),
('desktop_managed_qualification_core_review_codex/20261012-current-chat/independent-review.json','82da4c7dc1c6d38abd86d275ce9e9e4a678a6fa7a344818d2aab59724664e926'),
('desktop_managed_qualification_core_review_codex/20261012-current-chat/receipt-manifest.json','6b2857e6e17f13110373a372baf1e0751fa8ae405604611fdf615aadd4b6506f'),
('resume_cp398_codex/20261012-current-chat/continuation-cp415/source-scopes.json','e7eb4cb1fdfc50199680456e167e21e4532cdfedac666377e00c1b24ce180852')]:
    p=repo/'execution/v2.4/receipts/W05/W05-99'/name
    assert sha(p)==digest
    refs.append({'path':str(p.relative_to(repo)),'sha256':digest})
def source(old):return [{'path':p,'sha256':sha(wt/p),'bytes':(wt/p).stat().st_size} for p in git('diff','--name-only',old,commit).splitlines()]
delta,cumulative=source(parent),source(base)
assert len(delta)==4 and len(cumulative)==14
allowed=json.loads((repo/refs[-1]['path']).read_text(encoding='utf-8-sig'))['repair']['paths']
assert all(x['path'] in allowed for x in delta)
tests=[]
for label in ['attempt10-frozen-domain','attempt11-frozen-host','attempt12-frozen-review-overlay','attempt14-frozen-verifier']:
    invocation=json.loads((out/(label+'.invocation.json')).read_text(encoding='utf-8'))
    terminal=json.loads((out/(label+'.summary.json')).read_text(encoding='utf-8'))
    assert invocation['exit_code']==0 and not any(x['Action'] in ['skip','fail'] for x in terminal)
    passed=[x['Test'] for x in terminal if x['Action']=='pass' and 'Test' in x]
    tests.append({'prefix':label,'parent_passes':sum('/' not in x for x in passed),'subtest_passes':sum('/' in x for x in passed),'skips':0,'exit_code':0,'stdout_sha256':sha(out/(label+'.stdout'))})
binaries=[]
for name in ['researchos-control.exe','runtime-verifier.exe']:
    path=build/name
    info=subprocess.check_output([str(repo/'.local/tools/go1.27.1/go/bin/go.exe'),'version','-m',str(path)],cwd=wt,text=True,encoding='utf-8')
    assert 'vcs.revision='+commit in info and 'vcs.modified=false' in info
    (out/(name+'.build-metadata.txt')).write_text(info,encoding='utf-8')
    binaries.append({'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'source_commit':commit,'vcs_modified':False})
reviewtest=repo/'execution/v2.4/receipts/W05/W05-99/desktop_managed_qualification_core_review_codex/20261012-current-chat/reviewer_shutdown_fence_windows_test.go'
manifest={'schema':'researchos.desktop-managed-qualification-source-repair.v2','candidate_commit':commit,'parent_commit':parent,'cumulative_base_commit':base,'worktree':str(wt),'status':'SOURCE_FIXTURE_PENDING_INDEPENDENT_REVIEW','frozen_inputs':refs,'source_delta':delta,'cumulative_source':cumulative,'binaries':binaries,'tests':tests,'review_overlay':{'original_file':str(reviewtest),'sha256':sha(reviewtest),'test_functions':3,'original_bytes_unchanged':True},'private_protocol_changed':False,'real_model_calls':0,'paid_model_calls':0,'external_model_calls':0,'protected_holdout':False,'live_product_qualification':False,'formal_acceptance_delta':0,'parent_acceptance_delta':0,'actual_control_exit_codes':[0,0],'second_coordinator_denied':True,'host_synthetic_sse_calls':8,'limitations':['Actual control lifecycle and Host qualification remain distinct evidence layers.','New actual V2 admission/startup/abort checks run domain fixtures, not Electron end-to-end.','Original UNKNOWN ledger drain refusal unchanged.'],'evidence':[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file() and p.name!='source-bundle-final.json']}
(out/'source-bundle-final.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'candidate':commit,'manifest_sha256':sha(out/'source-bundle-final.json'),'source_delta':len(delta),'cumulative_files':len(cumulative),'tests':tests},ensure_ascii=False))
