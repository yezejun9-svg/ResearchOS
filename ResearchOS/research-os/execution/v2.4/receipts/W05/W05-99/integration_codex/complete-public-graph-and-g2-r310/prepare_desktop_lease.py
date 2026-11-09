import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path.cwd().resolve()
CURRENT = Path(__file__).resolve().parent
OUT = CURRENT.parent / 'desktop-http-exact15-lease-r311'
assert not OUT.exists()
OUT.mkdir()
BASE = ROOT / 'execution/v2.4'
CANON = [BASE / name for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
SOURCE = BASE / 'receipts/W13/W13-03/desktop_http_first_branch_revision_codex/a8e573ecbd20499c8bff9d4222dd9ffc'
REVIEW = BASE / 'receipts/W13/W13-03/desktop_http_first_branch_revision_independent_review_codex/0311803e945b45ab9f8a60c9a7452c01'
WT = ROOT / '.local/worktrees/codex-w1303-desktop-http-r311'
READS = {}


def read(path):
    path = Path(path).resolve()
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def pin(path, expected=None):
    path = Path(path).resolve()
    raw = read(path)
    result = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or result['sha256'] == expected
    return result


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return pin(OUT / name)


def script(name, source):
    ast.parse(source)
    with (OUT / name).open('xb') as stream:
        stream.write(source.encode('utf-8'))
    return pin(OUT / name)


cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [310, 138, 384]
lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = lock['git']['path']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert not WT.exists()
pins = {}
for key, path, expected in [
    ('previous_handoff', CURRENT / 'handoff-r310-running.json', 'c14d7fd45d2663067d2fbff8edfd093c7d0bd96d02117a4feab57fe9f1df6170'),
    ('source_handoff', SOURCE / 'handoff.json', '99c9c3fedaa45eb06845799113b99078d5b2c50627f0f3352a0eadfe6f76c1cf'),
    ('source_proposal', SOURCE / 'proposal.final.json', 'cca6f3f1737a04101af530c0a82553f9580f3f30991243acf05013374de0b348'),
    ('source_scope', SOURCE / 'source_scope.final.json', '5810092eee4dd4fa9c6cf2d0de43b4d997955d62ab6872586b32069da933f1be'),
    ('source_roster', SOURCE / 'finite_roster.expanded.json', '02b24caa6480359c2ee9a6f14ed0b9fb5cd876dc84b4985cf56a114ce0f45a29'),
    ('source_manifest', SOURCE / 'manifest.json', 'fbaaf6247f5a1fde8d37645c224eff02430f5b56dfbe6cb0d21c6c64b74d9a6c'),
    ('scope_review', REVIEW / 'review.json', 'b7902de192aec5185764c8418e5678d7ff9d399da8b572d5ca3cc05958c5a6b9'),
    ('implementation_conditions', REVIEW / 'implementation_conditions.json', '39064e116fee98869eed798974c3e775fd8006bfd0923fa59b3f4bf0c5e07a01'),
    ('protected_spans', REVIEW / 'protected_ranges_audit.json', '0b684318aa0270030c5930e45a5cdaaec884ec1a7d5b7e3d73d2c981b7d2d454')]:
    pins[key] = pin(path, expected)
review = json.loads(read(REVIEW / 'review.json'))
assert review['decision'] == 'SOURCE_SCOPE_READY_WITH_CONDITIONS' and review['product_source_ready'] is False
assert review['future_new_leaves'] == 159 and review['future_regression_units'] == 7
proposal = json.loads(read(SOURCE / 'proposal.final.json'))
supp = proposal['preflight_supplement_ref']
pins['preflight_supplement'] = pin(ROOT / supp['path'], supp['sha256'])
source_scope = json.loads(read(SOURCE / 'source_scope.final.json'))
assert source_scope['exact_paths'] == len(source_scope['paths']) == 15
for row in source_scope['paths']:
    path = ROOT / row['path']
    if row['exists_before']:
        assert pin(path, row['sha256'])['bytes'] == row['bytes']
    else:
        assert not path.exists()
pins['scope'] = save('scope_registration.json', {
    'schema': 'researchos.desktop-http-exact15-source-lease.v1', 'status': 'AUTHORIZED_BY_CAS311_ONLY_NOT_STARTED',
    'owner': 'codex:/root/sources_parent_impl', 'root_integrator': 'codex:/root', 'independent_reviewer': 'codex:/root/command_queue_impl',
    'card': 'W13-03', 'registration_checkpoint': 311, 'project_id': cp['project_id'],
    'base_commit': head, 'worktree': str(WT), 'branch': 'codex/w1303-desktop-http-r311',
    'exact_paths': [row['path'] for row in source_scope['paths']], 'path_bounds_ref': pins['source_scope'],
    'source_proposal_ref': pins['source_proposal'], 'source_roster_ref': pins['source_roster'],
    'scope_review_ref': pins['scope_review'], 'implementation_conditions_ref': pins['implementation_conditions'],
    'protected_spans_ref': pins['protected_spans'], 'preflight_supplement_ref': pins['preflight_supplement'],
    'protocol_precedence': 'Final six-key REQUEST/RESPONSE protocol and supplement; REQUEST fully validated and child reaped before any HTTP POST.',
    'tests': {'new_leaves': 159, 'old_regression_units': 7, 'HTTP_total_maximum': 386,
        'stage_failure_HTTP_expected': 0, 'actual_complete_compiler_graph': '-deps -test -compiled -json plus -work/-x generated/allWORK/archive closure',
        'real_offscreen_renderer_fixtures': 'Exactly two actual Desktop consumers, public loopback fixtures, no installedGUI/NVDA/formal claim.'},
    'authorized_build_outputs': 'New resources/client-wire development tree in own worktree only; unique fresh cache/WORK/exe/descriptor/React assets. Never overwrite running release or Main resources.',
    'receipt_root': str(WT / 'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex'),
    'source_commit_rule': 'Commit only exact15 product paths, receipts separately; no add-dot/reset/clean/old output writes. Protect declared old spans, schema/locks/SDK/API/nativeframe/Web continuity/host-launcher/preload/contextstore.',
    'process_rule': 'Owned child held runtime process handle and actual exit/stdio-close observations. No PID-only termination, no kill-return cleanup proof. Scope insufficiency stops only affected lane with exact amendment proposal.',
    'first_unexpected_stop': True, 'same_input_automatic_retry': False, 'counter_reset': False,
    'maximum_active_construction_tasks': 2, 'Main_product_source_writes': 0,
    'SDK_MODEL_external_paid_private_calls': 0, 'source_acceptance': False, 'Main_integration_authorized': False,
    'formal_increment': 0, 'remaining_gates': 'PublicHost1MiB/request acceptance beyond1MiB, actualattach/cancel/resume completion, nativeframing, browserContinuity, installedpackaging/GUI/NVDA/liveprovider remainHOLD.'})
old_source = (CURRENT / 'register.v2.py').read_text('utf-8')
header = old_source[:old_source.index("pins = prepared['pins']")]
header = header.replace('prepared_refs.v2.json', 'prepared_refs.json').replace('[309, 137, 379]', '[310, 138, 384]')
mutation = '''pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
assert scope['registration_checkpoint'] == 311 and scope['owner'] == 'codex:/root/sources_parent_impl'
assert len(scope['exact_paths']) == 15 and scope['tests']['new_leaves'] == 159 and scope['tests']['old_regression_units'] == 7
assert scope['base_commit'] == head and not Path(scope['worktree']).exists()
review = json.loads(read(pins['scope_review']['path']))
assert review['decision'] == 'SOURCE_SCOPE_READY_WITH_CONDITIONS' and review['product_source_ready'] is False
old_failures = json.loads(before[CANON[0]])['failure_counters']
assert len(old_failures) == 384 and cp['failure_counters'] == old_failures
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(desktop_http_exact15_scope_ref=pins['scope'],
    desktop_http_exact15_scope_review_ref=pins['scope_review'], desktop_http_exact15_state='SOURCE_LEASE_REGISTERED_WORKTREE_CREATION_PENDING',
    desktop_http_exact15_source_writer=scope['owner'], desktop_http_exact15_source_ready=False)
subtasks = ow['card_path_bindings']['W13-03']['subtasks']
assert 'desktop_http_exact15' not in subtasks
subtasks['desktop_http_exact15'] = {'owner': scope['owner'], 'current_source_writer': scope['owner'],
    'worktree': scope['worktree'], 'branch': scope['branch'], 'base_commit': head,
    'paths': scope['exact_paths'], 'scope_ref': pins['scope'], 'independent_scope_review_ref': pins['scope_review'],
    'state': 'SOURCE_LEASE_GRANTED_WORKTREE_CREATION_PENDING', 'source_ready': False,
    'source_acceptance': False, 'Main_product_source_writes': 0, 'formal_increment': 0,
    'historical_overlapping_W13_subtasks': 'Prior scopes remain historical; this unique current exact15 writer is exclusive. Root shared integrator serialized, no other live source writer on these paths.'}
cp['next_command'] = 'W05 CLI17+Windows4/list14/G2prepare scopes running independently. W13 Source exact15 lease registered; Root creates dedicated worktree at2cdb then Source implements final REQUEST/RESPONSE raw validation/lossless IPC/twoDesktop consumers plus159+7 fixtures, no Main/Host/native/Web/formal acceptance. Failure384 unchanged; all22/42 remainopen.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'DESKTOP_HTTP_EXACT15_SOURCE_LEASE_REGISTERED',
    'scope_ref': pins['scope'], 'review_ref': pins['scope_review'], 'audit_ref': pins['audit'],
    'failure_origins_before': 384, 'failure_origins_after': 384, 'counter_reset': False,
    'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=311, expected_previous_revision=310, updated_at=now, updated_by='codex:/root')
ow.update(revision=139, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
'''
tail = old_source[old_source.index('for path, raw in before.items():'):old_source.index("handoff_ref = save('handoff-r310-running.json'")]
tail = tail.replace('root310.tmp', 'root311.tmp').replace('[310, 138, 384]', '[311, 139, 384]').replace('[:379]', '[:384]')
tail = tail.replace('[309, 310]', '[310, 311]').replace('[137, 138]', '[138, 139]').replace('[379, 384]', '[384, 384]')
tail = tail.replace("'checkpoint': 310", "'checkpoint': 311").replace("'ownership': 138", "'ownership': 139").replace('old379_prefix', 'old384_prefix')
tail = tail.replace("'new_CLI17_Windows4_list14_and_G2_prepare_only': True", "'new_Desktop_exact15_source_lease_only': True")
handoff = '''handoff_ref = save('handoff-r311-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 311, 'failure_origins': 384, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'Desktop_scope_ref': pins['scope'], 'Desktop_source_writer': scope['owner'],
    'next': 'Root creates exact dedicated Desktop worktree, then Source implementation begins; ongoing W05 independent scopes retained.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0, 'SDK_MODEL_external_paid_private_calls': 0})
print(json.dumps({'checkpoint': 311, 'ownership': 139, 'failure_origins': 384, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
register = script('register.py', header + mutation + tail + handoff)
wrapper = (CURRENT / 'run.v2.py').read_text('utf-8')
wrapper = wrapper.replace('root_registration_r310_readonly_review_codex', 'root_registration_r311_readonly_review_codex')
wrapper = wrapper.replace('prepared_refs.v2.json', 'prepared_refs.json').replace('register.v2.py', 'register.py').replace('audit.v2.json', 'audit.json')
wrapper = wrapper.replace("review['reviewer'] == 'codex:/root/w05_merge_review'", "review['reviewer'] == 'codex:/root/command_queue_impl'")
wrapper = wrapper.replace("review['expected_before'] == [309, 137, 379] and review['expected_after'] == [310, 138, 384]", "review['expected_before'] == [310, 138, 384] and review['expected_after'] == [311, 139, 384]")
wrapper = wrapper.replace("cp['revision'] == 309 and len(cp['failure_counters']) == 379", "cp['revision'] == 310 and len(cp['failure_counters']) == 384")
wrapped = script('run.py', wrapper)
pins['audit'] = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1',
    'actor': 'codex:/root', 'state': 'DRAFT_PENDING_NONAUTHOR_REVIEW', 'expected_before': [310, 138, 384],
    'expected_after': [311, 139, 384], 'scope_ref': pins['scope'], 'scope_review_ref': pins['scope_review'],
    'counter_delta': 0, 'old384_prefix_unchanged': True, 'formal_increment': 0, 'Main_product_source_writes': 0,
    'ongoing_W05_scopes_unchanged': True, 'existing_source_paths_verified': 9, 'new_absent_paths_verified': 6,
    'scope_acceptance_is_not_source_acceptance': True, 'worktree_creation_after_CAS': True,
    'write_mechanics': 'Original/desired/intent first, allfour metadata HEAD/status guards before each replace; forward-only, no reset/rollback/autoretry.'})
prepared = {'canonical_before': [pin(path) for path in CANON], 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins,
    'verified_refs': [pin(path) for path in READS if path not in CANON], 'actual_source_exports_compile_cases': 0}
prepared_ref = save('prepared_refs.json', prepared)
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'state': 'DESKTOP_LEASE_DRAFT_NOT_EXECUTED', 'register': register, 'wrapper': wrapped,
    'prepared': prepared_ref, 'audit': pins['audit'], 'scope': pins['scope']}, ensure_ascii=True))
