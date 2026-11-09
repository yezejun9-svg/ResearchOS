from pathlib import Path
from datetime import datetime, timezone
import hashlib,json

main=Path(r'D:\作品集\ResearchOS\research-os')
root=main/'.local/worktrees/workbench-experience-20261104'
receipt=main/'execution/v2.4/receipts/W13/W13-03/workbench-experience-20261104/desktop-build'
def ref(path):
    path=Path(path)
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
summary={'schema':'researchos.desktop-development-build-attempt-summary.v1','at':datetime.now(timezone.utc).isoformat(),'failure_origin':'desktop-build/sparse-module-closure','attempt':1,'status':'FAILED_NATIVE_EXIT_1_NO_RETRY_IN_PLACE','output':str(root/'.local/development-ui-20261104'),'output_exists':(root/'.local/development-ui-20261104').exists(),'source_head':'3cd8e4ceba16ba6c4890fe2fd5a35324682b44f5','actual_exit':1,'failed_command':'core-go-list','reason':'Sparse candidate omitted local evaluation/holdout/jev, evaluation/evolution, evaluation/skills, ops/experiment_sandbox and ops/supervisor packages. Not a missing external module; no download requested.','raw_refs':[ref(receipt/'controller/complete-development-build/result.json'),ref(receipt/'controller/complete-development-build/stderr.raw'),ref(receipt/'build-01/failed.json'),ref(receipt/'build-01/commands/core-go-list/stderr.raw'),ref(receipt/'build-01/mu-vendor-5083.before.json')],'bundle_manifest':None,'dryrun':'NOT_RUN','source_seven_unchanged':True,'formal_increment':0,'first_failure_and_all_scratch_retained':True,'same_failure_origin_attempts_not_reset':True,'limits':['No Core/product GUI/provider or installation action took place.','Only one new output attempt2 is separately authorized; another same-origin failure stops the branch.']}
with (receipt/'summary.build-01.json').open('x',encoding='utf-8',newline='\n') as f: json.dump(summary,f,ensure_ascii=False,indent=2);f.write('\n')

p=Path(r'C:\Users\yqyyds\Documents\Codex\2026-11-04\task\workbench-desktop-build-controller.py')
s=p.read_text(encoding='utf-8')
s=s.replace("CONTROL = RECEIPT / 'controller'","CONTROL = RECEIPT / 'controller-02'")
s=s.replace("BUILD_RECEIPT = RECEIPT / 'build-01'","BUILD_RECEIPT = RECEIPT / 'build-02'")
s=s.replace("ROOT / '.local/development-ui-20261104'","ROOT / '.local/development-ui-20261104-r2'")
s=s.replace("ROOT / '.local/development-ui-20261104-dryrun-state'","ROOT / '.local/development-ui-20261104-r2-dryrun-state'")
s=s.replace("'expected_source_head':HEAD,", "'failure_origin':'desktop-build/sparse-module-closure','attempt_index':2,'prior_attempt_retained':True,'counters_reset':False,'expected_source_head':HEAD,")
s=s.replace("'docs/installation','tests/contracts'])", "'docs/installation','tests/contracts','evaluation/development/jev-v2','evaluation/evolution','evaluation/holdout/jev','evaluation/skills','ops/experiment_sandbox','ops/supervisor'])")
new=p.with_name('workbench-desktop-build-controller-r2.py')
new.write_text(s,encoding='utf-8',newline='\n')
print('Attempt1 sealed. Attempt2 controller prepared with statically enumerated same-module source closure; no old output or scratch removed.')
