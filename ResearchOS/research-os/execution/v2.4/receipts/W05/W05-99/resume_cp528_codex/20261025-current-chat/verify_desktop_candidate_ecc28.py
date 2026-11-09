import datetime,hashlib,json
from pathlib import Path
from preserve_main_baseline import verify,read,ref,git,R,N
A=N.parent.parent/'desktop_main7d_native_codex/20261025-current-chat/complete-tree';W=R/'.local/worktrees/desktop-main7d-native-20261025'
def new(p,v):
 with p.open('x',encoding='utf8')as stream:json.dump(v,stream,ensure_ascii=False,indent=2);stream.write('\n')
refs=[]
for name,sha in [('POSTCOMMIT-VALIDATION.json','72f0d5cf4db4ec775f5b103cf6529748c87ce57664679da15c3d38385264ee00'),('SOURCE-FREEZE-03.json','c6ac8745f27d91a7d74aa804acdc05f3a50932b0d414a91f63daefe75c00c113'),('PRECOMMIT-MANIFEST-r3.json','e0a7e587b3f1c6a613f738b56b5b2401cd8a3aa841308cae1e82da01b759301f')]:
 a=ref(A/name);assert a['sha256']==sha;refs.append(a)
p=read(A/'POSTCOMMIT-VALIDATION.json');f=read(A/'SOURCE-FREEZE-03.json');scope=read(N/'continuation-cp552/Desktop-complete-tree-source-scope.json')
assert git(W,'rev-parse','HEAD').decode().strip()==p['candidate_commit']=='ecc28dd3c91a0f68dcddb41b53325aa7f0e81419'
assert git(W,'show','-s','--format=%T','HEAD').decode().strip()==p['candidate_tree']=='1d44a02c9483fc529b08ffe81895ec443920bdd1'
assert git(W,'rev-parse','HEAD^').decode().strip()==p['parent_commit']==scope['base_commit']
assert not git(W,'status','--porcelain=v1','--untracked-files=all')
changed=set(git(W,'diff','HEAD^','HEAD','--name-only','-z').decode().strip('\0').split('\0'));assert changed==set(scope['source_write_allowlist'])==set(f['seven_file_hashes'])
for name,x in f['seven_file_hashes'].items():
 a=ref(W/name);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];assert hashlib.sha256(git(W,'show','HEAD:'+name)).hexdigest()==a['sha256'];refs.append(a)
x=f['patch'];a=ref(Path(x['path']));assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];refs.append(a)
result=read(A/'build-02/result.json');assert result['status']=='BUILT_NOT_NATIVE_TESTED' and result['source_drift']is False and result['public_vendor_drift']is False
B=Path(result['output']);a=ref(B/'development-manifest.json');assert a['sha256']==result['manifest_sha256']==p['tested_bundle_manifest_sha256']=='e1d61b68d12c61e2dda341df3541d2b4b541b9c2331af5da26ca56dff759b620';refs.append(a)
assert ref(A/'build-02/development-manifest.json')['sha256']==a['sha256'];refs.append(ref(A/'build-02/development-manifest.json'));manifest=read(B/'development-manifest.json');assert len(manifest['files'])==132 and manifest['electron']['file_count']==75
for x in manifest['files']:
 q=(B/x['path']).resolve();assert q.is_relative_to(B.resolve());a=ref(q);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];refs.append(a)
assert ref(B/'launch-development.mjs')['sha256']==f['seven_file_hashes']['apps/desktop/launch-development.mjs']['sha256']
for name in ['diagnostics.json','diagnostics-r3.json','build-02/result.json','FINAL-CANDIDATE.md']:refs.append(ref(A/name))
out={'schema':'researchos.desktop-final-candidate-root-verification.v1','candidate_commit':p['candidate_commit'],'candidate_tree':p['candidate_tree'],'parent':p['parent_commit'],'verified_refs':refs,'scope_paths':7,'bundle_root':str(B),'bundle_files':132,'bundle_bytes':sum(x['bytes']for x in manifest['files']),'source_and_build':'CURRENT_R3_SOURCE_AND_BUILD_PINNED_INDEPENDENT_FINAL_SEAL_PENDING','originals_preserved':verify(),'native_GUI_Core_launched':False,'formal_increment':0}
new(N/'Desktop-ecc28-candidate-root-verification.json',out)
denied=A/'precommit-02.temp-index';assert denied.is_file()
new(N/'Desktop-temp-index-policy-denial.json',{'schema':'researchos.desktop-temp-index-policy-denial.v1','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'Builder current-chat tool report; no native command started','rejected_action':'PowerShell Remove-Item -LiteralPath $p -Force','target':ref(denied),'reason':'rejected: blocked by policy','native_stdout_stderr_exit':'ABSENT_REJECTED_BEFORE_CREATEPROCESS','auto_review_denial':True,'retained':True,'retry_or_bypass':False,'not_in_author_diagnostics_r3':True,'formal_increment':0})
new(N/'C57-admin-session-user-preparing.json',{'schema':'researchos.C57-admin-session-resource-status.v1','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'user_reply':'我来准备独立管理员会话','status':'USER_PREPARING_NOT_VERIFIED','distinct_sid_available':False,'privileged_session_verified':False,'existing_original_action_scope_unchanged':True,'next':'When user provides ready session, first verify SID/elevation/required privileges read-only, then bind concrete C57 execution scope','formal_increment':0})
print(json.dumps({'candidate':p['candidate_commit'],'verified_refs':len(refs),'files':132,'bytes':out['bundle_bytes'],'originals_preserved':True,'native_GUI_Core_launched':False,'C57_admin':'USER_PREPARING','formal':0}))
