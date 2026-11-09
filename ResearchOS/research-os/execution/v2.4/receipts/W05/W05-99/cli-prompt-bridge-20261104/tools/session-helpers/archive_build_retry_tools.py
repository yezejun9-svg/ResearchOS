import json,hashlib
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
cwd=Path(__file__).resolve().parent
mapping={'compatibility-development-build-r2.py':out/'tools','prepare_compatibility_build_retry.py':out/'tools','build_cli_development.py':out/'tools','build_cli_development_r2.py':out/'tools','archive_build_retry_tools.py':out/'tools','start_builder_stdout_fix.py':out/'builder-stdout-fix/tools','integrate_builder_stdout_fix.py':out/'builder-stdout-fix/tools'}
rows=[]
for name,directory in mapping.items():
    original=cwd/name;target=directory/name;data=original.read_bytes()
    if target.exists():assert target.read_bytes()==data
    else:target.write_bytes(data)
    rows.append({'path':str(target.relative_to(root)),'sha256':hashlib.sha256(data).hexdigest()})
(out/'retry-tools-manifest.json').write_text(json.dumps({'status':'ARCHIVED_VERIFIED','files':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'archived':len(rows)}))
