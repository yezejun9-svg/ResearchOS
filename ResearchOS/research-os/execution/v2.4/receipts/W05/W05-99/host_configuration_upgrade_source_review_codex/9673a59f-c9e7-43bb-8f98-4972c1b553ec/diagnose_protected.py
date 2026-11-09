from pathlib import Path
import json,subprocess,hashlib
R=Path('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/codex-w0599-host-configuration-upgrade';O=R/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_source_review_codex/9673a59f-c9e7-43bb-8f98-4972c1b553ec';p=W/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/handoff-5375496dd2b24206b5db17fc9bc358c3/protected_sources.json';rows=[]
for r in json.loads(p.read_text(encoding='utf-8-sig')):
 b=(W/r['path']).read_bytes();g=subprocess.check_output(['git','--no-replace-objects','-C',str(W),'show',r['git_commit']+':'+r['path']]);h=hashlib.sha256(b).hexdigest();rows.append({'path':r['path'],'expected':r['sha256'],'actual':h,'git_bytes_same':b==g,'same':h==r['sha256']})
(O/'protected_drift_diagnostic.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps([r for r in rows if not r['same'] or not r['git_bytes_same']]))
