"""Read only completed public runner evidence; no product, SQL or process execution."""
from pathlib import Path
import hashlib
import json

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
P = HERE.parent / 'cli47-r308-7d5925db'
LAUNCH = HERE.parent / 'cli47-r308-launch-2676dbab'
PREP = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f'

def read(path):
    return json.loads(path.read_bytes())

def ref(path):
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def save(name, value):
    with (HERE / name).open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

frozen = read(P / 'execution.inputs.before-first-case.json')
pins = {x['path']: x for x in frozen}
known = read(P / 'execute.failure-known-inputs.json')
new = [x['ref'] for x in known if x['path'] not in pins]
drift = [x for x in known if x['path'] in pins and x.get('ref') != pins[x['path']]]
save('runtime.additions.json', new)
source_names = ['apps/cli/cli_http_status_test.go', 'apps/cli/cli_sessions_test.go',
 'apps/cli/cli_stream.go', 'apps/cli/cli_stream_test.go', 'apps/cli/cli_v2.go', 'apps/cli/cli_verbs.go',
 'tests/runtime/cli_contract/main.go', 'tests/runtime/cli_contract/v2verbs.go']
git = {x['path']: x for x in read(PREP / 'public_compiler_export_plan.v2.json')['git_resources']}
checkout = ROOT / '.local/independent-cli-exact8-0dcea526'
source = []
for path in source_names:
    actual = ref(checkout / path)
    source.append({'relative_path': path, 'candidate_git': git[path], 'exported_current': actual,
                   'same': actual['sha256'] == git[path]['sha256']})
save('source8.current.json', source)

matrix = []
all_leaves = []
for index, row in enumerate(read(PREP / 'finite_selectors.json')['selectors']):
    inv = P / 'invocations' / f'case-{index:02d}' / 'invocation.json'
    item = {'index': index, 'selector': row['selector'], 'expected_leaf_names': row['expected_leaf_names'],
            'status': 'NOT_RUN', 'native_exit': None, 'actual_leaves': [], 'source_acceptance': False}
    if inv.exists():
        observed = read(inv)
        raw = inv.parent / 'stdout.raw'
        events = [json.loads(line) for line in raw.read_text(encoding='utf-8').splitlines() if line.strip()]
        terminals = [e for e in events if e.get('Test') and e.get('Action') in ('pass', 'fail', 'skip')]
        leaves = [e for e in terminals if not any(t['Test'].startswith(e['Test'] + '/') for t in terminals)]
        compact = [{'name': e['Test'], 'action': e['Action']} for e in leaves]
        all_leaves += compact
        result = P / 'cases' / f'{index:02d}' / 'result.json'
        item.update(status='NATIVE_PASS_RECORDED' if result.exists() else 'NATIVE_PASS_CONTROLLER_CLOSURE_REFUSED',
                    native_exit=observed['native_exit'], actual_leaves=compact,
                    inventory_matches=sorted(e['name'] for e in compact)==sorted(row['expected_leaf_names']),
                    invocation=ref(inv), stdout=ref(raw), stderr=ref(inv.parent / 'stderr.raw'),
                    job_cleanup=observed['owned_process']['job_cleanup'],
                    result=ref(result) if result.exists() else None)
        if index == 3:
            item['controller_closure_limitation'] = 'After old known-input after-check, DB Path.as_uri loads 65 extra controller files; not in pre-case freeze. Native/Go proof retained; full controller closure not retrospectively qualified.'
        if index == 4:
            item['controller_closure_limitation'] = 'runtime.before already contained new files; enforcement only after native case. Native pass is original fact; no qualification result.'
    matrix.append(item)
save('selector_matrix.json', matrix)

python_root = Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib')
stdlib = []
for relative in ('pathlib/__init__.py', 'urllib/request.py'):
    path = python_root / relative
    target = HERE / ('public-source-' + relative.replace('/', '_'))
    with target.open('xb') as f:
        f.write(path.read_bytes())
    stdlib.append({'original': ref(path), 'copy': ref(target)})
save('readonly_cause.json', {
    'kind': 'CONTROLLER_PREDECLARED_RUNTIME_CLOSURE_GAP',
    'code_refs': stdlib,
    'runner': ref(PREP / 'runner.v2.py'),
    'source_causality': [
        'runner.v2 dump_closed_databases calls db.as_uri() for read-only SQLite URI.',
        'Python3.14 pathlib/__init__.py lines1264-1269 Path.as_uri imports urllib.request.pathname2url lazily.',
        'case03 runtime.after sampled before DB dump has no new resources; case04 runtime.before and after both have new resources.',
        'runner checks runtime containment after native execution, before post-processing; therefore case04 ran once before rejection.'
    ],
    'evidence_limit': 'No import trace was installed. Specific causal attribution combines exact source and timing snapshots; module import does not establish an HTTP call.',
    'before_case04': ref(P / 'invocations/case-04/runtime.before.json'),
    'after_case04': ref(P / 'invocations/case-04/runtime.after.json'),
    'case03_alltables': [ref(x) for x in (P/'cases/03').rglob('*.independent-alltables.json')],
    'new_resources': ref(HERE / 'runtime.additions.json'),
    'original_frozen_count': len(frozen), 'observed_known_count': len(known),
    'original_frozen_drift': drift, 'new_resource_count': len(new),
    'product_source_changes': 0, 'repair_or_retry': 0,
})

save('failure_origins.json', {'origins': [{
    'origin_id': 'CLI47-r308-execute-4d65b6-2caf3a',
    'single_invocation': True, 'counter_delta': 1,
    'tool_start': '4d65b6', 'tool_completion': '2caf3a', 'session_id': 52159,
    'outer_native_exit': 1, 'underlying_case_native_failures': 0,
    'reason': 'NEW_RUNTIME_INPUT_AFTER_CASE',
    'classification': 'INDEPENDENT_CONTROLLER_RUNTIME_CLOSURE_FAILURE',
    'outer': ref(LAUNCH / 'execute.outer.json'), 'stderr': ref(LAUNCH / 'execute.stderr.raw'),
    'stdout': ref(LAUNCH / 'execute.stdout.raw'), 'stopped': ref(P / 'execute.stopped.json'),
    'failure_known_inputs': ref(P / 'execute.failure-known-inputs.json'),
    'fixture_existence': ref(P / 'execute.failure-fixture-existence.json'),
    'native_case04': ref(P / 'invocations/case-04/invocation.json'),
    'counting': 'One runner native1; not five product failures and not 65 missing-input failures. Prior origins untouched.'
}]})
save('bounded_correction_proposal.json', {
    'status': 'READONLY_PROPOSAL_NOT_IMPLEMENTED_NOT_AUTHORIZED',
    'source8_changes': 0, 'SDK_SQL_changes': 0,
    'minimal_controller_change': [
        'In a new immutable runner/cohort only, perform pure local Path.as_uri conversion before first runtime inventory. No URL opening or SQL required to preload same URI conversion imports.',
        'Freeze actual helper/Python/loaded OS DLL closure including exact65 observed additions and report any further actual addition before any child.',
        'Check runtime containment before each case child and again after all case post-processing/closedDB export. Do not defer detection to following case.',
        'Preserve old runner, old7718 vector, original five outputs and actual native1. Reuse source/newCLI/testexe hashes only after current graph/archive/source verification; do not claim one-exe complete221 pass.',
        'Root decides finite continuation:42 never-run selectors plus any explicitly chosen single closure-incomplete control. Do not automatically rerun passed groups or all47.'
    ],
    'not_a_license_to_execute': True,
    'new_tools_and_resource_pins': ref(HERE / 'runtime.additions.json'),
    'all_existing_results_preserved': True,
})

summary = {
    'decision': 'STOPPED_CONTROLLER_RUNTIME_CLOSURE_GAP_SOURCE_ACCEPTANCE_WITHHELD',
    'candidate': 'b98738ac093ea55bb8700cfa724ddd9e6b2a1251',
    'root_scope': ref(ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/cli_independent_scope.v2.json'),
    'prepare_native_exit': read(LAUNCH / 'prepare.outer.json')['native_exit'],
    'execute_native_exit': read(LAUNCH / 'execute.outer.json')['native_exit'],
    'prepare': ref(P / 'prepare.completed.json'),
    'selector_processes_executed': sum(x['native_exit'] is not None for x in matrix),
    'selector_processes_not_run': sum(x['status'] == 'NOT_RUN' for x in matrix),
    'actual_leaf_pass': sum(x['action'] == 'pass' for x in all_leaves),
    'actual_leaf_fail': sum(x['action'] == 'fail' for x in all_leaves),
    'actual_leaf_skip': sum(x['action'] == 'skip' for x in all_leaves),
    'original_runner_result_count': len(list((P / 'cases').glob('*/result.json'))),
    'not_all_five_controller_closures_qualified': True,
    'known_frozen_input_count': len(frozen), 'later_observed_input_count': len(known),
    'known_input_drift_count': len(drift), 'new_unfrozen_runtime_inputs': len(new),
    'compile_inputs': len(read(P/'compile.inputs.before.json')),
    'compiled_archives': len(read(P/'compiled.archives.before.json')),
    'source8_current_same': all(x['same'] for x in source),
    'windows_signal_controls': 'NOT_RUN',
    'public_closed_DBs_with_alltable_receipt': len(list(P.rglob('*.independent-alltables.json'))),
    'scope_effects': {'SDK_worker_Node_model_paid_external_provider_calls': 0,
                     'fixture_loopback_HTTP_request_count': None,
                     'loopback_count_limitation': 'No aggregate network-call instrumentation; method/fixture raw kept. Imports alone are not network requests.'},
    'source_acceptance': False, 'Main_integration': False, 'formal_increment': 0,
    'held': ['existing2 session.list500', 'P01-03 realAPI', 'P02', 'actual attach completion', 'fullharness', 'parent/formal'],
    'matrix': ref(HERE/'selector_matrix.json'), 'cause': ref(HERE/'readonly_cause.json'),
    'failure_origins': ref(HERE/'failure_origins.json'),
    'proposal': ref(HERE/'bounded_correction_proposal.json'),
}
save('review.json', summary)
entries = [ref(x) for base in (P, LAUNCH, HERE) for x in sorted(base.rglob('*')) if x.is_file()]
save('manifest.json', {'schema':'researchos.independent-stopped-cohort-manifest.v1', 'entries': entries,
     'count':len(entries), 'bytes':sum(x['bytes'] for x in entries), 'self_and_handoff_excluded':True})
save('handoff.json', {'decision':summary['decision'], 'review':ref(HERE/'review.json'),
     'manifest':ref(HERE/'manifest.json'), 'failure_origins':ref(HERE/'failure_origins.json'),
     'cause':ref(HERE/'readonly_cause.json'), 'proposal':ref(HERE/'bounded_correction_proposal.json'),
     'actual_selector_native0':summary['selector_processes_executed'], 'actual_leaf_pass':summary['actual_leaf_pass'],
     'unrun_selectors':summary['selector_processes_not_run'], 'controller_native1_origins':1,
     'no_repair_no_retry':True})
print(json.dumps({x:ref(HERE/x) for x in ('review.json','failure_origins.json','manifest.json','handoff.json','bounded_correction_proposal.json')},ensure_ascii=False))
