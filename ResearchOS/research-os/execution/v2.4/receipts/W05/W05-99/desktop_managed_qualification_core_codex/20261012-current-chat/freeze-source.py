import hashlib,json,pathlib,re,subprocess
repo=pathlib.Path('D:/作品集/ResearchOS/research-os')
wt=repo/'.local/worktrees/w05-desktop-managed-qualification-core-20261012'
out=pathlib.Path(__file__).parent
build=repo/'.local/builds/desktop-managed-qualification-core-20261012'
commit='63dec0f43b7a30d36e68a9826dc36e633936318f'
base='dfefe326dd7f4ae528caaf311ae388f40b8f0841'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=wt,text=True,encoding='utf-8').strip()
assert git('rev-parse','HEAD')==commit and git('rev-parse','HEAD^')==base and git('status','--porcelain')==''
old=repo/'execution/v2.4/receipts/W05/W05-99/normal_runtime_qualification_source_repair_v2_codex/20261012-current-chat/source-bundle-final.json'
assert sha(old)=='eee1788eabec75ebba66ca0d2e31c3925daee2d8888328ab91d84d8d69df67ef'
source=[{'path':p,'sha256':sha(wt/p),'bytes':(wt/p).stat().st_size} for p in git('diff','--name-only',base,commit).splitlines()]
assert len(source)==12
results=[]
for name in ['attempt09-frozen-domain.txt','attempt10-frozen-host-private.txt','attempt11-frozen-verifier.txt']:
    raw=(out/name).read_text(encoding='utf-8-sig').replace('\r','')
    assert '\nFAIL' not in raw and '--- FAIL:' not in raw and '--- SKIP:' not in raw and '\nPASS\n' in raw
    results.append({'path':name,'sha256':sha(out/name),'parent_passes':len(re.findall(r'^--- PASS:',raw,re.M)),'subtest_passes':len(re.findall(r'^    --- PASS:',raw,re.M)),'skips':0})
binaries=[]
for name in ['runtime-verifier.exe','researchos-control.exe']:
    path=build/name
    info=subprocess.check_output([str(repo/'.local/tools/go1.27.1/go/bin/go.exe'),'version','-m',str(path)],cwd=wt,text=True,encoding='utf-8')
    assert 'vcs.revision='+commit in info and 'vcs.modified=false' in info
    binaries.append({'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'source_commit':commit,'vcs_modified':False})
manifest={'schema':'researchos.desktop-managed-qualification-source.v1','candidate_commit':commit,'parent_commit':base,'worktree':str(wt),'status':'SOURCE_FIXTURE_PENDING_INDEPENDENT_REVIEW','original_frozen_input':{'path':str(old.relative_to(repo)),'sha256':sha(old)},'source_delta':source,'binaries':binaries,'tests':results,'private_protocol':{'path':'private-protocol.md','sha256':sha(out/'private-protocol.md'),'protocol':'researchos-desktop-management/1','process_created_ns_type':'decimal-string','confirmation_ttl_seconds':60,'transport':'inherited-stdio-only','mode':'IN_PLACE','frozen_v2_native3_changed':False},'real_model_calls':0,'paid_model_calls':0,'external_model_calls':0,'protected_holdout':False,'live_product_qualification':False,'formal_acceptance_delta':0,'parent_acceptance_delta':0,'final_host_fixture':{'private_normal_synthetic_calls':2,'lost_reply_synthetic_calls':2,'root_revocation_cases':4,'synthetic_calls_per_revoke_case':1,'actual_control_generations':2,'actual_control_orderly_exit_codes':[0,0],'second_coordinator_denied':True,'retained_original_UNKNOWN_null':True,'verifier_tokens_revoked':True,'lost_reply_auto_replay':False},'known_limits':['Default Desktop client wiring awaits independent Source review and Root integration.','QuiesceForRelease retains original UNKNOWN ledger drain refusal.','Owned failed-test temporary directory cleanup was denied by automatic policy; retained outside evidence.'],'evidence':[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file() and p.name!='source-bundle-final.json']}
(out/'source-bundle-final.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'commit':commit,'source_files':len(source),'manifest_sha256':sha(out/'source-bundle-final.json'),'tests':results},ensure_ascii=False))
