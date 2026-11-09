from pathlib import Path
import hashlib,json
R=Path(r'D:\作品集\ResearchOS\research-os');E=Path(__file__).parent
for name in ['tests/ui/browser_smoke.py','tests/ui/w1303/preview_run.py']:
 p=R/name
 if p.is_file():
  lines=p.read_text(encoding='utf-8-sig').splitlines();print('UI_FIXTURE',name,'LINES',len(lines))
  for i,line in enumerate(lines):
   if i<130 or any(x in line for x in ['launch','token','server','RESEARCHOS','browser.new','context.route','fixture','baseURL','base_url','create_project']):
    print(str(i+1)+': '+line)
p=R/'execution/v2.4/receipts/W05/W05-99/original_backup_process_binding_codex/20261015-current-chat';refs=[]
for q in sorted(p.iterdir()):
 if q.is_file():
  b=q.read_bytes();refs.append({'path':str(q),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
for name in ['group1.exit.json','group2.exit.json','group3.exit.json','group4.exit.json','group4-results.json']:
 q=p/name
 if q.is_file():print('HISTORICAL_PARTIAL',name,q.read_text(encoding='utf-8-sig'))
out=E/'historical-process-binding-partial-preservation.json'
with out.open('x',encoding='utf8')as f:json.dump({'status':'PARTIAL_20261015_EVIDENCE_PRESERVED_NOT_CURRENT_VERIFICATION','files':refs,'current_process_claim':False,'actual_backup_gate_accepted':False,'original_mutation':False,'formal_increment':0},f,ensure_ascii=False,indent=2);f.write(chr(10))
print('PRESERVED_FILES',len(refs))
