"""Persist the resolved W09 peer-delivery gap and current Source continuations."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os

R = Path(r'D:\作品集\ResearchOS\research-os')
N = Path(__file__).resolve().parent
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT = Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree = ast.parse((N / 'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x, ast.FunctionDef)
    and x.name in {'pin', 'save', 'exact', 'outputs', 'capture'}], type_ignores=[]),
    'Root_original_helpers_only', 'exec'), globals())
prior = json.loads((N / 'pending-diagnostics.cp373.live1087.root.json').read_bytes())
rows = list(prior['pending'])
assert [x['ordinal'] for x in rows] == list(range(1067, 1087))
for ordinal, chunk in ((1087, 'd649fa'), (1088, '51549c')):
    def match(call, result):
        return any(x.get('chunk_id') == chunk for x in outputs(result['payload'].get('output')))
    pair = capture(AUDIT, ordinal, match, root=True)
    assert pair is not None
    standard = save('original%d.standard-binding.live1089.root.json' % ordinal, dict(
        schema='researchos.root-original-diagnostic-binding.v1', issued_by='codex:/root',
        original_capture_ref=pair[0], original_source_binding_ref=pair[1],
        original_source_binding_selector='$', original_ordinal=ordinal,
        original_bytes_unchanged=True, formal_authority=False))
    rows.append(dict(ordinal=ordinal, origin_ref=pair[0], origin_selector='$', capture_binding_ref=standard,
        description='Bounded Root public-delivery capture did not find the old W09 profile reviewer digest. Original complete tool pair retained; actual fresh reviewer redelivery resolved the gap and all four peer captures passed without Source/control rerun.',
        capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR', actual_outer_exit=1, actual_python_exit=1,
        actual_native_exit=None, actual_Go_exit=None, actual_SQLite_exit=None,
        actual_dispatcher_exit=None, actual_model_exit=None))
assert [x['ordinal'] for x in rows] == list(range(1067, 1089))
current = json.loads((N / 'main23.v4.activation-after.current4.actual.root.json').read_bytes())['current_canonical_refs']
for ref in current:
    exact(Path(ref['path']), ref['sha256'], ref['bytes'])
pending = save('pending-diagnostics.cp373.live1089.root.json', dict(prior,
    pending=rows, next_original_failure_ordinal=1089, registered_in_current_canon=False, counter_reset=False))
resume = save('RESUME.cp373-source-adoptions.live1089.root.json', dict(
    schema='researchos.root-execution-resume.v1', issued_by='codex:/root', root_thread_id=THREAD,
    created_utc=datetime.now(timezone.utc).isoformat(), canonical_refs=current,
    expected_revisions=dict(checkpoint=373, path_ownership=177, step_state=None, commands=39),
    pending_ref=pending, canonical_next_failure_ordinal=1067, next_original_failure_ordinal=1089,
    counter_reset=False, formal_cases_current_accepted=0, formal_cases_required=42, parent_tasks_required=22,
    Main23='QUALIFIED_CURRENT_MAIN23_BUILD',
    current_Main23_programme_qualification_ref=pin(N / 'main23.programme.qualification.bound.actual.root.json'),
    W09='FOUR_ACTUAL_PUBLIC_AUTHOR_REVIEW_DELIVERIES_VALIDATED_Q_NF3_SOURCE_ACCEPTED_ROOT_ADOPTER_SOURCE_TASK75_ACTIVE_CM39_UNCHANGED',
    W09_actual_source_audits_ref=exact(N / 'w09.reviewed-source-actual-audits.root.json',
        '18b5d44ccc3bafd1acd10a0171162254500b05c0e6a4d09328ac93698faabac9', 1663),
    old21='TASK70_CHANGES_REQUIRED_TWO_BOUNDARY_DEFECTS_TASK73_MINIMAL_SOURCE_REPAIR_ACTIVE_NO_ACTUAL_OLD21_BUILD',
    old21_previous_resource_scope_execution_grant=False,
    public22='READONLY83_COMPONENT_QUALIFIED_ORIGINAL1025_FAILURE_RETAINED',
    goal_status='ACTIVE', formal_acceptance=False, parent_acceptance=False,
    prior_resume_ref=pin(N / 'RESUME.cp373-main23-qualified.live1086.root.json')
        if (N / 'RESUME.cp373-main23-qualified.live1086.root.json').exists()
        else pin(N / 'RESUME.cp373-main23-qualified.live1087.root.json')))
handoff = R / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
old = handoff.read_bytes()
archive = N / 'historical.HANDOFF.before-live1089.root.md'
with archive.open('xb') as stream:
    stream.write(old); stream.flush(); os.fsync(stream.fileno())
prefix = ('# Current Root continuation: CP373 / OW177 / CM39 / live next1089\n\n'
    'Main23 current programme qualified with actual five-Go build, non-author review and genuine Root binding. '
    'W09 Q/NF3 four actual peer deliveries captured; Root adopter Source Task75 active. '
    'Old21 Caller needs two minimal Source fixes under Task73. No actual old21/full-W09 run yet. '
    'Goal ACTIVE; formal0/42; original counters and old body preserved.\n\n'
    'Current resume: ' + resume['path'] + '\nSHA256 ' + resume['sha256'] + ' bytes ' + str(resume['bytes']) + '\n\n'
    'Pending diagnostics: ' + pending['path'] + '\nSHA256 ' + pending['sha256'] + ' bytes ' + str(pending['bytes']) + '\n\n').encode()
with handoff.open('wb') as stream:
    stream.write(prefix + old); stream.flush(); os.fsync(stream.fileno())
assert handoff.read_bytes().endswith(old)
print(json.dumps(dict(resume_ref=resume, pending_ref=pending, pending_rows=len(rows),
    next_original_failure_ordinal=1089, handoff_ref=pin(handoff), Canonical_unchanged=True),
    ensure_ascii=False, indent=2))
