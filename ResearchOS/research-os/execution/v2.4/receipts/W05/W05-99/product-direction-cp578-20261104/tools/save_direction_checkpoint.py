import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=ROOT/'execution/v2.4/receipts/W05/W05-99/product-direction-cp578-20261104'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def put(path,value):
    temporary=path.with_name(path.name+'.direction-new')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temporary,path)

def main():
    cp_path=ROOT/'execution/v2.4/checkpoint.json'
    before=cp_path.read_bytes(); cp=json.loads(before)
    assert cp['revision']==578, 'Reconcile concurrent checkpoint before writing'
    review=OUT/'independent-design-review.json'
    assert review.exists(), 'Wait for independent proposal review'
    assert sha(review.read_bytes())=='e5cb8f684a5895fca1ec9c6696ac7198e9a9c9d19126181a509a481a5fba450b'
    assert sha((OUT/'PRODUCT_DIRECTION.md').read_bytes())=='084004d6a39b719f0d318b54d61f13b07e9df9af139f257efb0c40f81929f3a7'
    head=subprocess.check_output(['git','--no-optional-locks','-c','gc.auto=0','-c','maintenance.auto=false','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    assert head=='3cd8e4ceba16ba6c4890fe2fd5a35324682b44f5'
    state=(ROOT/'execution/v2.4/step_state.json').read_bytes()
    previous=json.loads((ROOT/'execution/v2.4/receipts/W13/W13-03/workbench-experience-20261104/scope-and-baseline.json').read_bytes())
    assert sha(state)==previous['step_state_sha256_before']
    assert len(cp['failure_counters'])==2319
    (OUT/'checkpoint.before.json').write_bytes(before)
    handoff=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md'
    (OUT/'handoff.before.md').write_bytes(handoff.read_bytes())
    paths=['apps/cli/main.go','apps/cli/cli_contract.go','apps/cli/cli_run_contract.go','apps/cli/coding_task.go',
      'apps/desktop/main/main.js','apps/desktop/main/lib/desktop-management.js','internal/domain/client_protocol_goal.go',
      'internal/domain/acceptance_goal.go','internal/domain/planning_brief.go','internal/domain/runtime_model_verification.go',
      'internal/host/runtime_tools_windows.go','internal/host/runtime_check_windows.go','internal/domain/runtime_coordinator_windows.go',
      'internal/api/v2.go','apps/web/src/components/activity-rail.jsx','adapters/runtime/mu/worker.mjs']
    sources=[{'path':name,'sha256':sha((ROOT/name).read_bytes())} for name in paths]
    plan=Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/contracts/execution.plan.json')
    native_root=ROOT/'execution/v2.4/receipts/W05/W05-99/product_host_native_20261028/native-init-diagnosis-02/environment-probe/execution-cp575-C-branch01'
    actual=json.loads((native_root/'RESULT.json').read_bytes())
    terminal=json.loads((native_root/'CONTROLLER-TERMINAL.json').read_bytes())
    assert actual['helper_calls']==2 and terminal['outer_exit_code']==0
    consumed={'scope_cp':575,'case_order':['C','D'],'helper_calls':2,'scope_call_cap':2,
      'status':'EXECUTED_SCOPE_CONSUMED_NO_USABLE_DIALOG','execution_at':actual['at'],
      'result_ref':(native_root/'RESULT.json').relative_to(ROOT).as_posix(),'result_sha256':sha((native_root/'RESULT.json').read_bytes()),
      'terminal_sha256':sha((native_root/'CONTROLLER-TERMINAL.json').read_bytes()),'do_not_repeat_old_scope':True,
      'failure_count_reconciliation':'No separate CD origin established; preserve original failure history and record consumed scope without inventing duplicate native failures.'}
    now=datetime.now(timezone.utc).isoformat()
    diagnostics=[('root','f4a0a9',1),('builder','a75d50',1),('builder','dde3f9',1),('builder','d09a81',1),('builder','f26bf5',0),('builder','0f9c61',0)]
    for owner,chunk,exit_code in diagnostics:
        cp['failure_counters'].append({'at':now,'origin_key':'20261104|product-direction-read|'+chunk,'attempts':1,
          'exit':exit_code,'tool_chunk':chunk,'owner':owner,'status':'READONLY_PATH_OR_GLOB_DIAGNOSTIC',
          'detail':'Read-only search used a PowerShell-unexpanded wildcard path or a guessed absent source name. Directory-plus-glob/actual-file reads completed the review. No product process, native run or source mutation.', 'counter_reset':False})
    evidence={'schema':'researchos.product-direction-review.v1','at':now,'head':head,'checkpoint_base':578,
      'input_plan_sha256':sha(plan.read_bytes()),'step_state_sha256':sha(state),'source_manifest':sources,
      'proposal_sha256':sha((OUT/'PRODUCT_DIRECTION.md').read_bytes()),'independent_review_sha256':sha(review.read_bytes()),
      'mode':'READ_ONLY_SOURCE_REVIEW_AND_PROPOSAL','proposal_applied':False,'product_runs':0,'model_calls':0,
      'legacy_scope_reconciliation':consumed,'formal_accepted':0,'formal_required':42,'parent_tasks_required':22,
      'previous_failure_records':2319,'new_read_diagnostics':6,'current_failure_records':len(cp['failure_counters'])}
    put(OUT/'context-and-findings.json',evidence)
    resume={'schema':'researchos.product-direction-resume.v1','checkpoint_revision':579,'at':now,'status':'PRODUCT_DIRECTION_REVIEW_READY',
      'head':head,'proposal_ref':'PRODUCT_DIRECTION.md','context_ref':'context-and-findings.json','review_ref':'independent-design-review.json',
      'task_card_execution_paused':True,'reason':'Latest user instruction asks independent product construction analysis before major architecture changes.',
      'formal_pointer':'W05-99','next_product_slice':'Unify host discovery/attachment and public CLI semantics, then close one real Go coding task and independent LIVE Goal acceptance.',
      'architecture_changes_applied':False,'source_changes_this_round':False,'original_ui_and_development_bundle_preserved':True,
      'formal_accepted':0,'formal_required':42,'failure_records':len(cp['failure_counters']),'counter_reset':False,
      'legacy_cp575_native_scope_consumed':True,'next':'Review proposal basis/impact; do not execute old CP575 command or blindly resume task cards.'}
    put(OUT/'RESUME.json',resume)
    cp['revision']=579;cp['expected_previous_revision']=578;cp['updated_at']=now
    cp['superseded_cp578_control_fields']={k:json.loads(before).get(k) for k in ['next_command','updated_at','next_step_id']}
    cp['next_command']='Read execution/v2.4/receipts/W05/W05-99/product-direction-cp578-20261104/PRODUCT_DIRECTION.md and RESUME.json. Latest user directs product architecture review first; task-card execution paused. CP575 native C/D scope already executed and exhausted; do not rerun.'
    cp['product_direction_review']={'status':'PROPOSED_NOT_APPLIED','at':now,'resume_ref':(OUT/'RESUME.json').relative_to(ROOT).as_posix(),'source_head':head,'task_card_execution_paused':True}
    cp['consumed_cp575_native_scope']=consumed
    assert cp_path.read_bytes()==before
    assert (ROOT/'execution/v2.4/step_state.json').read_bytes()==state
    put(cp_path,cp)
    prefix='# Current product-direction review CP579\n\nRead execution/v2.4/receipts/W05/W05-99/product-direction-cp578-20261104/RESUME.json and PRODUCT_DIRECTION.md first. Latest user asks independent product construction, not mechanical card execution. Proposal only; source/UI/build preserved at 3cd8e4ce, no architecture change applied. Old CP575 C/D was actually executed and its two-call scope is exhausted; the old NOT STARTED next_command is stale and must not be run. Full product goal unfinished, formal0/42.\n\n'
    temporary=handoff.with_name(handoff.name+'.direction-new');temporary.write_bytes(prefix.encode()+handoff.read_bytes());os.replace(temporary,handoff)
    print(json.dumps({'checkpoint':579,'status':resume['status'],'failure_records':len(cp['failure_counters']),'source_head':head,'architecture_applied':False}))

if __name__=='__main__':main()
