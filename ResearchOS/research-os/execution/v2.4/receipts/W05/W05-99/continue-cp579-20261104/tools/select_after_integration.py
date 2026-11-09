import json,subprocess
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104'
target=out/'task-packet-after-integration.json'
assert not target.exists()
argv=['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe','-X','utf8','D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/tools/task_packet.py','next','--state',str(root/'execution/v2.4/step_state.json')]
result=subprocess.run(argv,capture_output=True,encoding='utf-8',timeout=60)
target.write_text(result.stdout,encoding='utf-8')
(out/'task-packet-after-integration.stderr.txt').write_text(result.stderr,encoding='utf-8')
doc=json.loads(result.stdout) if result.stdout.strip().startswith('{') else {}
brief={'exit':result.returncode,'state_source':doc.get('state_source'),'product_acceptance':doc.get('product_acceptance'),'next_step':doc.get('step',{}).get('id'),'status':doc.get('status')}
(out/'task-packet-after-integration-result.json').write_text(json.dumps(brief,indent=2)+'\n',encoding='utf-8')
print(json.dumps(brief));assert result.returncode==0
