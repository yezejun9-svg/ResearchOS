import ast
import hashlib
import json
import sys
import traceback
import types
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
Q = Path(__file__).resolve().parent
C = R / 'execution/v2.4/receipts/W05/W05-99/public22_to_main23_continuation_caller_source_codex/continue-20261010-03'
S = R / 'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
G = R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'

def ref(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    path = Q / name
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return ref(path)

def main():
    hdf = json.loads((C / 'HDF.json').read_text(encoding='utf-8'))
    refs = [ref(C / 'HDF.json'), hdf['manifest_ref'], hdf['caller_ref'], hdf['calling_contract_ref'],
            hdf['original1201_preserved_ref'],
            ref(S / 'w09.w05-failed-scope-consumed-cp386.actual-audit.root.json'),
            ref(S / 'w09.w05-failed-scope-consumed-cp386.original.raw.jsonl'),
            ref(S / 'RESUME.cp386-br6-seed0-propose-failed-main-candidate.live1211.root.json')]
    raw = G.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    gm = types.ModuleType('p22_scope_diagnosis_guard'); gm.__file__ = str(G)
    exec(compile(raw, str(G), 'exec'), gm.__dict__)
    guard = gm.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    primary = None
    try:
        guard.acquire(refs)
        source = guard.get_buffer(hdf['caller_ref']['path']).decode('utf-8')
        tree = ast.parse(source)
        selections = {'lease', 'projection', 'scope_projection', 'build', 'registration', 'live', 'root_request'}
        functions = [{'name': node.name, 'line': node.lineno, 'end_line': node.end_lineno,
                      'source': ast.get_source_segment(source, node)} for node in tree.body
                     if isinstance(node, ast.FunctionDef) and node.name in selections]
        uses = []
        lines = source.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in {'KEY', 'SLICE'}:
                uses.append({'name': node.id, 'line': node.lineno, 'source': lines[node.lineno - 1]})
        outputs = [save('Source03-generation-excerpts.json', {'functions': functions, 'KEY_SLICE_uses': uses})]
        capture = json.loads(guard.get_buffer(str(S / 'w09.w05-failed-scope-consumed-cp386.actual-audit.root.json')))
        resume = json.loads(guard.get_buffer(str(S / 'RESUME.cp386-br6-seed0-propose-failed-main-candidate.live1211.root.json')))
        preserved = json.loads(guard.get_buffer(hdf['original1201_preserved_ref']['path']))
        outputs.append(save('basis.json', {'schema': 'researchos.public22-main23-generation-diagnosis-basis.v1',
                        'source_refs': refs, 'Source03_hdf': hdf, 'closed_scope_actual_audit': capture,
                        'Root_resume': resume, 'original1201_preserved': preserved,
                        'live_Canon_read': False, 'product_calls': 0}))
        print(json.dumps({'output_refs': outputs, 'capture': capture,
                          'resume_top_fields': list(resume), 'preserved': preserved,
                          'KEY_SLICE_uses': uses}, ensure_ascii=False))
    except BaseException as exc:
        primary = {'type': type(exc).__name__, 'message': str(exc)}
        traceback.print_exc()
    finally:
        closed = guard.close()
        cleanup_ref = save('SourceGuard.closed.json', closed)
        print(json.dumps({'cleanup_ref': cleanup_ref, 'primary': primary, 'closed': closed['closed'],
                          'retained_handles_count': closed['retained_handles_count']}, ensure_ascii=False))
    return 0 if primary is None and closed['closed'] and closed['retained_handles_count'] == 0 and closed['errors'] == [] else 1

if __name__ == '__main__':
    code = main()
    print('ROOT_PYTHON_EXIT=' + str(code))
    sys.exit(code)
