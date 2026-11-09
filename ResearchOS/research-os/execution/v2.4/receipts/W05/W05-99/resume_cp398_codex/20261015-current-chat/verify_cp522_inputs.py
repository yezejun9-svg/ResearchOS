import hashlib,json,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W05/W05-99';B=E/'resume_cp398_codex/20261015-current-chat'
BR=E/'qualification_failure_b_revision02_independent_review_codex/20261015-current-chat'
SA=E/'owned_core_stop_effect_state_revision05_source_codex/20261015-current-chat';SF=SA/'candidate-37a1f6d3-final'
Q=E/'online_backup_fixture_qualification_codex/20261015-current-chat'
SW=R/'.local/worktrees/owned-core-stop-effect-state-r5-20261015';QW=R/'.local/worktrees/online-backup-fixture-qualification-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
verified={};unresolved=[]
def check(v,parent):
 p=Path(v['path']);opts=[p] if p.is_absolute() else [parent/p,R/p,SW/p,QW/p,SA/p,SF/p,Q/p,BR/p]
 for q in opts:
  if q.is_file():
   a=ref(q)
   if a['sha256']==v['sha256']:
    if 'bytes'in v:assert a['bytes']==v['bytes']
    verified[str(q.resolve())]=a;return
 unresolved.append({'ref':v,'parent':str(parent)})
def nested(v,parent):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str)and isinstance(v.get('sha256'),str):check(v,parent)
  for x in v.values():nested(x,parent)
 elif isinstance(v,list):
  for x in v:nested(x,parent)
def manifest(p,sha):
 assert ref(p)['sha256']==sha;v=read(p);nested(v,p.parent)
 if isinstance(v.get('files'),dict):
  for name,x in v['files'].items():check(dict(x,path=name),p.parent)
 return v
bm=manifest(BR/'FINAL-manifest.json','5c5e96aeafbf3c11d970e2ffc5c61fc5709a0585916bd71edd3156f812f477cf')
sm=manifest(SF/'manifest.json','d0466ed18795e3beb11debdf20cde5b42cfd4bb9aee33213fda8e6d0c46e17d4')
qm=manifest(Q/'FINAL-manifest.json','663edb126788ecefa7e5464e9db9414e0d768f48c8c5d5ab3f97bf66acec229c')
assert ref(Q/'capture-index-supplement.json')['sha256']=='bc7da3e11ad65d094e954ba4936b3b15ef090a449ad1a419f068f620e8b70e27'
sup=read(Q/'capture-index-supplement.json');nested(sup,Q)
ci=read(SF/'command-index.json');sc=[]
for row in ci:
 d=Path(row['directory']);files={p.name:ref(p) for p in d.iterdir() if p.is_file()}
 for key in ['before_sha256','after_sha256','stdout_sha256','stderr_sha256']:
  matches=[a for a in files.values() if a['sha256']==row[key]];assert matches,(row,key)
  for a in matches:verified[a['path']]=a
 sc.append({'directory':str(d),'native_exit':row['native_exit'],'verified_digest_fields':4})
qh=read(Q/'source-helper-overlay-manifest.json');nested(qh,Q)
for name,x in qh['helper_and_overlay'].items():
 if isinstance(x,dict)and'sha256'in x:check(dict(x,path=x.get('path',name)),Q)
qi=read(Q/'command-index.json');rows=qi.get('commands',qi.get('records',[])) if isinstance(qi,dict) else qi
nested(qi,Q)
git=['git','-c','maintenance.auto=false','-c','gc.auto=0']
def g(w,*a):return subprocess.check_output(git+list(a),cwd=w)
assert g(SW,'rev-parse','HEAD').decode().strip()==sm['source_commit']
assert g(SW,'rev-parse','HEAD^{tree}').decode().strip()==sm['source_tree']
assert not g(SW,'status','--porcelain=v1','--untracked-files=all')
assert len(g(SW,'diff','--name-only',sm['main_base_commit'],sm['source_commit']).splitlines())==19
assert len(g(SW,'diff','--name-only','ab308912117dac59cadd5aa2e75b46a418e41b6b',sm['source_commit']).splitlines())==2
for v in sm['patches'].values():assert hashlib.sha256(g(SW,*v['argv'][1:])).hexdigest()==v['sha256']
assert g(QW,'rev-parse','HEAD').decode().strip()==qh['source_commit'];assert not g(QW,'status','--porcelain=v1','--untracked-files=all')
ledger=read(SF/'failure-ledger.json');normalstderr=[]
for x in ledger['rows']:
 if x['native_exit']==0:
  d=Path(x['directory'])
  for p in d.iterdir():
   if p.is_file()and hashlib.sha256(p.read_bytes()).hexdigest()==x['stderr_sha256']:normalstderr.append(p.read_text(encoding='utf-8-sig'))
out={'verified_ref_count':len(verified),'refs':list(verified.values()),'unresolved_refs':unresolved,'stop_capture_rows':sc,'stop_manifest_keys':list(sm),'backup_index_type':type(qi).__name__,'backup_rows':len(rows),'backup_first':rows[:1],'backup_last':rows[-1:],'backup_helper_keys':list(qh),'stop_native0_stderr':normalstderr,'B_payload112_verified':len(bm['payload_files'])==112,'actual_authority':False,'formal_increment':0}
p=B/'cp522-input-verification.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in out.items()if k not in ['refs','stop_capture_rows']},ensure_ascii=False));print('OUTPUT',json.dumps(ref(p),ensure_ascii=False))
