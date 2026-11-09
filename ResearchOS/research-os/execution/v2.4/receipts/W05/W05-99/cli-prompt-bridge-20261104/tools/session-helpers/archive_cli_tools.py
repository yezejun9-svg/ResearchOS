import hashlib,json
from pathlib import Path
cwd=Path(__file__).resolve().parent
assert cwd==Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task')
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
names=['fix_cli_scope_metadata.py','materialize_cli_prompt_closure.py','materialize_cli_prompt_closure_r2.py','prepare_compatibility_build_controller.py','compatibility-development-build.py','integrate_cli_prompt_bridge.py','checkpoint_cli_cp583.py','archive_cli_tools.py']
rows=[]
for name in names:
    source=cwd/name;destination=out/'tools'/name
    raw=source.read_bytes()
    if destination.exists():assert destination.read_bytes()==raw
    else:destination.write_bytes(raw)
    rows.append({'file':name,'sha256':hashlib.sha256(raw).hexdigest()})
(out/'tools-preintegration-manifest.json').write_text(json.dumps({'status':'ARCHIVED_VERIFIED_NO_TEMP_DELETION_YET','files':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'tools_archived':len(rows)}))
