#!/usr/bin/env python3
"""One optional Qwen attachment-reading probe. Never a product acceptance test."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'Qwen3.8-Flash'
INPUTS = ('00_START_HERE.md', '08_AGENT_EXECUTION_GOAL.md', 'tasks/steps/W00-01.md')
PROMPT = (
    'This is one read-only attachment comprehension probe, not construction authorization. '
    'Use only the three attached specification files. All agent tools are disabled. '
    'Do not create a Goal, modify files, run commands, or claim product acceptance. '
    'Return one JSON object with spec_version, repository_root, full_goal_path, first_step_id, '
    'first_step_title, first_step_dependencies, first_step_required_reads, '
    'completion_guard, unresolved_fields. Read these fields from the attachments; '
    'use null and explain if unavailable. Absolute paths explicitly shown in 00 are available; '
    'do not infer a state file exists or is absent without access. Answer explanatory text in Simplified Chinese. '
    'Do not infer your model identity or say any implementation is complete.'
)


def resolve_cli(value: str | None) -> Path:
    candidate = value or shutil.which('qodercli.exe') or str(Path.home() / '.qoder/bin/qodercli/qodercli.exe')
    path = Path(candidate).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f'Qoder CLI not found: {path}')
    if os.name == 'nt' and path.suffix.lower() != '.exe':
        raise ValueError('The bounded Windows probe requires a real .exe, not a shell wrapper.')
    return path


def build_argv(cli: Path, root: Path) -> list[str]:
    argv = [str(cli), '-w', str(root), '--model', MODEL,
            '--permission-mode', 'dont_ask', '--tools=', '--strict-mcp-config',
            '--max-model-request-retries', '0', '--max-output-tokens', '1200',
            '--no-session-persistence', '--output-format', 'json']
    for relative in INPUTS:
        path = (root / relative).resolve()
        if not path.is_file() or not path.is_relative_to(root.resolve()):
            raise ValueError(f'Missing or out-of-package attachment: {relative}')
        argv.extend(['--attachment', str(path)])
    return argv + ['-p', PROMPT]


def redact(text: str) -> str:
    text = re.sub(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+', 'Bearer [REDACTED]', text)
    text = re.sub(r'\b(?:sk-|gh[pousr]_|github_pat_|qoderpat_)[A-Za-z0-9_-]{10,}', '[REDACTED]', text)
    return re.sub(r'(?i)([\"\']?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|secret)[\"\']?\s*[:=]\s*)([\"\']?)[^\s,}\"\']+\2', r'\1[REDACTED]', text)


def run_windows(argv: list[str], cwd: Path, timeout: float, stdout, stderr, stdin) -> tuple[int, bool]:
    """Create suspended, attach to an unnamed kill-on-close job, then resume."""
    import ctypes as c
    from ctypes import wintypes as w
    import msvcrt

    class BasicLimits(c.Structure):
        _fields_ = [('process_time', c.c_longlong), ('job_time', c.c_longlong), ('flags', w.DWORD),
                    ('min_ws', c.c_size_t), ('max_ws', c.c_size_t), ('active', w.DWORD),
                    ('affinity', c.c_size_t), ('priority', w.DWORD), ('scheduling', w.DWORD)]

    class ExtendedLimits(c.Structure):
        _fields_ = [('basic', BasicLimits), ('io', c.c_ulonglong * 6),
                    ('process_memory', c.c_size_t), ('job_memory', c.c_size_t),
                    ('peak_process_memory', c.c_size_t), ('peak_job_memory', c.c_size_t)]

    class StartupInfo(c.Structure):
        _fields_ = [('cb', w.DWORD), ('reserved', w.LPWSTR), ('desktop', w.LPWSTR), ('title', w.LPWSTR),
                    ('x', w.DWORD), ('y', w.DWORD), ('xsize', w.DWORD), ('ysize', w.DWORD),
                    ('xchars', w.DWORD), ('ychars', w.DWORD), ('fill', w.DWORD), ('flags', w.DWORD),
                    ('show', w.WORD), ('reserved_size', w.WORD), ('reserved_ptr', c.c_void_p),
                    ('stdin', w.HANDLE), ('stdout', w.HANDLE), ('stderr', w.HANDLE)]

    class ProcessInfo(c.Structure):
        _fields_ = [('process', w.HANDLE), ('thread', w.HANDLE), ('pid', w.DWORD), ('tid', w.DWORD)]

    kernel = c.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'CreateJobObjectW': ([c.c_void_p, w.LPCWSTR], w.HANDLE),
        'SetInformationJobObject': ([w.HANDLE, c.c_int, c.c_void_p, w.DWORD], w.BOOL),
        'SetHandleInformation': ([w.HANDLE, w.DWORD, w.DWORD], w.BOOL),
        'CreateProcessW': ([w.LPCWSTR, w.LPWSTR, c.c_void_p, c.c_void_p, w.BOOL, w.DWORD,
                            c.c_void_p, w.LPCWSTR, c.POINTER(StartupInfo), c.POINTER(ProcessInfo)], w.BOOL),
        'AssignProcessToJobObject': ([w.HANDLE, w.HANDLE], w.BOOL),
        'ResumeThread': ([w.HANDLE], w.DWORD),
        'WaitForSingleObject': ([w.HANDLE, w.DWORD], w.DWORD),
        'GetExitCodeProcess': ([w.HANDLE, c.POINTER(w.DWORD)], w.BOOL),
        'TerminateProcess': ([w.HANDLE, w.UINT], w.BOOL),
        'CloseHandle': ([w.HANDLE], w.BOOL),
    }
    for name, (args, result) in signatures.items():
        function = getattr(kernel, name)
        function.argtypes, function.restype = args, result

    def checked(ok):
        if not ok:
            raise c.WinError(c.get_last_error())
        return ok

    job = checked(kernel.CreateJobObjectW(None, None))
    process = ProcessInfo()
    assigned = False
    try:
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        checked(kernel.SetInformationJobObject(job, 9, c.byref(limits), c.sizeof(limits)))
        startup = StartupInfo()
        startup.cb = c.sizeof(startup)
        startup.flags = 0x101  # STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW; SW_HIDE=0.
        for field, stream in (('stdin', stdin), ('stdout', stdout), ('stderr', stderr)):
            handle = msvcrt.get_osfhandle(stream.fileno())
            checked(kernel.SetHandleInformation(handle, 1, 1))
            setattr(startup, field, handle)
        command = c.create_unicode_buffer(subprocess.list2cmdline(argv))
        checked(kernel.CreateProcessW(argv[0], command, None, None, True, 0x08000004,
                                      None, str(cwd), c.byref(startup), c.byref(process)))
        # CREATE_SUSPENDED prevents children escaping before job assignment.
        checked(kernel.AssignProcessToJobObject(job, process.process))
        assigned = True
        if kernel.ResumeThread(process.thread) == 0xFFFFFFFF:
            raise c.WinError(c.get_last_error())
        wait = kernel.WaitForSingleObject(process.process, int(timeout * 1000))
        if wait == 258:
            return 124, True
        if wait != 0:
            raise c.WinError(c.get_last_error())
        code = w.DWORD()
        checked(kernel.GetExitCodeProcess(process.process, c.byref(code)))
        return code.value, False
    finally:
        # Only our unnamed job and its descendants are affected; no PID/name scans.
        if process.process and not assigned:
            kernel.TerminateProcess(process.process, 125)
        kernel.CloseHandle(job)
        if process.process:
            kernel.WaitForSingleObject(process.process, 5000)
            kernel.CloseHandle(process.process)
        if process.thread:
            kernel.CloseHandle(process.thread)


def run_bounded(argv: list[str], cwd: Path, timeout: float) -> tuple[int, str, str, bool]:
    with tempfile.TemporaryDirectory(prefix='researchos-qoder-probe-') as temp:
        out_path, err_path = Path(temp) / 'stdout', Path(temp) / 'stderr'
        with out_path.open('wb') as out, err_path.open('wb') as err, open(os.devnull, 'rb') as inp:
            if os.name == 'nt':
                code, timed_out = run_windows(argv, cwd, timeout, out, err, inp)
            else:
                import signal
                process = subprocess.Popen(argv, cwd=cwd, stdin=inp, stdout=out, stderr=err, start_new_session=True)
                timed_out = False
                try:
                    code = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    code, timed_out = 124, True
                finally:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=5)
        return code, out_path.read_text(encoding='utf-8', errors='replace'), err_path.read_text(encoding='utf-8', errors='replace'), timed_out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qoder-cli', help='Explicit native Qoder CLI executable.')
    parser.add_argument('--output', type=Path, help='Explicit report directory outside this specification package; required to run.')
    parser.add_argument('--print-only', action='store_true', help='Print argv without starting any process or writing a report.')
    parser.add_argument('--timeout', type=int, default=120, help='Wall-clock limit in seconds, 1 through 120 (default: 120).')
    args = parser.parse_args()
    if not 1 <= args.timeout <= 120:
        parser.error('--timeout must be between 1 and 120 seconds')
    if not args.print_only and args.output is None:
        parser.error('use --print-only or provide an explicit --output directory to run the probe')
    try:
        cli = resolve_cli(args.qoder_cli)
        argv = build_argv(cli, ROOT)
        if args.print_only:
            print(json.dumps({'status': 'PRINT_ONLY_NOT_RUN', 'argv': argv,
                              'timeout_seconds': args.timeout, 'agent_tools': 'NONE'}, ensure_ascii=False, indent=2))
            return 0
        output = args.output.expanduser().resolve()
        if output.is_relative_to(ROOT):
            raise ValueError('--output must be outside the immutable specification package')
        output.mkdir(parents=True, exist_ok=True)
        inputs = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in INPUTS}
        started = dt.datetime.now(dt.timezone.utc)
        before = time.monotonic()
        code, stdout, stderr, timed_out = run_bounded(argv, ROOT, args.timeout)
        report = {
            'schema_version': '1.0', 'kind': 'QODER_SPEC_ATTACHMENT_PROBE',
            'spec_version': '2.4.0', 'requested_model': MODEL,
            'status': 'TIMEOUT' if timed_out else ('RESPONSE_REQUIRES_REVIEW' if code == 0 else 'FAILED'),
            'started_at': started.isoformat(), 'elapsed_seconds': round(time.monotonic() - before, 3),
            'timeout_seconds': args.timeout, 'returncode': code,
            'executable': str(cli), 'argv': argv, 'input_sha256': inputs,
            'agent_tools': [], 'mcp': 'DISABLED_BY_STRICT_EMPTY_CONFIG',
            'product_acceptance': 'NOT_RUN', 'read_tool_call': 'NOT_RUN', 'goal_long_run': 'NOT_RUN',
            'stdout_redacted': redact(stdout)[:60000], 'stderr_redacted': redact(stderr)[:10000],
            'output_truncated': len(stdout) > 60000 or len(stderr) > 10000,
            'notice': 'Process exit is not semantic acceptance. Compare response fields with the attached files. Redaction covers common credential patterns; review before sharing.',
        }
        report_path = output / ('qoder-probe-' + started.strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8] + '.json')
        with report_path.open('x', encoding='utf-8') as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
        print(json.dumps({'status': report['status'], 'report': str(report_path), 'product_acceptance': 'NOT_RUN'}, ensure_ascii=False))
        return code if 0 <= code <= 255 else 1
    except (OSError, ValueError) as exc:
        print('PROBE_FAILED: ' + redact(str(exc)), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
