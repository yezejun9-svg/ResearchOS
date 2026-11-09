import hashlib,json,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W05/W05-99';B=Path(__file__).parent;S=E/'qualification_failure_b_revision03_source_codex/20261015-current-chat';W=R/'.local/worktrees/qualification-failure-b-r3-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
mp=S/'FINAL-manifest.json';assert ref(mp)['sha256']=='35d38269f51eddc5566c561aca948ad2c76429a79410fdef217bfe71b79b9274';m=read(mp);verified=[];unresolved=[]
def check(v,parent):
 p=Path(v['path']);opts=[p]if p.is_absolute()else[parent/p,S/p,R/p,W/p]
 for q in opts:
  if q.is_file()and ref(q)['sha256']==v['sha256']:
   a=ref(q)
   if 'bytes'in v:assert a['bytes']==v['bytes']
   verified.append(a);return
 unresolved.append({'ref':v,'parent':str(parent)})
def nested(v,parent):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str)and isinstance(v.get('sha256'),str):check(v,parent)
  for x in v.values():nested(x,parent)
 elif isinstance(v,list):
  for x in v:nested(x,parent)
nested(m,S)
if isinstance(m.get('files'),dict):
 for n,v in m['files'].items():check(dict(v,path=v.get('path',n)),S)
ci=read(S/'command-index.json');nested(ci,S)
rows=ci if isinstance(ci,list)else max([x for x in ci.values()if isinstance(x,list)],key=len)
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda *a:subprocess.check_output(git+list(a),cwd=W)
assert g('rev-parse','HEAD').decode().strip()=='fec4a4d7bc8aa4ce6ee1e0f9a7da024bd528ca3f';assert g('rev-parse','HEAD^{tree}').decode().strip()=='730be49f57988da8be32af27225848690d202e63';assert not g('status','--porcelain=v1','--untracked-files=all')
delta=g('diff','--name-only','1d3cc504da79df5bf0f69755011738d5adb827b0','HEAD').decode().splitlines();whole=g('diff','--name-only','f48fca0e4013bda19913a34d91da0cd23157a08b','HEAD').decode().splitlines()
# The authoritative accepted A exact base is read from the prior independent report.
base=read(E/'qualification_failure_b_revision02_independent_review_codex/20261015-current-chat/review.json')['base'];whole=g('diff','--name-only',base,'HEAD').decode().splitlines()
assert len(delta)==4 and len(whole)==9
for start,sha in [('1d3cc504da79df5bf0f69755011738d5adb827b0','f0990ab1e411327f20b9d45b1ff51f02e435c01c9892ba0d090958acdbb4187e'),(base,'3b77eaf0f5983b6a9cabedf1a421b9ab2a0655d16f29cbeb827be3fa3ea0df4d')]:assert hashlib.sha256(g('diff','--binary','--full-index',start,'HEAD')).hexdigest()==sha
md=(S/'FINAL.md').read_text(encoding='utf-8-sig');print('FINAL_MD_LENGTH',len(md),'TEXT\n'+md[:7000])
ledger=[json.loads(x)for x in (S/'diagnostic-ledger.jsonl').read_text(encoding='utf-8-sig').splitlines()if x.strip()];print('LEDGER',json.dumps(ledger,ensure_ascii=False))
print('MANIFEST_META',json.dumps({k:({'type':type(x).__name__,'count':len(x)}if isinstance(x,(dict,list))else x)for k,x in m.items()},ensure_ascii=False))
print('CI',json.dumps({'type':type(ci).__name__,'count':len(rows),'keys_first':list(rows[0]),'first_meta':{k:v for k,v in rows[0].items()if k not in ['argv','fullargv','full_argv','script','environment','env']},'keys_last':list(rows[-1])},ensure_ascii=False))
out={'manifest':ref(mp),'refs':verified,'verified_ref_count':len(verified),'unresolved':unresolved,'candidate':'fec4a4d7bc8aa4ce6ee1e0f9a7da024bd528ca3f','tree':'730be49f57988da8be32af27225848690d202e63','delta4':delta,'whole9':whole,'base':base,'command_count':len(rows),'diagnostic_ledger':ref(S/'diagnostic-ledger.jsonl'),'source_semantic_acceptance':False}
p=B/'B-r3-root-frozen-input-verification.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('ROOT_VERIFICATION',json.dumps({'output':ref(p),'verified':len(verified),'unresolved':unresolved},ensure_ascii=False))
