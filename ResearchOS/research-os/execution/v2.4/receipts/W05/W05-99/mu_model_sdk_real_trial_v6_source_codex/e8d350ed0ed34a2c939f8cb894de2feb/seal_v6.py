"""Seal immutable source-only v6 proposal after all static checks."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = ROOT / 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb'
V5 = ROOT / 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v5_source_codex/39387323960a441ca81f04b9bcdecd17'
REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v5_independent_source_review_codex/306871fc728a4229a2a7a829b610ca82'


def ref(path):
    raw = path.read_bytes()
    return {'path': path.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def write(name, obj):
    path = HERE / name
    raw = (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')
    with path.open('xb') as out:
        out.write(raw)
    return ref(path)


def write_raw(name, raw):
    path = HERE / name
    with path.open('xb') as out:
        out.write(raw)
    return ref(path)


v5_hdf = json.loads((V5 / 'handoff.json').read_bytes())
review_ref = ref(REVIEW / 'review.json')
assert (review_ref['sha256'], review_ref['bytes']) == (
    'b4eb749847e39c10d5fd3c00a9dd1d13be08c364fcdf93835335042585ddd695', 12305)
review = json.loads((REVIEW / 'review.json').read_bytes())
assert review['decision'] == 'REQUEST_CHANGES'
assert {item['id'] for item in review['requested_changes']} == {'R01-v5', 'R02-v5', 'R03-v5'}
v5_ref = ref(V5 / 'mu_sdk_trial.v5.final.proposed.py')
assert v5_ref == v5_hdf['runner_ref']
candidate_ref = ref(HERE / 'mu_sdk_trial.v6.graph.proposed.py')
old = (V5 / 'mu_sdk_trial.v5.final.proposed.py').read_text(encoding='utf-8')
new = (HERE / 'mu_sdk_trial.v6.graph.proposed.py').read_text(encoding='utf-8')
old_ast, new_ast = ast.parse(old), ast.parse(new)
stream_base = ast.parse((HERE / 'mu_sdk_trial.v6.latest_state.proposed.py').read_text(encoding='utf-8'))


def fn(tree, name):
    found = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(found) == 1, name
    return found[0]


assert ast.dump(fn(new_ast, 'original_cli_summary_stream')) == \
       ast.dump(fn(stream_base, 'original_cli_summary_stream'))
assert ast.dump(fn(new_ast, 'verified_cli_context_transition')) == \
       ast.dump(fn(stream_base, 'verified_cli_context_transition'))
assert {'verified_cli_draft_goal_transition', 'verify_ordinary_goal_graph'} <= \
       {node.name for node in new_ast.body if isinstance(node, ast.FunctionDef)}
assert '--draft' in new and 'created = {kind: after[kind] - before[kind]' in new
assert 'model_ledgers(db, doc["project_id"], run_id, ordinary_models,' in new
assert 'maximum_provider_requests": 3' in new and 'requested_output_tokens_total": 8192' in new

go_refs = []
for item in v5_hdf['go_refs']:
    actual = ref(Path(item['candidate']['path']))
    assert actual == item['candidate'] and actual['sha256'] == item['prior']['sha256']
    go_refs.append(actual)
cli_ref = ref(Path(v5_hdf['cli_producer_ref']['path']))
assert cli_ref == v5_hdf['cli_producer_ref']

stream_check = json.loads((HERE / 'precheck.v6.latest_state.json').read_bytes())
graph_check = json.loads((HERE / 'precheck.v6.graph.json').read_bytes())
assert stream_check['all_passed'] is True and len(stream_check['checks']) == 27 and graph_check['count'] == 18
assert all(item['decision'] in ('PASS', 'REJECT') for item in graph_check['checks'])

forward = ''.join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                       fromfile='v5/mu_sdk_trial.v5.final.proposed.py',
                                       tofile='v6/mu_sdk_trial.v6.graph.proposed.py')).encode('utf-8')
reverse = ''.join(difflib.unified_diff(new.splitlines(keepends=True), old.splitlines(keepends=True),
                                       fromfile='v6/mu_sdk_trial.v6.graph.proposed.py',
                                       tofile='v5/mu_sdk_trial.v5.final.proposed.py')).encode('utf-8')
forward_ref = write_raw('forward.v5-to-v6.diff', forward)
reverse_ref = write_raw('inverse.v6-to-v5.diff', reverse)

inverse_ref = write('source-inverse.json', {
    'schema': 'researchos.mu-sdk-trial-v6-source-inverse.v1',
    'basis_ref': v5_ref, 'candidate_ref': candidate_ref,
    'forward_diff_ref': forward_ref, 'reverse_diff_ref': reverse_ref,
    'exact_basis_bytes_recovery': 'Use immutable basis_ref; reverse diff independently shows every changed line.',
    'unchanged_v5_go_refs': go_refs, 'unchanged_cli_producer_ref': cli_ref,
    'main_writes': 0, 'canonical_writes': 0,
})

static_ref = write('static-audit.json', {
    'schema': 'researchos.mu-sdk-trial-v6-static-audit.v1',
    'candidate_ref': candidate_ref, 'ast_parse': True,
    'v6_stream_ast_same_as_27_control_basis': True,
    'v6_graph_pure_io_controls': 18, 'prior_stream_pure_io_controls': 27,
    'draft_command_argv_frozen': True, 'zero_bootstrap_effects_required_from_isolated_db': True,
    'new_goal_task_run_artifact_and_active_budget_chain_bound': True,
    'original_cli_producer_and_four_go_candidates_byte_unchanged': True,
    'candidate_execution': 0, 'go_calls': 0, 'cli_calls': 0, 'sdk_calls': 0,
    'provider_requests': 0, 'formal_case_accepted_delta': 0,
})

origins = [ref(HERE / ('tool-failure-origin-%03d.json' % number)) for number in (1, 2, 3, 4)]
report_ref = write('report.final.json', {
    'schema': 'researchos.mu-sdk-trial-v6-source-report.v1',
    'decision': 'SOURCE_PREPARATION_ONLY', 'source_acceptance': False,
    'review_ref': review_ref, 'candidate_ref': candidate_ref,
    'requested_changes': {
        'R01-v5': 'One final command summary follows contiguous same-session event records; terminal RUN_STATE and AVAILABLE Artifact must match original host report. EVENT_RESYNC_REQUIRED and foreign/duplicate/trailing records reject. Original stream AST retained from 27-control basis.',
        'R02-v5': 'Bootstrap goal argv includes --draft. The actual goal.start admission snapshot and saved CLI context bind a DRAFT Goal, NOT_STARTED execution, zero Task/Run/Ledger/effects in the isolated project DB. No provider request is inferred from an execution report.',
        'R03-v5': 'Normal session.send must admit a Goal different from historical DRAFT Goal. Same original JSONL summary/admitted snapshot and exact DB delta bind one ACTIVE Goal, Task, SETTLED Run and available Artifact IDs. Its Goal policy differs while Project/Global ancestors match the frozen draft chain.'},
    'remaining_authority': 'OPEN: Root actual registration/review/grant/Job/current source and fresh product qualification must be supplied independently before any execution.',
    'source_qualification': False, 'provider_requests': 0,
    'limits_future_only': {'maximum_provider_requests': 3, 'requested_output_tokens_total': 8192,
                           'total_wall_seconds': 300},
    'model_money': None, 'accounting': 'UNKNOWN',
    'two_fixed_codex_live_holds_unchanged': True,
    'new_failure_origins': origins, 'inherited_failure_origins_recounted': False,
    'main_writes': 0, 'canonical_writes': 0, 'formal_case_accepted_delta': 0,
    'controls': {'stream': 27, 'draft_and_graph': 18},
})

members = [ref(path) for path in sorted(HERE.iterdir())
           if path.is_file() and path.name not in ('manifest.json', 'handoff.json')]
manifest_ref = write('manifest.json', {
    'schema': 'researchos.mu-sdk-trial-v6-source-manifest.v1',
    'namespace': str(HERE), 'members': members, 'member_count': len(members),
    'sealed_source_only': True, 'producer_actor': 'codex:/root/live_resource_lookup',
})
handoff_ref = write('handoff.json', {
    'schema': 'researchos.mu-sdk-trial-v6-source-handoff.v1',
    'status': 'STOPPED_AFTER_SEAL', 'decision': 'SOURCE_PREPARATION_ONLY',
    'candidate_ref': candidate_ref, 'report_ref': report_ref,
    'manifest_ref': manifest_ref, 'static_audit_ref': static_ref,
    'inverse_ref': inverse_ref, 'review_ref': review_ref,
    'go_refs': go_refs, 'cli_producer_ref': cli_ref,
    'new_failure_origins': origins, 'formal_case_accepted_delta': 0,
    'actual_root_authority': None, 'actual_provider_requests': 0,
})
print(json.dumps({'candidate_ref': candidate_ref, 'report_ref': report_ref,
                  'manifest_ref': manifest_ref, 'handoff_ref': handoff_ref,
                  'inverse_ref': inverse_ref, 'static_audit_ref': static_ref,
                  'new_failure_origins': origins}, ensure_ascii=False, separators=(',', ':')))
