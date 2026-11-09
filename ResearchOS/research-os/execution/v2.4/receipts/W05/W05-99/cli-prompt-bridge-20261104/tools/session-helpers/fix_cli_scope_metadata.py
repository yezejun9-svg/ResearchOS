import json,hashlib,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
path=out/'scope.json';raw=path.read_bytes();scope=json.loads(raw)
bad='xecution/invocations/07aadf8d-ec63-48aa-b495-24bb49fe2cea/stdout.txt'
good='e'+bad
assert bad in scope['protected_before'] and good not in scope['protected_before']
assert scope['protected_before'][bad]=='ABSENT_BEFORE' and not (root/good).exists()
older=json.loads((root/'execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104/scope-and-baseline.json').read_bytes())
assert older['protected_tracked_before'][good]=='ABSENT_BEFORE'
(out/'scope.v1.before-metadata-fix.json').write_bytes(raw)
oldstatus=(out/'git-tracked.before.txt').read_bytes();(out/'git-tracked.before.v1.txt').write_bytes(oldstatus)
status=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks','status','--porcelain=v1','-uno'],cwd=root)
assert status.decode().splitlines()[0]==' D '+good
scope['protected_before'][good]=scope['protected_before'].pop(bad)
scope['metadata_correction']={'at':datetime.now(timezone.utc).isoformat(),'old_scope_sha256':hashlib.sha256(raw).hexdigest(),'cause':'git helper strip() removed first porcelain leading whitespace; first path was off by one. Actual deleted file is unchanged and was protected in CP581 integration evidence.','corrected_key':good,'no_source_or_deleted_file_changes':True}
assert path.read_bytes()==raw
temp=path.with_name(path.name+'.new');temp.write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(temp,path)
(out/'git-tracked.before.txt').write_bytes(status)
(out/'metadata-correction.json').write_text(json.dumps(scope['metadata_correction'],indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'CONTROL_METADATA_CORRECTED','protected_deleted_file_still_absent':True,'source_changes':0}))
