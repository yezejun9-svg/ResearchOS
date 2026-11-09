"""Prepare metadata-only next scope staging from the retained prior script."""
import ast
import hashlib
from pathlib import Path
import sys

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
OLD = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r326-477e329b79944cb0b33f9ead24811760/stage-r327-parallel.py'
raw = OLD.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '1245e90d082426fdc90497d4d62df4fb5a8ed886a1125a4e648b0654ab07694c'
text = raw.decode('utf-8')

def change(before, after):
    global text
    assert text.count(before) == 1, before[:100]
    text = text.replace(before, after)

change('changed compiler parallelism', 'explicit fresh test2json and rejected-load diagnostics')
change("UID = 'efa7776ec48e4a7abaa92ce85eb0dace'", "UID = 'bf943a8137c74df09e010347615b0eec'")
change("'cli43-fresh-held2-r327-'", "'cli43-fresh-held2-r328-'")
change("RUNNER_PACK = BASE / 'cli43_compiler_parallelism_preparation_codex/8ac0acd36c6047beaab455730692d078'", "RUNNER_PACK = BASE / 'cli43_test2json_preparation_codex/72d89fe5130e4e83a7dc44257289c1db'")
change("CLOSED = BASE / 'cli43_failed_execution_independent_review_codex/f41d184815b341e086a26d2a750f0b60/review.json'", "CLOSED = BASE / 'cli43_failed_execution_independent_review_codex/3199a5187cee46729d7b8b2a6a5f7317/review.json'")
change('cli43_current_bound_scope_independent_review_codex/bbd110051f5647d8b6386372ed2cd08c/review.json', 'cli43_current_bound_scope_independent_review_codex/b8b6f2f680cd4cb5986152ac4ef09994/review.json')
change('8cb8fb307dabe2668a736d7e964177a1fd67605a7f380d5f6e06d9268d59a6bb', '3e4fe1b97b9a3a937ed2c557d240c91477e309c0e114d0549fbb4e83cce9dbcb')
change('FAILED_EXECUTION_EVIDENCE_CLOSED_WITH_QUALIFICATION_WITHHELD', 'ACTUAL_FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD')
change('906e713f8ba9d6a0787b86d9b43b6d456f8b28d7784352df10e6d89f7543a605', '3f84b6b3c1230d237f0ac6c327e87b3d4152228810d47818d68c0c1b0b74c289')
change("['candidate_ref']['path']", "['runner_ref']['path']")
change("need(runner['sha256'] == '333d69e00a421efcbb08e9ddf06e1486e911cd82af4a0d46a8bb60c8203f2bea', 'Exact two compiler parallelism arguments')", "need(runner['sha256'] == '5297321f966da060d2f9e941d358052ef2dae63ccc6e1f1217e22bef87c52c0e', 'Exact independently reviewed test2json runner')\nhelper = pin(doc(RUNNER_PACK / 'handoff.json')['diagnostic_helper_ref']['path'])\nneed(helper['sha256'] == '9c771cd3b9fd41a71b70ced0b27ca45bd6a138b3ebff88ff50153530db407095', 'Exact independently reviewed diagnostic helper')")
change("== [326, 154, 450], 'Actual before tuple'", "== [327, 155, 459], 'Actual before tuple'")
change('Actual current canonical equals r326 desired', 'Actual current canonical equals r327 desired')
start = text.index("late_ref = pin(OLD / 'late-origins.capture.json')")
end = text.index("inputs['origin_cut_ref'] =", start)
oldblock = text[start:end]
newblock = """late_ref = pin(OLD / 'late-origins.capture.for-r328.json')
need(late_ref['sha256'] == '175c220137bc50a94e8af955797addf6b96cedb7535bfe87eb789de54af93af9', 'Fixed ten-origin cut retained verbatim')
late = doc(late_ref['path'])
need(late['before'] == [327,155,459] and late['after'] == [328,156,469] and len(late['origins']) == 10, 'Exact late cut')
origins = copy.deepcopy(late['origins'])
for row in origins:
    verified(row['evidence_ref'])
    need(all(old.get('evidence_ref', {}).get('sha256') != row['evidence_ref']['sha256'] for old in cp['failure_counters']), 'Origin already registered')
need(len({r['evidence_ref']['sha256'] for r in origins}) == 10, 'Distinct original evidence per origin')
inputs['before'] = [327, 155, 459]
inputs['after'] = [328, 156, 469]
"""
change(oldblock, newblock)
change("template['runner_ref'] = runner", "template['runner_ref'] = runner\ntemplate['debug_tree_helper_ref'] = helper")
change('scope.template.runner-v6.json', 'scope.template.runner-v7.json')
change("'477e329b79944cb0b33f9ead24811760', UID", "'efa7776ec48e4a7abaa92ce85eb0dace', UID")
change("inputs['r327_changed_input_provenance']", "inputs['r328_changed_input_provenance']")
change("'change': 'build-cli and build-test add -p=1; old quiet native1 cause remains UNKNOWN'", "'change': 'fresh cmd/test2json graph/build/buildinfo/pin then direct tool; first rejected hFile fact metadata only; old generation16 identity remains NULL'")
change("'parallelism_preparation_review_ref': pin(BASE / 'cli43_compiler_parallelism_static_independent_review_codex/3cd7de459bfb4caf8cbfa7044c75381c/review.json')", "'test2json_preparation_review_ref': pin(BASE / 'cli43_test2json_static_independent_review_codex/9fb108715041425d8c6dda77f2bd4d02/review.json')")
change("'triage_handoff_ref': pin(BASE / 'cli43_quiet_build_readonly_triage_codex/11fc59d13e2547ebbf71c593b46f596a/handoff.json')", "'triage_handoff_ref': pin(BASE / 'cli43_failed_execution_independent_review_codex/3199a5187cee46729d7b8b2a6a5f7317/handoff.json'), 'diagnostic_helper_ref': helper, 'late_cut_capture_ref': late_ref")
change('68a0986a0bfcf39948ab2f696e33ef9ec05b39bb5a23f8787f92bf0129fe3566', '320fef447b526c1696075c9ae11fe8439d582d893239ed659c486b21562f5137')
change('Original r326 namespace byte prefix preserved', 'Original r327 namespace byte prefix preserved')
ast.parse(text, filename='stage-r328-test2json.py')
dest = OUT / 'stage-r328-test2json.py'
with dest.open('xb') as stream:
    stream.write(text.encode('utf-8'))
print({'prepared_stage_sha256': hashlib.sha256(dest.read_bytes()).hexdigest(), 'bytes': dest.stat().st_size, 'staging_executed': False})
