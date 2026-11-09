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
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def ref(path, expected=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
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


# This input is authored by Root after receiving actual sealed independent refs.
config_raw = read(OUT / 'sealed_inputs.json')
config = json.loads(config_raw)
pins = {}
pins['g1_review'], g1_review = load('provider_g1_readonly_adjudication_independent_review_codex/4e2d905076ee4745af1988ff3f73d069/review.json', 'ead78be57f9b6bdacc905d4fe1ef361408fa155b1d2da77b0f518a97c94a3837')
pins['f08_type_review'], f08_type = load('review_f08_v5_type_boundary_codex/6379a72a595747ddb796fe6b508afd2e/review.v2.json', '40e9a93dfa4b78fe752b3140693ae616d8ffa2fdfc8342c64c113a9b37087630')
pins['f08_caller_proposal'], f08_caller = load('cancel_finalization_v5_startup_caller_revision_codex/4639ce79ec914062ad92c278533a128f/proposal.json', '3f374c2e90a859f60495b06f3b0b4565068e50882e9fdad81649558c4dd62fe5')
pins['f08_scope21'] = ref(PUBLIC / 'cancel_finalization_v5_startup_caller_revision_codex/4639ce79ec914062ad92c278533a128f/complete_scope21.json', '4c6145ef1f136d1cbd6977fbeb33f93919fff5347e49a71ac5c302f005712216')
pins['f08_caller_review'], f08_caller_review = load('review_f08_v5_startup_caller_codex/f2a1d3715c774ffd8dba7ba434a8209d/scope_review.json', 'c71f17168d3b664aba90514e4180d0c085a9bf18dcd78825fe7c9bb20ed7b87b')
pins['f08_conditions'] = ref(f08_caller_review['conditions_ref']['path'], 'b878ae778ad1c5e26b7f1971a00ac3e449359305bd1c54ec989732bb67174736')
assert f08_caller_review['verdict'] == 'SOURCE_SCOPE_READY_WITH_MANDATORY_IMPLEMENTATION_CONDITIONS'
assert not f08_caller_review['source_ready'] and not f08_caller_review['SQL24_edit_lease']
pins['g2_proposal'], g2 = load('g2_finite_implementation_scope_codex/dace3de0637d4cfc898a576ae324a5c7/scope_proposal.json', 'e3a9e1cbf0b902eb17a025333979194e7cf89a926061639f5189ff65f3167ef7')
pins['g2_selectors'], g2_selectors = load('g2_finite_implementation_scope_codex/dace3de0637d4cfc898a576ae324a5c7/finite_selectors.json', 'f248e013bb46f97cbaa502384512766c269ae429f5314ed80edc97cadbe21bf8')
pins['g2_runner'], g2_runner = load('g2_finite_implementation_scope_codex/dace3de0637d4cfc898a576ae324a5c7/runner_scope.json', '9a612a002e0be0541199d8e1f770e6fb96248ad2eda99e747ab2860fc8b5c890')
pins['cli_proposal'], cli = load('cli_contract_exact_fix_scope_codex/f12c3e1bc23b42fc9c4018e85f8f849d/scope_proposal.json', '44bcf2c138523765fca036a47ef2ed8913da511c03537cb5d7746807579032c8')
pins['cli_plan'], cli_plan = load('cli_contract_exact_fix_scope_codex/f12c3e1bc23b42fc9c4018e85f8f849d/future_execution_plan.json', 'f4761291096a3be5fa003f187798ad3023ff839a5ae4f1d20200d7b1d056d84a')
pins['cli_review'] = ref(config['cli_review']['path'], config['cli_review']['sha256'])
cli_review = json.loads(read(pins['cli_review']['path']))
assert cli_review['verdict'] == 'SOURCE_SCOPE_READY_WITH_CONDITIONS'
pins['cli_conditions'] = ref(config['cli_conditions']['path'], '1a211ed97b81ec3b4e240d1cf63a2a6871fe0b8628717dca9b4841ceaf426c21')
pins['cli_regression_roster'] = ref(config['cli_regression_roster']['path'], '50ce26550f5dcab58594a47b2d2bd8996bf05c4588a09b9cb2998da50bf7cb2a')
roster = json.loads(read(pins['cli_regression_roster']['path']))
assert roster['count'] == len(roster['entries']) == 21
assert all(not row['sdk_required'] and row['future'] == 'NOT_RUN' for row in roster['entries'])
assert len({row['selector'] for row in roster['entries']}) == 21
pins['resume_gap'], resume = load('integration_codex/cli-real-resume-producer-readonly-r302/findings.json', '5f31e46cc53cab872cdcb4b812ba09b1fa2bdc4a1116dd6d55ecf3075683275f')
pins['previous_handoff'] = ref(PUBLIC / 'integration_codex/handler-resource-and-diagnostics-r302/handoff-r302-running.json', 'e9904b9257624a950698749e2ee88e61ab0686e93918f606b19b30c91c14bacd')
assert g1_review['verdict'] == 'DEVELOPMENT_EVIDENCE_VERIFIED_UNDER_PRESERVED_HARNESS_FAILURE'
assert g1_review['original_G1']['outer_actual_exit'] == 1 and g1_review['original_G1']['termination_actual_exit'] == 128
assert g1_review['input_vector']['independent_fresh_count'] == 48392 and not g1_review['input_vector']['mismatches']
assert f08_caller['scope_count'] == 21 and not f08_caller['SQL24_lease'] and not f08_caller['SQLTEXT_changed']
assert cli['exact_source_count'] == 8 and cli['production_count'] == 3 and cli['test_count'] == 5
assert cli['baseline']['handler_frozen_commit'] == '22752a6a41732c8c158d7d7e1b8932ec958f8cb8'
assert cli_plan['numbers'] == {'new_case_rows': 41, 'immediate_NOT_RUN': 37, 'hold_NOT_RUN': 4, 'future_test_groups': 4, 'old_successful_ids': 69, 'old_failure_entries': 26}
assert cli['decisions']['P02'].startswith('HOLD')
assert len(g2_selectors['helpers']) == 18 and len(g2_selectors['native']) == 11
g2_order = [row['selector'] for row in g2_selectors['helpers'] + g2_selectors['native']]
assert len(set(g2_order)) == 29 and g2_order == g2_runner['execution_order']
assert all(row['status'] == 'NOT_RUN' for row in g2_selectors['helpers'] + g2_selectors['native'])
assert not g2_runner['automatic_retries']

manifests = []
manifest_sources = [
    ('provider_g1_readonly_adjudication_independent_review_codex/4e2d905076ee4745af1988ff3f73d069/manifest.json', '07e3d446450e6df4199c181f458b5f906545acf6329302587a7236d50a61e5ff'),
    ('review_f08_v5_type_boundary_codex/6379a72a595747ddb796fe6b508afd2e/manifest.v2.json', '3b5a4721c4cc39c3caad8001dc97ac6649d74683ff40085788ad7d2f862c5fb8'),
    ('cancel_finalization_v5_startup_caller_revision_codex/4639ce79ec914062ad92c278533a128f/manifest.json', '82b3b72cdccb2f130f443a002a879759ecd69445955cc76bfae47fb8e4df073b'),
    ('g2_finite_implementation_scope_codex/dace3de0637d4cfc898a576ae324a5c7/manifest.json', '47cedb16b568842a867b2e739a42b8863f33044e57b738061fe634c5937fc35e'),
    ('cli_contract_exact_fix_scope_codex/f12c3e1bc23b42fc9c4018e85f8f849d/final_manifest.json', 'ab292ebfa80818155167d89e3e34797aa0c5292e01cee7086f649be02682c30e'),
    ('integration_codex/cli-real-resume-producer-readonly-r302/manifest.json', 'f106dd43aeed114fd82dd215aad16ae2b5eda4e2bd7221f7072bbf996949d0ba'),
    ('review_f08_v5_startup_caller_codex/f2a1d3715c774ffd8dba7ba434a8209d/manifest.json', '5436bfe3654ca475c37603357e9181d2ad98c794a69fb86ab3e9913a441b9a5c'),
]
manifest_sources.append((config['cli_review_manifest']['path'].removeprefix('execution/v2.4/receipts/W05/W05-99/'), config['cli_review_manifest']['sha256']))
for relative, sha in manifest_sources:
    mf_ref, mf = load(relative, sha)
    parent = (ROOT / mf_ref['path']).parent
    rows = mf['files']
    assert len({row['path'] for row in rows}) == len(rows)
    for row in rows:
        path = (parent / row['path']).resolve()
        assert path.is_relative_to(parent)
        actual = ref(path, row['sha256'])
        assert actual['bytes'] == row['bytes']
    manifests.append({'manifest_ref': mf_ref, 'verified_listed_count': len(rows), 'bad': 0})

origins = []


def add(key, evidence, detail):
    origins.append({'origin_key': key, 'evidence_ref': evidence, 'detail': detail})


root_plan_ref, root_plan = load('integration_codex/handler-resource-and-diagnostics-r302/root-readonly-no-plan-match-original.json', config['root_plan_failure_sha256'])
assert root_plan['actual_outer_exit'] == 1
add(root_plan['origin_key'], root_plan_ref, root_plan)
root_resume_ref, root_resume = load('integration_codex/cli-real-resume-producer-readonly-r302/root-tool-originals.json', config['root_resume_failure_sha256'])
assert len(root_resume['origins']) == 2
for row in root_resume['origins']:
    assert row['actual_outer_exit'] == 1
    add(row['origin_key'], root_resume_ref, row)
g1_fail_ref, g1_fail = load('provider_g1_readonly_adjudication_independent_review_codex/4e2d905076ee4745af1988ff3f73d069/failure_origins.json', '27adec667f959f7c347adad4c9d44dfe2a10208aa22222d985780fe1cdccf749')
assert len(g1_fail['new_review_tools']) == 2
for row in g1_fail['new_review_tools']:
    assert row['actual_outer_exit'] == 1
    add('W05-99/root-g1-adjudication-independent/tool-' + row['tool_chunk'], g1_fail_ref, row)
reg_fail_ref, reg_fail = load('root_registration_r302_readonly_review_codex/b384197ff3c34bc4b55f73810e3e5ff1/failure_origins.json', '5e93fb15a33f2dc2d3658271da084d2f527126ecaa5c3954cf81b55a2370d3d9')
assert len(reg_fail['origins']) == 1
row = reg_fail['origins'][0]
assert row['actual_outer_exit'] == 1
add(row['origin_key'], reg_fail_ref, row)
cli_fail_ref, cli_fail = load('cli_contract_exact_fix_scope_codex/f12c3e1bc23b42fc9c4018e85f8f849d/tool_failure_origin.json', '7995afced7c62160a9ab56387bc5745792d6afcef078fb918007eca4799a6b35')
assert cli_fail['actual_outer_exit'] == 1
add('W05-99/cli-exact-fix-scope/tool-0fc7f1', cli_fail_ref, cli_fail)
for row in config['additional_origins']:
    evidence = ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    detail = json.loads(read(evidence['path']))
    assert row['actual_outer_exit'] == 1
    add(row['origin_key'], evidence, detail)
assert len(origins) == len({row['origin_key'] for row in origins}) == config['new_origin_count']

lock_ref = ref(ROOT / 'execution/toolchains/locked.json', '0958d3f313e8d09d471521787a2b8b9480a17a91d6e4aa722393741dcbd8e663')
lock = json.loads(read(ROOT / lock_ref['path']))['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256']
git = lock['git']['path']
assert hashlib.sha256(Path(git).read_bytes()).hexdigest() == lock['git']['sha256']
canon = []
for name, sha in [('checkpoint', '252c57c6d0b05ccba2b5ac3a235f72b55118051f5e0db90cddbd81d6f33986aa'), ('path_ownership', 'b50c37b34d4c6e2d08d9b153dfdc4b95701cbebc7dfc504354ba27f9fbdb74ce'), ('step_state', 'fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149'), ('commands', 'b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129')]:
    canon.append(ref(ROOT / 'execution/v2.4' / (name + '.json'), sha))
cp, ow = [json.loads(read(ROOT / row['path'])) for row in canon[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [302, 130, 330]
old = {row.get('origin_key') for row in cp['failure_counters']}
assert all(row['origin_key'] not in old for row in origins)
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert cp['current_effective_formal_status']['formal_cases_accepted'] == 0
assert all(path.read_bytes() == raw for path, raw in READS.items())

cli_scope = save('cli_implementation_scope.json', {'actor': 'codex:/root', 'source_author': 'codex:/root/sources_parent_impl',
    'status': 'AUTHORIZED_BY_CAS303_ONLY_NOT_EXECUTED', 'proposal_ref': pins['cli_proposal'], 'independent_review_ref': pins['cli_review'],
    'plan_ref': pins['cli_plan'], 'base_commit': '22752a6a41732c8c158d7d7e1b8932ec958f8cb8',
    'worktree': '.local/worktrees/codex-w0599-cli-contract-repair-r303', 'branch': 'work/codex-w0599-cli-contract-repair-r303',
    'paths': [row['path'] for row in cli['paths']], 'original_bounds_and_protections': cli['paths'],
    'new_test_groups': ['TestCLIProtocolAttachCompletionBarrier', 'TestCLIProtocolExitClassification', 'TestCLIProtocolInteractiveAuthority', 'TestCLIProtocolStrictResponse'],
    'new_case_rows': {'immediate': 37, 'held': 4},
    'case_count_qualification': '37 immediate scenario rows, not an assertion of37 test leaves or PASS events. Author must freeze actual expanded leaf inventory before first case; final receipt reports observed counts.',
    'mandatory_cli_conditions_ref': pins['cli_conditions'],
    'approved_exact_regression_roster_ref': pins['cli_regression_roster'],
    'approved_exact_regression_selectors': [row['selector'] for row in roster['entries']],
    'regression_execution_conditions': config['cli_regression_conditions'],
    'P04_ruling': 'Only legal full /2 REJECTED typed NOT_IMPLEMENTED means capability unavailable and exit3 under frozen resource/authorization-absence category. This is Root category interpretation, not per-error verbatim frozen mapping. Illegal top-level status/schema/identity remains1; preserve valid non2xx IO classification.',
    'P02': 'No edits or qualification. Original session-id target and fake snapshot completion remain diagnosed/HOLD; real Goal/Run pause/resume producer needs separate exact scope.',
    'caches': {'GOCACHE': '<owned-new-worktree>/.local/cli-r303/cache', 'GOTMPDIR': '<owned-new-worktree>/.local/cli-r303/gotmp', 'GOPATH': 'Existing pinned modules read-only; no install/download'},
    'resource_provision': 'Root/delegated author may create unique new worktree from exact22752 without altering oldWT/Main. Full git source is current frozen source; additional runtime/SDK inputs require actual hashes and locked offline closure, no protected dataset/generator/evaluation execution.',
    'before_first_case': 'Actual full Go platform/dependency/embed/stdlib/tool/source/test/CLI executable provenance and frozenschemas/runner/fixture before/after. Confirm exact37 and append immutable exact regression roster before execution; no broad dynamic future matching. Missing resource requires precise amendment.',
    'stop': 'First unexpected failure/skip/ref/cause/drift stops dependent batch, preserve native raws/closed own fixtureDB and original failure counts. No same-input blind retry or source outside exact8.',
    'restrictions': {'Main_authorWT_SDK_canonical_writes': 0, 'frozen_schema_SQL_provider_changes': 0, 'private_vault_model_paid_calls': 0, 'full_formal_CLI_harness': 'HOLD_NO_EXECUTION', 'formal_increment': 0, 'source_acceptance': False},
    'all_original_69_and26_preserved': True, 'counter_reset': False})
pins['cli_implementation_scope'] = cli_scope
root_review_ref = save('root_scope_review.json', {'actor': 'codex:/root', 'CLI_scope_ref': cli_scope,
    'G1': 'Original limited child0 evidence independently adjudicated; preserve two original harness failures and new readonly-review2 errors. No whole9 acceptance.',
    'F08': 'TYPE original caller gap retained; exact21 revision now nonauthor SOURCE_SCOPE_READY_WITH_MANDATORY_IMPLEMENTATION_CONDITIONS. Actual source/SQL24 edit/execution lease remains absent; engine installed fingerprints and52future controls still NOT_RUN.',
    'G2': 'Record finite18helpers+11native/29 anchored selectors and B01-B08. Implementation lease deferred until a construction slot is free and Root registers test2; current no edit/execution.',
    'handler38': 'Authorized independent execution is running on isolated checkout; successful source export/Go graph/four builds are preparation only. No source/parent/formal acceptance inferred.',
    'old_git_deletions_and_failure_prefix_preserved': True, 'formal_increment': 0})
audit_ref = save('audit.json', {'status': 'PUBLIC_SCOPE_AND_ORIGINALS_VERIFIED_NOT_PRODUCT_ACCEPTANCE', 'refs': pins,
    'manifests': manifests, 'origins': origins, 'canonical_before': canon, 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'current_formal': cp['current_effective_formal_status'],
    'Root_prepare_Go_Node_SQL_HTTP_model_executions': 0, 'counter_reset': False})
save('prepared_refs.json', {'pins': pins, 'audit_ref': audit_ref, 'root_review_ref': root_review_ref,
    'all_verified_refs': [ref(path) for path in sorted(READS, key=str) if path.is_relative_to(ROOT)],
    'canonical_before': canon, 'head': head, 'new_origin_count': len(origins), 'git_status_sha256': hashlib.sha256(status).hexdigest()})
print(json.dumps({'status': 'PREPARED_FOR_CAS303', 'audit_ref': audit_ref, 'scope_ref': cli_scope, 'origins': len(origins), 'manifests': len(manifests)}, ensure_ascii=True))
