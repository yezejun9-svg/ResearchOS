"""Execute registered construction checks. This is not the product worker/sandbox."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def invalid_number(value):
        raise ValueError('NONFINITE_JSON_NUMBER')
    return json.loads(text, object_pairs_hook=unique, parse_constant=invalid_number)


def read(path):
    return decode(path.read_text(encoding='utf-8-sig'))


def within(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('PATH_OUTSIDE_WORKSPACE')
    return path


def execute(key, selectors=None, *, root=ROOT):
    selectors = selectors or {}
    invocation = str(uuid.uuid4())
    output = within(root, 'execution/invocations') / invocation
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(invocation_id=invocation, command_key=key, started_at=now(),
                   status='ERROR', exit_code=1, child_exit_code=None, assertion_ids=[],
                   selectors=selectors, scope='CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE',
                   stdout_sanitized=True, stderr_sanitized=True)
    stdout, stderr = b'', b''
    secrets = [v.encode() for k, v in os.environ.items()
               if re.search(r'(TOKEN|SECRET|PASSWORD|API_KEY)', k, re.I) and len(v) >= 4]

    def fail(status, code=1):
        receipt.update(status=status, exit_code=code)

    try:
        registry_path = root / 'execution/commands.json'
        registry = read(registry_path)
        receipt['registered_command_revision'] = sha(registry_path)
        entry = registry['commands'].get(key)
        if not entry or entry['state'] != 'BOUND':
            fail('NOT_IMPLEMENTED', 3)
        elif platform.system() not in entry['platforms']:
            fail('UNSUPPORTED_PLATFORM', 4)
        elif any(value and value not in entry.get('selectors', {}).get(name, [])
                 for name, value in selectors.items()):
            fail('NOT_IMPLEMENTED', 3)
        elif any(not os.environ.get(name) for name in entry['required_env']):
            receipt['missing_environment_names'] = [n for n in entry['required_env'] if not os.environ.get(n)]
            fail('MISSING_CREDENTIAL_OR_ENVIRONMENT', 5)
        else:
            locked_path = root / 'execution/toolchains/locked.json'
            locked = read(locked_path)
            receipt['toolchain_revision'] = sha(locked_path)
            receipt['dispatcher_sha256'] = sha(Path(__file__))
            receipt['input_versions'] = []
            for argument in entry['argv']:
                path = (root / argument).resolve()
                if path.is_relative_to(root.resolve()) and path.is_file():
                    receipt['input_versions'].append({'path': path.relative_to(root).as_posix(), 'sha256': sha(path)})
            if 'git' in locked['tools']:
                git = locked['tools']['git']
                if sha(Path(git['path'])) != git['sha256']:
                    raise ValueError('GIT_TOOLCHAIN_CHANGED')
                revision = subprocess.run([git['path'], 'rev-parse', 'HEAD'], cwd=root,
                                          capture_output=True, text=True, timeout=10, check=True)
                receipt['code_revision'] = revision.stdout.strip()
            tool = locked['tools'][entry['executable_tool']]
            executable = Path(tool['path'])
            if not executable.is_absolute() or not executable.is_file():
                fail('MISSING_EXECUTABLE', 6)
            elif sha(executable) != tool['sha256']:
                fail('TOOLCHAIN_CHANGED', 6)
            else:
                argv = [str(executable), *entry['argv']]
                if any(secret in arg.encode() for secret in secrets for arg in argv):
                    fail('SECRET_IN_ARGUMENTS', 7)
                else:
                    cwd = within(root, entry['cwd'])
                    env = {name: os.environ[name] for name in entry['allowed_env'] if name in os.environ}
                    env.update(entry.get('fixed_env', {}))
                    env.update({'RESEARCHOS_' + name.upper(): value for name, value in selectors.items() if value})
                    for name, tool_name in entry.get('tool_env', {}).items():
                        selected = locked['tools'][tool_name]
                        path = Path(selected['path'])
                        if not path.is_file() or sha(path) != selected['sha256']:
                            raise ValueError('TOOLCHAIN_CHANGED')
                        env[name] = str(path)
                    receipt.update(argv=argv, cwd=str(cwd), environment_names=sorted(env),
                                   timeout_seconds=entry['timeout_seconds'])
                    process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE, shell=False)
                    receipt['pid'] = process.pid
                    try:
                        stdout, stderr = process.communicate(timeout=entry['timeout_seconds'])
                    except subprocess.TimeoutExpired:
                        parent_exited = process.poll() is not None
                        if parent_exited:
                            receipt['timeout_cleanup_unconfirmed'] = True
                        elif os.name == 'nt':
                            killer = Path(os.environ['SystemRoot']) / 'System32/taskkill.exe'
                            try:
                                stopped = subprocess.run([str(killer), '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=5)
                                receipt['timeout_cleanup_exit_code'] = stopped.returncode
                            except subprocess.TimeoutExpired:
                                receipt['timeout_cleanup_unconfirmed'] = True
                        else:
                            process.kill()
                        if not parent_exited:
                            try:
                                stdout, stderr = process.communicate(timeout=2)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                # A pipe held by an unconfirmed descendant cannot be closed
                                # synchronously: communicate's reader owns its lock.
                                receipt['timeout_cleanup_unconfirmed'] = True
                        fail('TIMEOUT', 8)
                    receipt['child_exit_code'] = process.returncode
                    if receipt['status'] != 'TIMEOUT':
                        report = None
                        try:
                            text = stdout.decode('utf-8')
                            try:
                                report = decode(text)
                            except json.JSONDecodeError:
                                report = decode(text.strip().splitlines()[-1])
                        except (ValueError, IndexError):
                            pass
                        ids = report.get(entry.get('assertion_field', 'assertion_ids'), []) if isinstance(report, dict) else []
                        valid_ids = isinstance(ids, list) and all(isinstance(x, str) and x for x in ids) and len(set(ids)) == len(ids)
                        if valid_ids:
                            receipt['assertion_ids'] = ids
                        if process.returncode != 0:
                            fail('COMMAND_FAILED', 1)
                        elif not isinstance(report, dict):
                            fail('INVALID_ASSERTION_REPORT', 9)
                        elif not isinstance(ids, list) or not ids:
                            fail('NOT_IMPLEMENTED', 3)
                        elif not valid_ids:
                            fail('INVALID_ASSERTION_REPORT', 9)
                        elif report.get('status') != 'PASS':
                            fail('CHECK_FAILED', 1)
                        elif 'assertions' in report and report['assertions'] != len(ids):
                            fail('INVALID_ASSERTION_REPORT', 9)
                        else:
                            receipt.update(status='PASS', exit_code=0, reported_scope=report.get('scope'))
    except (OSError, ValueError, KeyError, TypeError, IndexError, subprocess.SubprocessError) as exc:
        # The exception text can contain credentials from child output; never persist it.
        fail('DISPATCH_ERROR', 10)
        receipt['error_type'] = type(exc).__name__
    variants = set(secrets)
    for secret in secrets:
        variants.add(json.dumps(secret.decode(), ensure_ascii=True)[1:-1].encode())
        variants.add(json.dumps(secret.decode(), ensure_ascii=False)[1:-1].encode())
    for secret in sorted(variants, key=len, reverse=True):
        stdout = stdout.replace(secret, b'[REDACTED]')
        stderr = stderr.replace(secret, b'[REDACTED]')
    # Child assertion labels/scope are untrusted too.
    def sanitize(value):
        if isinstance(value, str):
            for secret in secrets:
                value = value.replace(secret.decode(), '[REDACTED]')
            return value
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        if isinstance(value, dict):
            return {sanitize(key): sanitize(item) for key, item in value.items()}
        return value
    receipt = sanitize(receipt)
    for name, data in [('stdout', stdout), ('stderr', stderr)]:
        path = output / (name + '.txt')
        path.write_bytes(data)
        receipt[name] = {'path': path.relative_to(root).as_posix(), 'sha256': sha(path)}
    receipt['ended_at'] = now()
    receipt_path = output / 'receipt.json'
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return receipt, receipt_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('key')
    for name in ('task_id', 'check_id', 'case_id'):
        parser.add_argument('--' + name.replace('_', '-'), default='')
    args = vars(parser.parse_args())
    result, reference = execute(args.pop('key'), args)
    print(json.dumps({'status': result['status'], 'assertions': len(result['assertion_ids']),
                      'invocation_id': result['invocation_id'], 'receipt': str(reference)}, ensure_ascii=False))
    sys.exit(result['exit_code'])
