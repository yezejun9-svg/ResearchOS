"""Exact W02 parent gates, preserving the two historical build handlers."""
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PARENTS = ('W02-G01', 'W02-G02', 'W02-G03')
LEGACY_TASKS = ('W02','W03','W04','W05','W06','W07','W08','W09','W10','W11','W12','W13','W18')


def route(environment):
    task = environment.get('RESEARCHOS_TASK_ID', 'W02')
    check = environment.get('RESEARCHOS_CHECK_ID', '')
    case = environment.get('RESEARCHOS_CASE_ID', '')
    if case or task not in LEGACY_TASKS:
        return 'reject', [], {}
    if task == 'W02' and check in PARENTS:
        return 'parent', ['-B', str(HERE / 'parent_driver.py'), check], {}
    if task == 'W02' and check in ('', 'W02-03'):
        return 'v24', ['apps/cli/build_check.py'], {}
    # The legacy handler itself rejects mismatched task/check pairs. Forward its
    # original argv and streams instead of converting that failure into success.
    return 'legacy', ['-X', 'utf8', 'ops/ci/build.py'], {'RESEARCHOS_EXECUTOR_ID': 'codex:/root'}


def main():
    kind, args, fixed = route(os.environ)
    if kind == 'reject':
        print(json.dumps({'status': 'NOT_IMPLEMENTED', 'assertion_ids': [], 'assertions': 0}))
        return 3
    env = dict(os.environ)
    if kind == 'legacy':
        env.pop('ELECTRON_OVERRIDE_DIST_PATH', None)
    env.update(fixed)
    return subprocess.call([sys.executable, *args], cwd=ROOT, env=env, shell=False)


if __name__ == '__main__':
    sys.exit(main())
