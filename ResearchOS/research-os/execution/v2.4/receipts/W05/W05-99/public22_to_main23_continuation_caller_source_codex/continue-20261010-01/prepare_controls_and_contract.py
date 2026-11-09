from pathlib import Path
import ast,copy,hashlib,json,types
N=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os')
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,obj):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
i=json.loads((N/'source-inputs.json').read_bytes())
i['main_recovery_source_ref']=pin(R/'internal/domain/backup_recovery.go')
(N/'source-inputs.json').write_text(json.dumps(i,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
raw=(N/'public22_to23_root.source.py').read_bytes();tree=ast.parse(raw)
m=types.ModuleType('continuation_source_controls');m.__file__=str(N/'public22_to23_root.source.py')
exec(compile(raw,m.__file__,'exec'),m.__dict__)
# Import only: none of the registration/native/SQL entry points run.
leaf=types.ModuleType('pure_leaf_controls');exec(compile(Path(i['leaf_runner_ref']['path']).read_bytes(),i['leaf_runner_ref']['path'],'exec'),leaf.__dict__)
contract=json.loads(Path(i['leaf_contract_ref']['path']).read_bytes());case=json.loads(Path(i['case_request_ref']['path']).read_bytes())
checks=[]
def check(name,condition):
 if not condition:raise AssertionError(name)
 checks.append(dict(id=name,result='PASS',kind='PURE_SOURCE_CONTROL'))
projection=m.continuation_projection(contract,case,str(R/'execution/v2.4/receipts/W05/W05-99/integration_codex/public22-continuation-'+'a'*32),i['main23_program_ref'],leaf)
check('exact_three_new_phases',[p['id'] for p in projection['phases']]==['upgrade22to23','backup23','verify23'])
old=leaf.compile_case(contract,case)
check('preserved_old_data_backup_opaque_key',all(projection['paths'][k]==old['paths'][k] for k in ['db22','data22','backup22','key','owner_file']))
check('new_working_copy_distinct',projection['paths']['workdb22']!=projection['paths']['db22'])
check('one_pinned_programme',all(p['argv'][0]==i['main23_program_ref']['path'] for p in projection['phases']))
check('upgrade_uses_only_working_copy',projection['phases'][0]['argv'][2]==projection['paths']['workdb22'])
# New SOURCE fact preservation: output hashing fails after the real job result.
for failure_at in [1,2]:
 call=dict(actual_exit=None,observation=None);count=[0];observed=dict(actual_exit=37,creation_time_100ns=134360324027646590,job_cleanup={'handles_closed':True})
 def fail_pin(path):
  count[0]+=1
  if count[0]==failure_at:raise OSError('injected output pin failure')
  return {'test_pin':str(path)}
 caught=False
 try:m.record_observation(call,observed,123,'out','err',fail_pin)
 except OSError:caught=True
 check('retain_actual_exit_output_pin_failure_'+str(failure_at),caught and call['actual_exit']==37 and call['observation'] is observed and call['creation_time_100ns_decimal']=='134360324027646590')
check('no_whole_old_runner_call',not any(isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute) and v.func.attr in ['run_registered_case','recheck_existing_public22'] for v in ast.walk(tree)))
check('single_new_job_callsite',sum(isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute) and v.func.attr=='run_owned' for v in ast.walk(tree))==1)
# Pure new23 postcondition controls: no database access and no fabricated runtime evidence.
fake=types.SimpleNamespace(validate_ledger=lambda *_:True,RESTORED='RESTORED_RECONCILIATION_REQUIRED')
before=dict(tables={'t':{'count':0,'rows_sha256':'x'}},schema_rows=[['trigger','fence','t','sql']],schema_sha256='a',credentials={'all_revoked_one':True})
manifest=dict(migrations=list(range(1,24)),schema_hash='sha256:a',id='b',inventory={})
report=dict(status=fake.RESTORED,backup_id='b',before={},after={},recovery={'credentials':'REVOKED_REPROVISION_LOCALLY'})
check('restore23_matching_tables',m.validate_restore23(fake,before,copy.deepcopy(before),manifest,report))
bad=copy.deepcopy(before);bad['tables']['t']['rows_sha256']='changed'
try:m.validate_restore23(fake,before,bad,manifest,report);rejected=False
except ValueError:rejected=True
check('restore23_reject_table_drift',rejected)
bad=copy.deepcopy(before);bad['schema_rows'][0][3]='wrong'
try:m.validate_restore23(fake,before,bad,manifest,report);rejected=False
except ValueError:rejected=True
check('restore23_reject_fence_drift',rejected)
check('backup23_matching_tables',m.validate_backup23(fake,before,copy.deepcopy(before),manifest))
# Full inverse: narrow scope registration preserves an unrelated sentinel and failure ledger.
cp=dict(revision=400,workers=[],work_in_progress={'root_next_failure_ordinal_live':1172},failure_counters={'total':999},unrelated={'keep':[1,2]})
ow=dict(revision=200,card_path_bindings={'W05-99':{'subtasks':{'unrelated':{'keep':True}}}},unrelated={'keep':True})
sr={'test':'scope'};orf={'test':'owner'};wr={'test':'worker'}
owner={'scope_ref':sr,'selected_worker_id':m.ROOT};worker={'scope_ref':sr,'selected_owner_ref':orf,'worker_id':m.ROOT}
a,b=m.projection(cp,ow,sr,orf,wr,{'test':'facts'},owner,worker,'future')
check('canonical_projection_inverse_preserves_other_work',a['unrelated']==cp['unrelated'] and b['unrelated']==ow['unrelated'] and a['failure_counters']==cp['failure_counters'])
# Verify only directly consumed pinned inputs; never recurse any historical mutable Canon or private paths.
refs=[i[k] for k in ['leaf_runner_ref','leaf_contract_ref','main23_bound_ref','main23_program_ref','existing22_decision_ref','existing22_hdf_ref','existing22_mf_ref','main_recovery_source_ref','runtime_resources_ref','reuse_registration_source_ref']]
for ref in refs:
 assert '/private/' not in ref['path'].replace('\\','/').lower()
 assert pin(ref['path'])['sha256']==ref['sha256']
save('delta-source-controls.json',dict(checks=checks,count=len(checks),actual_native_children=0,SQL_connections=0,Root_registration_calls=0,TP_calls=0,formal_acceptance=False))
save('current-direct-input-checks.json',dict(refs=refs,all_match=True,read_only=True,private_owner_or_key_bytes=False))
# Exact three-line tool pairs for the two Root-assigned original read failures.
session=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
calls={};head=None;offset=0;found={};observed_size=session.stat().st_size
with session.open('rb') as f:
 for line in f:
  here=offset;offset+=len(line)
  try:v=json.loads(line)
  except ValueError:continue
  p=v.get('payload',{})
  if v.get('type')=='session_meta' and head is None:head=(here,line,v)
  if v.get('type')=='response_item' and p.get('type') in ('custom_tool_call','function_call'):calls[p.get('call_id')]=(here,line,v)
  if v.get('type')=='response_item' and p.get('type') in ('custom_tool_call_output','function_call_output'):
   output=p.get('output','')
   for chunk in ['5b772b','5ce81a']:
    if chunk not in found and chunk in str(output) and p.get('call_id') in calls:
     found[chunk]=[head,calls[p['call_id']],(here,line,v)]
assert set(found)=={'5b772b','5ce81a'}
diagnostics=[]
for chunk,ordinal,outer,child in [('5b772b',1170,0,2),('5ce81a',1171,1,None)]:
 rows=found[chunk];blob=b''.join(x[1] for x in rows);out=N/('original'+str(ordinal)+'.raw.jsonl')
 with out.open('xb') as f:f.write(blob)
 binding=dict(schema='researchos.source-author-original-tool-binding.v1',source_actor='codex:/root/attach_restore_independent_review',
  source_audit_path=str(session),source_prefix_size_observed=observed_size,
  source_line_offsets=[x[0] for x in rows],source_line_bytes=[len(x[1]) for x in rows],
  original_line_sha256=[hashlib.sha256(x[1]).hexdigest() for x in rows],original_call_id=rows[1][2]['payload']['call_id'],original_capture_ref=pin(out),
  Root_assigned_ordinal=ordinal,tool_chunk_id=chunk,outer_exit=outer,rg_child_exit=child,Python_exit=None,Native_exit=None,automatic_retry=False,root_authority=False)
 save('original'+str(ordinal)+'.binding.json',binding);diagnostics.append(pin(N/('original'+str(ordinal)+'.binding.json')))
save('diagnostics.json',dict(original_failures=diagnostics,assigned_by='codex:/root',source_controls_not_native=True))
# Build exact field inventory from the executable, not an independently invented request schema.
def keys(name):
 return sorted({v.slice.value for v in ast.walk(tree) if isinstance(v,ast.Subscript) and isinstance(v.value,ast.Name) and v.value.id==name and isinstance(v.slice,ast.Constant) and isinstance(v.slice.value,str)})
save('root-calling-contract.source.json',dict(schema='researchos.public22-to-main23-continuation-calling-contract.v1',
 source_author=m.AUTHOR,caller_ref=pin(N/'public22_to23_root.source.py'),source_inputs_ref=pin(N/'source-inputs.json'),
 modes=['build','check','activate','execute'],cli='LOCKED_PYTHON -I -S -B -X utf8 CALLER MODE ref.path ref.sha256 ref.bytes [second_ref.path second_ref.sha256 second_ref.bytes]',
 registration_request_schema='researchos.root-public22-continuation-registration-request.v1',
 registration_request_required_fields=keys('q'),mode=m.MODE,
 Source_review_schema='researchos.public22-continuation-root-independent-source-decision.v1',
 Source_review_required_fields=keys('decision'),
 Source_review_HDF_fields=['actor_id','reviewed_utc','source_decision_ref','manifest_ref'],
 source_hdf_status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION',
 actual_request_schema='researchos.root-public22-continuation-actual-request.v1',actual_request_required_fields=keys('actual'),
 extra_actual_request_fields=dict(issued_by=m.ROOT,formal_acceptance=False,parent_acceptance=False),
 execute_second_ref='Preentry actual Root audit of the immutable actual_request_ref plus scope, registration result and current4; passed separately to avoid a self-reference cycle.',
 activation_second_ref='Root activation document binding facts_ref and before_canonical_refs, plus actual_audit_ref from a post-build original Root call.',
 required_root_hostpairs=['postreview_live_audit_ref','activation actual_audit_ref','execute separate preentry_ref','postexecution external call/output'],
 required_peer_hostpairs=['leaf_review_audit_ref','review_audit_ref','existing22_review_audit_ref','main23_review_audit_ref'],
 required_programme_root_hostpair='main23_root_binding_audit_ref binds the already-issued main23_bound_ref; q never mints a programme qualification',
 actual_root_thread=m.ROOT_THREAD,actual_root_log=m.ROOT_AUDIT,
 finite_lease_seconds_max=3600,current4='Dynamic exact hash+bytes+revision CAS; CP/OW increment1, SS/CM unchanged; old failure ledger and other owners preserved.',
 output_roots=dict(registration='integration_codex/public22-continuation-registration-{continuation_id}',execution='integration_codex/public22-continuation-{continuation_id}'),
 continuation_id='32 lowercase hex, fresh registration and output roots. q.created_utc must be after current4 post-review actual Root capture.',
 source_runtime='Independent own Source review must bind the runtime_resources_ref and declare runtime_closure_reviewed=true. Loaded Python/_sqlite3/native DLL closure is enforced at every Root preparation and actual execute entry.',
 resource_reuse=dict(existing22_decision_ref=i['existing22_decision_ref'],main23_bound_ref=i['main23_bound_ref'],main23_program_ref=i['main23_program_ref'],runtime_resources_ref=i['runtime_resources_ref']),
 original_request_unchanged=i['case_request_ref'],original1025='FAILED_RETAINED',original_four_children_replayed=False,
 phases=projection['phases'],phase_example_only=True,example_output_root=projection['paths']['root'],
 source_only_controls=pin(N/'delta-source-controls.json'),new_native_phase_limit=3,child_timeout_seconds=90,
 working_copy='FILE_SHARE_READ_ONLY held original22 bytes copied to fresh working22; observation of only the new copy before upgrade; original baseline/backup/restore pinned unchanged.',
 private_owner='No read/hash/copy. Existing private recovery key path passed only to qualified public native child; caller checks existence without reading bytes.',
 validation=['exact ledger1..23; integrity ok; FK0','original83 tables preserved except ledger addition and exact credential revocation; exactly3 empty new tables',
  'native plan binds original/target programme and schema hashes; exact Main restore fence','public emitted/persisted reports equal',
  'backup23 same schema+all table hashes; verify23 exact already-fenced schema and every table hash'],
 first_failure='No automatic retry. Native observation and exact decimal FILETIME stored before output pinning; NULL only when no observation returned. Final state retains primary and cleanup/publication errors; Root assigns ordinal and seals original external hostpair.',
 remaining_uncovered='No independent new negative public child; no schema23to24; no original-data cutover; full20to24 OPEN.',
 formal_acceptance=False,parent_acceptance=False,execution_grant=False,formal_case_accepted_delta=0))
print(json.dumps(dict(delta_controls=len(checks),diagnostic_ordinals=[1170,1171],contract_ref=pin(N/'root-calling-contract.source.json')),ensure_ascii=False))

