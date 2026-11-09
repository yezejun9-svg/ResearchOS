import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from resume_workbench import REPO, RECEIPT, write_json

spec=Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
argv=[sys.executable,'-B',str(spec/'tools/task_packet.py'),'next','--state',str(REPO/'execution/v2.4/step_state.json')]
result=subprocess.run(argv,cwd=spec,capture_output=True,encoding='utf-8')
parsed=json.loads(result.stdout) if result.stdout.strip().startswith('{') else None
write_json(RECEIPT/'next-card.json',{'at':datetime.now(timezone.utc).isoformat(),'cwd':str(spec),'argv':argv,
    'exit_code':result.returncode,'stdout':parsed or result.stdout,'stderr':result.stderr,'product_acceptance':'NOT_ASSERTED'})
print(json.dumps({'exit':result.returncode,'state_source':parsed.get('state_source') if parsed else None,
    'next_step':parsed.get('step',{}).get('id') if parsed else None,'product_acceptance':'NOT_ASSERTED'}))
sys.exit(result.returncode)
