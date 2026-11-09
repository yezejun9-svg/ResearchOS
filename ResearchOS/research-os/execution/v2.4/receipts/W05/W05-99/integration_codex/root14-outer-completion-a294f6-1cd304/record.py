import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
assert sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize


def ref(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


scope_path = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-root-replay-draft/root_finite14_scope.v3.json'
scope_ref = ref(scope_path)
assert scope_ref['sha256'] == '55e4c169937d2ecc4bc1aaa98e30538dab8071e9870ffd1c7c3309a636e81eda'
scope = json.loads(scope_path.read_bytes())
tool = json.loads((OUT / 'tool-result.json').read_bytes())
assert tool['exit_code'] == 0 and tool['chunk_id'] == '1cd304' and tool.get('session_id') is None
lock = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
completed = ROOT / scope['new_authorization_root'] / 'completed.json'
assert json.loads(completed.read_bytes())['actual_exit'] == 0
receipt = {'schema': 'researchos.root-finite14-outer-completion.v1', 'actor': 'codex:/root',
    'actual_outer_exit': 0, 'actual_native_launcher_exit': None, 'tool_initial_chunk': 'a294f6',
    'session_id': 6787, 'tool_completion_chunk': '1cd304', 'tool_result_ref': ref(OUT / 'tool-result.json'),
    'tool_capture': 'Saved JSON representation of actual final tool-return fields, including exact empty output; it is not separately redirected native process stdout.',
    'launcher_ref': scope['launcher_ref'], 'scope_ref': scope_ref, 'run_uuid': scope['run_uuid'],
    'cwd': 'D:/作品集/ResearchOS/research-os', 'argv': ['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe',
        '-I', '-S', '-X', 'utf8', scope['launcher_ref']['path'], 'D:/作品集/ResearchOS/research-os/' + scope_ref['path'], scope_ref['sha256']],
    'program_reported_completed_ref': ref(completed),
    'native_limit': 'No separate shell-native launcher exit capture; native remains null. completed reported0 and inner held-process native0 are independently recorded evidence.',
    'automatic_retry': False, 'counter_reset': False, 'source_acceptance': False, 'formal_increment': 0}
with (OUT / 'outer-completion.json').open('xb') as stream:
    stream.write((json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
print(json.dumps({'outer_completion': ref(OUT / 'outer-completion.json'), 'actual_outer_exit': 0, 'actual_native_launcher_exit': None}, ensure_ascii=True))
