"""Bounded local CLI metadata/auth-state probe. No prompt or model request.

Authentication text is classified in memory and never printed or persisted.
Only public --help output is retained. Does not read credential files.
"""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'product-v1-codex-local-probe-01'
EXE = Path('C:/nvm4w/nodejs/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe')
assert EXE.is_file() and not OUT.exists(), 'Inspect prior result/uncertain probe before retry'
OUT.mkdir()
result = dict(at=datetime.now(timezone.utc).isoformat(), executable=str(EXE),
    executable_sha256=hashlib.sha256(EXE.read_bytes()).hexdigest(),
    prompts_sent=0, model_requests_sent=0, credential_files_read_by_controller=0,
    raw_auth_output_persisted=False, real_task_qualified=False, probes=[])
for label, args in [('version', ['--version']), ('exec_help', ['exec', '--help']), ('login_status', ['login', 'status'])]:
    try:
        p = subprocess.run([str(EXE), *args], cwd=HERE, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
    except subprocess.TimeoutExpired:
        result['probes'].append(dict(kind=label, status='TIMEOUT_UNQUALIFIED', retry_permitted=False))
        break
    raw = p.stdout + b'\n' + p.stderr
    row = dict(kind=label, exit_code=p.returncode, stdout_bytes=len(p.stdout), stderr_bytes=len(p.stderr))
    if label == 'login_status':
        lower = raw.decode('utf-8', errors='replace').lower()
        row['authentication'] = ('logged_in' if p.returncode == 0 else 'not_confirmed')
        row['mode'] = ('chatgpt' if p.returncode == 0 and 'chatgpt' in lower else
                       'api_key' if p.returncode == 0 and 'api key' in lower else 'unknown')
        row['limitation'] = 'Credential presence/status is not model or quota qualification.'
    else:
        (OUT / (label + '.txt')).write_bytes(raw)
        if label == 'version': row['version'] = raw.decode('utf-8', errors='replace').strip()
        if label == 'exec_help':
            text = raw.decode('utf-8', errors='replace')
            row['advertised_flags'] = {flag: flag in text for flag in ['--json', '--ephemeral', '--sandbox', '--skip-git-repo-check', '--output-schema', '--ignore-user-config']}
    result['probes'].append(row)
    (OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
