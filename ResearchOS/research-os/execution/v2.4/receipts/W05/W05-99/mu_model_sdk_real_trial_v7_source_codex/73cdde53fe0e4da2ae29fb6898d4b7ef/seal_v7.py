"""Seal v7 Source-only revision with exact v6 inverse and review pins."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
V6 = ROOT / 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb'
REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_independent_source_review_codex/ef4206a717d4407bac66097b27e3a7a5'
HERE = ROOT / 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v7_source_codex/73cdde53fe0e4da2ae29fb6898d4b7ef'


def ref(path):
    raw = path.read_bytes()
    return {'path': path.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(),
            'bytes': len(raw)}


def put(name, obj):
    path = HERE / name
    raw = (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
    with path.open('xb') as out:
        out.write(raw)
    return ref(path)


def put_raw(name, raw):
    path = HERE / name
    with path.open('xb') as out:
        out.write(raw)
    return ref(path)


review_ref = ref(REVIEW / 'review.json')
assert (review_ref['sha256'], review_ref['bytes']) == (
    '2e8647bb612f5224081fcca6fc01530d2041e7cd22bbddbebbffcbd6d5c7c554', 9115)
review = json.loads((REVIEW / 'review.json').read_bytes())
assert review['decision'] == 'REQUEST_CHANGES'
assert {row['id'] for row in review['requested_changes']} == {'SDK-V6-R01', 'SDK-V6-R02'}
v6_ref = ref(V6 / 'mu_sdk_trial.v6.graph.proposed.py')
assert (v6_ref['sha256'], v6_ref['bytes']) == (
    'c4ad0061e6e62a8ae50c94d0b40ccf6aa703a20010b67dcb007537719c1f53f5', 82464)
candidate_ref = ref(HERE / 'mu_sdk_trial.v7.final.proposed.py')
old = (V6 / 'mu_sdk_trial.v6.graph.proposed.py').read_text(encoding='utf-8')
new = (HERE / 'mu_sdk_trial.v7.final.proposed.py').read_text(encoding='utf-8')
prior_ast, final_ast = ast.parse(old), ast.parse(new)


def defs(tree):
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


before, after = defs(prior_ast), defs(final_ast)
assert before.keys() == after.keys()
changed_defs = {name for name in before if ast.dump(before[name]) != ast.dump(after[name])}
assert changed_defs == {'original_cli_summary_stream', 'verify_ordinary_goal_graph', 'main'}
assert 'result_artifact_refs' in new and 'object_by_ref(db, project, reference, "Artifact")' in new
assert 'final_snapshot.get("active_run_id") == execution.get("run_id")' in new
assert 'final_snapshot.get("goal_id") == execution.get("goal_id")' in new
assert 'maximum_provider_requests": 3' in new and 'requested_output_tokens_total": 8192' in new
stream = json.loads((HERE / 'precheck.v7.stream.final.json').read_bytes())
graph = json.loads((HERE / 'precheck.v7.graph.final.json').read_bytes())
assert stream['all_passed'] is True and len(stream['checks']) == 38
assert graph['count'] == 25 and all(row['decision'] in ('PASS', 'REJECT') for row in graph['checks'])
v6_hdf = json.loads((V6 / 'handoff.json').read_bytes())
go_refs = v6_hdf['go_refs']
assert len(go_refs) == 4 and all(ref(Path(item['path'])) == item for item in go_refs)
cli_ref = v6_hdf['cli_producer_ref']
assert ref(Path(cli_ref['path'])) == cli_ref

forward = ''.join(difflib.unified_diff(old.splitlines(keepends=True),
                                       new.splitlines(keepends=True),
                                       fromfile='v6/mu_sdk_trial.v6.graph.proposed.py',
                                       tofile='v7/mu_sdk_trial.v7.final.proposed.py')).encode('utf-8')
reverse = ''.join(difflib.unified_diff(new.splitlines(keepends=True),
                                       old.splitlines(keepends=True),
                                       fromfile='v7/mu_sdk_trial.v7.final.proposed.py',
                                       tofile='v6/mu_sdk_trial.v6.graph.proposed.py')).encode('utf-8')
forward_ref = put_raw('forward.v6-to-v7.diff', forward)
reverse_ref = put_raw('inverse.v7-to-v6.diff', reverse)
inverse_ref = put('source-inverse.json', {
    'schema': 'researchos.mu-sdk-v7-source-inverse.v1',
    'basis_ref': v6_ref, 'candidate_ref': candidate_ref,
    'forward_diff_ref': forward_ref, 'reverse_diff_ref': reverse_ref,
    'exact_prior_bytes_recovery': 'Use the pinned immutable v6 basis; reverse diff lists all changed lines.',
    'changed_function_ast': sorted(changed_defs),
    'unchanged_prior_functions': len(before) - len(changed_defs),
    'unchanged_cli_producer_ref': cli_ref, 'unchanged_four_go_refs': go_refs,
    'main_writes': 0, 'canonical_writes': 0})

origins = [ref(HERE / ('tool-failure-origin-%03d.json' % number)) for number in (1, 2)]
audit_ref = put('static-audit.json', {
    'schema': 'researchos.mu-sdk-v7-static-audit.v1',
    'review_ref': review_ref, 'candidate_ref': candidate_ref,
    'ast_parse': True, 'changed_function_ast': sorted(changed_defs),
    'stream_pure_io_controls': 38, 'graph_and_draft_pure_io_controls': 25,
    'foreign_or_missing_final_goal_and_active_run_rejected': True,
    'typed_artifact_version_hash_conflict_and_foreign_project_rejected': True,
    'v6_four_go_and_cli_producer_bytes_unchanged': True,
    'candidate_execution': 0, 'go_calls': 0, 'cli_calls': 0,
    'sdk_calls': 0, 'provider_requests': 0, 'formal_increment': 0})
report_ref = put('report.final.json', {
    'schema': 'researchos.mu-sdk-v7-source-report.v1',
    'decision': 'SOURCE_PREPARATION_ONLY', 'source_acceptance': False,
    'review_ref': review_ref, 'candidate_ref': candidate_ref,
    'SDK-V6-R01': 'Original terminal Session snapshot goal_id and active_run_id now equal nonempty original execution Goal/Run. Admission and exact new DB graph constraints remain. --draft stays separate.',
    'SDK-V6-R02': 'Every AVAILABLE Artifact EntityRef is type/revision/hash checked in original JSONL. The same full ref reaches DB domain_versions, exact current Artifact and original Run/Task output ID binding; conflicting same-ID refs reject.',
    'controls': {'stream': 38, 'graph_and_draft': 25},
    'new_failure_origins': origins, 'inherited_origins_recounted': False,
    'model_money': None, 'accounting': 'UNKNOWN',
    'future_limits': {'maximum_provider_requests': 3,
                      'requested_output_tokens_total': 8192,
                      'total_wall_seconds': 300},
    'actual_root_authority': None, 'actual_provider_requests': 0,
    'source_qualification': False, 'formal_case_accepted_delta': 0,
    'main_writes': 0, 'canonical_writes': 0})
members = [ref(path) for path in sorted(HERE.iterdir())
           if path.is_file() and path.name not in ('manifest.json', 'handoff.json')]
manifest_ref = put('manifest.json', {
    'schema': 'researchos.mu-sdk-v7-source-manifest.v1',
    'namespace': HERE.as_posix(), 'member_count': len(members), 'members': members,
    'sealed_source_only': True, 'producer_actor': 'codex:/root/live_resource_lookup'})
handoff_ref = put('handoff.json', {
    'schema': 'researchos.mu-sdk-v7-source-handoff.v1',
    'status': 'STOPPED_AFTER_SEAL', 'decision': 'SOURCE_PREPARATION_ONLY',
    'candidate_ref': candidate_ref, 'report_ref': report_ref,
    'manifest_ref': manifest_ref, 'static_audit_ref': audit_ref,
    'inverse_ref': inverse_ref, 'review_ref': review_ref,
    'unchanged_cli_producer_ref': cli_ref, 'unchanged_four_go_refs': go_refs,
    'new_failure_origins': origins, 'actual_provider_requests': 0,
    'formal_case_accepted_delta': 0, 'actual_root_authority': None})
print(json.dumps({'candidate': candidate_ref, 'report': report_ref,
                  'manifest': manifest_ref, 'handoff': handoff_ref,
                  'inverse': inverse_ref, 'origins': origins},
                 ensure_ascii=False, separators=(',', ':')))
