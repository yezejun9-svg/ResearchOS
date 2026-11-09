"""Bind reviewed future runtime entrypoints and their exact Root contract."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import sys

N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W09/W09-99/w09_c19_caller_v7_source_codex/w09c19r3-1a11f30'
refresh=sys.argv[1:]==['--refresh-unsealed']
assert not (N/'HDF.json').exists() and not (N/'MF.json').exists()
rebindings=[]
def pin(p):
    p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value,raw=False):
    data=value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    p=N/name
    if p.exists():
        assert refresh
        before=p.read_bytes()
        rebindings.append(dict(path=str(p),whole_before_base64=base64.b64encode(before).decode(),whole_after_base64=base64.b64encode(data).decode(),
            before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(data).hexdigest()))
        p.write_bytes(data)
    else:
        with p.open('xb') as f:f.write(data)
    return pin(N/name)

runtime=(N/'main_c19_runtime.source.py').read_bytes();compile(runtime,'runtime','exec');runtime_pin=pin(N/'main_c19_runtime.source.py')
template=(N/'main_c19_launcher.template.py').read_bytes()
assert template.count(b'RUNTIME_SHA_BIND_AT_SOURCE_SEAL')==1
launcher=template.replace(b'RUNTIME_SHA_BIND_AT_SOURCE_SEAL',runtime_pin['sha256'].encode());compile(launcher,'launcher','exec')
save('main_c19_launcher.source.py',launcher,True)
for stage in ('prepare','run'):
    source=f'''"""Source-only future {stage} entrypoint; exact Root request required."""
import hashlib
from pathlib import Path
import sys
import types
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
def main():
    p=N/'main_c19_runtime.source.py';raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!={runtime_pin['sha256']!r}:raise ValueError('PINNED_RUNTIME_DRIFT')
    m=types.ModuleType('main_c19_{stage}_runtime');m.__file__=str(p)
    exec(compile(raw,str(p),'exec'),m.__dict__)
    m.stage({stage!r},sys.argv[1:])
if __name__=='__main__':main()
'''.encode()
    compile(source,stage,'exec');save(stage+'_main_c19.actual_owned.py',source,True)
c=json.loads((N/'source.choice.json').read_bytes())
bindings=dict(prepare_caller_ref='prepare_main_c19.actual_owned.py',producer_caller_ref='run_main_c19.actual_owned.py',
    launcher_ref='main_c19_launcher.source.py',runtime_ref='main_c19_runtime.source.py',choice_ref='source.choice.json',compiler_blueprint_ref='compiler-source-blueprint.json')
fields=['schema','status','issued_by','executor','source_handoff_ref','source_manifest_ref',*bindings,
    'source_review_handoff_ref','source_review_manifest_ref','source_review_decision_ref','adoption_outcome_ref',
    'adoption_review_handoff_ref','adoption_review_manifest_ref','adoption_review_decision_ref',
    'source_root','run_id','receipt_root','scratch_root','output_root','selected_tests','expected_native_ids','source21','main_seven_after_refs',
    'list_timeout_seconds','producer_timeout_seconds','inner_Go_timeout_seconds','maximum_go_test_runs','maximum_go_list_runs',
    'formal_dispatcher','formal_acceptance','Source_mutation','checkpoint_write','ownership_write','step_state_write','worktree_creation','automatic_retry',
    'formal_case_accepted_delta','external_model_provider_requests','paid_provider_requests','production_DB_writes']
assert len(fields)==len(set(fields))
contract=dict(schema='researchos.w09-main-c19-producer-root-calling-contract.v1',status='SOURCE_ONLY_NO_EXECUTION_GRANT',
    author='codex:/root/command_queue_impl',source_file_bindings=bindings,bound_source_refs={k:pin(N/v) for k,v in bindings.items()},
    scope_required_fields=fields,request_exact_fields=['schema','issued_by','scope_ref','canonical_vector_ref','calling_contract_ref'],
    request_schema='researchos.root-w09-main-c19-native-request.v1',root_scope_schema='researchos.root-w09-main-c19-native-scope.v1',
    root_scope_status='ROOT_AUTHORIZED_SINGLE_MAIN_C19_PRODUCER',scope_excludes_canonical_vector_ref=True,
    future_argv={stage:[c['tool_refs']['python']['path'],'-I','-S','-B','-X','utf8',str(N/(stage+'_main_c19.actual_owned.py')),
        'ROOT_REQUEST_ABSOLUTE_PATH','ROOT_REQUEST_BARE_SHA256','ROOT_REQUEST_BYTES'] for stage in ('prepare','run')},
    future_CWD=str(R),same_request_and_vector_for_both_stages=True,
    fixed_paths={k:c[k] for k in ('source_root','run_id','receipt_root','scratch_root','output_root')},
    current_adoption_requirement=dict(outcome_path=c['future_adoption_outcome_path'],source_handoff_ref=c['adoption_source_handoff_ref'],
        source_manifest_ref=c['adoption_source_manifest_ref'],decision_schema='researchos.w09-main-c19-independent-adoption-decision.v1',
        decision='ACTUAL_SEVEN_TARGET_ADOPTION_VERIFIED',actor_role='INDEPENDENT_NON_AUTHOR',actor_excludes=['codex:/root','codex:/root/command_queue_impl'],
        handoff_fields=['manifest_ref','actor_id','actual_decision_ref'],decision_fields=['schema','decision','actor_id','actor_role','adoption_outcome_ref',
            'source_handoff_ref','source_manifest_ref','final_target_refs','source21','all_handles_closed','formal_acceptance','formal_case_accepted_delta']),
    source_review_requirement=dict(decision_schema='researchos.w09-main-c19-producer-independent-source-decision.v1',
        decision='SOURCE_ACCEPTED_FOR_ROOT_SINGLE_MAIN_C19_PRODUCER',actor_role='INDEPENDENT_NON_AUTHOR',
        handoff_fields=['manifest_ref','actor_id','source_decision_ref'],decision_fields=['schema','decision','actor_role','actor_id',
            'source_handoff_ref','source_manifest_ref','calling_contract_ref',*bindings,'run_id','output_root','source21','actual_executed','formal_case_accepted_delta']),
    canonical_vector=dict(schema='researchos.w09-main-c19-native-canonical-vector.v1',fields=['schema','checkpoint_revision','ownership_revision','refs'],
        ordered_paths=[str(R/'execution/v2.4'/f'{n}.json') for n in ('checkpoint','path_ownership','step_state','commands')],
        minimum_exclusive_revisions=dict(checkpoint=367,ownership=171),requires_separate_new_native_owner=True,commands_exact_after_ref=c['main_seven_after_refs'][6]),
    ownership_pointer='/card_path_bindings/W09-99/subtasks/c19_main_root_native_producer',checkpoint_slice_id='C19_MAIN_ROOT_NATIVE_PRODUCER',
    owner_fields=['owner','current_source_writer','state','scope_ref','source_handoff_ref','source_manifest_ref','source_review_handoff_ref',
        'source_review_manifest_ref','adoption_outcome_ref','adoption_review_handoff_ref','source_root','run_id','receipt_root','scratch_root','output_root',
        'formal_case_accepted_delta','parent_acceptance'],worker_fields=['step_id','slice_id','owner','state','scope_ref','source_handoff_ref','source_review_handoff_ref','adoption_outcome_ref','run_id'],
    registered_state='ROOT_REGISTERED_PENDING_MAIN_C19_NATIVE',
    sequence=['Main7 actual and independent actual adoption review must be sealed first.',
        'Independent Source reviewer accepts this exact producer package; no actual run in Source stage.',
        'Root signs exact fresh scope, separately registers native owner/worker, then seals current four-document vector and request.',
        'Root calls prepare once. No Native executes; private profile/temp/gocache and closed readiness are created.',
        'Root calls run once with identical request/vector. One owned go list -export plus one owned Python producer; exactly one Go test with two selected parent tests.',
        'Root preserves exact raw files and all job/guard receipts; first failure stops. No automatic retry after exception, timeout, or process loss.',
        'Independent actual mode review must bind launcher impact as well as Source21 before either C19 router consumer.'],
    actual_commands=dict(go_list=[c['tool_refs']['go']['path'],*c['list_argv_suffix']],
        native_go_test=[c['tool_refs']['go']['path'],'test','-count=1','-json','-run','^(?:TestW09C19ChainInvalidation|TestW09C19ExplicitOriginAndUnknown)$','./internal/domain']),
    timeouts=dict(go_list=240,outer_producer=420,inner_Go=180,owned_job_cleanup_observation=5),
    compiler_closure=dict(expected_package_count=351,Source21=c['source21'],blueprint_ref=pin(N/'compiler-source-blueprint.json'),
        old_metadata_use='Finite package/path blueprint only; no old Native result is reused as a new result.',
        stable_Main_GOROOT_module_sources_held_before_list=True,actual_exports_generated_files_and_Module_GoMod_held_before_test=True,
        shared_old_GOCACHE_is_not_an_input=True,GOCACHE='fresh private scratch/gocache',network_module_fetch=False),
    UUID_adapter=dict(only_runner_private_uuid_object=True,stdlib_uuid_global_modified=False,Main_source_modified=False,
        exact_single_uuid4_call_required=True,second_call_or_other_attribute='REJECT',fixed_run_id=c['run_id'],
        launcher_pin_is_additional_to_Source21=True,mandatory_mode_review_inputs=['launcher_ref','runtime_ref','Root_request_ref','launcher.permit.json',
            'launcher.started.json','launcher.closed.json','actual_environment','actual_argv','run_id','output_root','Main_absolute_owned_and_raw_pins']),
    numeric_evidence=dict(original_result_JSON='Python lossless integer serialization; never PowerShell/JS numeric round-trip.',
        creation_time_100ns_decimal='Exact decimal string alongside unchanged original integer.',unobserved_individual_exit=None),
    actual_write_scope=['fixed receipt_root subtree','fixed scratch_root subtree','fixed output_root subtree'],
    forbidden_writes=['Main Source','CP/OW/SS/commands','old packets/receipts','production or trial DB','shared Source/dependency files'],
    receipt_rules=dict(prepare_ready='Only after preparation guards close successfully.',producer_closed='Only after owned jobs, packet byte archive and all guards close.',
        failed_attempt='Preserve raw stdout/stderr, actual exit or null, helper cleanup, partial packet if job is confirmed idle; stop.',
        ordinary_cleanup='Attempt all independent guard closes; never delete old paths or rewrite original raw evidence.',
        process_loss='Keep one-shot intent and partial evidence for explicit Root reconciliation; do not retry automatically.'),
    formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,actual_executed=False,execution_grant=False)
save('root-calling-contract.json',contract)
inverse=[]
for oldname,newname in [('prepare_w09_c19.actual_owned.py','prepare_main_c19.actual_owned.py'),('run_w09_c19.actual_owned.py','run_main_c19.actual_owned.py')]:
    old=(S/oldname).read_bytes();new=(N/newname).read_bytes()
    inverse.append(dict(original_ref=pin(S/oldname),proposed_ref=pin(N/newname),whole_before_base64=base64.b64encode(old).decode(),
        whole_after_base64=base64.b64encode(new).decode(),inverse_kind='complete_original_bytes_restorable',
        reason='Remove worktree/source overlay; delegate bounded Main-root stages to exact pinned runtime.'))
for name in ('main_c19_runtime.source.py','main_c19_launcher.source.py'):
    inverse.append(dict(original_ref=None,proposed_ref=pin(N/name),whole_before_base64=None,
        whole_after_base64=base64.b64encode((N/name).read_bytes()).decode(),inverse_kind='new_file_absence',original_Main_mutated=False))
save('caller.complete-byte-inverse.json',dict(schema='researchos.w09-main-c19-caller-complete-inverse.v1',files=inverse,
    old_callers_preserved=True,exact_helpers_reused=['SourceReadGuard','windows_owned_process.run_owned','closure_v7.verify_native/verify_owned/verify_c19'],
    no_new_tool_loop=True,no_Main_Source_patch=True))
if refresh:
    name='unsealed-binding-refinement.'+runtime_pin['sha256'][:12]+'.complete-byte-inverse.json'
    assert not (N/name).exists()
    save(name,dict(reason='Rebind current unsealed runtime after bounded Source corrections; each previous byte version retained.',changes=rebindings))
print(json.dumps(dict(status='SOURCE_CALLERS_BOUND',runtime_ref=runtime_pin,contract_ref=pin(N/'root-calling-contract.json'),actual=False)))
