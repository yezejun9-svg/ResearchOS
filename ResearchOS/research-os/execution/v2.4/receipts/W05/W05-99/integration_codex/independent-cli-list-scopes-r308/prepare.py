import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
CLI = BASE / 'receipts/W05/W05-99/cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f'
STATIC = BASE / 'receipts/W05/W05-99/cli_exact8_source_static_independent_review_codex/0dcea5260f384ac19401dfb055a541f6'
VERIFIED = {}


def ref(path, expected=None):
    path = Path(path)
    path = (path if path.is_absolute() else ROOT / path).resolve()
    assert path.is_relative_to(ROOT)
    raw = path.read_bytes()
    item = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected, str(path)
    VERIFIED[item['path']] = item
    return item


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


def manifest(path, expected):
    pin = ref(path, expected)
    value = json.loads(path.read_bytes())
    for entry in value['entries']:
        target = Path(entry['path'])
        if not target.is_absolute():
            target = path.parent / target
        actual = ref(target, entry['sha256'])
        if 'bytes' in entry:
            assert actual['bytes'] == entry['bytes']
    return pin


canonical = [ref(BASE / name) for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
cp = json.loads((BASE / 'checkpoint.json').read_bytes())
ow = json.loads((BASE / 'path_ownership.json').read_bytes())
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [307, 135, 367]
assert cp['plan_sha256'] == 'a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17'
assert cp['spec_manifest_sha256'] == '4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964'
lock_path = ROOT / 'execution/toolchains/locked.json'
lock = json.loads(lock_path.read_bytes())['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
for key in ['python', 'git']:
    assert hashlib.sha256(Path(lock[key]['path']).read_bytes()).hexdigest() == lock[key]['sha256']
git = lock['git']['path']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
pins = {
    'previous_handoff': ref(BASE / 'receipts/W05/W05-99/integration_codex/frozen-candidates-and-g2-r307/handoff-r307-running.json', '4ece24bd05a60b4b7aedb886d10eaf80794be32b8413c4dfe2cabd045ba0469d'),
    'previous_postaudit': ref(BASE / 'receipts/W05/W05-99/integration_codex/frozen-candidates-and-g2-r307/postexecution.audit.json', '13fdba36abdb5a32b05072697868ce32554b2261f841662a6a982e9f869cb171'),
    'cli_static_review': ref(STATIC / 'review.json', 'e665d2e2374a5985eba3820a5b4427f2f0babbb9f1f7f5df61e66a8fe551d8c0'),
    'cli_static_manifest': ref(STATIC / 'manifest.json', '3c663d282e12d662e2df3280f7672a568e24d44c1e72e8ef26ddf8e5eb3f1826'),
    'cli_original_prepared_manifest': manifest(CLI / 'manifest.json', '032e33859f375c53abc8805eb8106bf6640e24c3ee59fe8399d19caad57e4b23'),
    'cli_prepared_manifest': manifest(CLI / 'manifest.v2.json', 'a03e96b9079bafaca3e4b39af5ca6c73a25f3a68ff2cc3bd2ed57dafb58532d2'),
    'cli_prepared_handoff': ref(CLI / 'handoff.v2.json', '1dc734b6a58c5d3c6a47663443356a18a1484c8981a182d28c7abbf73f192368'),
    'cli_prepared_spec': ref(CLI / 'prepared_execution_spec.v2.json', 'cda578d93540f27d8d7841b9ed949f59f4064f5e8bcac1f52a2101b41057dce6'),
    'cli_runner': ref(CLI / 'runner.v2.py', '0ce807c883df72a26c748ce6123dd103cd69e5121d4627eca48b8943e4752a0d'),
    'cli_selectors': ref(CLI / 'finite_selectors.json', '4c4617581fef85664dbf15bf0ca33937844fdf019e1f2917732ce08a372a25e4'),
    'list_runner': ref(OUT / 'list_replay.py'),
    'owned_process_helper': ref(OUT / 'windows_owned_process.py', '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad'),
    'helper_root_static_review': ref(OUT / 'windows_helper_root_static_review.json'),
    'root_locator_origin': ref(OUT / 'root_locator_failure_origin.json'),
    'cli_locator_origins': ref(STATIC / 'failure_origins.json', '4077b240ed5fa10b981464f52d161def0b78bc7952b3c776833e698ee0df9e80'),
    'command_review_locator_origin': ref(BASE / 'receipts/W05/W05-99/root_registration_r307_readonly_review_codex/9c8390b186da409c94c3ee3d322af8cb/failure_origin.json', '26a5f9bd03b044e6540fe77cda2ac16fa193290a5e7e587b53a9d6237c935adb'),
}
# Use the handoff's typed origin reference rather than guessing its filename.
handoff = json.loads((CLI / 'handoff.v2.json').read_bytes())
origin_matches = []
for path in CLI.iterdir():
    if path.is_file() and path.suffix == '.json' and hashlib.sha256(path.read_bytes()).hexdigest() == '6b0188f43ed7f4cd0e3325003ea353c1f366f6b76f4140e7f51a69bc6823b7f2':
        origin_matches.append(path)
assert len(origin_matches) == 1
pins['cli_expected_absence_origin'] = ref(origin_matches[0], '6b0188f43ed7f4cd0e3325003ea353c1f366f6b76f4140e7f51a69bc6823b7f2')
roster = json.loads((CLI / 'finite_selectors.json').read_bytes())['selectors']
assert len(roster) == 47 and sum(len(row['expected_leaf_names']) for row in roster) == 221
spec = json.loads((CLI / 'prepared_execution_spec.v2.json').read_bytes())
paths = spec['paths']
for path in [Path(paths['checkout']), Path(paths['output']), ROOT / '.local/independent-session-list-r308-534857db',
             ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_identity_independent_replay_codex/root-r308-534857db']:
    assert not path.exists(), str(path)
for path in [OUT / 'register.py', OUT / 'run.py', OUT / 'list_replay.py', OUT / 'windows_owned_process.py', CLI / 'runner.v2.py']:
    ast.parse(path.read_bytes())
    ref(path)
cli_scope = {'schema': 'researchos.finite-nonauthor-execution-scope.v1', 'status': 'AUTHORIZED_BY_CAS308_ONLY_NOT_EXECUTED',
    'owner': 'codex:/root/w05_merge_review', 'source_commit': 'b98738ac093ea55bb8700cfa724ddd9e6b2a1251',
    'base_commit': '22752a6a41732c8c158d7d7e1b8932ec958f8cb8', 'output': paths['output'],
    'cli47_execution': {'candidate': 'b98738ac093ea55bb8700cfa724ddd9e6b2a1251', 'checkout': paths['checkout'], 'output': paths['output'],
        'prepared_manifest_sha256': pins['cli_original_prepared_manifest']['sha256'],
        'prepared_manifest_v2_sha256': pins['cli_prepared_manifest']['sha256'],
        'owned_process_helper_ref': pins['owned_process_helper'],
        'invocation_limit': 47, 'leaf_limit': 221, 'SDK_MODEL_EXTERNAL_PAID_CALLS': 0},
    'runner_ref': pins['cli_runner'], 'prepared_spec_ref': pins['cli_prepared_spec'], 'selectors_ref': pins['cli_selectors'],
    'source_static_review_ref': pins['cli_static_review'], 'same_input_automatic_retry': False,
    'source_export': 'Only the immutable518 public Git members and5921 readonly resources already classified in sealed v2 plan; no resource installation/fallback/private/vault data.',
    'required_before_case': 'Actual whole new Go graph/platform/embed/test source; public SQL/schemas; generated testmain/importcfg/importcfg.link/everyarchive; new CLI/test/harness-build-only exe; actualPython/helper/OS resources and env frozen. No old executable reuse.',
    'Windows': 'Original4control/3CTRL_BREAK assertions unchanged. New temporary child actual logged SHA/size must match new retained CLI; only ownTEMP observer may retain matching bytes, nonretention limits explicit.',
    'loopback': 'Only sealed selected private protocol fixture and one actual new-created public API disposable fixture; actual private vs CLIchild vs publicAPI layer labels kept. No Node/provider/SDK/model/external/paid.',
    'failure': 'First unexpected native failure, skip, timeout, missing input, closure drift or OSJob cleanup stops; original stdout/stderr/actualexit/Job facts/source vector/closed fixtures retained; rest NOT_RUN, no auto retry/reset.',
    'held': ['existing-open-readonly', 'existing-self-send', 'P01-03 realAPI layer gap', 'actual attach completion', 'P02', 'fullharness', 'Main integration', 'parent/formal'],
    'Main_product_source_writes': 0, 'author_worktree_source_writes': 0, 'source_acceptance': False, 'formal_increment': 0}
pins['cli_scope'] = save('cli_independent_scope.json', cli_scope)
names = ['NullContext', 'OwnedContext', 'ContextNotResultFilter', 'ExactReplayAfterCommit', 'ChangedPayloadConflict', 'ChangedSIDConflict', 'CrossProjectContext', 'ForeignPrincipalContext', 'ForeignPrincipalNullList', 'UnknownContext', 'ProjectGrantDenied', 'CrossProjectCursor', 'CrossPrincipalCursor', 'MalformedRequest']
list_scope = {'schema': 'researchos.finite-nonauthor-execution-scope.v1', 'status': 'AUTHORIZED_BY_CAS308_ONLY_NOT_EXECUTED',
    'owner': 'codex:/root', 'source_author': 'codex:/root/command_queue_impl',
    'source_commit': '534857db99fa5e694987f877af74c322eaa2a0b3', 'base_commit': '22752a6a41732c8c158d7d7e1b8932ec958f8cb8',
    'source_paths_sha256': {'internal/domain/client_protocol_sessions.go': '7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3',
        'internal/api/v2_sessions_test.go': 'e095e2be7418d4ca7bb677e33679f25e377e084bec305f538799baf8523ea9b0'},
    'runner_ref': pins['list_runner'], 'owned_process_helper_ref': pins['owned_process_helper'],
    'checkout': str(ROOT / '.local/independent-session-list-r308-534857db'),
    'output': str(ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_identity_independent_replay_codex/root-r308-534857db'),
    'ordered_cases': names, 'maximum_loopback_HTTP_calls_including_setup': 224, 'per_case_HTTP_calls_maximum': 16,
    'SDK_worker_MODEL_external_paid_private': 0, 'native_case_timeout_seconds': 150, 'outer_case_timeout_seconds': 180,
    'public_export': 'Exact immutable Git blobs under adapters/internal/migrations/spec/apps/cli/tests/contracts/bootstrap plus go.mod/go.sum/VERSION, source-only. Protected development embedded JSON included. No execution/qualification/third_party export/private vault/user DB.',
    'fresh_compilation': 'Actual full Go deps/test/compiled/platform/embed sources plus GOROOT and public modules/tools; own new cache/tmp/temp; GOTOOLCHAINlocal/GOENVoff/GOWORKoff/GOPROXYoff/GOSUMDBoff/CGO0/windowsamd64. Readonly gofmt-l only. New testexe, full actualWORK, copied generated testmain/importcfg/importcfg.link and all referencedarchives before cases.',
    'wire_and_DB': 'Unchanged native full service schema/original identity/domain ContentHash/journal/alltable assertions. Root independently verifies actual request/response raw SHA/bytes, original journal/raw envelope/response binding; readonly closedcopy sqlite_schema/allcolumns/alltypedrowmultisets, bytehash unchanged.',
    'rowid_limit': 'All declared columns and SQLite storage types compared. Implicit rowid not separately exported by the existing test helper; this scope does not claim an independent open-before/closed-after implicit-rowid comparison.',
    'short_transport': 'L05/L06 HTTP409 COMMAND_ID_CONFLICT and L14 HTTP400 INVALID_REQUEST preserve actual original short wrapper; never forge fullCommandResponse. L02 sameprincipal different readonlyclient valid withoutwriterclaim.',
    'protected_old_test_body_sha256': 'c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1',
    'first_unexpected_stop': True, 'same_input_automatic_retry': False, 'source_writes': 0, 'Main_product_source_writes': 0,
    'author_worktree_source_writes': 0, 'old_DB_writes': 0, 'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0}
pins['list_scope'] = save('list_independent_scope.json', list_scope)
origins = []
for key, actor, origin_key, native in [
    ('cli_locator_origins', 'codex:/root/w05_merge_review', 'readonly-export-plan/dc40e0', 1),
    ('command_review_locator_origin', 'codex:/root/command_queue_impl', 'r307-readonly-scope-display-dfeb2c', 1),
    ('root_locator_origin', 'codex:/root', 'codex:/root/readonly-locator/9ab357', None),
    ('cli_expected_absence_origin', 'codex:/root/w05_merge_review', 'readonly-expected-absence/09ff5c', None),
]:
    origins.append({'actor': actor, 'origin_key': origin_key, 'actual_outer_exit': 1, 'actual_native_exit': native,
        'kind': 'READONLY_TOOL_ORIGIN_NOT_PRODUCT_TEST_FAILURE', 'evidence_ref': pins[key], 'product_cases': 0, 'paid_calls': 0,
        'automatic_same_input_retry': False, 'counter_reset': False})
assert not any(row['origin_key'] in {old.get('origin_key') for old in cp['failure_counters']} for row in origins)
audit = {'canonical_before': canonical, 'Main_head': head, 'git_status_sha256': hashlib.sha256(status).hexdigest(),
    'origins': origins, 'fixed_cut': 4, 'expected_transition': [[307, 135, 367], [308, 136, 371]],
    'CLI47_and_list14_not_run': True, 'Main_HOLD': True, 'G2_source_writer_continues_without_modified_lease': True,
    'late_Source_G2_339800_798239_62f172_pending_next_CAS': True, 'source_acceptance': False, 'formal_increment': 0}
pins['audit'] = save('audit.json', audit)
assert canonical == [ref(BASE / name) for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
prepared = {'canonical_before': canonical, 'head': head, 'git_status_sha256': hashlib.sha256(status).hexdigest(),
    'pins': pins, 'origins': origins, 'verified_refs': list(VERIFIED.values()), 'actual_source_exports_compile_cases': 0}
save('prepared_refs.json', prepared)
print(json.dumps({'prepared_refs': ref(OUT / 'prepared_refs.json'), 'audit': pins['audit'],
    'cli_scope': pins['cli_scope'], 'list_scope': pins['list_scope'], 'verified_refs': len(prepared['verified_refs']), 'actual_product_cases': 0}, ensure_ascii=True))
