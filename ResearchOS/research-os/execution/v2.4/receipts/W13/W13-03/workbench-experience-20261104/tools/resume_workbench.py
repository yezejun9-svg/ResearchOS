import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

REPO = Path('D:/作品集/ResearchOS/research-os')
RECEIPT = REPO / 'execution/v2.4/receipts/W13/W13-03/workbench-experience-20261104'
CANDIDATE = REPO / '.local/worktrees/workbench-experience-20261104'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def write_json(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    temporary = path.with_name(path.name + '.workbench-new')
    temporary.write_bytes(raw)
    os.replace(temporary, path)

def git(*args):
    return subprocess.run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', *args], cwd=REPO, check=True, capture_output=True).stdout

def main():
    RECEIPT.mkdir(parents=True, exist_ok=False)
    checkpoint = REPO / 'execution/v2.4/checkpoint.json'
    raw = checkpoint.read_bytes()
    state = json.loads(raw)
    assert state['revision'] == 575, 'Checkpoint moved; reconcile before writing'
    identity = json.loads((REPO / 'execution/project_identity.json').read_bytes())
    assert identity['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
    head = git('rev-parse', 'HEAD').decode().strip()
    assert head == 'ecc28dd3c91a0f68dcddb41b53325aa7f0e81419'
    (RECEIPT / 'checkpoint.before.json').write_bytes(raw)
    handoff = REPO / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
    (RECEIPT / 'handoff.before.md').write_bytes(handoff.read_bytes())
    tracked = git('status', '--porcelain=v1', '-uno')
    (RECEIPT / 'git-tracked.before.txt').write_bytes(tracked)
    (RECEIPT / 'git-full.before.txt').write_bytes(git('status', '--porcelain=v1'))
    (RECEIPT / 'worktrees.before.txt').write_bytes(git('worktree', 'list', '--porcelain'))
    protected = {}
    for line in tracked.decode('utf-8').splitlines():
        path = line[3:]
        target = REPO / path
        protected[path] = digest(target.read_bytes()) if target.is_file() else 'ABSENT_BEFORE'
    targets = {}
    for base in ['apps/web/src', 'apps/web/dist']:
        for path in (REPO / base).rglob('*'):
            if path.is_file():
                targets[path.relative_to(REPO).as_posix()] = digest(path.read_bytes())
    failures = digest(json.dumps(state['failure_counters'], sort_keys=True, ensure_ascii=False).encode())
    scope = {
        'schema': 'researchos.workbench-iteration.v1', 'at': datetime.now(timezone.utc).isoformat(),
        'executor_id': 'codex:/root', 'builder_id': 'codex:/root/workbench_builder',
        'project_id': identity['project_id'], 'base_head': head, 'parent_checkpoint': 575,
        'step_id': 'W13-03', 'mode': 'DEVELOPMENT_ONLY', 'product_acceptance': 'NOT_ASSERTED',
        'candidate': str(CANDIDATE), 'allowed_paths': ['apps/web/src/**', 'tests/ui/**'],
        'purpose': 'User-requested clean conversational Desktop, visible project activity, tool and iteration evidence; preserve existing API and permissions',
        'failure_counter_count_before': len(state['failure_counters']), 'failure_counter_sha256_before': failures,
        'step_state_sha256_before': digest((REPO / 'execution/v2.4/step_state.json').read_bytes()),
        'protected_tracked_before': protected, 'source_and_dist_before': targets,
        'outstanding_gates': ['W05-99', '22 parent task acceptance', '42 formal cases', 'W13-03 physical NVDA/foreground', 'Windows installer/native lifecycle', 'original CP575 native-helper/installer branches'],
        'external_actions': 'No Qoder, push, deploy, original data, original processes, installer or native recovery actions'
    }
    write_json(RECEIPT / 'scope-and-baseline.json', scope)
    resume = {'schema':'researchos.workbench-resume.v1', 'checkpoint_revision':576, 'status':'IN_PROGRESS',
              'step_id':'W13-03', 'candidate':str(CANDIDATE), 'base_head':head,
              'failure_counters_preserved':len(state['failure_counters']), 'formal_accepted':0, 'formal_required':42,
              'scope_ref': 'scope-and-baseline.json', 'next':'Finish UI candidate, build, isolated rendering checks, independent source review; retain all existing blocked gates'}
    write_json(RECEIPT / 'RESUME.json', resume)
    assert checkpoint.read_bytes() == raw, 'Concurrent checkpoint write; do not replace'
    state['expected_previous_revision'] = 575
    state['revision'] = 576
    state['user_workbench_iteration'] = {'status':'IN_PROGRESS', 'step_id':'W13-03',
        'resume_ref': (RECEIPT / 'RESUME.json').relative_to(REPO).as_posix(),
        'at':datetime.now(timezone.utc).isoformat(), 'failure_counters_preserved':len(state['failure_counters'])}
    write_json(checkpoint, state)
    prefix = '# Current user-requested workbench continuation CP576\n\nRead execution/v2.4/receipts/W13/W13-03/workbench-experience-20261104/RESUME.json for the new independent UI iteration. CP575 native/installer branches and all failure counters are preserved. W13-03 development only; full 22-parent/42-case goal remains unfinished.\n\n'
    temporary = handoff.with_name(handoff.name + '.workbench-new')
    temporary.write_bytes(prefix.encode('utf-8') + handoff.read_bytes())
    os.replace(temporary, handoff)
    print(json.dumps({'checkpoint':576,'receipt':str(RECEIPT),'protected_tracked':len(protected),'failure_counters':len(state['failure_counters'])}, ensure_ascii=False))

if __name__ == '__main__':
    main()
