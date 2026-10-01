"""build.check handler for W02-03: real build + launch + handshake + isolation checks.

Runs: go builds of researchos CLI and existing control plane; isolated test host on
127.0.0.1:18923 with fresh data dir; CLI doctor handshake; electron thin-shell smoke;
shutdown isolation proof. Prints one JSON assertion report (dispatcher requirement).
"""
import json, os, subprocess, sys, time, urllib.request, hashlib, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
GO = ROOT / '.local' / 'tools' / 'go1.27.1' / 'go' / 'bin' / 'go.exe'
HOST = 'http://127.0.0.1:18923'
DISCOVERY = ROOT / '.local' / 'v24_host.json'
TEST_DATA = '.local/v24test_host'
ids, failures, notes = [], [], []


def ok(label, cond, detail=''):
    if cond:
        ids.append(label)
    else:
        failures.append({'id': label, 'detail': str(detail)[:300]})


def sh(argv, cwd=ROOT, env=None, timeout=300):
    e = dict(os.environ)
    e.update({'GOTOOLCHAIN': 'local', 'GOENV': 'off', 'GOPATH': str(ROOT / '.local' / 'gopath'),
              'GOCACHE': str(ROOT / '.local' / 'gocache'), 'CGO_ENABLED': '1'})
    if env:
        e.update(env)
    return subprocess.run(argv, cwd=str(cwd), env=e, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=timeout)


old_lock_hashes = {}
data_root = ROOT / '.local' / 'data'
if data_root.exists():
    for p in data_root.rglob('*'):
        if p.is_file() and ('lock' in p.name.lower() or p.name.endswith(('.sqlite', '.sqlite-wal', '.sqlite-shm'))):
            old_lock_hashes[str(p)] = hashlib.sha256(p.read_bytes()[:65536]).hexdigest()

# A1: build own CLI
r = sh([str(GO), 'build', '-o', str(ROOT / '.local' / 'bin' / 'researchos.exe'), './apps/cli'])
ok('A1_CLI_BUILD', r.returncode == 0, r.stderr[-300:])
# A2: version
r = sh([str(ROOT / '.local' / 'bin' / 'researchos.exe'), 'version'])
ok('A2_CLI_VERSION', r.returncode == 0 and 'researchos-client/2' in r.stdout and 'researchos ' in r.stdout, r.stdout[:120])
# A3: help marks unimplemented
r = sh([str(ROOT / '.local' / 'bin' / 'researchos.exe'), 'help'])
ok('A3_CLI_HELP_NOTIMPL', r.returncode == 0 and 'NOT_IMPLEMENTED' in r.stdout and 'doctor' in r.stdout, r.stdout[:160])
# A4: unimplemented command exits nonzero, no swallowed success
r = sh([str(ROOT / '.local' / 'bin' / 'researchos.exe'), 'chat'])
ok('A4_CLI_UNIMPLEMENTED_NONZERO', r.returncode == 3 and 'NOT_IMPLEMENTED' in r.stdout, (r.returncode, r.stdout[:120]))
# A5: build control plane (existing Go host untouched)
r = sh([str(GO), 'build', '-o', str(ROOT / '.local' / 'bin' / 'ros-control-w0203.exe'), './apps/control'])
ok('A5_CONTROL_BUILD', r.returncode == 0, r.stderr[-300:])
# A6: launch isolated test host
host_proc = None
try:
    env = {'RESEARCHOS_DATA_DIR': TEST_DATA, 'RESEARCHOS_LISTEN': '127.0.0.1:18923'}
    host_proc = subprocess.Popen([str(ROOT / '.local' / 'bin' / 'ros-control-w0203.exe')],
                                 cwd=str(ROOT), env={**os.environ, 'GOTOOLCHAIN': 'local', **env},
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
    up = False
    for _ in range(60):
        try:
            with urllib.request.urlopen(HOST + '/healthz', timeout=2) as resp:
                up = resp.status == 200
                if up:
                    break
        except Exception:
            time.sleep(1)
    ok('A6_TEST_HOST_UP', up, 'healthz 200 on isolated data dir')
    if up:
        DISCOVERY.parent.mkdir(exist_ok=True)
        DISCOVERY.write_text(json.dumps({'url': HOST, 'pid': host_proc.pid, 'data_dir': TEST_DATA,
                                         'started_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}), encoding='utf-8')
        # A7: doctor handshake via discovery
        r = sh([str(ROOT / '.local' / 'bin' / 'researchos.exe'), 'doctor'])
        j = {}
        try:
            j = json.loads(r.stdout.strip().splitlines()[-1])
        except Exception:
            pass
        ns = subprocess.run(['netstat', '-ano', '-p', 'TCP'], capture_output=True, text=True,
                            encoding='utf-8', errors='replace').stdout or ''
        listen_pids = {ln.split()[-1] for ln in ns.splitlines() if ':18923' in ln and 'LISTENING' in ln}
        ok('A7_DOCTOR_HANDSHAKE', r.returncode == 0 and j.get('health') == 'UP' and j.get('client_protocol') == 'researchos-client/2'
           and str(host_proc.pid) in listen_pids and j.get('host_pid') == host_proc.pid, {'doctor': j, 'netstat_pid': sorted(listen_pids)})
    else:
        out = host_proc.stdout.read() if host_proc.stdout else ''
        notes.append('host boot log tail: ' + (out or '')[-400:])
        ok('A7_DOCTOR_HANDSHAKE', False, 'host not up')
        DISCOVERY.write_text(json.dumps({'url': HOST, 'pid': -1, 'data_dir': TEST_DATA}), encoding='utf-8')
    # A8: electron shell smoke
    if (ROOT / 'apps' / 'desktop' / 'node_modules' / '.bin').exists():
        r = sh([str(ROOT / 'apps' / 'desktop' / 'node_modules' / '.bin' / 'electron.cmd'),
                str(ROOT / 'apps' / 'desktop' / 'main' / 'main.js')], timeout=180,
               env={'ROS_DESKTOP_SMOKE': '1', 'ELECTRON_DISABLE_SECURITY_WARNINGS': '1'})
        rep = None
        for line in (r.stdout or '').splitlines():
            if line.startswith('ROS_DESKTOP_REPORT'):
                rep = json.loads(line[len('ROS_DESKTOP_REPORT'):])
        ok('A8_DESKTOP_SHELL_UP', bool(rep) and rep['host_health'] == 'UP' and rep['protocol'] == 'researchos-client/2',
           (rep, (r.stderr or '')[-200:]))
        notes.append('A8 retries built into shell: hostStatus probes up to 4 times with 400ms backoff and reports error/latency')
    else:
        ok('A8_DESKTOP_SHELL_UP', False, 'electron not installed yet: run apps/desktop npm install step')
finally:
    # A9: shutdown isolation - stop ONLY our test host and prove old assets untouched
    if host_proc and host_proc.poll() is None:
        subprocess.run(['taskkill', '/PID', str(host_proc.pid), '/T', '/F'], capture_output=True)
        time.sleep(1)
    still_down = True
    try:
        with urllib.request.urlopen(HOST + '/healthz', timeout=2):
            still_down = False
    except Exception:
        pass
    ports_ok = True
    try:
        with urllib.request.urlopen('http://127.0.0.1:8787/healthz', timeout=2):
            ports_ok = False  # old protected port must remain closed
    except Exception:
        pass
    drift = []
    for p, h in old_lock_hashes.items():
        try:
            if hashlib.sha256(pathlib.Path(p).read_bytes()[:65536]).hexdigest() != h:
                drift.append(p)
        except Exception:
            drift.append(p + ':unreadable')
    ok('A9_SHUTDOWN_ISOLATION', still_down and ports_ok and not drift,
       {'test_host_stopped': still_down, 'old_8787_still_closed': ports_ok, 'old_data_drift': drift[:3]})
    if DISCOVERY.exists():
        DISCOVERY.unlink()

report = {'status': 'PASS' if not failures else 'FAIL', 'assertions': len(ids),
          'assertion_ids': ids, 'failures': failures, 'notes': notes,
          'scope': 'CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE'}
print(json.dumps(report, ensure_ascii=False))
sys.exit(0 if not failures else 1)
