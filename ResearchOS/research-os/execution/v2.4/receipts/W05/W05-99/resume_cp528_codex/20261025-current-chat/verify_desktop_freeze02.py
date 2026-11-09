import json
from pathlib import Path
from preserve_main_baseline import verify,read,ref,git,R,N
W=R/'.local/worktrees/desktop-main7d-native-20261025';A=N.parent.parent/'desktop_main7d_native_codex/20261025-current-chat/complete-tree'
f=A/'SOURCE-FREEZE-02.json';assert ref(f)['sha256']=='6d885a649bb020d702487d5331f394cc43b3fd1c22d00a11822289ba7d644d3b';v=read(f)
s=read(N/'continuation-cp552/Desktop-complete-tree-source-scope.json');assert set(v['candidate_delta'])==set(s['source_write_allowlist']) and len(v['seven_file_hashes'])==7
assert git(W,'rev-parse','HEAD').decode().strip()==v['base_commit'] and git(W,'show','-s','--format=%T','HEAD').decode().strip()==v['base_tree']
changes=set()
for args in [('diff','--name-only','-z'),('diff','--cached','--name-only','-z'),('ls-files','--others','--exclude-standard','-z')]:changes.update(x for x in git(W,*args).decode().split('\0')if x)
assert changes==set(s['source_write_allowlist']);refs=[ref(f)]
for name,x in v['seven_file_hashes'].items():
 a=ref(W/name);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];refs.append(a)
x=v['patch'];a=ref(Path(x['path']));assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];refs.append(a)
for tag,x in v['focused_checks'].items():
 for kind in ['stdout','stderr']:
  a=ref(A/(tag+'.'+kind+'.raw'));assert a['sha256']==x[kind+'_sha256'];refs.append(a)
 p=A/(tag+'.native-exit.txt');assert p.read_text(encoding='utf-8-sig').strip()==x['exit']=='0';refs.append(ref(p))
out={'schema':'researchos.desktop-freeze02-root-verification.v1','candidate':'UNCOMMITTED_BASE_PLUS_EXACT7_DELTA','verified_refs':refs,'source_input_digest':v['source_snapshot_digest'],'source_input_count':591,'originals_preserved':verify(),'independent_review':'RUNNING_BOUND_TO_SOURCE_FREEZE_02','complete_build':'IN_PROGRESS_NOT_YET_ACCEPTED','mock_checks_only':True,'native_GUI_Core_launched':False,'formal_increment':0}
with(N/'Desktop-freeze02-root-verification.json').open('x',encoding='utf8')as stream:json.dump(out,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'source_paths':7,'verified_refs':len(refs),'Main_preserved':True,'C57_preserved':True,'build':'IN_PROGRESS','formal':0}))
