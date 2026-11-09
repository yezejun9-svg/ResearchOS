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
PUBLIC = ROOT / RP / 'provider_typed_route_independent_replay_codex/public-r294-1816149c-d1d2-4998-b76b-2acd0ed57126'
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
assert (cp['revision'], ow['revision'], len(cp['failure_counters'])) == (294, 122, 285)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
status = subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert len([x for x in status.splitlines() if x[:2] == b' D']) == 11
manifest_ref = ref(PUBLIC / 'manifest.json', 'c5a250fdf555ae0426a2e4eb93fb6ced61c7fa48e4daf94d51e57eb89c0db754')
manifest = json.loads((ROOT / manifest_ref['path']).read_bytes())
assert len(manifest['files']) == 405
for row in manifest['files']:
    check(row)
review_ref = ref(PUBLIC / 'review.json', '977ff4f7f0ea8035e2ea15ba1d9b12994ce7649434465083af5099433f500141')
review = json.loads((ROOT / review_ref['path']).read_bytes())
assert review['decision'] == 'EXACT2_REPAIR_SOURCE_READY_WITH_SCHEMA22_PUBLIC_PROOF_AND_DECLARED_OPEN_GATES'
assert review['this_public_cohort']['PASS'] == 12 and review['this_public_cohort']['FAIL'] == review['this_public_cohort']['SKIP'] == 0
assert review['this_public_cohort']['inputs'] == 48381 and not review['this_public_cohort']['drift']
assert review['prior_nonself_internal64']['PASS'] == 64 and review['prior_nonself_internal64']['not_repeated']
assert review['cumulative'] == {'actual': 78, 'PASS': 76, 'FAIL_retained': 2, 'single_executable_PASS_claim': False}
assert not review['whole_original9_SOURCE_READY'] and not review['Main23_verified'] and not review['formal_increment']
for row in review['proof_refs']:
    check(row)
check(review['this_public_cohort']['binary'])
provider_failure_ref = ref(PUBLIC / 'failure_origins.json', '9b4f8b44ff8e4b53fa359b31c3e350503892efa73a4ec99cb1097e259f7b3b19')
provider_failures = json.loads((ROOT / provider_failure_ref['path']).read_bytes())
save('provider-proof-root-audit.json', {'manifest_ref': manifest_ref, 'files_checked': 405, 'all_hashes_match': True,
    'review_ref': review_ref, 'cumulative_actual': 78, 'retained_public_failures': 2,
    'source_acceptance': 'Only exact2 source-ready in schema22 original9 candidate; whole9/Main23/formal not accepted.'})
copies = []
def copy_handler(row):
    rel = Path(row['path'])
    assert not rel.is_absolute() and rel.is_relative_to(HP)
    source = HANDLER / rel
    s = ref(source, row['sha256'])
    raw = source.read_bytes()
    target = ROOT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == raw
    else:
        with target.open('xb') as f:
            f.write(raw)
    got = ref(target)
    copies.append({'source': s, 'copy': got})
    return got

def copy_nested(o):
    if isinstance(o, dict):
        if 'path' in o and 'sha256' in o and str(o['path']).startswith(HP.as_posix() + '/'):
            copy_handler(o)
        else:
            for v in o.values():
                copy_nested(v)
    elif isinstance(o, list):
        for v in o:
            copy_nested(v)

queue_ref = copy_handler({'path': (HP / 'queue-proof-correction-0387b3f68af046dd9350a3af14dae10a/failure_and_correction.json').as_posix(),
    'sha256': '98b79285fa8df5be9e99dec0490a7c689bcfab844455a8eb32dd9991d7b43a11'})
cli_ref = copy_handler({'path': (HP / 'cli-configure-builder-failure-cc2ec04ab59a40f38d7db1d63d87299f/failure_origins.json').as_posix(),
    'sha256': 'c65da8c35dc4bdb443b44d0f398eea50042d9c52e5c947d01fb1e7359d0034a7'})
queue = json.loads((ROOT / queue_ref['path']).read_bytes())
cli = json.loads((ROOT / cli_ref['path']).read_bytes())
copy_nested(queue)
copy_nested(cli)
for doc, fields, exit_code in [(queue, 'failure', 1), (queue, 'new_source_verified', 0), (cli, 'batch_refs', 1)]:
    inv = doc[fields]['command.invocation.json']
    result = doc[fields]['result.json']
    assert json.loads((ROOT / inv['path']).read_bytes())['exit'] == exit_code
    assert json.loads((ROOT / result['path']).read_bytes())['exit'] == exit_code
assert cli['actual_exits'] == {'build': 0, 'batch': 1, 'same_cause_stream_child': 1}
assert cli['one_failed_batch_origin'] and queue['new_actual_batch_origins'] == 1
old = copy.deepcopy(cp['failure_counters'])
new_rows = [
    {'origin_key': 'W05-99/handler-validation/run-4a443382280b4be9bedfc19e1ed5c919:command', 'evidence_ref': queue_ref,
        'detail': {'actual_exit': 1, 'cause': 'New originalSessionTasks misclassified queued STEER/FOLLOW_UP as new Task producer; original7 queue tests passed; onefailedbatch.', 'fixed_distinct_cohort': queue['new_source_verified']['result.json'], 'red_closed_db': 'Not retained; Fatal beforeVACUUM; no fabricated snapshot.'}},
    {'origin_key': 'W05-99/handler-validation/run-96f39204f9694d999c2c4ea4f5e0fdb3:command', 'evidence_ref': cli_ref,
        'detail': {'actual_exit': 1, 'same_cause_child_exit': 1, 'count_once': True, 'events': cli['test_events'], 'cause': cli['diagnosis'], 'actual_model_calls': 0}},
    {'origin_key': 'W05-99/root-read-tool/379d37', 'evidence_ref': None,
        'detail': {'actual_exit': 1, 'chunk': '379d37', 'cause': 'Read guessed Main contracts/execution.plan.json; file absent, before planned scope key read. Actual package plan path is separate; no product/plan mutation.', 'raw_basis': 'Original native tool transcript, no reconstructed byte stream.'}},
    {'origin_key': 'W05-99/root-read-tool/c4df64', 'evidence_ref': None,
        'detail': {'actual_exit': 1, 'chunk': 'c4df64', 'cause': 'rg called absent Main spec/v2.4/contracts paths; frozen spec is in v24-continuation worktree. No product/source mutation.', 'raw_basis': 'Original native tool transcript, no reconstructed byte stream.'}}]
save('new-failure-origin-registration.json', {'origins': new_rows, 'actual_new_unique': 4, 'reset': False})
origin_ref = ref(OUT / 'new-failure-origin-registration.json')
for row in new_rows:
    assert row['origin_key'] not in {x.get('origin_key') for x in cp['failure_counters']}
    row = copy.deepcopy(row)
    if row['evidence_ref'] is None:
        row['evidence_ref'] = origin_ref
    cp['failure_counters'].append(dict(row, attempts=1, retries_used=0, status='ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE',
        count_once=True, counter_reset=False, formal_increment=0))
assert cp['failure_counters'][:285] == old and len(cp['failure_counters']) == 289
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cli_gap = {'schema': 'researchos.root.cli-model-configuration-readonly-gap.v1', 'at': now,
    'actual_successful_source_read_chunks': ['037a48', '0f1671', 'b92259', '2b99e8', 'f2a1fe'],
    'source_refs': [ref(ROOT / p) for p in ['apps/cli/cli_v2.go', 'apps/cli/cli_contract.go', 'apps/cli/cli_verbs.go']],
    'observations': ['v2EnvelopeFor181-193 requires epoch for all host.configure and omits expected_revision.',
        'setModel473-549 requires caller settled flag/record for first default configuration; sends model_id as provider/model label and persists label to c.Model rather than opaque returned model_config_ref.',
        'verbSteps session.create158 consumes cfg.Model as model_config_ref; no separate opaque reference is currently stored.',
        'newV2Context191-219 keeps Host discovery baseURL; no observed providerURL-to-HostURL override claim.'],
    'required_next': 'Author read-only exact minimal product/test scope proposal for default4null/scoped4nonnull configure, validrevision/model-ID and typed response/globalidentity, originallocal claims versus authoritativeHost settlement, actualopaqueRef usage innewSession; nonauthor scope review and Root registration before source outside33.',
    'scope': 'Readonly proposal only. Current exact33 fixture direct rawHTTP→Decode/Execute remains separately authorized; not productCLI/defaultUX acceptance.',
    'implementation_authorized': False, 'formal_increment': 0}
save('cli-configuration-product-gap.json', cli_gap)
cli_gap_ref = ref(OUT / 'cli-configuration-product-gap.json')
save('handler-public-copy-audit.json', {'copies': copies, 'count': len(copies), 'Main_product_source_writes': 0})
for p, raw in before.items():
    with (OUT / (p.stem + '.original.json')).open('xb') as f:
        f.write(raw)
provider = ow['card_path_bindings']['W05-99']['subtasks']['provider_typed_route_independent_replay']
provider.update(state='EXACT2_SOURCE_READY_SCHEMA22_PUBLIC12_COMPLETE_WHOLE9_MAIN23_OPEN',
    current_review_ref=review_ref, public12_pass=12, internal64_pass_retained=64,
    cumulative_actual=78, retained_failed_public_controls=2, public_controls_remaining=0,
    source_ready_paths=review['source_acceptance_scope'], whole9_source_ready=False, Main23_accepted=False)
cp['work_in_progress'].update(provider_independent_public12_completed_review_ref=review_ref,
    provider_independent_exact2_source_ready=True, provider_independent_whole9_source_ready=False,
    configuration_handler_queue_proof_correction_ref=queue_ref, configuration_handler_cli_builder_failure_ref=cli_ref,
    configuration_cli_product_readonly_gap_ref=cli_gap_ref,
    pending_actual_failure_imports=['F08 author closed-contract revision tools includingde02b4, awaiting sealed exact refs; currenthandler newCLI fixture cohort executing'],
    next_action='Complete exact33 actualHTTP/SDK fixtures and finalsource matrix; readonly productCLI configuration/opaqueRef gap proposal before further source ownership. Provider exact2 has independent64+12source22 evidence; whole9 gapmapping only then Root decides currentMain23 proof. F08 revised20 design sourceonly/noSQL24lease beforehandlerfreeze and whole revised contract acceptance.')
cp['open_obligations_before_next_card'].append({'kind': 'CLI_CONFIGURATION_DEFAULT_AND_SCOPED_PUBLIC_CONTRACT', 'status': 'OPEN_READONLY_SCOPE_PROPOSAL',
    'evidence_ref': cli_gap_ref, 'blocks': 'W05-99 completeCLI/formalacceptance', 'resource_branch_only': True})
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'PROVIDER_EXACT2_PUBLIC12_COMPLETE_AND_CLI_PRODUCT_GAP_REGISTERED',
    'review_ref': review_ref, 'cli_gap_ref': cli_gap_ref, 'failure_origins_before': 285, 'failure_origins_after': 289,
    'whole9_Main23_formal_increment': 0})
cp.update(revision=295, expected_previous_revision=294, head=head, updated_at=now, updated_by='codex:/root')
ow.update(revision=123, amended_at=now, amended_by='codex:/root')
for row in [manifest_ref, review_ref, provider_failure_ref, queue_ref, cli_ref, cli_gap_ref, origin_ref]:
    if row['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(row['path'])
save('record.json', {'checkpoint': [294, 295], 'ownership': [122, 123], 'failure_origins': [285, 289],
    'provider_internal_pass': 64, 'provider_public_pass': 12, 'provider_public_failures_retained': 2,
    'source_ready_scope': 'exact2 only schema22', 'Main_product_source_writes': 0, 'formal_increment': 0})
assert all(p.read_bytes() == raw for p, raw in before.items())
assert subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
for p, value in zip(CANON[:2], [cp, ow]):
    temp = p.with_name(p.name + '.root295.tmp')
    with temp.open('xb') as f:
        f.write(encode(value))
    assert p.read_bytes() == before[p]
    os.replace(temp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({'checkpoint': 295, 'ownership': 123, 'failure_origins': 289,
    'provider_exact2_review_ref': review_ref, 'cli_gap_ref': cli_gap_ref,
    'Main_product_source_writes': 0, 'formal_increment': 0}, ensure_ascii=True))
