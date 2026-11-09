import hashlib
import json
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize != 0:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PUBLIC = ROOT / 'execution/v2.4/receipts/W05/W05-99'
READS = {}


def read(path):
    path = Path(path).resolve()
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def ref(path, expected=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT), path
    raw = read(path)
    sha = hashlib.sha256(raw).hexdigest()
    assert expected is None or sha == expected, path
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha, 'bytes': len(raw)}


def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return ref(OUT / name)


def load(relative, sha):
    receipt = ref(PUBLIC / relative, sha)
    return receipt, json.loads(read(ROOT / receipt['path']))


pins = {}
pins['resource'], resource = load('integration_codex/handler38-public-compile-resource-corrected-r302/resource_amendment.json', 'ea3b9bdd9984547850668a7d34b543fc5a55a1732c9c201573cf53241e090301')
pins['resource_review'], resource_review = load('handler38_compile_resource_scope_independent_review_codex/05f6c9b025f645c498e7e61e165b2435/review.json', '5cc700d88545ba8ff7797c1ee0217d8ef098ce129284293b5e4c00f731976fb1')
pins['g1_result'], g1 = load('integration_codex/provider-g1-readonly-adjudication-r301/result.json', '52ac2375e105d1285601270d66bf004053f79e22dfe33bb9896d9ea566e97e2d')
pins['g1_invocation'], g1_inv = load('integration_codex/provider-g1-readonly-adjudication-r301/outer.invocation.json', 'f74b0725dd1fc071d1b9b0cb5496e75b25cc65e7507c443515e1367ce1801515')
pins['f08_review'], f08 = load('review_f08_v5_whole20_34_sources_codex/3ca4d268f6cb4e0995a035605bd8c4ca/source_review.json', '8484d4f702d3a7583177634faf22033f9a817638701508344fcf65c4629eca9a')
pins['f08_type_revision'], type_revision = load('cancel_finalization_v5_type_boundary_clarification_codex/fd227767c4d34e4aa243faa96b45d3cb/scope_revision.json', '6d4f2f97a70f6dc0bfb6a22a81347d76e7549e1bffe89bdebbd615c2a9254c34')
pins['cli_review'], cli = load('cli_contract_diagnostic_independent_review_codex/735595fc3d59460cab80916fbd7e2b54/source_review.json', '9a7fcc685afb2f3412be02cd72b1a921b8294e5afee9d5780a17efe785635805')
pins['cli_proposal'], cli_proposal = load('cli_contract_diagnostic_independent_review_codex/735595fc3d59460cab80916fbd7e2b54/scope_proposal.json', 'a8da795cdde9275899484ef51085278aec3bd18944863f4153b3eeb4a5e2d3d4')
pins['g2_review'], g2 = load('provider_whole9_g2_scope_review_codex/7e669aee3a924198a6e955f69fd127ac/review.json', 'bb7c16e671385b7b17e355c23b4485e5c02778e0f22e29258838f38bcb857c62')
pins['g2_conditions'] = ref(g2['mandatory_conditions']['path'], 'be918fd84c6e30c13926efce4167b950e22e693f64f4de2d006bfd69bb99cb59')
pins['g2_selectors'] = ref(g2['future_selectors']['path'], 'c2bc2149210a0c5a791a8e63da335e7d4be84d20f1f2cf120e376d949e5aadc6')
pins['previous_handoff'] = ref(PUBLIC / 'integration_codex/handler-and-g1-originals-r301/handoff-r301-running.json', 'ac9c383dffb96928f4e04bf83389139898bcaa6f836e9d70f2ccba8b1a593bd0')

assert resource['file_count'] == 12 and len(resource['preparation_correction']['next_pathspecs']) == 15
assert resource_review['decision'] == 'SOURCE_RESOURCE_SCOPE_READY_PENDING_ROOT_CAS302'
for item in resource['exact_additional_public_compile_files']:
    actual = ref(item['root_readonly_snapshot_ref']['path'], item['sha256'])
    assert actual['bytes'] == item['bytes'] and not item['path'].endswith('_test.go')
assert g1_inv['actual_exit'] == 0
assert g1['status'] == 'ORIGINAL_NATIVE_G1_EVIDENCE_VERIFIED_UNDER_PRESERVED_FAILED_HARNESS'
assert g1['actual_full_input_count'] == 48392
assert g1['original_outer_actual_exit'] == 1 and g1['original_termination_actual_exit'] == 128
assert g1['original_Go3_actual_exit'] == g1['original_JS3_actual_exit'] == 0
assert g1['original_Go_test_pass_events'] == 13 and g1['original_JS_actual_counts'] == {'tests': 26, 'pass': 26, 'fail': 0, 'cancelled': 0, 'skipped': 0, 'todo': 0}
for stream in ['stdout', 'stderr']:
    actual = ref(PUBLIC / ('integration_codex/provider-g1-readonly-adjudication-r301/outer.' + stream + '.raw'), g1_inv[stream + '_sha256'])
    pins['g1_outer_' + stream] = actual
assert not g1['whole9_source_acceptance'] and not g1['formal_increment']
pins['g1_current_vector'] = ref(g1['current_input_vector_ref']['path'], g1['current_input_vector_ref']['sha256'])
for bucket in ['retained_executed_artifacts', 'original_generated_testmain']:
    for path, expected in g1[bucket].items():
        actual = ref(path, expected['sha256'])
        assert actual['bytes'] == expected['bytes']
assert g2['source_acceptance'] == 'NO_SOURCE_READY' and g2['scope_only']
assert cli['original_result'] == {'successful_ids': 69, 'failed_entries': 26, 'exit': 1, 'promotions': 0}

manifest_sources = [
    ('handler38_compile_resource_scope_independent_review_codex/05f6c9b025f645c498e7e61e165b2435/manifest.json', '5cd1425c5ef4fceffaafd59621ecc58a6449c1746e4a096953a5d4f1de3b0186'),
    ('cli_contract_diagnostic_independent_review_codex/735595fc3d59460cab80916fbd7e2b54/manifest.json', '9699dacb12eb34863b010a39b1969c53a68d2175b3f399d364f5ed5f7c5d8de1'),
    ('provider_whole9_g2_scope_review_codex/7e669aee3a924198a6e955f69fd127ac/manifest.json', 'a735cc37d906b17244e6ca5f3c5992ad953769fd305c9f2517d75908e7b589ee'),
    ('cancel_finalization_v5_type_boundary_clarification_codex/fd227767c4d34e4aa243faa96b45d3cb/manifest.json', '16d7a324a4b575d05a5506d178690654064a0a6f95e00c3c4fa76175d8396f6b'),
    ('review_f08_v5_whole20_34_sources_codex/3ca4d268f6cb4e0995a035605bd8c4ca/manifest.json', '5fe4bb12f1860f45dead384a65848f610301ec2c1275fcf30b464f2bc94f03ff'),
]
manifests = []
for relative, sha in manifest_sources:
    mf_ref, mf = load(relative, sha)
    parent = (ROOT / mf_ref['path']).parent
    rows = mf['files']
    assert len({row['path'] for row in rows}) == len(rows)
    for row in rows:
        p = (parent / row['path']).resolve()
        assert p.is_relative_to(parent)
        actual = ref(p, row['sha256'])
        assert actual['bytes'] == row['bytes'], p
    manifests.append({'manifest_ref': mf_ref, 'verified_listed_count': len(rows), 'bad': 0})

origins = []


def origin(key, receipt, detail):
    origins.append({'origin_key': key, 'evidence_ref': receipt, 'detail': detail})


f08_diag_ref, f08_diag = load('review_f08_v5_whole20_34_sources_codex/3ca4d268f6cb4e0995a035605bd8c4ca/diagnostics.json', '23ef97433bfae42c4180ee14c4a3970d0c81b1b9e604ccca37f48c006c535b5a')
assert len(f08_diag['nonzero']) == 2
for item in f08_diag['nonzero']:
    assert item['outer_exit'] == 1
    origin('W05-99/f08-v5-whole20-readonly/tool-' + item['chunk'], f08_diag_ref, item)
review_fail_ref, review_fail = load('root_registration_r301_readonly_review_codex/1d53da158fe44682b7f80089b0eb7752/failure_origins.json', 'b90435005885ab7ac1d8a97233747d63f8c267ad2879182c0af060bb39a2cfa2')
assert len(review_fail['origins']) == 1
item = review_fail['origins'][0]
assert item['actual_outer_exit'] == 1
origin(item['origin_key'], review_fail_ref, item)
type_fail_ref, type_fail = load('cancel_finalization_v5_type_boundary_clarification_codex/fd227767c4d34e4aa243faa96b45d3cb/failure-origin.read-locator.json', 'e505d77d47193ecda70120ada1138490b503a991797ad6934bad0904d69560fe')
assert type_fail['actual_outer_exit'] == 1 and type_fail['actual_tool_chunk'] == '229457'
origin('W05-99/f08-type-bound-readonly/tool-229457', type_fail_ref, type_fail)
handler_fail_ref, handler_fail = load('handler38_independent_replay_codex/39b9d78230514551bee80c7970bfa160/failure_origins.json', '47b583b43f779a36eebcac5391635dd2cbbba2c0c8c8f8239721087ecee254b3')
assert len(handler_fail['origins']) == 1
item = handler_fail['origins'][0]
assert item['native_actual_exit'] == 128 and item['outer_tool_exit'] == 1
for kind in ['invocation_ref', 'stdout_ref', 'stderr_ref', 'driver_ref']:
    actual = ref(item[kind]['path'], item[kind]['sha256'])
    assert actual['bytes'] == item[kind]['bytes']
origin(item['origin_key'], handler_fail_ref, item)
resource_fail_ref, resource_fail = load('integration_codex/handler38-public-compile-resource-corrected-r302/root-resource-prepare-original-failure.json', '7e565f751a5be53d1964dfd6178c28ddd9c18ac0988252d71b58eb9465d187f6')
assert resource_fail['actual_outer_exit'] == 1
origin(resource_fail['origin_key'], resource_fail_ref, resource_fail)
cli_fail_ref, cli_fail = load('cli_contract_diagnostic_independent_review_codex/735595fc3d59460cab80916fbd7e2b54/failure_origin.json', '78dffb796993906d473195e60bb28b858962570cf6284300ba8a76a9cb4dc00c')
assert cli_fail['native_outer_exit'] == 1 and cli_fail['product_or_test_exit'] is None
origin('W05-99/cli-diagnostic-independent/tool-2b6b4f', cli_fail_ref, cli_fail)
g2_fail_ref, g2_fail = load('provider_whole9_g2_scope_review_codex/7e669aee3a924198a6e955f69fd127ac/tool_diagnostics.json', '9cb74f03f5da6fb0727b3ec0817c5cc262c84edc990ee939cec97d8fff0c4eb9')
assert len(g2_fail['nonzero']) == 1 and g2_fail['nonzero'][0]['actual_outer_exit'] == 1
origin('W05-99/provider-g2-scope-readonly/tool-ed311b', g2_fail_ref, g2_fail['nonzero'][0])
assert len(origins) == len({item['origin_key'] for item in origins}) == 8

lock_ref = ref(ROOT / 'execution/toolchains/locked.json', '0958d3f313e8d09d471521787a2b8b9480a17a91d6e4aa722393741dcbd8e663')
lock = json.loads(read(ROOT / lock_ref['path']))['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256']
git = lock['git']['path']
assert hashlib.sha256(Path(git).read_bytes()).hexdigest() == lock['git']['sha256']
canon = []
for name, sha in [('checkpoint', '284469cf99a99eccb56e0fe8121209d7246ff04ad290a40568855a0ce23d1f28'), ('path_ownership', '5612e81a99da2398fc73f0eebea5cf40b37ee22b779fd34a6f8e045983161f99'), ('step_state', 'fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149'), ('commands', 'b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129')]:
    actual = ref(ROOT / 'execution/v2.4' / (name + '.json'), sha)
    canon.append(actual)
cp, ow = [json.loads(read(ROOT / row['path'])) for row in canon[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [301, 129, 322]
assert all(row['origin_key'] not in {old.get('origin_key') for old in cp['failure_counters']} for row in origins)
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert cp['current_effective_formal_status']['formal_cases_accepted'] == 0
assert all(path.read_bytes() == raw for path, raw in READS.items())
audit_ref = save('audit.json', {'status': 'PUBLIC_ORIGINALS_VERIFIED_NOT_ACCEPTANCE', 'refs': pins, 'manifests': manifests, 'origins': origins, 'canonical_before': canon, 'head': head, 'git_status_sha256': hashlib.sha256(status).hexdigest(), 'current_formal': cp['current_effective_formal_status'], 'Go_Node_SQL_HTTP_models_this_prepare': 0, 'counter_reset': False})
root_review_ref = save('root_scope_review.json', {'actor': 'codex:/root', 'audit_ref': audit_ref, 'handler_scope': 'Authorize corrected single preparation with exactly15 pathspecs and12 compile-only files after nonauthor CAS-script review; same A-E and6C09; no dataset or evaluation execution. First unexpected stops.', 'G1': 'Register actual limited development evidence under preserved original outer1 and termination128; original chain2 stays. Independent readonly adjudication review pending; no whole9 SourceReady.', 'F08': 'Old whole20/34 review plus TYPE/BOUND revision recorded; current independent revision review identifies startup postadditive caller gap, pending final. No SQL24 lease or formal acceptance.', 'G2': 'Register proposal, B01-B08 and exact11 future selectors as NOT_AUTHORIZED; no source edit/execution lease until finite helper names/control counts and runner are frozen.', 'CLI': 'Record static P01-P03 gaps. P04 legal capability-unavailable NOT_IMPLEMENTED exit3 is recommended category interpretation, pending precise scope; invalid top-level status remains1. No product/source/test/harness lease.', 'formal_increment': 0, 'counter_reset': False})
save('prepared_refs.json', {'pins': pins, 'audit_ref': audit_ref, 'root_review_ref': root_review_ref, 'all_verified_refs': [ref(path) for path in sorted(READS, key=str) if path.is_relative_to(ROOT)], 'canonical_before': canon, 'head': head, 'git_status_sha256': hashlib.sha256(status).hexdigest()})
print(json.dumps({'status': 'PREPARED_CAS302', 'audit_ref': audit_ref, 'root_review_ref': root_review_ref, 'origins': len(origins), 'manifests': len(manifests)}, ensure_ascii=True))
