"""Generate new metadata-only scope staging from the preserved reviewed predecessor."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import uuid

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
BASE = ROOT / 'execution/v2.4/receipts/W05/W05-99'
original = BASE / 'integration_codex/cli43-fresh-held2-r327-efa7776ec48e4a7abaa92ce85eb0dace/stage-r328-test2json.py'
raw = original.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'faf66685db9ac878189b03a3aa1e4247ced1fa0036e0ad60c7a52c7824a460a9'
uid, review_uid = uuid.uuid4().hex, uuid.uuid4().hex
text = raw.decode('utf-8')

def once(old, new):
    global text
    assert text.count(old) == 1, old
    text = text.replace(old, new)

once("UID = 'bf943a8137c74df09e010347615b0eec'", "UID = '" + uid + "'")
once("OUT = OLD.parent / ('cli43-fresh-held2-r328-' + UID)", "OUT = OLD.parent / ('cli43-fresh-held2-r329-' + UID)")
text = text.replace('cli43_failed_execution_independent_review_codex/3199a5187cee46729d7b8b2a6a5f7317',
                    'cli43_failed_execution_independent_review_codex/684f0c8b739541fe8da3b2f06ca78d09')
text = text.replace('3e4fe1b97b9a3a937ed2c557d240c91477e309c0e114d0549fbb4e83cce9dbcb',
                    '2685967ed7728d44182d671093cfee220b84bb438ea5d6524253573876750203')
once('cli43_current_bound_scope_independent_review_codex/b8b6f2f680cd4cb5986152ac4ef09994',
     'cli43_current_bound_scope_independent_review_codex/' + review_uid)
for old, new in [('[328,156,469]', '[329,157,481]'), ('[328, 156, 469]', '[329, 157, 481]'),
                 ('[327,155,459]', '[328,156,469]'), ('[327, 155, 459]', '[328, 156, 469]')]:
    text = text.replace(old, new)
text = text.replace('late-origins.capture.for-r328.json', 'late-origins.capture.for-r329.json')
text = text.replace('175c220137bc50a94e8af955797addf6b96cedb7535bfe87eb789de54af93af9',
                    '34f37419ecc6715ffe7e28cb80f3b716fdffc746db0126bc86b5fa6d77e57416')
text = text.replace("len(late['origins']) == 10", "len(late['origins']) == 12")
text = text.replace("len({r['evidence_ref']['sha256'] for r in origins}) == 10", "len({r['evidence_ref']['sha256'] for r in origins}) == 12")
text = text.replace('Fixed ten-origin', 'Fixed twelve-origin').replace('r327 desired', 'r328 desired').replace('Original r327', 'Original r328')
text = text.replace("replace('efa7776ec48e4a7abaa92ce85eb0dace', UID)", "replace('bf943a8137c74df09e010347615b0eec', UID)")
text = text.replace("SCOPE_SHA = '320fef447b526c1696075c9ae11fe8439d582d893239ed659c486b21562f5137'",
                    "SCOPE_SHA = 'edec4df6c5f4fcce632008517adff4c4b2a82f64bc4715d87c8a53e7fd3e19c3'")
hook = "template['debug_tree_helper_ref'] = helper\n"
once(hook, hook + """fix_root = BASE / 'cli43_http_bytes_ownership_preparation_codex/310e0bf842a34df6813dad1126e2970a'
fix_review = BASE / 'cli43_http_bytes_ownership_independent_review_codex/2c1fd6a5825447b99c8f7a9d6ceaa483/review.json'
need(pin(fix_root / 'handoff.json')['sha256'] == '2f8804bade77ee6bdf5c838055709167551ce76eab5f14acfd858e19d53ed56b', 'Exact byte ownership preparation')
need(pin(fix_review)['sha256'] == 'f6901f7c442c9e7aff7ebc36d47739f3316eb2f1cb3b5ba7316116d5e16b9789', 'Actual independent ownership review')
fix = doc(fix_root / 'handoff.json')
template['instrumentation_ref'] = pin(fix['instrumentation_plan_ref']['path'])
template['instrumentation_helper_ref'] = pin(fix['helper_ref']['path'])
need(template['instrumentation_ref']['sha256'] == 'a6262abc7510fc7974b5bebe71cc46a237d568729268e1686991024e6f8bf253', 'Reviewed plan')
need(template['instrumentation_helper_ref']['sha256'] == '37a3a61abe8fe81718021b17c7243fb3410c066a107cf346ec636b04bae176d9', 'Reviewed helper')
need(template['instrumented_source_ref']['sha256'] == fix['unchanged_instrumented_test_ref']['sha256'], 'Business tests unchanged')
""")
begin = "inputs['r328_changed_input_provenance'] = "
end = "save(OUT / 'root-inputs.runtime-bound.json', inputs)"
start, stop = text.index(begin), text.index(end)
text = text[:start] + """inputs['r329_changed_input_provenance'] = {
    'prior_run_independent_failed_closure_ref': pin(CLOSED),
    'same_input_retry': False, 'change': 'Export-only cli43Bytes immediately bytes.Clone before raw/len/SHA; no business or validator change.',
    'ownership_preparation_handoff_ref': pin(fix_root / 'handoff.json'),
    'ownership_preparation_review_ref': pin(fix_review),
    'runner_and_debug_helper_unchanged_from_r328': True,
    'prior_actual_root_completion_ref': pin(OLD / 'root-launch.outer-completion.json'),
    'prior_root_closed_manifest_ref': pin(OLD / 'root-launch.closed.manifest.json'),
    'late_cut_capture_ref': late_ref}
""" + text[stop:]
ast.parse(text)
new_file = OUT / 'stage-r329-http-owned-bytes.py'
with new_file.open('xb') as f:
    f.write(text.encode('utf-8'))
assert original.read_bytes() == raw
def pin(p):
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}
proof = {'actor': 'codex:/root', 'original_stage_ref': pin(original), 'new_stage_ref': pin(new_file),
    'new_root_namespace': str(OUT.parent / ('cli43-fresh-held2-r329-' + uid)),
    'reserved_independent_review_path': str(BASE / 'cli43_current_bound_scope_independent_review_codex' / review_uid / 'review.json'),
    'before': [328,156,469], 'after': [329,157,481], 'old_stage_original_bytes_equal': True,
    'Python_AST_without_target_execution': True, 'stage_executed': False, 'formal_increment': 0}
with (OUT / 'r329-stage-preparation.json').open('xb') as f:
    f.write((json.dumps(proof, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
print(json.dumps(proof, ensure_ascii=False))
