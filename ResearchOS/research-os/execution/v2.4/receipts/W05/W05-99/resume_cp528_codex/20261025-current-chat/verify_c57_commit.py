from pathlib import Path
import hashlib,json,subprocess
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;P=N.parent.parent/'qualification_maintenance_c57_codex/20261025-current-chat';W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
mf=P/'C57-COMMIT-SOURCE57-MANIFEST.json';assert ref(mf)['sha256']=='1b673c4563599dac13fb27fac85bed0c2954e53389a5c033c19c31ee28f9a734';m=read(mf)
assert m['commit']=='08d63ed86356a93fe5715732cfeae0624c5cb6c9' and m['tree']=='aad52d16816d63e78d5b94473c56fd2bca5353ce'
scope=read(N/'continuation-cp533/C57-source-scope.json');assert len(m['files'])==57 and {x['path']for x in m['files']}==set(scope['source_allowlist'])
g=lambda *a:subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0']+list(a),cwd=W)
assert g('rev-parse','HEAD').decode().strip()==m['commit'];assert g('rev-parse','HEAD^{tree}').decode().strip()==m['tree'];assert g('rev-parse','HEAD^').decode().strip()==m['parent']==scope['base_commit']
assert not g('status','--porcelain=v1','--untracked-files=all')
changed=g('diff','--name-only','-z',m['parent'],m['commit']).decode().strip(chr(0)).split(chr(0));assert len(changed)==52 and set(changed)<=set(scope['source_allowlist'])
for x in m['files']:
 raw=g('show',m['commit']+':'+x['path']);assert hashlib.sha256(raw).hexdigest()==x['sha256'] and len(raw)==x['bytes'];assert (W/x['path']).read_bytes()==raw;assert x['changed_in_commit']==(x['path']in changed)
for x in scope['inherited43_other_paths_must_remain_exact']:
 raw=g('show',m['commit']+':'+x['path']);assert hashlib.sha256(raw).hexdigest()==x['sha256'] and len(raw)==x['bytes']
checks=[];refs=[ref(mf)]
for stem in ['079-boot-v11-c-env','081-combined-v11-tests','082-combined-v11-windows-build']:
 candidates=list(P.glob(stem.split('-')[0]+'*.native-exit.txt'));assert len(candidates)==1
 q=candidates[0];name=q.name.removesuffix('.native-exit.txt');assert int(q.read_text(encoding='utf-8-sig').strip())==0
 for suffix in ['.recipe.txt','.stdout.raw','.stderr.raw','.native-exit.txt']:refs.append(ref(P/(name+suffix)))
 checks.append({'id':name,'native_exit':0})
out={'schema':'researchos.c57-exact57-root-verification.v1','commit':m['commit'],'tree':m['tree'],'parent':m['parent'],'manifest':ref(mf),'allowlist57':True,'actual_changed52':True,'inherited40_exact':True,'clean_worktree':True,'all57_git_blobs_and_worktree_exact':True,'source_files':m['files'],'author_final_tests':checks,'verified_refs':refs,'independent_acceptance':False,'formal_increment':0}
with(N/'C57-commit-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items()if k not in ['source_files','verified_refs']},ensure_ascii=False))
