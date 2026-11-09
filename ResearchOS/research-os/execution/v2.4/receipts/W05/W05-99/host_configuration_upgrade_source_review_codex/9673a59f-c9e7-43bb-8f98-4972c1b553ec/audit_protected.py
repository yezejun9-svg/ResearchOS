from pathlib import Path
import json,hashlib,subprocess
R=Path('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/codex-w0599-host-configuration-upgrade';O=R/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_source_review_codex/9673a59f-c9e7-43bb-8f98-4972c1b553ec';N=W/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
protect=json.loads((N/'handoff-5375496dd2b24206b5db17fc9bc358c3/protected_sources.json').read_text(encoding='utf-8-sig'));result=[]
for row in protect:
 p=row['path'];b=(W/p).read_bytes();g=subprocess.check_output(['git','--no-replace-objects','-C',str(W),'show',row['git_commit']+':'+p]);assert b==g and sha(b)==row['sha256'];result.append({'path':p,'sha256':sha(b),'git':row['git_commit'],'unchanged':True})
checks=[]
for name in ['closure-f7166f2b1e974cbdba4e2855c45966ab','closure-e24d5ab7b9e6444abc8fc2e087aca6f5']:
 d=N/name;a=json.loads((d/'source_before.json').read_text(encoding='utf-8-sig'));z=json.loads((d/'source_after.json').read_text(encoding='utf-8-sig'));assert a==z;inv=json.loads((d/'test.invocation.json').read_text(encoding='utf-8-sig'));assert inv['exit']==0
 checks.append({'namespace':str(d),'inputs':len(a),'before_after_equal':True,'before_sha256':sha((d/'source_before.json').read_bytes()),'invocation':inv,'invocation_sha256':sha((d/'test.invocation.json').read_bytes())})
save('protected_and_target_build_audit.json',{'protected':result,'builds':checks})
print(json.dumps({'protected':len(result),'builds':len(checks)}))
