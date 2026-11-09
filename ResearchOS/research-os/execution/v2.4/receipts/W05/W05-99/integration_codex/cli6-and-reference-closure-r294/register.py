import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
RP = Path('execution/v2.4/receipts/W05/W05-99')
HANDLER = ROOT / '.local/worktrees/codex-w0599-host-configuration-handler'
HP = RP / 'host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec'
REVIEW = ROOT / RP / 'handler_cli_fixture_scope_independent_review_codex/5f6e202c-f8e9-408d-8612-543d813b8309'
PUBLIC = ROOT / RP / 'provider_typed_route_independent_replay_codex/79e9ab97-1451-4537-94db-e8259c9c67fa'
CANON = [BASE / n for n in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]

def encode(o):
    return (json.dumps(o, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')

def save(n, o):
    with (OUT / n).open('xb') as f:
        f.write(encode(o))

def ref(p, expected=None):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    assert p.is_relative_to(ROOT), str(p)
    raw = p.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if expected:
        assert sha == expected, str(p)
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha, 'bytes': len(raw)}

def check(row):
    got = ref(row['path'], row['sha256'])
    if 'bytes' in row:
        assert got['bytes'] == row['bytes']
    return got

before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert (cp['revision'], ow['revision'], len(cp['failure_counters'])) == (293, 121, 283)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
status = subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert len([x for x in status.splitlines() if x[:2] == b' D']) == 11
assert not any(x[:1] not in [b' ', b'?'] for x in status.splitlines())
manifest_ref = ref(REVIEW / 'manifest.json', '3d4f25cb7b3f6de2326691b52abad16a66c2e1c45bb550e6895879591159ffa6')
manifest = json.loads((ROOT / manifest_ref['path']).read_bytes())
assert len(manifest['files']) == 29
for row in manifest['files']:
    check(row)
review_ref = ref(REVIEW / 'scope_review.json', 'c79dcd94aa72fcf9d5b0dc03d3a70a06e5b116ba948d56c6b7347f4b1193f99d')
review = json.loads((ROOT / review_ref['path']).read_bytes())
assert review['decision'] == 'SOURCE_SCOPE_READY_CONDITIONAL_EXACT6_TEST_ONLY'
assert review['total_design_source_paths'] == 33 and review['source_accepted'] is False
proposal_source_ref = check(review['proposal'])
proposal = json.loads((ROOT / proposal_source_ref['path']).read_bytes())
proposal_rel = HP / 'cli-fixture-scope-5e5a201d4cd64f31a1d056aebbce8429/proposal.json'
assert (HANDLER / proposal_rel).resolve() == (ROOT / proposal_source_ref['path']).resolve()
target = ROOT / proposal_rel
target.parent.mkdir(parents=True, exist_ok=True)
raw = (HANDLER / proposal_rel).read_bytes()
if target.exists():
    assert target.read_bytes() == raw
else:
    with target.open('xb') as f:
        f.write(raw)
proposal_ref = ref(target, '48b72473b5e9b181bbce73b8d74a842282f35284cbd02f8db75c35b7110da1ef')
sub = ow['card_path_bindings']['W05-99']['subtasks']['host_configuration_public_handlers']
assert len(sub['paths']) == 27
new_paths = []
for row in review['exact_additional_paths']:
    check(row['before'])
    assert (ROOT / row['before']['path']).resolve() == (HANDLER / row['path']).resolve()
    assert row['path'].endswith('_test.go') and row['path'] not in sub['paths']
    original = next(x for x in proposal['entries'] if x['path'] == row['path'])
    git_bytes = subprocess.check_output(['git', 'show', head + ':' + row['path']], cwd=HANDLER)
    assert hashlib.sha256(git_bytes).hexdigest() == original['head_sha256'] == row['before']['sha256']
    new_paths.append(row['path'])
assert len(new_paths) == len(set(new_paths)) == 6
protected_stream = ref(HANDLER / 'apps/cli/cli_stream_test.go')
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cli_amendment = {'schema': 'researchos.root.handler-exact33-cli-fixture-amendment.v1', 'at': now,
    'actor': 'codex:/root', 'executor': 'codex:/root/sources_parent_impl',
    'original_scope_ref': sub['scope_ref'], 'proposal_ref': proposal_ref, 'independent_scope_review_ref': review_ref,
    'exact_additional_paths': review['exact_additional_paths'], 'mandatory_conditions': review['mandatory_conditions'],
    'specific_bound_corrections': review['specific_proposal_bound_corrections'],
    'protected_cli_stream_test_ref': protected_stream, 'effective_source_paths': sub['paths'] + new_paths,
    'effective_source_path_count': 33, 'authorized': True, 'production_paths_added': [],
    'full_cli_runner': 'Distinct closed cohort native480s / outer600s. Original180s incomplete failure remains. Do not silently rerun identical inputs or hide protected failures.',
    'actual_sdk_count': 'Per exact child process declare qualifier/ordinary loopback calls; FIXTURE only, external/paid/private0.',
    'source_accepted': False, 'formal_increment': 0}
save('cli6_scope_amendment.json', cli_amendment)
cli_amendment_ref = ref(OUT / 'cli6_scope_amendment.json')

public_proposal_ref = ref(PUBLIC / 'public-overlay-relation-correction-proposal.json', 'bc596426bb61387d6db4f9408596803e51f22103fc7c0f2638317849e2f30037')
public_proposal = json.loads((ROOT / public_proposal_ref['path']).read_bytes())
for k in ['original_overlay', 'production_source', 'causal_evidence']:
    check(public_proposal[k])
assert public_proposal['public_retry_request_if_authorized']['total_new_cases'] == 12
assert public_proposal['public_retry_request_if_authorized']['cumulative_if_all12_executed'] == 78
public_amendment = {'schema': 'researchos.root.provider-public12-reference-closure-amendment.v1', 'at': now,
    'actor': 'codex:/root', 'executor': 'codex:/root/w05_merge_review', 'proposal_ref': public_proposal_ref,
    'original_execution_scope_ref': cp['work_in_progress']['provider_typed_route_independent_execution_scope_ref'],
    'previous_public12_amendment_ref': cp['work_in_progress']['provider_independent_public12_amendment_ref'],
    'root_actual_primary_source_check': {'chunks': ['de9839', '94ee82', 'd7f1cb'], 'actual_exit_each': 0,
        'source_ref': public_proposal['production_source'],
        'lines': 'store.go235-300 recursive refs,171-180 relationKind,302-339 exact target/history validation and row insertion; terminal relation arrays share one path per member.'},
    'exact_edit': 'Only domain_refs branch within new owned independentRestoreDelta copy, including local nested expected-reference closures; no other helper, assertion, product or original overlay changes except gofmt.',
    'required_rules': public_proposal['required_rule'],
    'independent_expected_generation': 'Use explicitly frozen producer semantics and previously validated exact appended versions/event order. Do not call production refs/ref/put/validator as acceptance oracle. Compare complete reference multiset excluding nondeterministic insertion rowid; separately require original typed rows/rowids unchanged, new rowid uniqueness and exact append count. VersionRef ID/kind/revision/content_hash and real target immutable row match; scalar targets use producer-time version. Parent_policy cross-project and owner special cases retain actual semantics if reached, no generic whitelist/contains bypass.',
    'new_public_budget': 12, 'positive_order': [1, 0, 2, 3, 4, 5], 'negative_count': 6,
    'retained_internal_pass': 64, 'retained_failed_public': 2, 'cumulative_actual_before': 66, 'cumulative_planned_after': 78,
    'cohort_rule': 'New overlay/compiler/exe/complete before+after+current closure, old64 and both stopped public inputs/raw retained. Different exe/cohorts explicit; no claim78PASS or76PASS single executable.',
    'first_unexpected_stop': True, 'automatic_additional_edit_or_retry_authorized': False,
    'source9_original7_SQL_changes': 0, 'Node_MODEL_HTTP_paid_private_calls': 0,
    'source2_accepted': False, 'whole9_accepted': False, 'Main23_accepted': False, 'formal_increment': 0,
    'authorized': True}
save('public12_reference_scope_amendment.json', public_amendment)
public_amendment_ref = ref(OUT / 'public12_reference_scope_amendment.json')
old = copy.deepcopy(cp['failure_counters'])
origins = [
    {'origin_key': 'W05-99/handler-read-tool/3f47e5', 'detail': proposal['tool_diagnostic'], 'evidence_ref': proposal_ref},
    {'origin_key': 'W05-99/root-read-tool/1c8b1b', 'detail': {'chunk': '1c8b1b', 'actual_exit': 1,
        'cause': 'rg --files against existing but not-yet-populated reviewer namespace returned no paths. Receipt appeared later; no product/source mutation.',
        'raw_basis': 'Actual original tool transcript, not reconstructed byte stream.'}, 'evidence_ref': review_ref}]
for row in origins:
    assert row['origin_key'] not in {x.get('origin_key') for x in cp['failure_counters']}
    cp['failure_counters'].append(dict(row, attempts=1, retries_used=0, status='ACTUAL_READ_TOOL_NONZERO_NO_PRODUCT_CASE',
        count_once=True, counter_reset=False, formal_increment=0))
assert cp['failure_counters'][:283] == old and len(cp['failure_counters']) == 285
for p, raw in before.items():
    with (OUT / (p.stem + '.original.json')).open('xb') as f:
        f.write(raw)
sub['paths'] += new_paths
sub.update(state='EXACT33_HANDLER_AND_PRECISE_CLI_TEST_FIXTURE_IMPLEMENTATION_AUTHORIZED', cli6_amendment_ref=cli_amendment_ref)
provider = ow['card_path_bindings']['W05-99']['subtasks']['provider_typed_route_independent_replay']
provider.update(state='PUBLIC12_EXACT_FULL_REFERENCE_CLOSURE_CORRECTION_AUTHORIZED_TWO_FAILURES_RETAINED',
    public_reference_amendment_ref=public_amendment_ref, maximum_controls=78,
    completed_internal_controls=64, retained_failed_public_controls=2, public_controls_remaining=12,
    maximum_controls_meaning='64 old internalPASS plus2 retained public failures plus12 new public invocations; separate executables/cohorts, not78 successful controls.')
cp['work_in_progress'].update(configuration_handler_cli6_scope_amendment_ref=cli_amendment_ref,
    provider_independent_public_reference_amendment_ref=public_amendment_ref,
    pending_actual_failure_imports=['F08 author revision locator toolde02b4 awaiting sealed import; new handler queued-command counterexample currently executing'],
    next_action='Complete exact33 handler fixtures/current causal tests/sourcefreeze; execute separately authorized provider public12 with full relation-reference closure, retain64PASS+2fail. Independently review complete handler source/current matrix before Main integration. F08 closed contract remains readonly pending handler freeze and whole revised design acceptance.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'EXACT33_CLI_FIXTURE_SCOPE_AND_PROVIDER_REFERENCE_CLOSURE_PUBLIC12_AUTHORIZED',
    'cli_amendment_ref': cli_amendment_ref, 'provider_amendment_ref': public_amendment_ref,
    'failure_origins_before': 283, 'failure_origins_after': 285, 'formal_increment': 0})
cp.update(revision=294, expected_previous_revision=293, head=head, updated_at=now, updated_by='codex:/root')
ow.update(revision=122, amended_at=now, amended_by='codex:/root')
for row in [cli_amendment_ref, review_ref, manifest_ref, proposal_ref, public_amendment_ref, public_proposal_ref]:
    if row['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(row['path'])
save('record.json', {'checkpoint': [293, 294], 'ownership': [121, 122], 'failure_origins': [283, 285],
    'handler_source_paths': [27, 33], 'provider_cumulative_budget': 78, 'Main_product_source_writes': 0, 'formal_increment': 0})
assert all(p.read_bytes() == raw for p, raw in before.items())
assert subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
for row in review['exact_additional_paths']:
    check(row['before'])
assert ref(HANDLER / 'apps/cli/cli_stream_test.go') == protected_stream
for p, value in zip(CANON[:2], [cp, ow]):
    temp = p.with_name(p.name + '.root294.tmp')
    with temp.open('xb') as f:
        f.write(encode(value))
    assert p.read_bytes() == before[p]
    os.replace(temp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({'checkpoint': 294, 'ownership': 122, 'failure_origins': 285,
    'cli6_amendment_ref': cli_amendment_ref, 'provider_reference_amendment_ref': public_amendment_ref,
    'Main_product_source_writes': 0, 'formal_increment': 0}, ensure_ascii=True))
