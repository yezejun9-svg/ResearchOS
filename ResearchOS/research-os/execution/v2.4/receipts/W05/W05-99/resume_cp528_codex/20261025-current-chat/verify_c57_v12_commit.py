from pathlib import Path
import hashlib,json,subprocess
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;E=N.parent.parent;P=E/'qualification_maintenance_c57_codex/20261025-current-chat';T=E/'qualification_maintenance_c57_independent_review_codex/20261025-current-chat/token-privilege-static';W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
mf=P/'C57-V12-COMMIT-SOURCE57-MANIFEST.json';assert ref(mf)['sha256']=='5ce73534294539434c70405df7e3b50f6df0b3cea9f9f9a4f03033036f0f5555';m=read(mf)
assert m['commit']=='03aa4d687dfaa541d9b18d4c766805307a537d1d'and m['tree']=='81059bc4cdba04716fcd2607496485bbbf22bc80'and m['parent']=='08d63ed86356a93fe5715732cfeae0624c5cb6c9'
scope=read(N/'continuation-cp533/C57-source-scope.json');assert len(m['files'])==57 and {x['path']for x in m['files']}==set(scope['source_allowlist']) and m['baseline']==scope['base_commit']
g=lambda *a:subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0']+list(a),cwd=W)
for expr,key in [('HEAD','commit'),('HEAD^{tree}','tree'),('HEAD^','parent')]:assert g('rev-parse',expr).decode().strip()==m[key]
assert not g('status','--porcelain=v1','--untracked-files=all')
delta=g('diff','--name-only','-z',m['parent'],m['commit']).decode().strip(chr(0)).split(chr(0));assert delta==['internal/recoveryboundary/boot_windows.go','internal/recoveryboundary/boot_windows_test.go']==m['delta_paths']
changed=g('diff','--name-only','-z',m['baseline'],m['commit']).decode().strip(chr(0)).split(chr(0));assert len(changed)==52 and set(changed)<=set(scope['source_allowlist'])
for x in m['files']:
 raw=g('show',m['commit']+':'+x['path']);assert hashlib.sha256(raw).hexdigest()==x['sha256']and len(raw)==x['bytes'];assert (W/x['path']).read_bytes()==raw
 assert x['changed_in_delta']==(x['path']in delta) and x['changed_from_085b']==(x['path']in changed)
for x in scope['inherited43_other_paths_must_remain_exact']:
 raw=g('show',m['commit']+':'+x['path']);assert hashlib.sha256(raw).hexdigest()==x['sha256']and len(raw)==x['bytes']
seal=T/'v12-static-seal.json';assert ref(seal)['sha256']=='bc82dff57c5f70a8e594d29c8b0c53b12f5e9ad08e8da6aa1aad81541cc29a89';s=read(seal);assert len(s['files'])==32 and s['verdict']=='SOURCE_P1_PRIVILEGE_ADMISSION_GAP_CLOSED_STATIC';refs=[ref(mf),ref(seal)]
for x in s['files']:
 a=ref(T/x['name']);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];refs.append(a)
checks=[]
for stem in ['096-v12-interface','097-v12-windows-build']:
 assert int((P/(stem+'.native-exit.txt')).read_text(encoding='utf-8-sig').strip())==0
 for suffix in ['.recipe.txt','.stdout.raw','.stderr.raw','.native-exit.txt']:refs.append(ref(P/(stem+suffix)))
 checks.append({'id':stem,'native_exit':0})
out={'schema':'researchos.c57-v12-exact57-root-verification.v1','commit':m['commit'],'tree':m['tree'],'parent':m['parent'],'baseline':m['baseline'],'manifest':ref(mf),'delta':delta,'cumulative_changed52':True,'allowlist57_exact':True,'inherited40_exact':True,'clean_worktree':True,'all57_git_blobs_and_worktree_exact':True,'independent_static_P1_closed':True,'static_seal':ref(seal),'native_independent_v12_pending':True,'author_checks':checks,'verified_refs':refs,'formal_increment':0}
with(N/'C57-v12-commit-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items()if k!='verified_refs'},ensure_ascii=False))
