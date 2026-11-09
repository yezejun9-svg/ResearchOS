import hashlib,json,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=ROOT/'execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(path,value):
    tmp=path.with_name(path.name+'.new');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,path)
cpfile=ROOT/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw)
assert cp['revision']==579 and len(cp['failure_counters'])==2325
head=subprocess.check_output(['git','--no-optional-locks','-c','gc.auto=0','-c','maintenance.auto=false','rev-parse','HEAD'],cwd=ROOT).decode().strip()
assert head=='3cd8e4ceba16ba6c4890fe2fd5a35324682b44f5'
OUT.mkdir(parents=True,exist_ok=False)
for name in ['routing-author','host-author','reviews']: (OUT/name).mkdir()
(OUT/'checkpoint.before.json').write_bytes(raw)
(OUT/'commands.before.json').write_bytes((ROOT/'execution/v2.4/commands.json').read_bytes())
(OUT/'step_state.before.json').write_bytes((ROOT/'execution/v2.4/step_state.json').read_bytes())
status=subprocess.check_output(['git','--no-optional-locks','-c','gc.auto=0','-c','maintenance.auto=false','status','--porcelain=v1','-uno'],cwd=ROOT)
(OUT/'git-tracked.before.txt').write_bytes(status)
protected={}
for line in status.decode().splitlines():
    path=line[3:];p=ROOT/path
    protected[path]=sha(p.read_bytes()) if p.is_file() else 'ABSENT_BEFORE'
counter_sha=sha(json.dumps(cp['failure_counters'],sort_keys=True,ensure_ascii=False).encode())
now=datetime.now(timezone.utc).isoformat()
scope={'schema':'researchos.cp579-implementation.v1','at':now,'base_head':head,'project_id':'aede0678-7308-43dc-b9f2-cfe3d90cfdfb',
 'user_direction':'Implement exact W05 routing and compatible shared host discovery, preserving LIVE gates, old data and counters.',
 'routing_owner':'codex:/root/workbench_builder','routing_worktree':str(ROOT/'.local/worktrees/w05-runtime-routing-20261104'),
 'host_owner':'codex:/root/resume_audit','host_worktree':str(ROOT/'.local/worktrees/shared-host-discovery-20261104'),
 'root_integrator':'codex:/root','max_construction_tasks':2,'registry_owner':'codex:/root','registry_revision_before':40,
 'registry_sha256_before':sha((OUT/'commands.before.json').read_bytes()),'protected_tracked_before':protected,
 'step_state_sha256_before':sha((OUT/'step_state.before.json').read_bytes()),'failure_record_count_before':2325,'failure_prefix_sha256':counter_sha,
 'excluded_actions':['consumed CP575 native scope','policy-rejected old Codex LIVE probe','original-data operations','paid provider calls','changing frozen standards','external PASS imports'],
 'formal_increment':0,'mode':'SOURCE_IMPLEMENTATION_AND_DEVELOPMENT_VERIFICATION'}
put(OUT/'scope-and-baseline.json',scope)
put(OUT/'reconnection.json',{'at':now,'checkpoint_before':579,'main':head,'both_worktrees_clean':True,'receipt_absent_before':True,'startup_script_absent_before':True,
 'uncertain_previous_write_reconciled':'CP580 and receipt did not land; now initializing once under the same authorization.',
 'environment_disconnect':'Prior exec-server transport disconnected/unavailable; no source implementation or product run occurred.'})
for origin,chunk,code,detail in [
 ('readonly-glob','5bfee2',0,'Internal rg used unexpanded runtime* path; batched outer exit0; subsequent reads completed.'),
 ('reconnection-absent-startup-script','7a8068',1,'Read of the uncertain startup script found it absent. TestPath then confirmed both script and receipt absent; expected pre-execution failure reconciliation, not a product failure.')]:
 cp['failure_counters'].append({'at':now,'origin_key':'20261104|cp579-implementation|'+origin,'attempts':1,'exit':code,'tool_chunk':chunk,'status':'READONLY_TOOL_DIAGNOSTIC','detail':detail,'counter_reset':False})
resume={'schema':'researchos.cp580-resume.v1','checkpoint_revision':580,'status':'IMPLEMENTING_ROUTING_AND_HOST_COMPAT','base_head':head,
 'scope_ref':'scope-and-baseline.json','reconnection_ref':'reconnection.json','current_card':'W05-99','active_owners':[scope['routing_owner'],scope['host_owner']],
 'formal_accepted':0,'formal_required':42,'failure_records':len(cp['failure_counters']),'counter_reset':False,
 'next':'Freeze both candidates, targeted development tests and independent review; root alone patches registry against revision40. No old native or paid-model retry.'}
put(OUT/'RESUME.json',resume)
cp['expected_previous_revision']=579;cp['revision']=580;cp['updated_at']=now
cp['product_direction_review']['implementation_authorized_at']=now;cp['product_direction_review']['task_card_execution_paused']=False
cp['current_implementation']={'status':resume['status'],'at':now,'resume_ref':(OUT/'RESUME.json').relative_to(ROOT).as_posix(),'formal_increment':0}
cp['next_command']=resume['next']+' Read execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104/RESUME.json first.'
assert cpfile.read_bytes()==raw
put(cpfile,cp)
handoff=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';tmp=handoff.with_name(handoff.name+'.new')
tmp.write_bytes(b'# Current implementation CP580\n\nRead execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104/RESUME.json. Reconnection confirmed the previous CP580 write did not land; initialized once. Two isolated source owners active, LIVE gates unchanged, CP575 consumed scope prohibited. Full goal unfinished/formal0 of42.\n\n'+handoff.read_bytes());os.replace(tmp,handoff)
print(json.dumps({'checkpoint':580,'receipt':str(OUT),'failure_records':len(cp['failure_counters'])}))
