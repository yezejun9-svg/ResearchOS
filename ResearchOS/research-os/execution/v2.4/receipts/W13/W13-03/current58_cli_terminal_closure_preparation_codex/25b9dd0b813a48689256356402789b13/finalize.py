"""Pure IO/AST compatibility corrections from actual old wire; no candidate execution."""
import ast
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
OLD = ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r331-c4f309c5528f5d42be5e7eeb146a20aa'

def ref(path):
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    raw = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode()
    with (OUT/name).open('xb') as f:
        f.write(raw)

previous = (OUT/'close-root-launch.current58.proposed.py').read_bytes()
source = previous.decode()
edits = []
def replace(before, after):
    global source
    assert source.count(before) == 1
    source = source.replace(before, after)
    edits.append({'before': before, 'after': after})

replace("    assert pin(row['path']) == row\n    return READS[row['path']]", """    path = Path(row['path'])
    if not path.is_absolute():
        assert path.as_posix() == row['path'] and '..' not in path.parts
        path = ROOT / path
    actual = pin(path)
    assert actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes']
    return READS[actual['path']]""")
replace("assert grant['scope_ref'] == q['scope_ref']", """assert verified(grant['scope_ref']) == verified(q['scope_ref'])
assert (ROOT / grant['scope_ref']['path']).resolve() == Path(q['scope_ref']['path']).resolve()
assert grant['binding']['run_uuid'] == q['run_uuid'] and grant['binding']['source_commit'] == q['source_commit']""")
replace("expected_argv = [scope['python_ref']['path'], '-I'", "expected_argv = ['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe', '-I'")
replace("executor_rows = full_manifest(q['executor_manifest_ref'], executor)\nlauncher_rows = full_manifest(q['launcher_manifest_ref'], launcher)\n", "")
replace("assert type(final['exit_code']) is int and 'session_id' not in final", """assert type(final['exit_code']) is int and 'session_id' not in final""")
# Manifest reads follow authenticated-to-request terminal input/response pairing, never before it.
replace("assert tools['automatic_retry'] is False and tools['counter_reset'] is False", """assert tools['automatic_retry'] is False and tools['counter_reset'] is False
executor_rows = full_manifest(q['executor_manifest_ref'], executor)
launcher_rows = full_manifest(q['launcher_manifest_ref'], launcher)""")
replace("for entry in q['additional_sealed_refs']:\n    verified(entry)", """assert type(q['additional_sealed_refs']) is list and q['additional_sealed_refs']
for entry in q['additional_sealed_refs']:
    verified(entry)""")
final = source.encode()
ast.parse(final)
inverse = source
for item in reversed(edits):
    assert inverse.count(item['after']) == 1 if item['after'] else True
    if item['after']:
        inverse = inverse.replace(item['after'], item['before'])
    else:
        anchor = "assert Path(q['launcher_manifest_ref']['path']).parent == launcher\n"
        assert inverse.count(anchor) == 1
        inverse = inverse.replace(anchor, anchor+item['before'])
assert inverse.encode() == previous
save('close-root-launch.current58.final.proposed.py', final)
save('wire-compatibility.inverse.json', {'previous_ref': ref(OUT/'close-root-launch.current58.proposed.py'), 'final_ref': ref(OUT/'close-root-launch.current58.final.proposed.py'), 'edits': edits, 'whole_byte_inverse_equal': True, 'reason': 'Actual grant scope ref is ROOT-relative, caller Python argv uses slash literal; terminal pairing precedes E/L member reads.'})
extra = [OLD/'root-launch.intent.json', ROOT/'execution/v2.4/receipts/W05/W05-99/cli43_fresh_compiler_authorization_codex/c4f309c5528f5d42be5e7eeb146a20aa/authorization.execute.json']
save('additional-inputs.json', [ref(p) for p in extra])
contract = json.loads((OUT/'contract.json').read_bytes())
contract['selected_source_ref'] = ref(OUT/'close-root-launch.current58.final.proposed.py')
contract['literal_compatibility'] = ['ROOT-relative grant scope_ref and canonical copies are read using ROOT; SHA/bytes and actual raw remain exact.', 'Caller argv Python slash literal matches sealed caller source; remaining argv equals exact actual intent.', 'Final terminal action pairing checked before E/L manifest member reads.']
contract['failure_closure_limit'] = 'A failed run can be recorded if authentic terminal/caller evidence and both complete sealed E/L manifests exist; missing or contradictory evidence fails closed rather than creates SUCCESS.'
save('contract.final.json', contract)
print(json.dumps({'final_source_ref': ref(OUT/'close-root-launch.current58.final.proposed.py'), 'AST_only': True, 'candidate_executed': False}, ensure_ascii=False))
