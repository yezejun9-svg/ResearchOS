"""Ordinary Desktop launch with an owned process handle retained until exit."""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import time

ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
ELECTRON = ROOT / 'apps/desktop/node_modules/electron/dist/electron.exe'
ELECTRON_HASH = '8d205e25b40da3ada4a08c92f32bfbd8e8d38edb4bfe443deea77fc9de685bac'
DATA_ROOT = ROOT / '.local/live/current-chat-normal-desktop-first-use-20261012/data'
USER_DATA = ROOT / '.local/live/current-chat-normal-desktop-first-use-20261012/electron-user-data'

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

parser = argparse.ArgumentParser()
parser.add_argument('--package', required=True)
parser.add_argument('--receipts', required=True)
parser.add_argument('--cdp-port', type=int, required=True)
args = parser.parse_args()
package = pathlib.Path(args.package).resolve()
out = pathlib.Path(args.receipts).resolve()
assert package.is_relative_to(pathlib.Path('C:/Users/yqyyds/.codex').resolve())
assert out.is_relative_to((ROOT / 'execution/v2.4/receipts/W05/W05-99').resolve())
assert 1024 < args.cdp_port < 65536
assert hashlib.sha256(ELECTRON.read_bytes()).hexdigest() == ELECTRON_HASH
assert (package / 'apps/desktop/main/main.js').is_file()
assert (DATA_ROOT / 'researchos.sqlite').is_file() and (USER_DATA / 'desktop-context.json').is_file()
out.mkdir(parents=True, exist_ok=True)
assert not (out / 'launch.json').exists()
environment = os.environ.copy()
removed = []
for name in ['RESEARCHOS_CONTROL_EXE', 'RESEARCHOS_DESKTOP_VERIFIER_MANIFEST',
             'RESEARCHOS_DESKTOP_RUNTIME_ASSETS_DIR', 'RESEARCHOS_DESKTOP_LEGACY_WORKBENCH',
             'ROS_DESKTOP_SMOKE', 'ROS_DESKTOP_NATIVE_SMOKE', 'ROS_DESKTOP_CAPTURE_PATH']:
    if name in environment:
        removed.append(name)
        del environment[name]
explicit = {
    'RESEARCHOS_DATA_DIR': str(DATA_ROOT), 'RESEARCHOS_DESKTOP_USER_DATA': str(USER_DATA),
    'RESEARCHOS_CLI_DISCOVERY': str(DATA_ROOT / 'discovery.json'),
    'RESEARCHOS_HOST_DISCOVERY': str(DATA_ROOT / 'discovery.json'),
}
environment.update(explicit)
argv = [str(ELECTRON), str(package / 'apps/desktop'), '--remote-debugging-address=127.0.0.1',
        f'--remote-debugging-port={args.cdp_port}']
with (out / 'electron.stdout.raw').open('xb') as stdout, (out / 'electron.stderr.raw').open('xb') as stderr:
    process = subprocess.Popen(argv, cwd=package / 'apps/desktop', env=environment, stdout=stdout, stderr=stderr)
    write_new(out / 'launch.json', {'schema': 'researchos.normal-desktop-launch-owned-handle/1',
        'at': now(), 'pid': process.pid, 'argv': argv, 'cwd': str(package / 'apps/desktop'),
        'explicit_environment': explicit, 'removed_environment_names': removed,
        'smoke_mode': False, 'data_preserved': True, 'process_handle_owned': True,
        'models_dispatched_by_observer': 0, 'tools_dispatched_by_observer': 0, 'formal_increment': 0})
    print(json.dumps({'event': 'ordinary_desktop_launched', 'pid': process.pid,
                     'receipt': str(out / 'launch.json'), 'retaining_process_handle': True}), flush=True)
    started = time.monotonic()
    exit_code = process.wait()
    write_new(out / 'electron-process-wait.observed.json', {
        'schema': 'researchos.owned-process-wait/1', 'at': now(), 'pid': process.pid,
        'actual_numeric_wait_status': exit_code, 'duration_seconds': time.monotonic() - started,
        'observer_kill_or_signal': False,
        'core_worker_verifier_exit_status': 'NOT_INFERRED_FROM_ELECTRON_WAIT', 'formal_increment': 0})
    print(json.dumps({'event': 'electron_wait_completed', 'pid': process.pid,
                     'actual_numeric_wait_status': exit_code}), flush=True)
