"""Seal the add-only Scope7 recovery source without importing it."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = ROOT / ('execution/v2.4/receipts/W05/W05-99/'
               'scope7_grant_recovery_source_preparation_codex/'
               '8821517157754457be7645afa51c5177')
UID = '9eccde97a9fa4815941768cacaf590dc'
REG = ROOT / ('execution/v2.4/receipts/W05/W05-99/integration_codex/'
              'desktop58-finite169-go3-r339-' + UID)
PF = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
             'desktop58_finite_grant_preflight_codex/' + UID)
AUTH = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
               'desktop58_finite_authorization_codex/' + UID)
GATE = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
               'desktop58_cli2_fact_abi_revision_preparation_codex/'
               'ddc11e9721a6490baf1f0032c6bf6d16/'
               'authorization_adapter.v4.cli2_fact.proposed.py')
PIPELINE = GATE.parent / 'metadata_pipeline.desktop58.bound.v4.proposed.py'
DIAGNOSTIC = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
                     'desktop58_grant_resume_diagnostic_codex/' + UID +
                     '/failures658-660-and-current-state.original.json')
BOUNDARY = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
                   'desktop58_grant_recovery_independent_review_codex/'
                   '96fdce9d0e3043c0a5d6aa82808749ad/boundary-review.json')
EXPECTED = {
    'gate': (GATE, '2db48d991390dc7706aad553cdc5530d005e90273f6e3eec1231c14dc4c067be', 60679),
    'pipeline': (PIPELINE, 'c0a085f9b720ebdb89a78fb5cf367bd262d2823fe15a9f2686545b99aebe7755', 38316),
    'scope': (REG / 'scope_registration.json', 'c8f9b66b22b2fd3092bd7161f3dd30cd927bc5bc192bb6e9ebece38582db9859', 25595),
    'grant': (AUTH / 'authorization.execute.json', '6b0ef299508d98c8f1dca47e3d01116ceae98aca7914d318f3ed6d13bc3f6c10', 33548),
    'REG manifest': (REG / 'manifest.json', 'b76fba76e3134321a19b90ce2a6b50bf31d89dfd106f9b6c0e1704baec01875c', 34164),
    'grant started': (REG / 'grant.started.json', '7a31f2fde04692c359d78fc2bfc3945d1159e62d66f8eacd634775439050a51e', 409),
    'Root diagnostic': (DIAGNOSTIC, '233cfd48e5ff6aef7cf69b0e6c6633c16ef34b64976486f3fefca1904406ae36', 11192),
    'independent boundary': (BOUNDARY, 'a54265b97224dda0b4457fe264fc76377862990dbb4b1e652bb7717dd4252dee', 3335),
    'independent physical pins': (BOUNDARY.parent / 'disk-assessment.json', '82d667aab0593d2a35ceadddacfd0985790ba821425d4834eed36d2883fd3a9f', 178184),
    'checkpoint': (ROOT / 'execution/v2.4/checkpoint.json', '4ed88a919cecc93d544c3b7a88745f45bcbc5b43156517d3ccccc6aa3cdc258b', 3412478),
    'path ownership': (ROOT / 'execution/v2.4/path_ownership.json', '8d954eff78630ff678ac9d1abbc5a88cadca60285a4d16a32f857ac2f12d37d3', 192055),
    'step state': (ROOT / 'execution/v2.4/step_state.json', 'fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149', 257446),
    'commands': (ROOT / 'execution/v2.4/commands.json', 'b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129', 68156),
}


def pin(p):
    raw = p.read_bytes()
    return {'path': p.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def put(name, value):
    target = HERE / name
    raw = (json.dumps(value, sort_keys=True, ensure_ascii=False,
                      indent=2, allow_nan=False) + '\n').encode('utf-8')
    with target.open('xb') as output:
        output.write(raw)
    return pin(target)


fixed = {}
for name, (path, sha, size) in EXPECTED.items():
    actual = pin(path)
    need(actual['sha256'] == sha and actual['bytes'] == size,
         name + ' actual pin changed before seal')
    fixed[name] = actual
need(not any(path.exists() for path in
             (AUTH / 'grant.completed.json', PF / 'manifest.json',
              AUTH / 'manifest.json')),
     'one of three terminal files already exists')
precheck = json.loads((HERE / 'precheck.scope7.v5.json').read_text(encoding='utf-8'))
need(precheck['count'] == 32 and
     all(item['result'] in ('PASS', 'REJECT', 'PASS_SYNTHETIC')
         for item in precheck['checks']) and
     precheck['gate_executions'] == 0 and precheck['recovery_executions'] == 0,
     'pure IO evidence not closed')
previous = HERE / 'scope7_grant_recover.proposed.py'
need(pin(previous)['sha256'] ==
     'b7f004b5f83ff8a0fe63a9fefaade32aa21ccecdf070172be32aa78d2e094286',
     'immutable v1 actual source changed')
candidate = HERE / 'scope7_grant_recover.v2.proposed.py'
tree = ast.parse(candidate.read_text(encoding='utf-8'), filename=str(candidate))
need(all(isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign,
                           ast.AnnAssign, ast.FunctionDef, ast.If,
                           ast.Expr))
         for node in tree.body), 'unexpected top-level executable node')
need(len([node for node in tree.body if isinstance(node, ast.If)]) == 1,
     'unexpected top-level execution branch')
need(not (ROOT / 'execution/v2.4/scope7_grant_recover.py').exists(),
     'candidate target already installed')
candidate_ref = pin(candidate)
backward = ''.join(difflib.unified_diff(
    candidate.read_text(encoding='utf-8').splitlines(True),
    previous.read_text(encoding='utf-8').splitlines(True),
    fromfile='scope7_grant_recover.v2.proposed.py',
    tofile='scope7_grant_recover.proposed.py', n=3))
need(bool(backward), 'v2 inverse missing')
inverse_ref = put('source.inverse.json', {
    'schema': 'researchos.scope7-recovery-source-inverse.v1',
    'status': 'ADD_ONLY_SOURCE_PREPARATION',
    'candidate_ref': candidate_ref,
    'previous_ref': pin(previous),
    'inverse_to_previous_unified_diff': backward,
    'future_install_target': None,
    'inverse': 'remove only a future byte-identical installed source if Root adopts it',
    'old_grant_and_original_facts_inverse': None,
    'warning': 'never delete an actual partial grant/manifest recovery result automatically'})
template_ref = put('future-inputs.template.json', {
    'schema': 'researchos.scope7-recovery-future-inputs-template.v1',
    'review_ref': None,
    'review_required_fields': ['schema', 'decision', 'reviewer_id',
                               'source_path', 'source_sha256', 'scope_ref',
                               'grant_ref', 'diagnostic_ref',
                               'boundary_review_ref', 'disk_assessment_ref',
                               'grant_started_ref',
                               'requests'],
    'review_decision_required': 'READY_SOURCE_ONLY',
    'process_ref': None,
    'process_required_fields': ['schema', 'actor', 'run_uuid', 'method',
                                'matching_processes', 'native_probe_exit',
                                'command_filter_contains', 'observed_at'],
    'attempt_root': None,
    'attempt_parent': 'execution/v2.4/receipts/W05/W05-99/scope7_grant_recovery_execution_codex',
    'source_ref': candidate_ref,
    'current_authority_and_review_are_not_created_by_this_template': True})
report_ref = put('report.json', {
    'schema': 'researchos.scope7-grant-recovery-source-report.v1',
    'status': 'SOURCE_PREPARATION_ONLY',
    'run_uuid': UID, 'canonical_tuple': [339, 167, 645],
    'fixed_origin_cut': 645,
    'original_grant_outer_exit': None,
    'original_grant_python_exit': None,
    'original_grant_native_exit': None,
    'new_verifier_execution': 'NOT_RUN',
    'source_acceptance': False, 'formal_increment': 0,
    'candidate_ref': candidate_ref,
    'fixed_inputs': fixed,
    'physical_snapshot': {
        'preflight_existing_files': 32,
        'authorization_existing_files': 34,
        'copy_pairs': 32,
        'Git_Job_original_records': 6,
        'runtime_observation_refs': 3,
        'REG_sealed_members': 123,
        'REG_only_added_after_seal': 'grant.started.json',
        'three_terminal_files': 'ABSENT',
        'execution_leafs': 'ABSENT'},
    'implementation': {
        'gate': 'exact fixed 2db48d source; validate_grant before any terminal metadata write',
        'extra': 'admission 3 Git Job facts, all 32 copy pairs, six ordered timestamps, REG after-seal delta, current four canon, three runtime observations',
        'writes': ['AUTH/grant.completed.json', 'PF/manifest.json',
                   'AUTH/manifest.json'],
        'provenance': 'separate Root recovery attempt/fact directory; old three exits stay null',
        'failure': 'exclusive create, partial facts retained, no automatic retry or rollback'},
    'controls_ref': pin(HERE / 'precheck.scope7.v5.json'),
    'selected_tool_io_ref': pin(HERE / 'tool-io.selected.json'),
    'final_tool_io_ref': pin(HERE / 'tool-io.final.json'),
    'v2_tool_io_ref': pin(HERE / 'tool-io.v2.json'),
    'static_tool_failure_origin_ref': pin(HERE / 'failure-origin-001.json'),
    'future_inputs_template_ref': template_ref,
    'inverse_ref': inverse_ref,
    'open_until_Root_execution': [
        'New nonauthor review of this exact source and immutable inputs',
        'Fresh Root Win32_Process empty observation for the exact UID',
        'Root allocation of a fresh once-only recovery fact directory',
        'Actual pinned gate result and three exclusive terminal outputs',
        'Independent review of actual recovery output before any product launch'
    ]})
names = ['scope7_grant_recover.proposed.py',
         'scope7_grant_recover.v2.proposed.py', 'precheck_scope7.py',
         'precheck.scope7.v5.json', 'tool-io.selected.json',
         'tool-io.final.json', 'tool-io.v2.json', 'source.inverse.json',
         'future-inputs.template.json', 'failure-origin-001.json', 'report.json']
members = [pin(HERE / name) for name in names]
manifest_ref = put('manifest.json', {
    'schema': 'researchos.scope7-grant-recovery-source-manifest.v1',
    'namespace': HERE.relative_to(ROOT).as_posix(),
    'members': members, 'count': len(members),
    'excluded_only_self': True, 'formal_increment': 0})
handoff_ref = put('handoff.json', {
    'schema': 'researchos.scope7-grant-recovery-source-handoff.v1',
    'status': 'STOPPED_SOURCE_ONLY',
    'report_ref': report_ref, 'manifest_ref': manifest_ref,
    'candidate_ref': candidate_ref, 'inverse_ref': inverse_ref,
    'future_inputs_template_ref': template_ref,
    'pure_io_ref': pin(HERE / 'precheck.scope7.v5.json'),
    'next_action': 'independent source review by codex:/root/w05_merge_review; Root alone may fill actual future inputs and execute once',
    'original_grant_exits': {'outer': None, 'python': None, 'native': None},
    'formal_increment': 0})
print(json.dumps({'report': report_ref, 'manifest': manifest_ref,
                  'handoff': handoff_ref, 'candidate': candidate_ref,
                  'inverse': inverse_ref, 'template': template_ref},
                 ensure_ascii=False, separators=(',', ':')))
