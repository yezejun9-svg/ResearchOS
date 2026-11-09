"""Create the next metadata staging program; do not execute a target."""
import ast
import hashlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
old_path = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r325-71b091d20d94443bbf4e732d201eeb29/stage-r326-buildvcs.py'
source = old_path.read_text(encoding='utf-8')

def one(before, after):
    global source
    assert source.count(before) == 1, before
    source = source.replace(before, after)

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
one('Root metadata staging for a changed Go-list input;', 'Root metadata staging for changed compiler parallelism;')
one("UID = '477e329b79944cb0b33f9ead24811760'", "UID = 'efa7776ec48e4a7abaa92ce85eb0dace'")
one("'cli43-fresh-held2-r326-'", "'cli43-fresh-held2-r327-'")
one('cli43_go_list_buildvcs_preparation_codex/7755e144441e424398e805ffb7ff0595', 'cli43_compiler_parallelism_preparation_codex/8ac0acd36c6047beaab455730692d078')
one('cli43_failed_execution_independent_review_codex/30c8c1f371bb4b7d9126c196f46eee8d/review.json', 'cli43_failed_execution_independent_review_codex/f41d184815b341e086a26d2a750f0b60/review.json')
one('cli43_current_bound_scope_independent_review_codex/7403e1aa621c4378820a3f79247e5b19/review.json', 'cli43_current_bound_scope_independent_review_codex/bbd110051f5647d8b6386372ed2cd08c/review.json')
one('3c265b63b5d0448bc09b5d9882f123df587d0447d5dc17cac70343785bb56884', '8cb8fb307dabe2668a736d7e964177a1fd67605a7f380d5f6e06d9268d59a6bb')
one('e8ef79e529db919f4e6dc6cc897f9532dc5ca6a5ddc102e26adbfa06a55fe843', '906e713f8ba9d6a0787b86d9b43b6d456f8b28d7784352df10e6d89f7543a605')
one("['runner_ref']['path']", "['candidate_ref']['path']")
one('9b70911e66417124f00f992476dedf3d88eb0f5b28c40964a7fce0ba9bef55b4', '333d69e00a421efcbb08e9ddf06e1486e911cd82af4a0d46a8bb60c8203f2bea')
one("'Single flag candidate'", "'Exact two compiler parallelism arguments'")
one('== [325, 153, 442]', '== [326, 154, 450]')
one("'Actual current canonical equals r325 desired'", "'Actual current canonical equals r326 desired'")
start = source.index("source_origins = BASE / 'f08_proof_evaluator_implementation_preparation_codex/")
end = source.index("template = json.loads(verified(inputs['scope_template_ref'])", start)
replacement = '''late_ref = pin(OLD / 'late-origins.capture.json')
need(late_ref['sha256'] == 'afd2d0f0d09aa6c7c0d9ba78e3e7dbd031e2f05e09963aaed3e641dc32822531', 'Original late8 capture')
late = doc(late_ref['path'])
need(late['registered_origin_count'] == 450 and len(late['origins']) == 8, 'Exact late cut')
origin_paths = [path(row['origin_ref']['path']) for row in late['origins']]
origin_paths.append(BASE / 'cli43_fresh_compiler_executor_codex/477e329b79944cb0b33f9ead24811760/failure.origin.json')
origins = []
for p in origin_paths:
    ref = pin(p, relative=True)
    need(all(old.get('evidence_ref', {}).get('sha256') != ref['sha256'] for old in cp['failure_counters']), 'Origin already registered')
    classification = ('SINGLE_GO_BUILD_NATIVE_EXIT_WITH_UNDETERMINED_CAUSE_NOT_PRODUCT_CASE' if p.name == 'failure.origin.json' else
        'COORDINATION_TOOL_DIAGNOSTIC_NO_INFERRED_NATIVE_FAILURE' if p.name == 'failure-origin.collaboration-source-map-limit.json' else
        'READONLY_INVENTORY_NO_MATCH_EXIT_NO_INFERRED_PRODUCT_FAILURE' if p.name == 'failure-origin.a76746.json' else
        'ACTUAL_TOOL_OR_METADATA_FAILURE_NOT_PRODUCT_CASE')
    origins.append({'evidence_ref': ref, 'original_payload': doc(p), 'counter_reset': False,
                    'automatic_same_input_retry': False, 'classification': classification})
need(len(origins) == 9 and len({row['evidence_ref']['sha256'] for row in origins}) == 9, 'Exact new origin cut')
inputs['before'] = [326, 154, 450]
inputs['after'] = [327, 155, 459]
inputs['origin_cut_ref'] = save(OUT / 'failure-origins.cut.json', {'before': inputs['before'], 'after': inputs['after'],
    'counter_reset': False, 'origins': origins, 'nested_launch_exits_counted_once': True,
    'native_NULL_fields_and_original_payloads_preserved': True,
    'new_later_origins_not_added_to_this_fixed_cut': True})
'''
source = source[:start] + replacement + source[end:]
one('scope.template.runner-v5.json', 'scope.template.runner-v6.json')
one("prior.name.replace('71b091d20d94443bbf4e732d201eeb29', UID)", "prior.name.replace('477e329b79944cb0b33f9ead24811760', UID)")
one("inputs['r326_changed_input_provenance']", "inputs['r327_changed_input_provenance']")
one("'change': 'go-list adds -buildvcs=false; old rejected executable identity remains UNKNOWN'", "'change': 'build-cli and build-test add -p=1; old quiet native1 cause remains UNKNOWN',\n    'parallelism_preparation_review_ref': pin(BASE / 'cli43_compiler_parallelism_static_independent_review_codex/3cd7de459bfb4caf8cbfa7044c75381c/review.json'),\n    'prior_actual_root_completion_ref': pin(OLD / 'root-launch.outer-completion.json'),\n    'prior_root_closed_manifest_ref': pin(OLD / 'root-launch.closed.manifest.json'),\n    'triage_handoff_ref': pin(BASE / 'cli43_quiet_build_readonly_triage_codex/11fc59d13e2547ebbf71c593b46f596a/handoff.json')")
one('c942ced8bc4e34668e74997a1950150816ee819298e54a448b588e0e3ea2eb20', '68a0986a0bfcf39948ab2f696e33ef9ec05b39bb5a23f8787f92bf0129fe3566')
one("'Original r325 namespace byte prefix preserved'", "'Original r326 namespace byte prefix preserved'")
ast.parse(source, filename='stage-r327-parallel.py')
data = source.encode('utf-8')
with (OUT / 'stage-r327-parallel.py').open('xb') as stream:
    stream.write(data)
print({'prepared_script_sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'actual_target_execution': False})
