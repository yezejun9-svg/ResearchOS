from pathlib import Path
import json,hashlib
R=Path(r'D:\\作品集\\ResearchOS\\research-os');B=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/host_stored_finalpath_diagnosis_codex/20261015-current-chat'
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
m=json.loads((E/'FINAL-manifest.json').read_bytes())
print('RETAINED_NAMES',[x['path']for x in m['files']])
for x in m['files']:
 if any(k in x['path'].lower()for k in ['ledger','command-index']):print('DETAIL',x['path'],(E/x['path']).read_text(encoding='utf-8-sig'))
refs=[ref(E/n)for n in ['06-freeze.raw.txt','06-freeze.exit.txt']]
print('FREEZE',[(x,(Path(x['path']).read_text(encoding='utf-8-sig')))for x in refs])
p=B/'host-finalpath-root-freeze-closure.json'
with p.open('x',encoding='utf8')as f:json.dump({'manifest':ref(E/'FINAL-manifest.json'),'excluded_final_capture_now_closed':refs,'native_exit':int((E/'06-freeze.exit.txt').read_text()),'verified_own_manifest_refs':40},f,ensure_ascii=False,indent=2);f.write(chr(10))
assert json.loads(p.read_bytes())['native_exit']==0
print('OUTPUT',ref(p))
