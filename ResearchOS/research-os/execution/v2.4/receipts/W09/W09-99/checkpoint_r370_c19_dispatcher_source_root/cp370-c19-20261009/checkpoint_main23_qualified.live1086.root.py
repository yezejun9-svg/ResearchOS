"""Retain later original diagnostics and publish the current continuation."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os

R = Path(r'D:\作品集\ResearchOS\research-os')
N = Path(__file__).resolve().parent
B = R / 'execution/v2.4/receipts/W05/W05-99'
W = R / 'execution/v2.4/receipts/W09/W09-99'
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT = Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree = ast.parse((N / 'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x, ast.FunctionDef)
    and x.name in {'pin', 'exact', 'save', 'outputs', 'capture'}], type_ignores=[]),
    'Root_original_helpers_only', 'exec'), globals())
previous = json.loads((N / 'pending-diagnostics.cp373.live1074.root.json').read_bytes())
rows = list(previous['pending'])
assert [x['ordinal'] for x in rows] == list(range(1067, 1074))

def append(ordinal, raw, source_binding, outer, python, description, source_selector='$'):
    exact(Path(raw['path']), raw['sha256'], raw['bytes'])
    exact(Path(source_binding['path']), source_binding['sha256'], source_binding['bytes'])
    standard = save('original%d.standard-binding.live1086.root.json' % ordinal, dict(
        schema='researchos.root-original-diagnostic-binding.v1', issued_by='codex:/root',
        original_capture_ref=raw, original_source_binding_ref=source_binding,
        original_source_binding_selector=source_selector, original_ordinal=ordinal,
        original_bytes_unchanged=True, formal_authority=False))
    rows.append(dict(ordinal=ordinal, origin_ref=raw, origin_selector='$', capture_binding_ref=standard,
        description=description, capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR', actual_outer_exit=outer,
        actual_python_exit=python, actual_native_exit=None, actual_Go_exit=None,
        actual_SQLite_exit=None, actual_dispatcher_exit=None, actual_model_exit=None))

builder_review = B / 'schema21_programme_builder_independent_source_review_codex/review-main21b-20261010-01'
failures = json.loads((builder_review / 'original-review-failures.full-IO.json').read_bytes())
descriptions = {
    1074: 'Old21 independent Source checks used two incorrect reviewer assumptions: direct Name AST and controls75+8. Actual outer/Python0; two semantic Source checks failed in one invocation. Product not run.',
    1075: 'Old21 reviewer read the Root receipt namespace under W05 instead of its actual W09 path; Python and product not invoked.'}
for original in failures['originals']:
    append(original['ordinal'], original['raw_ref'], original['binding_ref'], original['outer_exit'],
        original['Python_exit'], descriptions[original['ordinal']])
caller = B / 'schema21_root_caller_registration_source_codex/s21root-20261010-01'
descriptions = {
    1076: 'Old21 Source numbered-SQL parser tried int(next) for the genuine next_v24_sessions.sql addon. Prior guard closure UNKNOWN_NOT_SERIALIZED; no product calls.',
    1077: 'Old21 Source first parser revision again included the genuine addon. Original retained; exact numbered regex continuation passed25 controls, prior closure unknown.',
    1079: 'Source read-only PowerShell called GetType on null. Nonterminating error preserved; outer0, numeric inner/Python/product exits unobserved.'}
for ordinal in (1076, 1077):
    origin = json.loads((caller / ('failure-origin.%d.json' % ordinal)).read_bytes())
    append(ordinal, origin['original_capture_ref'], origin['capture_binding_ref'],
        origin['actual_outer_exit'], origin['actual_python_exit'], descriptions[ordinal])

def root_original(ordinal, chunk, outer, python, description):
    def match(call, result):
        return any(x.get('chunk_id') == chunk for x in outputs(result['payload'].get('output')))
    pair = capture(AUDIT, ordinal, match, root=True)
    assert pair is not None, 'COMPLETE_ACTUAL_ROOT_PAIR_REQUIRED'
    append(ordinal, pair[0], pair[1], outer, python, description)

root_original(1078, 'd4f3b3', 1, None, 'Root rg guessed a nonexistent host-configuration Source namespace; no Python or product invocation.')
origin = json.loads((caller / 'failure-origin.1079.json').read_bytes())
append(1079, origin['original_capture_ref'], origin['capture_binding_ref'],
    origin['actual_outer_exit'], origin['actual_python_exit'], descriptions[1079])
root_original(1080, '95384f', 1, 1, 'Root programme binding reader passed peer=False for a real v2 peer capture. Actual observation retained; v2 sealer corrected peer=True and passed without product rerun.')
root_original(1081, '6f252c', 1, None, 'Root guessed a nonexistent old helper filename after successful reading of the actual checkpoint script. No Python/product execution.')

batch_dir = W / 'task71_entrypoint_read_codex/task71-20261010-01'
batch_ref = exact(batch_dir / 'actual-diagnostic-pairs.raw.jsonl', 'af6be7de85dc5a9eed4875f778e925b6d88766c16dbd431dff99995e48ea738e', 117678)
batch_binding_ref = exact(batch_dir / 'actual-diagnostic-pairs.binding.json', '18c6666b6f30aedbb5d913af042dfd8e02e6cfaac36cb38028d00402bd4e54da', 3209)
batch_binding = json.loads(Path(batch_binding_ref['path']).read_bytes())
batch_lines = Path(batch_ref['path']).read_bytes().splitlines(keepends=True)
assert len(batch_lines) == len(batch_binding['source_lines']) == 9
source_lines = {}
with Path(batch_binding['source_audit_path']).open('rb') as audit:
    for raw, entry in zip(batch_lines, batch_binding['source_lines']):
        assert len(raw) == entry['length'] and hashlib.sha256(raw).hexdigest() == entry['sha256']
        audit.seek(entry['offset'])
        assert audit.read(entry['length']) == raw
        source_lines[entry['offset']] = raw
for index, pair in enumerate(batch_binding['pairs'][:3]):
    ordinal = pair['root_assigned_ordinal']
    assert ordinal == 1082 + index and pair['outer_exit'] == 1
    selected = b''.join(source_lines[x] for x in pair['source_line_offsets'])
    path = N / ('original%d.selected-source.actual-host.raw.jsonl' % ordinal)
    with path.open('xb') as stream:
        stream.write(selected); stream.flush(); os.fsync(stream.fileno())
    append(ordinal, pin(path), batch_binding_ref, 1, None,
        'Task71 read-only entrypoint query guessed a nonexistent file path; original complete source tool pair retained. Product not invoked.', '$.pairs[%d]' % index)

def collab_limit(call, result):
    return ('Task72' in json.dumps(call['payload'], ensure_ascii=False)
        and 'agent thread limit reached' in json.dumps(result['payload'], ensure_ascii=False))
pair = capture(AUDIT, 1085, collab_limit, root=True)
assert pair is not None
append(1085, pair[0], pair[1], None, None,
    'Followup resource-review dispatch was rejected by actual concurrent agent thread limit; no reviewer turn or process started.')
rows.sort(key=lambda x: x['ordinal'])
assert [x['ordinal'] for x in rows] == list(range(1067, 1086))
current = json.loads((N / 'main23.v4.activation-after.current4.actual.root.json').read_bytes())['current_canonical_refs']
for ref in current:
    exact(Path(ref['path']), ref['sha256'], ref['bytes'])
cp = json.loads(Path(current[0]['path']).read_bytes())
assert cp['revision'] == 373 and len(cp['failure_counters']) == 1064
assert cp['work_in_progress']['root_next_failure_ordinal_live'] == 1067
pending_ref = save('pending-diagnostics.cp373.live1086.root.json', dict(previous, pending=rows,
    next_original_failure_ordinal=1086, counter_reset=False, registered_in_current_canon=False))
qualification_ref = exact(N / 'main23.programme.qualification.bound.actual.root.json',
    'f4075c4e6250226e9c21a2e3cb3cb3d9ee3412c567a5caab391832ad7715ab6c', 6117)
resume_ref = save('RESUME.cp373-main23-qualified.live1086.root.json', dict(
    schema='researchos.root-execution-resume.v1', issued_by='codex:/root', root_thread_id=THREAD,
    created_utc=datetime.now(timezone.utc).isoformat(), canonical_refs=current,
    expected_revisions=dict(checkpoint=373, path_ownership=177, step_state=None, commands=39),
    canonical_next_failure_ordinal=1067, next_original_failure_ordinal=1086, registered_failure_records=1064,
    pending_ref=pending_ref, counter_reset=False, Main23='QUALIFIED_CURRENT_MAIN23_BUILD',
    current_Main23_programme_qualification_ref=qualification_ref,
    old21='CALLER_SOURCE_INDEPENDENT_REVIEW_FOUND_EMPTY_PENDING_COUNTER_REGRESSION_REPAIR_PENDING_NO_ACTUAL_BUILD',
    old21_runtime_manifest_ref=pin(N / 'old21.runtime-manifest.actual.root.json'),
    old21_runtime_scope_execution_grant=False,
    W09='PROFILE_CM40_AND_THREE_SELECTOR_SOURCE_ACCEPTED_PENDING_ROOT_ADOPTION_NO_ACTUAL_FULL_GROUPS',
    public22='READONLY83_COMPONENT_QUALIFIED_ORIGINAL1025_FAILURE_RETAINED',
    formal_cases_current_accepted=0, formal_cases_required=42, parent_tasks_required=22,
    goal_status='ACTIVE', formal_acceptance=False, parent_acceptance=False,
    prior_resume_ref=pin(N / 'RESUME.cp373-main23-built-pending-review.live1074.root.json')))
handoff = R / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
old = handoff.read_bytes()
archive = N / 'historical.HANDOFF.before-live1086.root.md'
with archive.open('xb') as stream:
    stream.write(old); stream.flush(); os.fsync(stream.fileno())
prefix = ('# Current Root continuation: CP373 / OW177 / CM39 / live next1086\n\n'
    'Main23 current build has five Go exits0, independent programme review and genuine Root qualification binding. '
    'Old21 Source review found a counter-regression boundary; repair precedes actual build. '
    'W09 reviewed Source awaits Root adoption. Goal ACTIVE; formal0/42. Counters and prior work preserved.\n\n'
    'Current resume: ' + resume_ref['path'] + '\nSHA256 ' + resume_ref['sha256'] + ' bytes ' + str(resume_ref['bytes']) + '\n\n'
    'Pending diagnostics: ' + pending_ref['path'] + '\nSHA256 ' + pending_ref['sha256'] + ' bytes ' + str(pending_ref['bytes']) + '\n\n').encode()
with handoff.open('wb') as stream:
    stream.write(prefix + old); stream.flush(); os.fsync(stream.fileno())
assert handoff.read_bytes().endswith(old)
print(json.dumps(dict(resume_ref=resume_ref, pending_ref=pending_ref, pending_rows=len(rows),
    next_original_failure_ordinal=1086, handoff_ref=pin(handoff),
    programme_qualification_ref=qualification_ref, Canonical_unchanged=True), ensure_ascii=False, indent=2))
