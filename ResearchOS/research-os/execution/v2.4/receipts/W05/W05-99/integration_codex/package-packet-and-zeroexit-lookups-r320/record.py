import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path
import subprocess

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PACKAGE = Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')

def ref(path):
    p = Path(path).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return ref(OUT / name)

diagnostic = save('zeroexit.path-diagnostics.json', {
    'schema': 'researchos.actual-readonly-tool-diagnostics.v1',
    'actor': 'codex:/root', 'counter_reset': False,
    'observations': [
        {'tool_trace': 'b1bbcd', 'actual_outer_exit': 0, 'actual_native_exit': None,
         'path': 'contracts/execution.plan.json', 'error': 'Get-Content cannot find path',
         'correction': '66663f actual inventory found external package contracts/execution.plan.json; 11a5a6 verified its fixed SHA a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17.'},
        {'tool_trace': '74a67e', 'actual_outer_exit': 0, 'actual_native_exit': None,
         'path': 'tools/task_packet.py', 'error': 'Get-Content cannot find path',
         'correction': '66663f actual inventory found external package tools/task_packet.py; 11a5a6 read the actual source.'},
    ],
    'nonzero_execution_origins_added': 0,
    'limit': 'PowerShell retained nonterminating lookup errors while final commands returned outer0. No separate cmdlet native exit was captured; neither native1 nor a nonzero tool exit is invented.',
    'product_executions': 0, 'HTTP': 0, 'formal_increment': 0,
})
plan_ref = ref(PACKAGE / 'contracts/execution.plan.json')
assert plan_ref['sha256'] == 'a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17'
tool_ref = ref(PACKAGE / 'tools/task_packet.py')
state_ref = ref(ROOT / 'execution/v2.4/step_state.json')
assert state_ref['sha256'] == 'fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149'
argv = [sys.executable, '-I', '-S', '-X', 'utf8', tool_ref['path'], 'next', '--state', state_ref['path']]
with (OUT / 'next.stdout.raw').open('xb') as stdout, (OUT / 'next.stderr.raw').open('xb') as stderr:
    result = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=30)
invocation = save('next.invocation.json', {'argv': argv, 'cwd': str(ROOT), 'actual_native_exit': result.returncode,
    'tool_ref': tool_ref, 'plan_ref': plan_ref, 'state_ref': state_ref,
    'stdout_ref': ref(OUT / 'next.stdout.raw'), 'stderr_ref': ref(OUT / 'next.stderr.raw'),
    'product_executions': 0, 'automatic_retry': False, 'counter_reset': False})
assert result.returncode == 0
packet = json.loads((OUT / 'next.stdout.raw').read_bytes())
assert ref(PACKAGE / 'contracts/execution.plan.json') == plan_ref
assert ref(PACKAGE / 'tools/task_packet.py') == tool_ref
assert ref(ROOT / 'execution/v2.4/step_state.json') == state_ref
manifest = save('manifest.json', {'entries': [ref(p) for p in sorted(OUT.iterdir()) if p.is_file()], 'self_excluded': True})
handoff = save('handoff.json', {'packet_invocation_ref': invocation, 'diagnostics_ref': diagnostic,
    'manifest_ref': manifest, 'eligibility_is_acceptance': False, 'formal_increment': 0})
print(json.dumps({'handoff_ref': handoff, 'packet_keys': list(packet), 'packet_read_only': True}, ensure_ascii=True))
