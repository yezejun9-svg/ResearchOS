import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os').resolve()
OUT = Path(__file__).resolve().parent
WT = ROOT / '.local/worktrees/codex-w0599-provider-binding'
BASE = 'execution/v2.4/receipts/W05/W05-99/'
REVIEW = BASE + 'provider_typed_route_independent_review_codex/4a4322c2-c21d-4327-b54f-6c99584b1776/'
AUTHOR = BASE + 'provider_binding_executor_codex/typed-route-final-6c47a88a198349b4bd2a3d3d223510b1/'
ALLOWED_AUTHOR = [AUTHOR, BASE + 'provider_binding_executor_codex/typed-route-5188793d240a4f1197f92bbc510ad9e1/']
MAIN_HEAD = '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
CANDIDATE = '6fb5263681c17f0e50920c354dc07ed440a23714'
CANON = [ROOT / ('execution/v2.4/' + n) for n in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
GIT = 'C:/Program Files/Git/cmd/git.exe'


def enc(o):
    return (json.dumps(o, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def save(name, value):
    with (OUT / name).open('xb') as f:
        f.write(enc(value))


def ref(path, expected=None):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    b = p.read_bytes()
    digest = hashlib.sha256(b).hexdigest()
    if expected:
        assert digest == expected, str(p)
    label = p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p)
    return {'path': label, 'sha256': digest, 'bytes': len(b)}


def check_absolute(item):
    actual = ref(item['path'])
    assert actual['sha256'] == item['sha256'] and actual['bytes'] == item['bytes'], item['path']


before = {p: p.read_bytes() for p in CANON}
cp, ownership = [json.loads(before[p]) for p in CANON[:2]]
assert (cp['revision'], ownership['revision'], len(cp['failure_counters'])) == (287, 115, 250)
assert subprocess.check_output([GIT, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == MAIN_HEAD
assert subprocess.check_output([GIT, 'rev-parse', 'HEAD'], cwd=WT).decode().strip() == CANDIDATE
assert not subprocess.check_output([GIT, 'status', '--short', '--untracked-files=no'], cwd=WT)
review_ref = ref(REVIEW + 'source_review.final.json', 'b9825a70fc99573ae9c10704ab06a8cfca1244a834b73e4557223a3e7d99a8d3')
proposal_ref = ref(REVIEW + 'execution_scope_proposal.final.json', 'af0e1ed0fe1c8b4722ea11ff6ec9f96ba1d2ddfec33b0eab3b9775e0e590eaca')
resource_ref = ref(REVIEW + 'public_resource_chain_supplement.final.json', '1209871436d2eca23b94559aeba390728eb0148430eb5fc08dab120983b32e63')
review_manifest_ref = ref(REVIEW + 'manifest.final.json', '30dc432be7f5d842eb6bf620637e6270fec76bb1fe672d9d3688b1fb7604a7a9')
for item in json.loads((ROOT / review_manifest_ref['path']).read_bytes())['files']:
    check_absolute(item)
proposal = json.loads((ROOT / proposal_ref['path']).read_bytes())
review = json.loads((ROOT / review_ref['path']).read_bytes())
assert proposal['maximum_cases'] == 76 and proposal['candidate'] == CANDIDATE
assert [s['maximum'] for s in proposal['stages']] == [64, 6, 6]
assert review['decision'] == 'STATIC_SOURCE_REVIEW_COMPLETE_REPLAY_SCOPE_READY_PENDING_ROOT_CAS' and not review['source_acceptance']
for row in proposal['source9']:
    check_absolute(row['actual'])
for row in proposal['original7_inputs']:
    check_absolute(row['original'])
    check_absolute(row['author_copy'])
author_handoff_ref = ref(WT / AUTHOR / 'handoff.json', '9db2ae92768dca695ac4c882220b6e30953612e378ee58d0f828a19766bada8d')
author_manifest_ref = ref(WT / AUTHOR / 'manifest.json', 'd72657266613d9f68f25f36cc2968cb231a161963d5040869d8cc12213403df3')
author_handoff = json.loads((ROOT / author_handoff_ref['path']).read_bytes())
assert (author_handoff['actual_tests'], author_handoff['pass'], author_handoff['fail'], author_handoff['skip']) == (64, 64, 0, 0)
closure_ref = ref(BASE + 'integration_codex/provider-author-closure-r287/closure.json', 'cff73f4e3af4b6cafac5dd9c615e31e8e980cda8353abbecd9f612fa92c75482')
supplement_ref = ref(BASE + 'integration_codex/provider-public-source-supplement-r287/supplement.json', '086a55f36a3c0fc1688525e44dfdf199056cb55498034bd1f6e3397980fec137')
supplement = json.loads((ROOT / supplement_ref['path']).read_bytes())
assert supplement['complete_inputs_checked'] == 20693 and not supplement['source_acceptance']
assert json.loads((ROOT / (BASE + 'integration_codex/provider-public-source-supplement-r287/verify.invocation.json')).read_bytes())['actual_exit'] == 0

# Copy only the two explicitly reviewed public namespaces, with exclusive creation.
manifest = json.loads((ROOT / author_manifest_ref['path']).read_bytes())
copy_rows = copy.deepcopy(manifest['files'])
copy_rows.append({'path': AUTHOR + 'manifest.json', 'sha256': author_manifest_ref['sha256'], 'bytes': author_manifest_ref['bytes']})
assert len(copy_rows) == 654
copied = []
for row in copy_rows:
    rel = row['path'].replace('\\', '/')
    assert any(rel.startswith(prefix) for prefix in ALLOWED_AUTHOR)
    source = (WT / rel).resolve()
    target = (ROOT / rel).resolve()
    assert source.is_relative_to(WT.resolve()) and target.is_relative_to(ROOT)
    b = source.read_bytes()
    assert hashlib.sha256(b).hexdigest() == row['sha256'] and len(b) == row['bytes']
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == b
    else:
        with target.open('xb') as f:
            f.write(b)
    assert ref(target)['sha256'] == row['sha256']
    copied.append({'source': str(source), 'target': target.relative_to(ROOT).as_posix(), 'sha256': row['sha256'], 'bytes': row['bytes']})
save('author-public-copy-audit.json', {'files': copied, 'count': len(copied), 'private_resources': 0, 'source_writes': 0})

recovery_refs = [ref(BASE + 'integration_codex/provider-zero-model-recovery-r275/scope_registration.json', '20a3800192d178e41ee7f4985f5fbbc7816b73189d74964198f2d7e355344ecd'),
                 ref(BASE + 'integration_codex/configuration-test-and-p12-resource-r276/p12_resource_scope_registration.json', '859dd7ddd949b00aebaac059f80610c1e1d00281cccc26ed5677d764e58a2deb')]
public_compile_files = []
for item in recovery_refs:
    data = json.loads((ROOT / item['path']).read_bytes())
    public_compile_files += copy.deepcopy(data.get('recovery_files', data.get('allowed_files', [])))
assert len(public_compile_files) == 12
for row in public_compile_files:
    actual = ref(WT / row['path'])
    assert actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes']
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
scope = {'schema': 'researchos.root.provider-typed-route-independent-execution-scope.v1', 'actor': 'codex:/root',
         'executor_verifier': 'codex:/root/w05_merge_review', 'source_author': 'codex:/root/command_queue_impl',
         'at': now, 'card': 'W05-99', 'main_head': MAIN_HEAD, 'candidate_head': CANDIDATE,
         'proposal_ref': proposal_ref, 'static_source_review_ref': review_ref,
         'mandatory_public_resource_chain_ref': resource_ref,
         'author_handoff_ref': author_handoff_ref, 'root_author_closure_ref': closure_ref,
         'root_public_source_supplement_ref': supplement_ref,
         'execution_authorized_now': True, 'maximum_controls': 76,
         'stages': proposal['stages'], 'source9': proposal['source9'], 'original7_inputs': proposal['original7_inputs'],
         'isolated_build_scope': proposal['isolated_build_scope'], 'synthetic_workspace_boundary': proposal['synthetic_workspace_boundary'],
         'new_isolated_checkout': '.local/independent-provider-typed-route-r288-d4fd01da69224e05a135e0b01794826c',
         'public_compile_files_explicit': public_compile_files,
         'public_compile_files_basis': recovery_refs,
         'export_policy': 'Enumerate candidate immutable Git public source/compiler/test/numberedSQL/contracts only, record exact exported paths/blobs before compile. The explicitly listed12 public Go dependencies are allowed. No generated formal holdout/private state or external workspace. Existing public generator source compile is allowed, but executing generator/test/DPAPI is not. Frozen public v2.4 contract package is read-only. Do not add Main SQL23 or silently restore extra missing files; stop for exact resource amendment if necessary.',
         'dataset_resource': 'No dataset instance or new fixture restored by this registration. Public development data not needed by these anchored selectors; unexpected dependency stops precompile.',
         'public_overlay': 'One review-owned independent_provider_public_boundary_windows_test.go with explicit go -overlay; production exact9 and original SQL/SDK unchanged. Fully frozen overlay/driver/specs before first case.',
         'first_unexpected_stop': proposal['first_unexpected_stop'], 'not_authorized': proposal['not_authorized'],
         'effects': {'model': 0, 'provider': 0, 'paid': 0, 'HTTP': 0, 'Node': 0, 'SDK_worker': 0, 'private_resource_reads': 0},
         'history': copy.deepcopy(proposal['historical_chain']), 'protected_shared_protocol_writer': 'sources_parent_impl handler27 single writer, no interference',
         'source_acceptance': False, 'formal_increment': 0,
         'credit_boundary': 'Independent new bounded execution can establish exact2 repair/public source22 consumer evidence only. No historical held chain qualification, no original9 whole SOURCE_READY, no LIVE/Main23/full42 credit.'}
assert not (ROOT / scope['new_isolated_checkout']).exists()
save('scope_registration.json', scope)
scope_ref = ref(OUT / 'scope_registration.json')

for p, b in before.items():
    with (OUT / (p.stem + '.original.json')).open('xb') as f:
        f.write(b)
old_failures = copy.deepcopy(cp['failure_counters'])
failed_inv = ref(BASE + 'integration_codex/provider-author-closure-r287/verify.invocation.json')
assert json.loads((ROOT / failed_inv['path']).read_bytes())['actual_exit'] == 1
key = 'W05-99/Root/provider-public-input-classification/' + failed_inv['sha256']
assert key not in {f.get('origin_key') for f in old_failures}
cp['failure_counters'].append({'origin_key': key, 'attempts': 1, 'retries_used': 0,
    'status': 'ACTUAL_READONLY_CLOSURE_CHECKER_EXIT1_PUBLIC_GIT_SOURCE_PATH_MISCLASSIFICATION',
    'evidence_ref': failed_inv, 'detail_ref': closure_ref, 'correction_ref': supplement_ref,
    'product_test_failure': False, 'counter_reset': False, 'formal_increment': 0})
assert cp['failure_counters'][:250] == old_failures and len(cp['failure_counters']) == 251
diagnostic_ref = ref(REVIEW + 'failure_origins.json', '20b193e9e80e0c614fbd5dbc43a1dcb2e23754e66eb44ecf2dbb91dcc3e30f57')
for d in json.loads((ROOT / diagnostic_ref['path']).read_bytes())['origins']:
    assert d['outer_exit'] == 0
    cp.setdefault('preserved_unindexed_tool_diagnostics', []).append({'evidence_ref': diagnostic_ref, 'detail': d,
          'reason': 'Actual outer0 read-only diagnostics preserved; no fabricated exit1 or product failure.'})
subtasks = ownership['card_path_bindings']['W05-99']['subtasks']
subtasks['provider_transport_reasoning_binding'].update(current_source_writer=False,
    state='FROZEN_EXACT2_TYPED_ROUTE_AUTHOR64_PUBLIC_CLOSURE_REVIEWED_PENDING_NONSELF76',
    candidate_head=CANDIDATE, typed_route_author_handoff_ref=author_handoff_ref,
    independent_static_review_ref=review_ref, independent_execution_scope_ref=scope_ref)
subtasks['provider_typed_route_independent_replay'] = {'owner': 'codex:/root/w05_merge_review',
    'source_author': 'codex:/root/command_queue_impl', 'root': 'codex:/root',
    'state': 'NONAUTHOR76_ZERO_MODEL_PUBLIC_CONSUMER_REPLAY_AUTHORIZED', 'scope_ref': scope_ref,
    'candidate_head': CANDIDATE, 'worktree': scope['new_isolated_checkout'], 'current_source_writer': False,
    'production_source_writes': 0, 'overlay_owned': 'independent_provider_public_boundary_windows_test.go',
    'receipt_namespace': BASE + 'provider_typed_route_independent_replay_codex/**', 'maximum_controls': 76}
cp['failure_chains']['W05-99/P9-P12-SR01'].update(status='THREE_FAILURES_PRESERVED_AUTHOR64_PASS_PENDING_NONSELF76',
    author64_handoff_ref=author_handoff_ref, independent_execution_scope_ref=scope_ref,
    author_source_repair_attempts=3, actual_failed_invocations=3)
cp['work_in_progress'].update(provider_typed_route_author_handoff_ref=author_handoff_ref,
    provider_typed_route_author_closure_ref=supplement_ref,
    provider_typed_route_independent_static_review_ref=review_ref,
    provider_typed_route_independent_execution_scope_ref=scope_ref,
    provider_typed_route_scope_state='AUTHOR_SOURCE2_FROZEN_NONSELF76_AUTHORIZED_NO_ACCEPTANCE',
    next_action='Implement handler27 in isolated WT; independently execute provider64+6public+6public-negative under sealed scope. F08 readonly design only until handler shared lease release. No old retry/reset or formal credit.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'PROVIDER_AUTHOR64_PUBLIC_CLOSURE_AND_NONSELF76_SCOPE_REGISTERED',
    'scope_ref': scope_ref, 'review_ref': review_ref, 'copied_public_files': len(copied),
    'complete_author_inputs': 20693, 'failure_origins': [250, 251], 'formal_increment': 0})
cp.update(revision=288, expected_previous_revision=287, head=MAIN_HEAD, updated_at=now, updated_by='codex:/root')
ownership.update(revision=116, amended_at=now, amended_by='codex:/root')
for item in [scope_ref, review_ref, proposal_ref, resource_ref, review_manifest_ref, diagnostic_ref, author_handoff_ref, author_manifest_ref, closure_ref, supplement_ref, failed_inv]:
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
save('record.json', {'checkpoint': [287, 288], 'ownership': [115, 116], 'failure_origins': [250, 251],
    'author_public_files_copied': len(copied), 'author_inputs_checked': 20693,
    'independent_max_controls': 76, 'scope_ref': scope_ref, 'formal_increment': 0})
assert all(p.read_bytes() == b for p, b in before.items())
for p, value in zip(CANON[:2], [cp, ownership]):
    tmp = p.with_name(p.name + '.root288.tmp')
    with tmp.open('xb') as f:
        f.write(enc(value))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({'checkpoint': 288, 'ownership': 116, 'failure_origins': 251, 'public_files_copied': len(copied),
    'scope_ref': scope_ref, 'nonself_controls': 76, 'formal_increment': 0}, ensure_ascii=True))
