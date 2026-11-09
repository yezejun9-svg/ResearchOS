import json,hashlib,subprocess,re
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/source43_b_stop_finalpath_codex/20261025-current-chat';OLD=E.parent/'20261015-current-chat';W=R/'.local/worktrees/source43-b-stop-finalpath-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
verified=[]
def check(p,want=None):
 b=p.read_bytes();v={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if want:
  assert v['sha256']==want['sha256'],(str(p),'hash')
  if 'bytes'in want:assert v['bytes']==want['bytes'],(str(p),'bytes')
 verified.append(v);return v
f=read(E/'FINAL-manifest.json');check(E/'FINAL-manifest.json')
for name,want in f['evidence'].items():check(E/name,want)
files=read(E/'source43-files.json');assert len(files)==43
for name,want in files.items():check(W/name,want)
commands=read(E/'command-index.json')['recorded_commands']
for c in commands:
 check(E/c['invocation']);check(E/c['stdout']['path'],c['stdout']);check(E/c['stderr']['path'],c['stderr']);ep=E/c['id']/'exit.json';check(ep);e=read(ep);actual=e.get('native_exit',e.get('exit_code',e.get('exit')))
 assert actual==c['exit'],(c['id'],e)
ledger=read(E/'diagnostic-ledger.json')
for c in ledger['old_failures_or_missing_exit']:
 for name,v in c.items():
  if isinstance(v,dict)and 'sha256'in v:check(OLD/c['id']/name,v)
 check(OLD/c['id']/'exit.json')
for name in f['buildinfo']:
 check(E/name);v=(E/name).read_text(encoding='utf8');assert 'vcs.modified=false'in v and f['source_commit']in v
for name in f['builds'].values():
 e=read(E/name);assert e.get('native_exit',e.get('exit_code',e.get('exit')))==0
git=['git','-c','maintenance.auto=false','-c','gc.auto=0']
full=subprocess.check_output(git+['diff','--binary',f['main_base'],f['source_commit']],cwd=W)
fix=subprocess.check_output(git+['diff','--binary',f['base_b_commit'],f['source_commit'],'--','internal/host/roots_windows.go','internal/host/roots_windows_test.go'],cwd=W)
assert full==(E/'full43-from-Main4f.patch').read_bytes();assert fix==(E/'fix2-from-baseB.patch').read_bytes()
matrix=read(E/'claim-test-matrix.json');counts=[]
for c in matrix['results']:
 text=(E/c['receipt']/'stdout.raw').read_text(encoding='utf8');events={'pass':[],'fail':[],'skip':[]}
 for line in text.splitlines():
  try:v=json.loads(line)
  except json.JSONDecodeError:continue
  if isinstance(v,dict)and v.get('Test')and v.get('Action')in events:events[v['Action']].append(v['Test'])
 if not any(events.values()):
  for status,test in re.findall(r'--- (PASS|FAIL|SKIP): ([^ ]+)',text):events[status.lower()].append(test)
 for status in events:assert events[status]==c[status+'_events'],(c['receipt'],status,len(events[status]),len(c[status+'_events']))
 counts.append({'receipt':c['receipt'],'exit':c['native_exit'],**{k:len(v)for k,v in events.items()}})
out={'status':'FROZEN_AUTHOR_SOURCE_AND_COMMAND_EVIDENCE_VERIFIED_NOT_INDEPENDENT_ACCEPTANCE','author_final':check(E/'FINAL-manifest.json'),'source_commit':f['source_commit'],'source_tree':f['source_tree'],'verified_count':len(verified),'verified_refs':verified,'source_count':len(files),'commands_count':len(commands),'patch_bytes_match_exact_git':True,'test_counts':counts,'ledger_counts':{'old_native_failures':len(ledger['old_failures_or_missing_exit']),'new_native_failures':len(ledger['new_recorded_failures']),'new_launcher_failures':len(ledger['launcher_binding_failures_without_subprocess_receipt'])},'supplement_status':'AWAITING_049_050_APPEND_ONLY_SEAL','formal_increment':0,'unresolved':[]}
with (N/'Source43-author-root-verification.json').open('x',encoding='utf8')as h:json.dump(out,h,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in out.items()if k not in ['verified_refs']},ensure_ascii=False,indent=2))
