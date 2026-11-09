import json, os, subprocess, hashlib
from datetime import datetime, timezone
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104'
target=out/'main-dispatch-verification.json'
assert not target.exists(), 'Inspect previous execution; do not replay blindly'
assert json.loads((root/'execution/v2.4/commands.json').read_bytes())['revision']==41
python=Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe')
env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','PROGRAMFILES','PROGRAMFILES(X86)','PATH'}}
rows=[]
for selector,value in [('check-id','W05-G02'),('check-id','W05-H08'),('check-id','W05-P01'),('check-id','W05-U02'),('case-id','A04')]:
    argv=[str(python),'-X','utf8',str(root/'execution/command_dispatcher/dispatch.py'),'test.runtime','--spec','v2.4','--task-id','W05','--'+selector,value]
    run=subprocess.run(argv,cwd=root,env=env,capture_output=True,encoding='utf-8',timeout=950)
    brief=json.loads(run.stdout)
    receipt_path=Path(brief['receipt']); receipt=json.loads(receipt_path.read_bytes())
    child=json.loads((root/receipt['stdout']['path']).read_bytes())
    valid=(run.returncode==1 and receipt['status']=='COMMAND_FAILED' and receipt['child_exit_code']==1 and receipt['assertion_ids']==[] and child['status']=='BLOCKED' and child['reason_code']=='IMPLEMENTATION_GAP' and child['measurement_mode']=='NOT_RUN' and child['passed_count']==0 and not child['native_executed'] and not child['provider_executed'])
    if value=='A04': valid=valid and child['expected_assertion_ids']==[f'A04-{i:02d}' for i in range(1,7)]
    rows.append({'selector':value,'argv':argv,'dispatcher_exit':run.returncode,'receipt':str(receipt_path.relative_to(root)),'receipt_sha256':hashlib.sha256(receipt_path.read_bytes()).hexdigest(),'status':receipt['status'],'child_exit':receipt['child_exit_code'],'raw_status':child['status'],'raw_reason':child['reason_code'],'expected_assertion_ids':child['expected_assertion_ids'],'interpretation_matches':valid})
    target.write_text(json.dumps({'scope':'CONSTRUCTION_ROUTING_ONLY','status':'RUNNING','rows':rows,'formal_increment':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert valid, value
    print(json.dumps({'selector':value,'routing_checked':valid,'status':receipt['status']}),flush=True)
result={'scope':'CONSTRUCTION_ROUTING_ONLY','status':'PASS_DEVELOPMENT_NEGATIVE_CHECKS','at':datetime.now(timezone.utc).isoformat(),'rows':rows,'formal_increment':0,'native_calls':0,'provider_calls':0,'interpretation':'All five current LIVE selectors enter the intended frozen v2.4 preflight and fail closed; no LIVE assertion was executed or accepted.'}
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
