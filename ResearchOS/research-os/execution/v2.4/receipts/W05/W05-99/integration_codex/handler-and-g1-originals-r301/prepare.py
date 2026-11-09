import hashlib
import json
from pathlib import Path
import re
import sys

if sys.flags.optimize != 0:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
AUTHOR = ROOT / '.local/worktrees/codex-w0599-host-configuration-handler'
PUBLIC = Path('execution/v2.4/receipts/W05/W05-99')
HANDLER = PUBLIC / 'host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec'
READS = {}


def read(path):
    path = Path(path).resolve()
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def ref(path, expected=None):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    raw = read(path)
    sha = hashlib.sha256(raw).hexdigest()
    assert expected is None or sha == expected, str(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha, 'bytes': len(raw)}


def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return ref(OUT / name)


copies = []


def publish(relative, expected):
    relative = Path(relative)
    assert not relative.is_absolute() and relative.is_relative_to(HANDLER)
    source = AUTHOR / relative
    raw = read(source)
    assert hashlib.sha256(raw).hexdigest() == expected
    target = ROOT / relative
    if target.exists():
        assert read(target) == raw
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
    result = ref(target, expected)
    copies.append(result)
    return result


numeric_ref = publish(HANDLER / 'numeric-c09-cohort-2f04515cfc9e4693b39b67bc94dad8d9/cohorts.json', '22aac98b587f74848ea205e3e2bb86e35dd99ddfdcb79029424223ddcbd08d40')
whole_ref = publish(HANDLER / 'whole-cli-failure-fa4c692c4bb342e1af99ad2e860c9996/failure_origin.json', '6433cc6c93285cd2a3fed0093467a646264850be6782f21877718fedc6e524ef')
completion_ref = publish(HANDLER / 'commit-completion-2ea72c8b670a40b18f98c1521dbf82fd/completion.json', '1bdf6b1dc81bb27011f4c8d5916e1426a220bb746ff37e78d0d1dc5bde0dcbd0')
numeric = json.loads(read(ROOT / numeric_ref['path']))
whole = json.loads(read(ROOT / whole_ref['path']))
completion = json.loads(read(ROOT / completion_ref['path']))
origins = []
for batch, expected_events, evidence_ref, cause in [
    (numeric['cohorts'][0], {'pass': 59, 'fail': 1, 'skip': 0}, numeric_ref, numeric['new_failure_cause']),
    (whole, {'pass': 282, 'fail': 12, 'skip': 0}, whole_ref, whole['causes']),
]:
    for row in batch['refs'] + batch['closed_db_refs']:
        publish(row['path'], row['sha256'])
    records = {Path(row['path']).name: row for row in batch['refs']}
    actual = json.loads(read(ROOT / records['result.json']['path']))
    invocation = json.loads(read(ROOT / records['command.invocation.json']['path']))
    assert actual == batch['result']
    assert actual['exit'] == invocation['exit'] == 1
    assert actual['test_events'] == expected_events and actual['input_count'] == 39071 and not actual['source_drift']
    assert read(ROOT / records['source.before.json']['path']) == read(ROOT / records['source.after.json']['path'])
    events = [json.loads(line) for line in read(ROOT / records['command.stdout']['path']).splitlines() if line]
    counts = {action: sum(event.get('Action') == action and 'Test' in event for event in events) for action in ['pass', 'fail', 'skip']}
    assert counts == expected_events, counts
    origins.append({'origin_key': 'W05-99/handler-final-originals/' + batch.get('run', batch.get('batch_origin')), 'evidence_ref': evidence_ref,
                    'detail': {'actual_exit': 1, 'test_events': counts, 'cause': cause, 'result_ref': records['result.json'], 'count_once_per_batch': True}})

late = completion['late_diagnostic_origin']
assert late['tool_chunk'] == '24e185' and late['actual_outer_exit'] == 1
origins.append({'origin_key': 'W05-99/handler-final-originals/tool-24e185', 'evidence_ref': completion_ref, 'detail': late})
review_failure_ref = ref(ROOT / PUBLIC / 'handler38_final_source_review_codex/a639cfcf998f4c7fb182db19c6788c3b/failure_origins.json', '252f6b70445676d0246a6e547ca11b2f30410fc37f98ef27d727cbbb9fc80067')
review_failure = json.loads(read(ROOT / review_failure_ref['path']))
assert len(review_failure['origins']) == 1 and review_failure['origins'][0]['actual_outer_exit'] == 1
origins.append({'origin_key': 'W05-99/handler-final-review/tool-7a75e5', 'evidence_ref': review_failure_ref, 'detail': review_failure})
root_diagnostic_ref = save('root-readonly-tool-original.json', {'tool_chunk': '49560c', 'actual_outer_exit': 1,
    'cause': 'Readonly lookup guessed proposal.json; actual F08 v5 file is scope_proposal.json. Corrected exact read ffdcbf/116ebc exited0.',
    'original_locator': 'functions.exec/exec_command chunk49560c; original tool result retained in conversation',
    'original_raw_file_available': False, 'native_test_failure': False, 'source_or_canonical_mutation': False})
origins.append({'origin_key': 'W05-99/root-readonly/tool-49560c', 'evidence_ref': root_diagnostic_ref, 'detail': json.loads(read(ROOT / root_diagnostic_ref['path']))})

g1 = ROOT / PUBLIC / 'provider_whole9_g1_root_executor_codex/788ce69c409b472799ee1389b778f9da'
outer = ROOT / PUBLIC / 'integration_codex/provider-g1-esm-attempt2-scope-r300'
g1_refs = [ref(f) for f in sorted(g1.iterdir()) if f.is_file()]
outer_refs = [ref(outer / name) for name in ['g1.outer.invocation.json', 'g1.outer.stdout.raw', 'g1.outer.stderr.raw']]
for directory, names, exit_key in [(g1, ['head', 'node-resolve-alias', 'bundle', 'go-list', 'go-compile', 'go-buildinfo', 'go3', 'js3'], 'actual_exit')]:
    for name in names:
        inv = json.loads(read(directory / (name + '.invocation.json')))
        assert inv[exit_key] == 0
        for stream in ['stdout', 'stderr']:
            assert hashlib.sha256(read(directory / (name + '.' + stream + '.raw'))).hexdigest() == inv[stream + '_sha256']
outer_inv = json.loads(read(outer / 'g1.outer.invocation.json'))
assert outer_inv['actual_exit'] == 1
for stream in ['stdout', 'stderr']:
    assert hashlib.sha256(read(outer / ('g1.outer.' + stream + '.raw'))).hexdigest() == outer_inv[stream + '_sha256']
assert json.loads(read(g1 / 'js3.termination.json'))['actual_exit'] == 128
raw = read(g1 / 'js3.stdout.raw')
summary = {key.decode(): int(value) for key, value in re.findall(rb'^# (tests|pass|fail|cancelled|skipped|todo) (\d+)\r?$', raw, re.M)}
assert summary == {'tests': 26, 'pass': 26, 'fail': 0, 'cancelled': 0, 'skipped': 0, 'todo': 0}
old_matches = [line.decode('utf-8') for line in raw.splitlines() if re.search(rb'#\s*(SKIP|TODO)\b', line, re.I)]
assert old_matches == ['# todo 0']
compiled = json.loads(read(g1 / 'compiled-dependencies.before.json'))
current = json.loads(read(g1 / 'inputs.failure.current.json'))
assert compiled == current and len(compiled) == 48392
assert read(g1 / 'compiled-dependencies.before.json') == read(g1 / 'inputs.pre-case.json') == read(g1 / 'inputs.failure.current.json')
g1_audit_ref = save('g1.originals.audit.json', {'state': 'FAILED_HARNESS_ORIGINALS_VERIFIED_NOT_ACCEPTED',
    'g1_original_refs': g1_refs, 'outer_original_refs': outer_refs, 'outer_actual_exit': 1,
    'Go3_actual_exit': 0, 'JS3_actual_exit': 0, 'JS_actual_summaries': summary,
    'actual_original_old_detector_matches': old_matches, 'termination_actual_exit': 128,
    'compiled_inputs_count': 48392, 'before_precase_failurecurrent_identical': True,
    'external_model_or_paid_calls': 0, 'new_Go_Node_SQL_or_model_execution': 0,
    'interpretation': 'Original native children passed. The original harness failed on standard TODO0 summary; preserve the failure. Corrected complete raw parser and fresh retained artifact/input verification are separate future readonly work.',
    'formal_increment': 0, 'whole9_source_acceptance': False})
origins.append({'origin_key': 'W05-99/provider-whole9-g1-tap-harness/attempt2-788ce69c409b472799ee1389b778f9da', 'evidence_ref': g1_audit_ref,
    'detail': {'actual_exit': 1, 'Go3_actual_exit': 0, 'JS3_actual_exit': 0, 'termination_actual_exit': 128,
               'cause': 'TAP standard summary # todo 0 incorrectly matched test-point directive guard',
               'count_once_per_batch_including_outer_and_termination': True}})
assert len(origins) == 6
assert all(path.read_bytes() == data for path, data in READS.items())
audit_ref = save('originals.audit.json', {'actor': 'codex:/root', 'origins': origins, 'handler_public_copies': copies,
    'review_failure_ref': review_failure_ref, 'g1_originals_audit_ref': g1_audit_ref,
    'expected_transition': {'checkpoint': [300, 301], 'ownership': [128, 129], 'failure_origins': [316, 322]},
    'old_counter_prefix_preserved': True, 'counter_reset': False, 'formal_increment': 0})

review_base = ROOT / PUBLIC / 'handler38_final_source_review_codex'
review_first = review_base / 'a639cfcf998f4c7fb182db19c6788c3b'
review_final = review_base / '1bfca99c7bd04ec7842ab2c810c35522'
tap = ROOT / PUBLIC / 'provider_whole9_g1_tap_harness_readonly_codex/ae441a8a6f194cb193b23344225ef408'
manifest_checks = []
for directory, expected in [
    (review_first, '801bc2f2a38f10ebfcf759d35853b7381679536d745b9f9408010a9a93461d44'),
    (review_final, '5f8f8f26581638878dcdc8809286956f6fde2977a320ca446380eb517fb72f07'),
    (tap, '2d64c8e1e90190ca337e5d08d632d0f80145321d682e72752dd9cf85c16f496a'),
]:
    manifest_ref = ref(directory / 'manifest.json', expected)
    manifest = json.loads(read(directory / 'manifest.json'))
    rows = manifest['files'] if 'files' in manifest else manifest['entries']
    for row in rows:
        relative = Path(row['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        actual = ref(directory / relative, row['sha256'])
        assert actual['bytes'] == row['bytes']
    manifest_checks.append({'manifest_ref': manifest_ref, 'entries_verified': len(rows)})

candidate_meta = []
for name, expected in [
    ('source.freeze.json', '05617de59195ea064ece1ffba4c2e0b35941c968428f36c802055aa10a0042fd'),
    ('handoff.json', '1da649ffb7c5acf3b6205e752b2d5e5d38681f561341bd2e19dae91d10c12c84'),
    ('evidence.manifest.json', '8389512c902ceac802d8e4c26b91b9bf4690fc90103f9e82375b2db9ea28792b'),
    ('coverage.actual.v2.json', 'f0f40b6f75f99425e1d669a2b095be63f5942d2940ca9d95736b632184fab194'),
]:
    candidate_meta.append(publish(HANDLER / 'candidate-review-2174dd5f0df043cd9f523945cc135cc2' / name, expected))

review_ref = ref(review_final / 'review.json', '8e5570173a067a8e115657814ed75fac6a5db6b1ef570db7dab49b42281ed6b3')
plan_ref = ref(review_first / 'execution_plan.json', '4a41630817bde8849014b062c34989510b2a4a31a3458c7f2ff42c73a4c98053')
supplement_ref = ref(review_final / 'execution_scope_supplement.json', 'd62e479d0dca032d58df63a2b29edbfe227d59a112b3beccaece92179a66ddaf')
review = json.loads(read(ROOT / review_ref['path']))
plan = json.loads(read(ROOT / plan_ref['path']))
supplement = json.loads(read(ROOT / supplement_ref['path']))
assert review['candidate'] == plan['candidate'] == supplement['candidate'] == '22752a6a41732c8c158d7d7e1b8932ec958f8cb8'
assert review['manifest'] == {'files': 3332, 'bytes': 1453286578, 'bad': 0}
assert not review['source_acceptance'] and review['formal_increment'] == 0
assert len(plan['batches'][0]['exact_top_selectors']) == 39
assert [batch['id'] for batch in plan['batches']] == ['A', 'B', 'C', 'D', 'E']
assert supplement['source_scope']['production_modifications'] == supplement['source_scope']['canonical_modifications'] == 0
root_review_ref = save('root_scope_review.json', {'actor': 'codex:/root', 'source_author': 'codex:/root/sources_parent_impl',
    'nonauthor_reviewer': 'codex:/root/w05_merge_review', 'review_ref': review_ref, 'plan_ref': plan_ref,
    'supplement_ref': supplement_ref, 'manifest_checks': manifest_checks, 'published_candidate_metadata': candidate_meta,
    'decision': 'PRECISE_HANDLER38_NONSELF_EXECUTION_AND_READONLY_TAP_ADJUDICATION_AUTHORIZED_FOR_REGISTRATION',
    'source_acceptance': False, 'whole_current_Main_composition': False, 'formal_increment': 0,
    'C09_boundary': 'Six receipt-owned copies with actual session.attach renewal. Two positive controls precede four exact-cause negatives. Only new explicitly SYNTHETIC permission/nonhead-Run/effect facts; immutable original producers/proofs untouched. This does not qualify a real permission or recovery lifecycle.',
    'failure_boundary': 'Original outer failures and taskkill128 retained. One attempt per new scope; first unexpected stops only dependent lane. No held1811/history5/Q10/historical14/LIVE execution.',
    'source_protection': 'Frozen handler38 source commit, no Main/authorWT/product/SDK/private-vault writes. Source overlays restricted to one new receipt-owned test file.'})
bundle_ref = ref(ROOT / '.local/w0599-main-stream-integration-r268/mu-worker.mjs', '2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441')
closed_fixture_ref = publish(supplement['C09_closed_input']['path'], supplement['C09_closed_input']['sha256'])
handler_scope_ref = save('handler38_independent_execution_scope.json', {'actor': 'codex:/root', 'executor': 'codex:/root/w05_merge_review',
    'source_author': 'codex:/root/sources_parent_impl', 'status': 'AUTHORIZED_BY_ROOT_CAS301_ONLY',
    'Main_head': '2cdb0d43d5a600eef13c8f1735946a9adf52d079', 'candidate_source_commit': plan['candidate'],
    'candidate_evidence_commit': '49aa8c6b3214997bcbbe28d10bed0df487d06601',
    'candidate_completion_commit': 'b01cd99531e88f344566f664f6e0dd4801521931',
    'root_review_ref': root_review_ref, 'review_ref': review_ref, 'plan_ref': plan_ref, 'supplement_ref': supplement_ref,
    'checkout': plan['owned_future_checkout'], 'receipts': plan['owned_receipts'],
    'operations': ['Create isolated detached checkout from exact frozen source commit',
        'Read/hash public source and exact fixed tool/SDK/compiler closure',
        'Build exact A-E test binaries and fixture CLI with pinned offline toolchain',
        'Execute A-E once, exact selectors and original limits from bound plan',
        'Prepare one new test-only physical C09 overlay and absolute Go mapping',
        'After overlay/spec/fixture/compiler before-case freeze execute six bound C09 controls once',
        'Only own generated/copy fixture SQL writes, loopback FIXTURE SDK HTTP and child processes',
        'Close/checkpoint own generated stores and preserve raw/typed-row/DB/budget evidence'],
    'overlay_virtual_relative': 'internal/domain/handler_configuration_independent_review_test.go',
    'C09_selector': '^TestIndependentHandlerConfigurationC09$', 'C09_closed_fixture_ref': closed_fixture_ref,
    'fixed_Main_bundle_ref': bundle_ref, 'no_provider9_bundle_substitution': True,
    'restrictions': {'Main_product_or_canonical_writes': 0, 'author_candidate_product_writes': 0,
        'shared_SDK_writes': 0, 'user_vault_or_private_data_calls': 0, 'external_paid_model_calls': 0,
        'held_cases': plan['held'], 'source_acceptance': False, 'formal_increment': 0,
        'automatic_retries': 0, 'new_generic_generator_or_holdout_execution': 0,
        'Linux_compile': 'Not included; separate precise amendment only if needed'},
    'stop': supplement['stop'], 'original_failure_audit_ref': audit_ref,
    'required_before_first_case': 'Verify CAS301 ownership, all immutable refs/38 Git blobs/tool pins, full actual Go source/embed/platform closure and fixed SDK/junction bytes, physical overlay/mapping/specs/fixtures/testexe hashes. Missing exact public resource stops affected batch for Root amendment; no silent source export or alternate implementation.'})
tap_proposal_ref = ref(tap / 'proposal.json', 'a456735d8fc523d45515927a4fb7ccb210ada3c1a2f320e103f54e6506af3fba')
tap_scope_ref = save('provider_g1_readonly_adjudication_scope.json', {'actor': 'codex:/root', 'executor': 'codex:/root',
    'provider_source_author': 'codex:/root/command_queue_impl', 'status': 'AUTHORIZED_BY_ROOT_CAS301_ONLY',
    'proposal_ref': tap_proposal_ref, 'original_audit_ref': g1_audit_ref,
    'operations': ['Create new receipt-only Python raw adjudicator',
        'Execute ten proposed offline TAP string controls and strict complete raw parser controls',
        'Verify sealed child/outer raw hashes, exact actual Go3/TAP26 events, original ESM/build/compiler provenance',
        'Fresh hash retained executed testexe/bundle and all48392 public compiler/source/SDK/tool inputs against original frozen vectors',
        'Seal separate original-native-evidence adjudication with actual original outer1 preserved'],
    'repeated_Go_Node_SQL_HTTP_model_tests': 0, 'new_product_or_SDK_source_writes': 0,
    'private_or_paid_calls': 0, 'failure_counter_reset': False, 'original_result_overwrite': False,
    'no_claim_original_outer_succeeded': True, 'whole9_source_acceptance': False, 'formal_increment': 0,
    'stop': 'First raw/ref/input/artifact mismatch stops readonly adjudication; no rebuild or test rerun substitutes missing original proof.'})
assert all(path.read_bytes() == data for path, data in READS.items())
save('prepared_refs.json', {'audit_ref': audit_ref, 'root_review_ref': root_review_ref, 'handler_scope_ref': handler_scope_ref,
    'tap_scope_ref': tap_scope_ref, 'candidate_metadata': candidate_meta, 'review_ref': review_ref,
    'plan_ref': plan_ref, 'supplement_ref': supplement_ref, 'completion_ref': completion_ref})
print(json.dumps({'audit_ref': audit_ref, 'unique_new_failed_origins': len(origins), 'handler_files': len(copies), 'g1_files': len(g1_refs),
    'handler_scope_ref': handler_scope_ref, 'tap_scope_ref': tap_scope_ref}, ensure_ascii=True))
