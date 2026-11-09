import json,hashlib
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W05/W05-99';B=Path(__file__).parent
out={}
for name in ['owned_core_stop_effect_state_revision05_independent_review_codex','online_backup_fixture_independent_review_codex']:
 d=E/name/'20261015-current-chat';m=json.loads((d/'FINAL-manifest.json').read_text(encoding='utf-8-sig'));ci=json.loads((d/'command-index.json').read_text(encoding='utf-8-sig'))
 if isinstance(ci,list):rows=ci
 else:
  arrays=[x for x in ci.values()if isinstance(x,list)];rows=max(arrays,key=len)if arrays else[]
 v={'manifest_excluded':m.get('excluded',m.get('excluded_terminal_envelope')),'index_type':type(ci).__name__,'record_count':len(rows),'first':rows[:1],'last':rows[-1:],'native_exit_fields':{}}
 for row in rows:
  for k in ['native_exit','nativeExit','exit_code','exit']:
   if k in row and not isinstance(row[k],(dict,list)):
    key=str(row[k]);v['native_exit_fields'][key]=v['native_exit_fields'].get(key,0)+1;break
 out[name]=v
p=B/'independent-review-capture-shapes-cp522.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(out,ensure_ascii=False))
