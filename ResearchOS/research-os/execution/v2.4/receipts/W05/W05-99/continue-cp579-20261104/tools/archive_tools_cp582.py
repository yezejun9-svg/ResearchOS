import json,hashlib,os
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os')
old=root/'execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104'
new=root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
cwd=Path(__file__).resolve().parent
assert cwd==Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task')
cp=json.loads((root/'execution/v2.4/checkpoint.json').read_bytes());assert cp['revision']==582
handoff=root/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes()
saved=new/'handoff.cp581.before-cli-bridge.md'
assert not saved.exists();saved.write_bytes(before)
prefix=b'# Current resume CP582\n\nRead execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/RESUME.json and scope.json. W05/host compatibility integrated at fc2b1a50662580b1a0fca92559ca26be6e959f01, independent review and five fail-closed dispatch probes complete. One isolated CLI prompt-bridge constructor active; no model/native or acceptance authorization is added. Previous evidence remains under continue-cp579-20261104. Formal0/42; not all22parents.\n\n'
temp=handoff.with_name(handoff.name+'.cp582.new');temp.write_bytes(prefix+before);os.replace(temp,handoff)
names=['start_cp579_implementation.py','inspect_cp580.py','inspect_status_cp580.py','inspect_receipts_cp580.py','prepare_registry_cp580.py','integrate_cp580.py','verify_dispatch_cp580.py','select_after_integration.py','checkpoint_cp581.py','archive_tools_cp582.py']
rows=[]
for name in names+['start_cli_prompt_bridge.py']:
    source=cwd/name;assert source.parent==cwd and source.is_file()
    destination=(new if name=='start_cli_prompt_bridge.py' else old)/'tools'/name
    destination.parent.mkdir(exist_ok=True)
    data=source.read_bytes()
    if destination.exists():assert destination.read_bytes()==data
    else:destination.write_bytes(data)
    assert source.read_bytes()==destination.read_bytes()
    rows.append({'temporary':str(source),'archive':str(destination.relative_to(root)),'sha256':hashlib.sha256(data).hexdigest()})
for row in rows:
    path=Path(row['temporary']);assert path.parent==cwd
    path.unlink()
(old/'tools-archive.json').write_text(json.dumps({'status':'ARCHIVED_VERIFIED_AND_REMOVED_EXACT_TEMP_HELPERS','files':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'archived_helpers':len(rows),'checkpoint':582,'handoff_updated':True}))
