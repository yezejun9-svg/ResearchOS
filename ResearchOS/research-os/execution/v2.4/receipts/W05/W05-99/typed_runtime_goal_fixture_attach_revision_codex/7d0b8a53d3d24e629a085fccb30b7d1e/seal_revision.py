import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json

Q=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
T=R/'.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1'
A=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2'
P=Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
Q3=R/'execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49'
def pin(path):
 raw=path.read_bytes()
 return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,data):
 path=Q/name
 with path.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 return pin(path)
for name in ['HDF.json','MF.json','static-checks.json']:
 if (Q/name).exists():raise RuntimeError('exclusive seal path already exists: '+name)
if (Q/'candidate-root').exists():raise RuntimeError('candidate Source must remain absent')
source=json.loads((Q/'source-pins.json').read_text(encoding='utf-8'))
inputs=source['input_pins']
for ref in inputs:
 current=pin(Path(ref['path']))
 if current!=ref:raise RuntimeError('source input changed: '+ref['path'])
actual=json.loads((Q/'actual-inspection.json').read_text(encoding='utf-8'))
for ref in actual['input_pins']:
 if pin(Path(ref['path']))!=ref:raise RuntimeError('actual diagnostic input changed: '+ref['path'])

requests=[
 (P/'22_CLIENT_INTERFACE_DETAILS.md',[(114,143)]),
 (P/'contracts/client.protocol.schema.json',[(17,70),(1471,1493),(1683,1715),(4774,4788),(4928,4948)]),
 (T/'internal/domain/client_protocol.go',[(726,772),(906,967),(1036,1081),(1127,1187),(1239,1262)]),
 (T/'internal/domain/v24_sessions.go',[(153,177)]),
 (T/'internal/domain/client_protocol_journal.go',[(46,138),(144,201),(241,351)]),
 (T/'internal/domain/client_protocol_sessions.go',[(153,189)]),
 (T/'internal/domain/runtime_tool_integration_windows_test.go',[(31,43),(148,154)]),
 (T/'internal/domain/runtime_permission_windows_test.go',[(187,193)]),
 (T/'internal/domain/runtime_session_events_windows_test.go',[(477,499)]),
 (Q3/'candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go',[(566,576)])]
excerpts=[]
for path,ranges in requests:
 lines=path.read_text(encoding='utf-8').splitlines()
 excerpts.append({'source_ref':pin(path),'ranges':[{'start_line':start,'end_line':min(end,len(lines)),'exact_lines':[{'line':n,'text':lines[n-1]} for n in range(start,min(end,len(lines))+1)]} for start,end in ranges]})
existing_excerpts=json.loads((Q/'contract-excerpts.json').read_text(encoding='utf-8'))
if existing_excerpts!={'schema':'researchos.readonly-contract-excerpts.v1','authority':'NONE','excerpts':excerpts}:raise RuntimeError('existing contract excerpts differ')
excerpts_ref=pin(Q/'contract-excerpts.json')

expected={
 'runtime_permission_windows_test.go':('7a7b74c268093a0f33304800c6723c5fa7f1689dfdab6a2407b9cb9eab887d15',18858),
 'runtime_tool_integration_windows_test.go':('2cc071afca77ddb68eb171c785395d6ec4bfa58a744c80f54a2aaf9dc4fb9c1b',12211),
 'runtime_session_events_windows_test.go':('f2359edd55bb648b26287d9b672f7d48ab01358965f073a99444bd0ab651f30f',25115),
 'client_protocol_goal_test.go':('4809121015b1345adc4777385236cf692f2e4b53de2ab56cc97b89acffeb30e0',16059)}
preserved=[]
for name,(sha,size) in expected.items():
 base=Q3/'candidate-root/internal/domain'/name
 current=T/'internal/domain'/name
 if pin(base)['sha256']!=sha or pin(base)['bytes']!=size:raise RuntimeError('accepted original fixture pin drift')
 delta=json.loads((Q/'actual-format-delta.json').read_text(encoding='utf-8'))
 observed=next(row for row in delta if row['name']==name)
 if observed['base_ref']!=pin(base) or observed['actual_T6_ref']!=pin(current):raise RuntimeError('diagnosed format input drift')
 equal=base.read_bytes()==current.read_bytes()
 if name!='client_protocol_goal_test.go' and not equal:raise RuntimeError('unexpected original runtime fixture difference')
 if observed['byte_equal']!=equal:raise RuntimeError('format observation mismatch')
 preserved.append({'name':name,'base_ref':pin(base),'actual_T6_ref':pin(current),'byte_equal':equal,'Root_formatted_delta_ref':pin(Q/'actual-format-delta.json'),'candidate_changed':False})
static_ref=write('static-checks.json',{'schema':'researchos.source-blocked-checks.v1','authority':'NONE','candidate_root_absent':True,'candidate_Source_files':0,'production_Source_files_changed':0,'original_fixtures_preserved':preserved,'native_execution':None,'Go_execution':None,'gofmt_execution':None,'SQL_execution':None,'model_provider_requests':0,'private_credential_reads':0,'mechanical_failures':1,'failure_origin_ref':pin(Q/'failure-origin.826.json'),'base_input_drift':0,'native_business_assertion_counts':'Original Q3 pins unchanged; three runtime files T6 byte-equal, Goal only independently recorded Root gofmt whitespace delta. No assertion edit or Go AST execution.'})

report_ref=pin(Q/'report.md')
hdf=write('HDF.json',{
 'schema':'researchos.source-preparation-blocked-handoff.v1',
 'namespace':str(Q),
 'status':'BLOCKED_PRODUCTION_ATTACH_COMPLETION',
 'authority':'NONE',
 'formal_acceptance':False,
 'candidate_root':None,
 'candidate_Source_files':[],
 'production_Source_writes':0,
 'Main_canonical_writes':0,
 'original_Q3_and_T6_immutable':True,
 'Root_actual_native_leaf_failures_preserved':8,
 'Root_actual_parent_runtime_failures_preserved':6,
 'Root_reported_observation':{'pass':61,'fail':6,'skip':0,'authority':'Root observation; independent acceptance pending'},
 'actual_ref':pin(A/'validation.closed.json'),
 'actual_inspection_ref':pin(Q/'actual-inspection.json'),
 'report_ref':report_ref,
 'contract_excerpts_ref':excerpts_ref,
 'source_pins_ref':pin(Q/'source-pins.json'),
 'static_checks_ref':static_ref,
 'available_original_tool_IO_refs':[pin(Q/'tool-io.json'),pin(Q/'tool-io-supplement.json'),pin(Q/'tool-io-recovery.json')],
 'source_input_refs':inputs,
 'mechanical_failures_this_author':1,
 'failure_origin_ref':pin(Q/'failure-origin.826.json'),
 'original_failed_seal_script_ref':pin(Q/'seal.py'),
 'distinct_recovery':'This new seal_revision.py preserves original seal.py/67d70a failure and accounts for separately observed T6 Goal gofmt delta; no original attempt rerun.',
 'prior_failure823':'Root actual native reporter/Python failure evidence remains unchanged; not retried or reset',
 'minimal_product_behavior_required':[
  'Same authenticated owner renews valid lease without changing writer epoch; obey exact current revision CAS and published AttachResult.',
  'Transfer preserves Task/Goal/follow-up queue; no implicit cancellation, resumption or second writer before tools/runtime settle.',
  'Persist original attach intent/identity; atomically transfer owner and new epoch/revision only after required settlement and revalidation.',
  'Publish exact original command CLIENT_HANDOFF where a transfer occurs and return real COMPLETED/AttachResult with matching snapshot and write_owner_acquired.',
  'Replay exact original command without duplicate transfer and expose its real terminal; never invent a completed response in a test helper.',
  'Use same authenticated project/OS principal, same client, exact model/provider/credential/Host binding, real lease and epoch gates.'
 ],
 'deferred_fixture_boundary':{
  'after_independently_reviewed_production_correction_only':True,
  'changed_original_inputs_if_transfer_retained':{'runtime_permission_windows_test.go':'attach return binding and first send current revision/epoch','runtime_tool_integration_windows_test.go':'attach return binding and first send current revision/epoch','runtime_session_events_windows_test.go':'attach return binding and first send current revision/epoch'},
  'all_business_assertions_and_four_original_Source_currently_unchanged':True,
  'event_snapshot_substitute_acceptance':False,
  'strict_JSONL_TLS_exact_configuration_resource_pins_Root_job_requirements':'Unchanged Q3; must remain in any later fixture',
  'formal_test_acceptance':False
 },
 'next_actor':'Root assigns production Source author; independent review and fresh actual precede fixture follow-up',
 'MF_exclusions':['MF.json','seal-tool-io.json'],
 'MF_exclusion_reason':'MF cannot hash itself; post-seal complete author tool IO independently pinned in final delivery without mutating this manifest.'
})
members=[]
for p in sorted(p for p in Q.rglob('*') if p.is_file()):
 if p.name in ['MF.json','seal-tool-io.json']:continue
 members.append({'relative_path':p.relative_to(Q).as_posix(),**pin(p)})
manifest=write('MF.json',{'schema':'researchos.immutable-readonly-diagnostic-manifest.v1','namespace':str(Q),'authority':'NONE','status':'BLOCKED_PRODUCTION_ATTACH_COMPLETION','candidate_Source_files':0,'member_count':len(members),'members':members,'exclusions':['MF.json','seal-tool-io.json'],'handoff_ref':hdf})
for ref in members:
 current=pin(Path(ref['path']))
 if current['sha256']!=ref['sha256'] or current['bytes']!=ref['bytes']:raise RuntimeError('member drift during seal')
print(json.dumps({'namespace':str(Q),'status':'BLOCKED_PRODUCTION_ATTACH_COMPLETION','authority':'NONE','MF':manifest,'HDF':hdf,'report':report_ref,'contract_excerpts':excerpts_ref,'source_pins':pin(Q/'source-pins.json'),'static_checks':static_ref,'member_count':len(members),'Source_changes':0,'author_execution':{'Go':None,'native':None,'SQL':None,'model':0},'author_mechanical_failures':1,'failure_origin':pin(Q/'failure-origin.826.json')},ensure_ascii=False))
