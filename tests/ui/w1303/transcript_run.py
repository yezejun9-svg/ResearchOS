"""Drive a fresh 201-message fixture through real CLI and Electron read paths."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import queue
import sqlite3
import subprocess
import sys
import tempfile
import threading
import uuid


ROOT = Path(__file__).resolve().parents[3]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            value.update(chunk)
    return value.hexdigest()


def save(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def counts(database: Path, project: str) -> dict:
    uri = database.resolve().as_uri() + '?mode=ro'
    with sqlite3.connect(uri, uri=True, timeout=10) as db:
        task = db.execute("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task'", (project,)).fetchone()[0]
        run = db.execute("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run'", (project,)).fetchone()[0]
        effect = db.execute('SELECT count(*) FROM resource_effects WHERE project=?', (project,)).fetchone()[0]
    return {'task': task, 'run': run, 'effect': effect}


def snapshot_from_cli(raw: str) -> tuple[dict, dict]:
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if len(rows) != 1 or rows[0].get('status') != 'COMPLETED':
        raise RuntimeError('CLI status did not complete')
    operations = rows[0].get('operations') or []
    if [item.get('method') for item in operations[:2]] != ['session.get', 'host.status'] or any(item.get('status') != 'COMPLETED' for item in operations[:2]):
        raise RuntimeError('CLI status omitted completed session.get or host.status')
    return rows[0], operations[0].get('result') or {}


def main() -> int:
    run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    out = ROOT / 'execution/v2.4/receipts/W13/W13-03' / ('transcript-gui-' + run_id)
    out.mkdir(parents=True, exist_ok=False)
    temp = Path(tempfile.mkdtemp(prefix='researchos-w13-ui-transcript-', dir=ROOT / '.local'))
    lock_file = ROOT / 'execution/toolchains/locked.json'
    locked = json.loads(lock_file.read_text(encoding='utf-8-sig'))['tools']
    go, node, python = [Path(locked[name]['path']) for name in ('go', 'node', 'python')]
    env = dict(os.environ, GOTOOLCHAIN='local', GOENV='off', RESEARCHOS_TASK_ID='W13',
               RESEARCHOS_DESKTOP_USER_DATA=str(temp / 'electron-user-data'),
               RESEARCHOS_CLI_CONFIG=str(temp / 'cli-config.json'))
    env.pop('ROS_DESKTOP_SMOKE', None)
    report = {'schema': 'researchos.desktop-transcript-observation.v1', 'step_id': 'W13-03',
              'run_id': run_id, 'status': 'EXECUTING', 'measurement_mode': 'FIXTURE', 'whole_card_accepted': False,
              'provider_calls': 0, 'commands': [], 'checks': {}, 'source_hashes': {}, 'tool_hashes': {},
              'limitations': ['Folder choice used a fixture callback, not a human OS picker.',
                              'No provider or Run was invoked; this is not a LIVE response or independent acceptance.']}
    helper = log = None

    def command(argv, name, timeout=180):
        options = dict(cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
        if os.name == 'nt':
            options['creationflags'] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run([str(arg) for arg in argv], **options)
        (out / (name + '.stdout.txt')).write_text(result.stdout, encoding='utf-8')
        (out / (name + '.stderr.txt')).write_text(result.stderr, encoding='utf-8')
        report['commands'].append({'argv': [str(arg) for arg in argv], 'exit_code': result.returncode})
        if result.returncode:
            raise RuntimeError(f'{name} exited {result.returncode}; raw output retained')
        return result.stdout

    def check(name, okay):
        report['checks'][name] = bool(okay)
        if not okay:
            raise RuntimeError('assertion failed: ' + name)

    try:
        check('WINDOWS_ONLY', os.name == 'nt')
        check('PINNED_PYTHON', Path(sys.executable).resolve() == python.resolve())
        for name, executable in [('go', go), ('node', node), ('python', python)]:
            check('PINNED_' + name.upper() + '_HASH', executable.is_file() and digest(executable) == locked[name]['sha256'])
            report['tool_hashes'][name] = {'path': str(executable), 'sha256': digest(executable)}
        report['source_hashes'][lock_file.relative_to(ROOT).as_posix()] = digest(lock_file)
        for folder in ['tests/ui/w1303/workspace_fixture', 'apps/web/src', 'apps/desktop/main', 'apps/desktop/preload',
                       'internal/domain', 'apps/cli']:
            for file in sorted((ROOT / folder).rglob('*')):
                if file.is_file() and file.suffix in ('.go', '.js', '.jsx', '.cjs', '.css'):
                    report['source_hashes'][file.relative_to(ROOT).as_posix()] = digest(file)
        for file in [ROOT / 'tests/ui/w1303/transcript.cjs', ROOT / 'tests/ui/w1303/transcript_run.py']:
            report['source_hashes'][file.relative_to(ROOT).as_posix()] = digest(file)
        vite = ROOT / 'apps/web/node_modules/vite/bin/vite.js'
        check('INSTALLED_VITE', vite.is_file())
        report['tool_hashes']['vite_js'] = digest(vite)
        command([node, vite, 'build', ROOT / 'apps/web'], 'web-build')
        binary, cli = temp / 'transcript-fixture.exe', temp / 'researchos-cli.exe'
        command([go, 'build', '-o', binary, './tests/ui/w1303/workspace_fixture'], 'fixture-build')
        command([go, 'build', '-o', cli, './apps/cli'], 'cli-build')
        report['tool_hashes']['fixture_exe'], report['tool_hashes']['cli_exe'] = digest(binary), digest(cli)
        electron = ROOT / 'apps/desktop/node_modules/electron/dist/electron.exe'
        check('INSTALLED_ELECTRON', electron.is_file())
        report['tool_hashes']['electron_exe'] = digest(electron)
        log = (out / 'fixture.stderr.txt').open('w', encoding='utf-8')
        helper = subprocess.Popen([str(binary), '--dir', str(temp / 'service'), '--transcript'], cwd=ROOT, env=env,
                                  stdout=subprocess.PIPE, stderr=log, text=True, encoding='utf-8', errors='replace',
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        lines = queue.Queue()
        threading.Thread(target=lambda: lines.put(helper.stdout.readline()), daemon=True).start()
        fixture = json.loads(lines.get(timeout=150))
        (out / 'fixture.ready.json').write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        for field in ('base_url', 'discovery_file', 'project_id', 'session_id', 'goal_id', 'task_id', 'transcript_artifact_ref'):
            check('READY_' + field.upper(), bool(fixture.get(field)))
        check('FIXTURE_COUNTS', fixture['seed_count'] == 200 and fixture['visible_count'] == 200 and fixture['full_count'] == 201)
        check('FIXTURE_NO_RUN_EFFECT', fixture['after_run_count'] == 0 and fixture['after_effect_count'] == 0 and fixture['after_task_count'] == fixture['before_task_count'] + 1)
        env.update(RESEARCHOS_CLI_DISCOVERY=fixture['discovery_file'], RESEARCHOS_PROJECT_ID=fixture['project_id'],
                   RESEARCHOS_SESSION_ID=fixture['session_id'])
        current_counts = counts(temp / 'service/data/researchos.sqlite', fixture['project_id'])
        check('PREVIEW_START_COUNTS', current_counts == {'task': fixture['after_task_count'], 'run': 0, 'effect': 0})
        before_raw = command([cli, 'status', '--project', fixture['project_id'], '--session', fixture['session_id'], '--output', 'jsonl'], 'cli-before')
        _, before = snapshot_from_cli(before_raw)
        ref = fixture['transcript_artifact_ref']
        check('CLI_SCOPE_AND_REF', before.get('project_id') == fixture['project_id'] and before.get('session_id') == fixture['session_id'] and
              before.get('goal_id') == fixture['goal_id'] and before.get('transcript_artifact_ref') == ref)
        check('CLI_VISIBLE_200', len(before.get('messages') or []) == 200 and before.get('has_earlier_messages') is True)
        check('CLI_WATERMARK', before.get('event_sequence') == fixture['snapshot_event_sequence'])
        input_file = temp / 'transcript-input.json'
        save(input_file, fixture)
        command([node, ROOT / 'tests/ui/w1303/transcript.cjs', input_file, out], 'electron-transcript', 180)
        after_raw = command([cli, 'status', '--project', fixture['project_id'], '--session', fixture['session_id'], '--output', 'jsonl'], 'cli-after')
        _, after = snapshot_from_cli(after_raw)
        check('CLI_READS_NO_EVENT', before.get('event_sequence') == after.get('event_sequence') == fixture['snapshot_event_sequence'])
        check('CLI_READS_SAME_REF', after.get('transcript_artifact_ref') == ref)
        final_counts = counts(temp / 'service/data/researchos.sqlite', fixture['project_id'])
        save(out / 'read-only-counts.json', {'before': current_counts, 'after': final_counts})
        check('CLI_DESKTOP_READ_ONLY', final_counts == current_counts)
        report['fixture'] = {key: value for key, value in fixture.items() if key not in ('base_url', 'discovery_file')}
        report['status'] = 'PASS'
    except Exception as error:
        report['status'], report['error'] = 'FAIL', str(error)
    finally:
        if helper and helper.poll() is None:
            helper.terminate()
            try:
                helper.wait(timeout=10)
            except subprocess.TimeoutExpired:
                helper.kill(); helper.wait(timeout=5)
        if log:
            log.close()
        report['temporary_data'], report['temporary_data_retained'] = str(temp), True
        report['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        save(out / 'run.json', report)
    print(json.dumps({'status': report['status'], 'receipt': str(out / 'run.json'), 'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
