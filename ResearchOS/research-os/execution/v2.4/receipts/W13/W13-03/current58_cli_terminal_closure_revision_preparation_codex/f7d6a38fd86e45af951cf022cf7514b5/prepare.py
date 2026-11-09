"""Two-hunk pure IO/AST source preparation, never candidate execution."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
P13 = ROOT/'execution/v2.4/receipts/W13/W13-03'
OLD = P13/'current58_cli_terminal_closure_preparation_codex/25b9dd0b813a48689256356402789b13'
REVIEW = P13/'current58_cli_terminal_closure_independent_source_review_codex/7c2f53785d284c10b329e9aa7c6c3541'
OUT = Path(__file__).resolve().parent

def ref(path):
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, data):
    raw = data if isinstance(data, bytes) else (json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    with (OUT/name).open('xb') as stream:
        stream.write(raw)

inputs = [OLD/n for n in ('close-root-launch.current58.final.proposed.py','contract.final.json','request.proposed.json','handoff.json','manifest.json')]
inputs += [REVIEW/n for n in ('review.json','handoff.json','manifest.json')]
before = [ref(path) for path in inputs]
assert before[0]['sha256'] == '4ba31acaa6358f8625bd03e0f7de11e915ef0cd1d52f52ac54669331e4efd2b6'
assert before[5]['sha256'] == 'dc9b4c790b2a75ad9ea666f5464dfb498b3f01ba2001291fbf1fd93f3d46ac6c'
assert before[6]['sha256'] == 'b44cf45a08c656346fbafe0b0d66cd79ad92d057ed0e41f01aa6c88c5cbc50ac'
assert before[7]['sha256'] == 'bc157cb1bc114e28596cd6d1074a3460be4dc06e64354b9b2ec21926a75a7ac1'
old = inputs[0].read_bytes()
edits = [
    {'id':'C58-CLOSE-R01', 'before':b"markers = re.findall(r'^PythonNativeExit=([0-9]+)\\s*$', final['output'], flags=re.MULTILINE)",
     'after':b"markers = re.findall(r'^(?:PythonNativeExit|ACTUAL_PYTHON_EXIT)=([0-9]+)\\s*$', final['output'], flags=re.MULTILINE)"},
    {'id':'C58-CLOSE-R02', 'before':b"assert Path(q['executor_manifest_ref']['path']).parent == executor\nassert Path(q['launcher_manifest_ref']['path']).parent == launcher",
     'after':b"assert Path(q['executor_manifest_ref']['path']) == executor / 'manifest.json'\nassert Path(q['launcher_manifest_ref']['path']) == launcher / 'manifest.json'"},
]
new = old
for edit in edits:
    assert new.count(edit['before']) == 1
    new = new.replace(edit['before'], edit['after'])
inverse = new
for edit in reversed(edits):
    assert inverse.count(edit['after']) == 1
    inverse = inverse.replace(edit['after'], edit['before'])
assert inverse == old
old_ast, new_ast = ast.parse(old), ast.parse(new)
old_defs = {n.name:ast.dump(n, include_attributes=False) for n in old_ast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
new_defs = {n.name:ast.dump(n, include_attributes=False) for n in new_ast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert old_defs == new_defs
assert b'assert len(markers) <= 1\npython_native_exit = int(markers[0]) if markers else None\nif python_native_exit is not None:\n    assert python_native_exit == final[\'exit_code\']' in new
assert new[new.index(b'closed = {'):] == old[old.index(b'closed = {'):]
save('close-root-launch.current58.v2.proposed.py', new)
save('two-hunk.inverse.json', {'source_ref':before[0], 'selected_ref':ref(OUT/'close-root-launch.current58.v2.proposed.py'), 'edits':[{'id':e['id'],'before_hex':e['before'].hex(),'after_hex':e['after'].hex()} for e in edits], 'whole_byte_inverse_equal':True})
save('source.diff', ''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='old4ba.proposed.py',tofile='v2.proposed.py')).encode())
save('inputs.before.json', before)
after = [ref(path) for path in inputs]
assert before == after
save('inputs.after.json', after)
save('static-audit.json', {'AST_parse':True,'whole_byte_inverse_equal':True,'exact_hunks':2,'unchanged_definition_names':list(old_defs),'completion_and_publication_tail_byte_equal':True,'original_marker_count_and_outer_equality_guards_byte_unchanged':True,'inputs':len(before),'input_drift_count':0,'candidate_imports':0,'candidate_calls':0,'current_E_L_export_caller_reads':0,'target_calls':0,'new_failure_origins':[]})
save('contract.json', {'status':'SOURCE_PREPARATION_ONLY_NOT_RUN','inherits_contract_ref':before[1],'request_template_ref':before[2],'review_ref':before[5],'fixes':{'C58-CLOSE-R01':'One anchored noncapturing alternation accepts only PythonNativeExit and ACTUAL_PYTHON_EXIT. Existing total-count <=1 rejects duplicate same-label or mixed-label entries even when equal. Marker/outer equality remains. No marker remains NULL.','C58-CLOSE-R02':'Selected MF paths must equal the corresponding executor/manifest.json and launcher/manifest.json before full_manifest. Original publication pins those same canonical files through unchanged READS drift guards.'},'future_controls_NOT_RUN':['one legacy marker','one actual marker','no marker keeps NULL','duplicate same label refuses','two labels same value refuse','contradictory labels refuse','marker versus outer mismatch refuses','canonical manifest pair','same-directory alternate manifest refuses','published MF identity equals fully verified MF identity'],'unchanged':['original completion wire and full output tail','firstcause/native NULL','all nine definitions','case/compile/source/formal qualification false/PENDING','Root supplies actual terminal and MF/request refs','no candidate import or target execution'], 'actual_Run_qualification':False})
print(json.dumps({'selected_ref':ref(OUT/'close-root-launch.current58.v2.proposed.py'),'input_count':len(before),'AST_only':True,'target_calls':0},ensure_ascii=False))
