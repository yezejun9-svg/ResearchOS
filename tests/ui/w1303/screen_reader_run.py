"""Observe real NVDA speech while keyboard navigating one isolated Electron window.

The only collected speech is text appended to NVDA's own Speech Viewer while
ResearchOS is the foreground window. This is development evidence, not formal
accessibility acceptance or a substitute for a human screen-reader review.
"""
from __future__ import annotations

import datetime as dt
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import time
import uuid

import psutil
import win32api
import win32con
import win32gui
import win32process

from nvda_viewer import inspect as speech_viewer


ROOT = Path(__file__).resolve().parents[3]
LOCAL = ROOT / '.local'
ASSETS = (ROOT.parent.parent / 'nvda-w1303' if ROOT.parent.name == 'worktrees'
          and ROOT.parent.parent.name == '.local' else LOCAL / 'nvda-w1303')
NVDA = ASSETS / 'portable/nvda.exe'
SOURCE = ASSETS / 'nvda_2026.2.exe'
SOURCE_SHA256 = 'f3f8d29974a88d687b3c4809be192219ec579c5bdabcda5aaf53635288bca824'


def wait_for(predicate, seconds: float, message: str):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        try:
            result = predicate()
        except (RuntimeError, json.JSONDecodeError):
            result = None
        if result:
            return result
        time.sleep(.2)
    raise RuntimeError(message)


def send_keys(*keys: int) -> None:
    for key in keys:
        win32api.keybd_event(key, 0, 0, 0)
    for key in reversed(keys):
        win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)


def main() -> int:
    run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    out = ROOT / 'execution/v2.4/receipts/W13/W13-03' / ('screen-reader-' + run_id)
    out.mkdir(parents=True)
    report = {'schema': 'researchos.nvda-speech-observation.v1', 'status': 'EXECUTING',
              'step_id': 'W13-03', 'measurement_mode': 'DEVELOPMENT', 'provider_calls': 0,
              'formal_cases_accepted': [], 'run_id': run_id, 'steps': [],
              'speech_source': 'NVDA 2026.2 native Speech Viewer RichEdit',
              'limitations': ['Only the temporary ResearchOS Electron window was navigated.',
                              'This sampled title, navigation and form focus; it is not exhaustive screen-reader acceptance.']}
    temp = Path(tempfile.mkdtemp(prefix='researchos-w1303-nvda-', dir=LOCAL))
    fixture = electron = nvda = log = None
    done = temp / 'done'
    try:
        if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256 or not NVDA.is_file():
            raise RuntimeError('official NVDA download hash or portable binary unavailable')
        if any(process.info['name'] and process.info['name'].lower() == 'nvda.exe'
               for process in psutil.process_iter(['name'])):
            raise RuntimeError('another NVDA process exists; refusing to replace it')
        locked = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8-sig'))['tools']
        go, node = Path(locked['go']['path']), Path(locked['node']['path'])
        for name, binary in [('go', go), ('node', node)]:
            if hashlib.sha256(binary.read_bytes()).hexdigest() != locked[name]['sha256']:
                raise RuntimeError(f'{name} tool hash mismatch')
        env = dict(os.environ, GOTOOLCHAIN='local', GOENV='off', RESEARCHOS_TASK_ID='W13',
                   RESEARCHOS_DESKTOP_USER_DATA=str(temp / 'electron-user-data'),
                   PROCESSOR_ARCHITECTURE='AMD64')
        env.pop('ROS_DESKTOP_SMOKE', None)
        binary = temp / 'workspace-fixture.exe'
        subprocess.run([str(go), 'build', '-o', str(binary), './tests/ui/w1303/workspace_fixture'],
                       cwd=ROOT, env=env, check=True, timeout=180, capture_output=True)
        log = (out / 'fixture.stderr.txt').open('w', encoding='utf-8')
        fixture = subprocess.Popen([str(binary), '--dir', str(temp / 'service')], cwd=ROOT,
                                   env=env, stdout=subprocess.PIPE, stderr=log, text=True, encoding='utf-8')
        fixture_line = fixture.stdout.readline()
        if not fixture_line:
            raise RuntimeError('workspace fixture failed to announce readiness')
        setup = json.loads(fixture_line)
        for key in ['project_id', 'discovery_file']:
            if not setup.get(key):
                raise RuntimeError(f'workspace fixture omitted {key}')
        input_file = temp / 'input.json'
        input_file.write_text(json.dumps(setup, ensure_ascii=False), encoding='utf-8')
        ready = temp / 'electron-ready.json'
        focus_request, focus_ack = temp / 'focus-request', temp / 'focus-ack.json'
        electron_log = (out / 'electron.stderr.txt').open('w', encoding='utf-8')
        electron = subprocess.Popen([str(node), str(ROOT / 'tests/ui/w1303/screen_reader.cjs'),
                                     str(input_file), str(ready), str(done), str(focus_request),
                                     str(focus_ack)], cwd=ROOT, env=env,
                                    stdout=subprocess.DEVNULL, stderr=electron_log)
        native = wait_for(lambda: json.loads(ready.read_text(encoding='utf-8')) if ready.exists() else None,
                          45, 'temporary Electron did not become ready')
        hwnd = int(native['hwnd'])
        report['electron'] = native
        report['nvda_download_sha256'] = SOURCE_SHA256
        nvda = subprocess.Popen([str(NVDA), '--no-sr-flag', '--disable-addons', '--no-logging'],
                                cwd=NVDA.parent, env=env, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        viewer = wait_for(lambda: speech_viewer(nvda.pid) if nvda.poll() is None else None,
                          12, 'NVDA Speech Viewer did not appear')
        report['nvda_pid'] = nvda.pid
        report['viewer'] = {key: viewer[key] for key in ['source', 'window_handle', 'title', 'editor_handle']}
        # Do not save pre-existing speech. It may be from unrelated desktop activity.
        previous = viewer['speech']
        focus_request.write_text('focus owned window', encoding='utf-8')
        focus_result = wait_for(lambda: json.loads(focus_ack.read_text(encoding='utf-8')) if focus_ack.exists() else None,
                                5, 'Electron did not acknowledge its own focus request')
        report['electron_focus_request'] = focus_result
        foreground = win32gui.GetForegroundWindow()
        report['foreground_after_focus'] = {'hwnd': foreground,
                                            'pid': win32process.GetWindowThreadProcessId(foreground)[1] if foreground else None,
                                            'target_hwnd': hwnd,
                                            'target_pid': win32process.GetWindowThreadProcessId(hwnd)[1]}
        if foreground != hwnd:
            switch = ctypes.windll.user32.SwitchToThisWindow
            switch.argtypes = [ctypes.c_void_p, ctypes.c_bool]
            switch.restype = None
            switch(hwnd, True)
            time.sleep(.3)
            foreground = win32gui.GetForegroundWindow()
        report['foreground_after_switch'] = {'hwnd': foreground,
                                             'pid': win32process.GetWindowThreadProcessId(foreground)[1] if foreground else None}
        if foreground != hwnd:
            raise RuntimeError('OS foreground remains outside ResearchOS after target-only switch; physical screen-reader navigation blocked')
        report['input_method'] = 'Windows keybd_event to OS-focused ResearchOS Electron window'
        actions = [('title', (win32con.VK_INSERT, ord('T')))]
        actions += [(f'tab-{index:02d}', (win32con.VK_TAB,)) for index in range(1, 35)]
        for name, keys in actions:
            if win32gui.GetForegroundWindow() != hwnd:
                raise RuntimeError('OS foreground left ResearchOS; stopping physical keyboard input')
            send_keys(*keys)
            time.sleep(.45)
            current = speech_viewer(nvda.pid)['speech']
            if not current.startswith(previous):
                raise RuntimeError('Speech Viewer history changed unexpectedly')
            delta = current[len(previous):]
            previous = current
            report['steps'].append({'action': name, 'speech': delta,
                                    'electron_foreground': win32gui.GetForegroundWindow() == hwnd})
        spoken = '\n'.join(step['speech'] for step in report['steps'])
        report['checks'] = {
            'title': 'ResearchOS' in spoken or '设置与设备' in spoken,
            'navigation': any(label in spoken for label in ['主导航', '工作台', '周期', '资源']),
            'form_labels': any(label in spoken for label in ['并发上限', '研究周期', '时区']),
            'focus_maintained': all(step['electron_foreground'] for step in report['steps']),
        }
        report['status'] = 'PASS' if all(report['checks'].values()) else 'PARTIAL'
    except Exception as error:
        report['status'], report['error'] = 'BLOCKED', str(error)
    finally:
        done.write_text('close', encoding='utf-8')
        if electron:
            try:
                electron.wait(timeout=10)
            except subprocess.TimeoutExpired:
                electron.terminate(); electron.wait(timeout=10)
        if nvda and nvda.poll() is None:
            nvda.terminate()
            try:
                nvda.wait(timeout=10)
            except subprocess.TimeoutExpired:
                nvda.kill(); nvda.wait(timeout=5)
        if fixture and fixture.poll() is None:
            fixture.terminate(); fixture.wait(timeout=10)
        if log:
            log.close()
        if 'electron_log' in locals():
            electron_log.close()
        report['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        (out / 'observation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        if temp.resolve().is_relative_to(LOCAL.resolve()):
            try:
                def clear_readonly(function, path, error):
                    if not Path(path).resolve().is_relative_to(temp.resolve()):
                        raise error
                    os.chmod(path, stat.S_IWRITE)
                    function(path)
                shutil.rmtree(temp, onexc=clear_readonly)
            except OSError as cleanup_error:
                report['temporary_data_retained'] = str(temp)
                report['cleanup_error'] = str(cleanup_error)
                (out / 'observation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'receipt': str(out / 'observation.json'),
                      'checks': report.get('checks'), 'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
