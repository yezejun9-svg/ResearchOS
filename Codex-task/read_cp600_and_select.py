import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
SPEC = Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
OUT = HERE / 'cp600-root-readback'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def git(*args): return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '--no-optional-locks', '-C', str(ROOT), *args], stderr=subprocess.STDOUT).decode('utf-8')
assert not OUT.exists(), 'Inspect prior readback rather than overwrite'
cp = read(ROOT / 'execution/v2.4/checkpoint.json')
assert cp['revision'] == 600 and len(cp['failure_counters']) == 2448
assert git('rev-parse', 'HEAD').strip() == cp['current_Main_HEAD'] == 'b8e9efeee3c95dcb8577e5f3fee56ed0b812afc1'
receipt = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/clients'
assert read(receipt / 'root-integration-journal.json')['status'] == 'MAIN_CHECKPOINT_HANDOFF_SAVED'
integrated = read(receipt / 'integration.json')
for rel, digest in integrated['source_sha256'].items(): assert sha(ROOT / rel) == digest, rel
protected = read(ROOT / 'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json')['protected_preserved']
for rel, digest in protected.items(): assert (sha(ROOT / rel) if (ROOT / rel).is_file() else 'ABSENT_BEFORE') == digest, rel
status = git('status', '--porcelain=v1', '-uno')
assert len(status.splitlines()) == 20
OUT.mkdir()
command = [r'C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\python.exe', str(SPEC / 'tools/task_packet.py'), 'next', '--state', str(ROOT / 'execution/v2.4/step_state.json')]
result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(OUT / 'task-packet.stdout.json').write_bytes(result.stdout)
(OUT / 'task-packet.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
packet = json.loads(result.stdout)
summary = dict(checkpoint=600, main_head=cp['current_Main_HEAD'], source_pins=len(integrated['source_sha256']), protected_entries=len(protected), original_tracked_statuses=20,
    failure_records=2448, formal_increment=0, selector_exit=result.returncode, selector_keys=list(packet),
    selector_plan_source=packet.get('plan_source'), selector_step=packet.get('step', {}).get('id'),
    selector_authority=packet.get('execution_authority'), model_probe_replay_allowed=False)
(OUT / 'readback.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=True))
