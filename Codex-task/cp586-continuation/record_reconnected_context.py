import json,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
base=Path(__file__).resolve().parent
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104'
info={'at':datetime.now(timezone.utc).isoformat(),'status':'NATIVE_RECONNECTED_AND_VERIFIED','native_chunks':['fe959c','17ad56'],'head':'556cdc353f47167e5609f23291bf2746e3c8896f','project_id':'aede0678-7308-43dc-b9f2-cfe3d90cfdfb','D_checkpoint':587,'D_failure_records':2386,'D_product_source_writes':0,'D_business_database_writes':0,'D_metadata_receipt_and_checkpoint_written':True,'old_default_loopback_failure_preserved':True,'higher_profile_loopback_ref':str(base/'loopback-capability-elevated.json'),'higher_profile_loopback':'SELF_OWNED_LOOPBACK_AVAILABLE','actual_model_server_starts':0,'inference_calls':0,'formal_increment':0}
(base/'RECONNECTED.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
for name in ['RECONNECTED.json','loopback-capability-elevated.json','check_loopback_capability_elevated.py']:
    source=base/name;target=out/'sandbox-progress'/name
    assert not target.exists();target.write_bytes(source.read_bytes());assert target.read_bytes()==source.read_bytes()
argv=['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe','-X','utf8','D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/tools/task_packet.py','next','--state',str(root/'execution/v2.4/step_state.json')]
run=subprocess.run(argv,capture_output=True,encoding='utf-8',timeout=60)
(out/'task-packet-after-reconnect.stdout.json').write_text(run.stdout,encoding='utf-8');(out/'task-packet-after-reconnect.stderr.txt').write_text(run.stderr,encoding='utf-8')
assert run.returncode==0
doc=json.loads(run.stdout)
print(json.dumps({'checkpoint':587,'selector_exit':run.returncode,'state_source':doc.get('state_source'),'next_step':doc.get('step',{}).get('id'),'product_acceptance':doc.get('product_acceptance')}))
