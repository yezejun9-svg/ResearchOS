"""Source preparation only. Never imports or executes the adoption caller."""
import ast
import base64
import copy
import hashlib
import json
import sys
import types
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
N = Path(__file__).resolve().parent
W = R / 'execution/v2.4/receipts/W09/W09-99'
CV = W / 'w09_c19_consumer_v7_caller_source_codex/consv7-1a11f5e'
PR = W / 'w09_c19_caller_v7_source_codex/w09c19r3-1a11f30'
AR = W / 'w09c19_v7_actual_independent_review_codex/review-37dedbd890c44a93975558f2851d8675'
ACT = W / 'integration_codex/w09c19v7-producer-1a11f30'
CC = W / 'integration_codex/w09c19v7-consumers-1a11f30'
CR = W / 'w09c19_v7_consumers_actual_independent_review_codex/consumer-review-37dedbd890c44a93975558f2851d8675'
GP = R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
K = R / 'execution/v2.4/receipts/W05/W05-99/queue_executor_codex/frozen-package-input'
TARGETS = ('internal/domain/domain_test.go', 'internal/domain/retrieval_test.go',
           'ops/ci/retrieval.py', 'internal/domain/w09_evidence_export_test.go',
           'ops/ci/w09_formal_router.py', 'ops/ci/w09_evidence_closure.py',
           'execution/v2.4/commands.json')
ENV6 = [f'RESEARCHOS_W09_{a}_{b}' for a in ('NATIVE_REPORT', 'TOOL_RUN', 'MODE_DECISION') for b in ('REF', 'SHA256')]
KEYS = ('test.research.fixture', 'test.retrieval')
inputs = {}

def pin(p):
    p = Path(p).resolve(strict=True)
    raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def observe(p, expected=None):
    ref = pin(p)
    if expected is not None:
        assert ref == expected, ('PIN_DRIFT', str(p))
    k = ref['path'].casefold()
    assert k not in inputs or inputs[k] == ref
    inputs[k] = ref
    return ref

def doc(p):
    observe(p)
    return json.loads(Path(p).read_bytes())

def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    with (N / name).open('xb') as f:
        f.write(raw)
    return pin(N / name)

def manifest_inputs(folder):
    h = doc(folder / 'HDF.json')
    m = doc(folder / 'MF.json')
    assert h['manifest_ref'] == pin(folder / 'MF.json')
    members = m['members']
    for member in (members.values() if isinstance(members, dict) else members):
        ref = {k: member[k] for k in ('path', 'sha256', 'bytes')}
        ref['sha256'] = ref['sha256'].removeprefix('sha256:')
        observe(ref['path'], ref)
    return h

def replace_registry(raw):
    original = json.loads(raw)
    desired = copy.deepcopy(original)
    for key in KEYS:
        row = desired['commands'][key]
        row['executable_tool'] = 'python'
        row['argv'] = ['-B', '-X', 'utf8', 'ops/ci/w09_formal_router.py', key]
        row['allowed_env'] += ENV6
        if 'W09' not in row['selectors']['task_id']:
            row['selectors']['task_id'].append('W09')
        row['selectors']['case_id'] = ['C19']
        if key == 'test.research.fixture':
            row['tool_env']['RESEARCHOS_GO'] = 'go'
    text = raw.decode('utf-8')
    newline = '\r\n' if '\r\n' in text else '\n'
    spans = []
    for key in KEYS:
        marker = '    ' + json.dumps(key) + ': '
        assert text.count(marker) == 1
        start = text.index(marker) + len(marker)
        old, count = json.JSONDecoder().raw_decode(text[start:])
        assert old == original['commands'][key]
        replacement = json.dumps(desired['commands'][key], ensure_ascii=False, indent=2).replace('\n', newline + '    ')
        spans.append(dict(command=key, start=start, end=start + count,
                          before=text[start:start+count], after=replacement))
    updated = text
    for span in sorted(spans, key=lambda x:x['start'], reverse=True):
        updated = updated[:span['start']] + span['after'] + updated[span['end']:]
    assert json.loads(updated) == desired
    inverse = updated
    for span in spans:
        marker = '    ' + json.dumps(span['command']) + ': '
        start = inverse.index(marker) + len(marker)
        _, count = json.JSONDecoder().raw_decode(inverse[start:])
        assert inverse[start:start+count] == span['after']
        inverse = inverse[:start] + span['before'] + inverse[start+count:]
    assert inverse.encode('utf-8') == raw
    return updated.encode('utf-8'), dict(schema='researchos.w09-main-c19-registry-two-entry-byte-inverse.v1',
        spans=spans, whole_original_base64=base64.b64encode(raw).decode(),
        whole_proposed_base64=base64.b64encode(updated.encode()).decode(), full_byte_inverse=True,
        unchanged_top_level_keys=[k for k in original if k != 'commands'],
        unchanged_other_entries=[k for k in original['commands'] if k not in KEYS])

def main():
    assert N == W / 'main_c19_source_registry_integration_codex/mainc19-1a11f84'
    assert pin(GP)['sha256'] == 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    cvh = manifest_inputs(CV)
    prh = manifest_inputs(PR)
    arh = manifest_inputs(AR)
    crh = manifest_inputs(CR)
    assert pin(AR/'HDF.json')['sha256'] == 'd6adce580965b6d8c607a5176a45043dbfb445a51d7d50d5a7f2195b89dcaa16'
    assert pin(AR/'MF.json')['sha256'] == '511830b94ffdd4059727d09bc240e02acb6976b5ee7f50ff1ac9f320cd3f4218'
    choice = doc(CV/'source.choice.json')
    assert cvh['choice_ref'] == pin(CV/'source.choice.json')
    assert list(choice['six_source_refs']) == list(TARGETS[:6])
    packet = doc(ACT/'native-packet.public-index.json')
    report_ref = observe(packet['original_report_ref']['path'], packet['original_report_ref'])
    report = doc(report_ref['path'])
    closed_ref = observe(CC/'consumers.closed.json')
    assert closed_ref['sha256'] == '8dd7f3d0ecd90f4b35b497917db132005e369e1501c9ff2a5fd31a82dab0c53c'
    closed = doc(closed_ref['path'])
    assert closed['all_owned_jobs_closed'] and closed['all_acquired_guards_closed']
    assert pin(CR/'HDF.json')['sha256']=='5ee925444fa3377b09cf2464dd91c786c87adcec8035b451ad0717c5f02980f8'
    assert pin(CR/'MF.json')['sha256']=='6635364ecbc9eeff19f62667ff81c93a0a972483bfcbf01158b96f135ed55a7f'
    assert crh['decision']=='ACTUAL_TWO_C19_COMPONENT_CONSUMERS_VERIFIED_PASS' and crh['consumer_closed_ref']==closed_ref
    for ref in closed['invocation_refs'] + [v['ref'] for v in closed['guard_cleanups']]:
        observe(ref['path'], ref)
    for item in ('validation.closed.json','canonical.pre-run.exact.json'):
        doc(ACT/item)
    for p in (GP, Path(__file__), N/'adopt_main_c19.source.py', N/'check_source.py', R/'execution/project_identity.json',
              R/'execution/toolchains/locked.json', K/'contracts/execution.plan.json', K/'tools/task_packet.py',
              R/'execution/command_dispatcher/dispatch.py', R/'execution/v2.4/formal_case_index.py'):
        observe(p)
    lock = doc(R/'execution/toolchains/locked.json')
    for name in ('python','go'):
        observe(lock['tools'][name]['path'])
    before = []
    for rel in TARGETS:
        p = R/rel
        before.append(observe(p) if p.is_file() else None)
    assert [r is None for r in before] == [False,False,False,True,True,True,False]
    sources = report['version_manifest']['source_sha256']
    assert len(sources) == 21
    applicability = []
    for rel, digest in sources.items():
        if rel in choice['six_source_refs']:
            ref = choice['six_source_refs'][rel]
            observe(ref['path'], ref)
            assert digest == 'sha256:' + ref['sha256']
            applicability.append(dict(path=rel, disposition='EXACT_SEALED_SOURCE_TO_ADOPT', desired_ref=ref))
        else:
            ref = observe(R/rel)
            assert digest == 'sha256:' + ref['sha256']
            applicability.append(dict(path=rel, disposition='CURRENT_MAIN_ALREADY_EXACT', current_ref=ref))
    assert sum(x['disposition']=='CURRENT_MAIN_ALREADY_EXACT' for x in applicability)==15
    mod = types.ModuleType('w09_main_c19_source_guard')
    mod.__file__ = str(GP)
    exec(compile(GP.read_bytes(), str(GP), 'exec'), mod.__dict__)
    guard = mod.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    try:
        guard.acquire(list(inputs.values()))
        raw = guard.get_buffer(str((R/TARGETS[-1]).resolve()))
        proposed, inverse = replace_registry(raw)
        with (N/'commands.proposed.json').open('xb') as f:f.write(proposed)
        inverse_ref = save('commands.complete-byte-inverse.json', inverse)
        changes = []
        for i, rel in enumerate(TARGETS):
            original = None if before[i] is None else guard.get_buffer(before[i]['path'])
            backup_ref = None
            if original is not None:
                with (N/f'before.{i}.raw').open('xb') as f:f.write(original)
                backup_ref = pin(N/f'before.{i}.raw')
            after_ref = choice['six_source_refs'][rel] if i<6 else pin(N/'commands.proposed.json')
            changes.append(dict(target=str((R/rel).resolve()),relative=rel,before_ref=before[i],
                                before_archive_ref=backup_ref,after_source_ref=after_ref,
                                after_target_ref=dict(after_ref,path=str((R/rel).resolve()))))
        change_ref = save('change-set.json', dict(schema='researchos.w09-main-c19-seven-target-change-set.v1',
            author='codex:/root/command_queue_impl', root=str(R.resolve()), target_count=7, targets=changes,
            source21=applicability, source21_report_ref=report_ref, original_consumer_closed_ref=closed_ref,
            producer_actual_review_handoff_ref=pin(AR/'HDF.json'),producer_actual_review_manifest_ref=pin(AR/'MF.json'),
            component_actual_review_handoff_ref=pin(CR/'HDF.json'),component_actual_review_manifest_ref=pin(CR/'MF.json'),
            source_consumer_handoff_ref=pin(CV/'HDF.json'),source_consumer_manifest_ref=pin(CV/'MF.json'),
            producer_source_handoff_ref=pin(PR/'HDF.json'),producer_source_manifest_ref=pin(PR/'MF.json'),
            guard_ref=pin(GP),toolchain_ref=pin(R/'execution/toolchains/locked.json'),
            python_ref=pin(lock['tools']['python']['path']),identity_ref=pin(R/'execution/project_identity.json'),
            registry_inverse_ref=inverse_ref, formal_case_accepted_delta=0,
            copies_producer_report_or_raw=False,main_adoption_executed=False))
        save('root-calling-contract.json',dict(
            schema='researchos.w09-main-c19-source-calling-contract.v1',status='SOURCE_ONLY_NO_EXECUTION_GRANT',
            caller_ref=pin(N/'adopt_main_c19.source.py'),change_set_ref=change_ref,
            exact_targets=[str((R/r).resolve()) for r in TARGETS],
            future_argv=[lock['tools']['python']['path'],'-I','-S','-B','-X','utf8',str(N/'adopt_main_c19.source.py'),
                         'ROOT_POSTREGISTRATION_REQUEST_ABSOLUTE_PATH','ROOT_REQUEST_BARE_SHA256','ROOT_REQUEST_BYTES'],
            root_request_schema='researchos.root-w09-main-c19-adoption-request.v1',
            root_request_exact_fields=['schema','issued_by','scope_ref','canonical_vector_ref','caller_ref'],
            root_scope_schema='researchos.root-w09-main-c19-adoption-scope.v1',
            root_scope_status='ROOT_AUTHORIZED_SEVEN_TARGET_SOURCE_ADOPTION_ONLY',
            scope_required_fields=['schema','status','issued_by','executor','caller_ref','change_set_ref',
                'source_handoff_ref','source_manifest_ref','exact_targets','journal_root','formal_case_accepted_delta',
                'formal_dispatcher','formal_acceptance','producer_rerun','copy_native_packet','new_Go_SQL_API_model_calls',
                'checkpoint_write','ownership_write','step_state_write','consumer_closed_ref',
                'source_review_handoff_ref','source_review_manifest_ref','source_review_decision_ref',
                'component_review_handoff_ref','component_review_manifest_ref'],
            root_scope_has_no_canonical_vector_ref=True,
            sequence=['Independent Source reviewer seals HDF/MF plus exact decision member.',
                'Root issues registration scope binding seven targets and the sealed Source/review pairs.',
                'Root separately registers scope_ref into successor CP/OW; this caller cannot write them.',
                'Root seals ordered checkpoint/path_ownership/step_state/commands vector after registration.',
                'Root issues a separate request binding scope_ref/vector_ref/caller_ref, avoiding a hash cycle.',
                'Only a subsequent explicit Root execution may call the source caller once.'],
            vector_schema='researchos.w09-main-c19-adoption-canonical-vector.v1',
            vector_exact_fields=['schema','checkpoint_revision','ownership_revision','refs'],
            vector_order=['checkpoint.json','path_ownership.json','step_state.json','commands.json'],
            vector_revision_predicate='Explicit integer CP > 366 and OW > 170; each equals its pinned document. No fixed next pair.',
            commands_vector_ref='Must exactly equal target 7 before_ref; commands are exclusively CAS-checked and then changed.',
            ownership_json_pointer='/card_path_bindings/W09-99/subtasks/c19_main_source_registry_adoption',
            ownership_role_checks=dict(shared_integrator='qoder-desktop:/root/platform_owner',
                active_integrator_id='codex:/root',w09_parent_owner='codex:/root',preserve_historical_shared_integrator=True),
            owner_exact_field_bindings=dict(owner='codex:/root',current_source_writer=None,scope_ref='EXACT_ROOT_REGISTRATION_SCOPE_REF',
                exact_targets='EXACT_ORDERED_SEVEN_ABSOLUTE_TARGETS',state='ROOT_REGISTERED_PENDING_SOURCE_ADOPTION',
                source_handoff_ref='THIS_SOURCE_HDF_REF',source_manifest_ref='THIS_SOURCE_MF_REF',
                source_review_handoff_ref='FUTURE_SOURCE_INDEPENDENT_HDF_REF',source_review_manifest_ref='FUTURE_SOURCE_INDEPENDENT_MF_REF',
                component_review_handoff_ref=pin(CR/'HDF.json'),component_review_manifest_ref=pin(CR/'MF.json'),
                journal_root=str(N/'actual-adoption'),formal_case_accepted_delta=0,formal_dispatcher=False,parent_acceptance=False),
            checkpoint_worker_exact_field_bindings=dict(step_id='W09-99',slice_id='C19_MAIN_SOURCE_REGISTRY_ADOPTION',
                owner='codex:/root',state='ROOT_REGISTERED_PENDING_SOURCE_ADOPTION',scope_ref='EXACT_ROOT_REGISTRATION_SCOPE_REF',
                exact_targets='EXACT_ORDERED_SEVEN_ABSOLUTE_TARGETS',source_review_handoff_ref='FUTURE_SOURCE_INDEPENDENT_HDF_REF',
                component_review_handoff_ref=pin(CR/'HDF.json')),
            source_review_decision_schema='researchos.w09-main-c19-independent-source-decision.v1',
            source_review_decision_value='SOURCE_ACCEPTED_FOR_ROOT_SEVEN_TARGET_ADOPTION',
            source_review_required_fields=['schema','decision','actor_role','actor_id','source_handoff_ref','source_manifest_ref',
                'caller_ref','change_set_ref','exact_targets','formal_case_accepted_delta','actual_adoption_executed'],
            source_review_actor_role='INDEPENDENT_NON_AUTHOR',source_review_actor_must_differ_from=['codex:/root/command_queue_impl','codex:/root'],
            source_review_handoff_required_fields=['manifest_ref','actor_id','source_decision_ref'],
            source_review_decision_must_be_manifest_member=True,
            component_review_handoff_ref=pin(CR/'HDF.json'),component_review_manifest_ref=pin(CR/'MF.json'),
            component_actual_schema=crh['schema'],component_actual_decision=crh['decision'],
            original_consumer_closed_ref=closed_ref,
            runtime_business_targets=7,runtime_journal_root=str(N/'actual-adoption'),
            runtime_receipt_names=['intent.json','committed.json','failed.json','owned-handles.cleanup.actual.json','input-guard.cleanup.actual.json','outcome.json'],
            ordinary_failure='Rollback existing bytes under exclusive handles; mark only CREATE_NEW-owned absent targets delete-on-close.',
            crash_atomic=False,process_loss='Retain durable complete before/after intent; explicit Root reconciliation required, no automatic rerun.',
            actual_adoption=False,formal_case_accepted_delta=0,registry_entry_change_count=2,
            proposed_registry_required_env_unchanged=True,dispatcher_source_unchanged=True,
            after_adoption_required=['New explicit Root dispatch scope and actual dispatcher receipts.',
                'Independent current applicability review and production W09 formal profile before any CURRENT formal claim.']))
        save('source-input-pins.original.json', dict(refs=list(inputs.values()),count=len(inputs)))
        for ref in inputs.values():assert pin(ref['path'])==ref
    finally:
        cleanup=guard.close()
        save('source-preparation.guard.cleanup.actual.json',cleanup)
        assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
    print(json.dumps(dict(status='SOURCE_PREPARED_NOT_EXECUTED',change_set_ref=change_ref,
        input_count=len(inputs),targets=7,existing_before=4,absent_before=3,
        source21_count=21,other15_current_exact=True,guard_closed=True),ensure_ascii=False))

if __name__=='__main__':main()
