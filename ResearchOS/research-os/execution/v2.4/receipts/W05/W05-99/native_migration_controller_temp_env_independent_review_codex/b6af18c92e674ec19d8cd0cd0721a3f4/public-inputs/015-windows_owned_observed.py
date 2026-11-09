"""Receipt-only Windows child runner; importing this module starts no process.

The caller owns stdout/stderr, raw receipts, tool pins and the decision to stop.
An unnamed, non-inherited Job owns exactly this suspended child and descendants.
No PID lookup, taskkill, shell, breakaway flag or pre-existing Job is used.
"""

import ctypes
import copy
from ctypes import wintypes
import math
import os
from pathlib import Path
import subprocess
import time


def runtime_resource_paths():
    """Read actual loaded Windows/Python module paths; never start a process.

    The caller must hash/freeze these files and this helper, plus its ordinary
    Python source/dependency closure. Paths are actual loaded modules, not a
    guessed System32 list. This is a point-in-time inventory, not a claim about
    every possible future dynamically loaded DLL.
    """
    if os.name != 'nt':
        raise RuntimeError('runtime_resource_paths requires Windows')
    import msvcrt  # Load the same CRT bridge used by run_owned before inventory.
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.GetCurrentProcess.argtypes, api.GetCurrentProcess.restype = [], wintypes.HANDLE
    api.K32EnumProcessModules.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.HANDLE),
                                        wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    api.K32EnumProcessModules.restype = wintypes.BOOL
    api.GetModuleFileNameW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD]
    api.GetModuleFileNameW.restype = wintypes.DWORD
    capacity = 256
    for _ in range(3):
        modules = (wintypes.HANDLE * capacity)()
        needed = wintypes.DWORD()
        if not api.K32EnumProcessModules(api.GetCurrentProcess(), modules, ctypes.sizeof(modules), ctypes.byref(needed)):
            raise ctypes.WinError(ctypes.get_last_error())
        if needed.value <= ctypes.sizeof(modules):
            if needed.value % ctypes.sizeof(wintypes.HANDLE):
                raise RuntimeError('Unexpected Windows module inventory size')
            paths = set()
            for handle in modules[:needed.value // ctypes.sizeof(wintypes.HANDLE)]:
                buffer = ctypes.create_unicode_buffer(32768)
                length = api.GetModuleFileNameW(handle, buffer, len(buffer))
                if not length or length >= len(buffer):
                    raise ctypes.WinError(ctypes.get_last_error())
                path = Path(buffer.value).resolve()
                if not path.is_file():
                    raise RuntimeError('Loaded module is not an accessible file: ' + str(path))
                paths.add(str(path))
            return sorted(paths, key=str.casefold)
        capacity = needed.value // ctypes.sizeof(wintypes.HANDLE) + 32
    raise RuntimeError('Windows module inventory changed repeatedly; no stable bounded inventory')


def run_owned_observed(argv, cwd, env, stdout, stderr, timeout, stdin=None, creation_flags=0, on_observation=None, cancel_requested=None):
    """Return JSON-safe observations, including on preparation/launch failure.

    timeout covers preparation through the primary process AND Job becoming idle.
    Termination cleanup has a separate bounded five-second observation window.
    An actual_exit of None means no confirmed primary-process exit was observed.
    stdin=None means NUL; otherwise the caller supplies and retains its binary
    input file (including its immutable raw receipt). stdout/stderr likewise
    remain caller-owned. Default console inheritance matches ordinary Popen.
    """
    result = {
        'actual_exit': None, 'timed_out': False, 'error': None,
        'owned_child_pid': None, 'creation_time_100ns': None,
        'resumed': False, 'elapsed_seconds': None, 'stage': 'VALIDATE',
        'job_cleanup': {
            'unnamed_exclusive_job': True, 'kill_on_job_close_configured': False,
            'assigned_before_resume': False, 'termination_requested': False,
            'termination_succeeded': None, 'termination_code_requested': None,
            'unassigned_suspended_child_termination_requested': False,
            'unassigned_suspended_child_termination_succeeded': None,
            'active_processes_last_observed': None, 'job_idle_confirmed': False,
            'primary_exit_confirmed': False, 'handles_closed': False,
            'errors': [],
        },
    }
    cleanup = result['job_cleanup']
    started = time.monotonic()
    handles = []
    attribute_buffer = None
    attribute_initialized = False
    nul = None
    api = None
    process = None
    job = None
    assigned = False
    stage = 'VALIDATE'

    def error_text(exc):
        return type(exc).__name__ + ': ' + str(exc)

    def emit_observation(event):
        if on_observation is not None:
            snapshot = copy.deepcopy(result)
            snapshot['stage'] = stage
            on_observation(event, snapshot)

    def check_cancel():
        if cancel_requested is not None and cancel_requested():
            raise RuntimeError('Root requested owned case cancellation')

    def record_error(exc):
        text = error_text(exc)
        result['error'] = text if result['error'] is None else result['error'] + '; ' + text

    try:
        if os.name != 'nt':
            raise RuntimeError('run_owned requires Windows')
        if not isinstance(argv, (list, tuple)) or not argv or any(not isinstance(v, str) or '\0' in v for v in argv):
            raise ValueError('argv must be a nonempty sequence of NUL-free strings')
        if not Path(argv[0]).is_absolute() or not Path(argv[0]).is_file():
            raise ValueError('argv[0] must name an existing absolute executable')
        if not Path(cwd).is_absolute() or not Path(cwd).is_dir():
            raise ValueError('cwd must name an existing absolute directory')
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('timeout must be a finite positive number')
        if isinstance(creation_flags, bool) or not isinstance(creation_flags, int) or not 0 <= creation_flags <= 0xFFFFFFFF:
            raise ValueError('creation_flags must be a DWORD integer')
        if creation_flags & (0x01000000 | 0x00000001 | 0x00000002):
            raise ValueError('breakaway and debugger process creation flags are prohibited')
        if not isinstance(env, dict):
            raise ValueError('env must be a complete string dictionary')
        folded = set()
        for key, value in env.items():
            if not isinstance(key, str) or not key or '=' in key or '\0' in key or not isinstance(value, str) or '\0' in value:
                raise ValueError('invalid environment entry')
            if key.upper() in folded:
                raise ValueError('case-insensitive duplicate environment key')
            folded.add(key.upper())
        if on_observation is not None and not callable(on_observation):
            raise ValueError('on_observation must be callable')
        if cancel_requested is not None and not callable(cancel_requested):
            raise ValueError('cancel_requested must be callable')
        check_cancel()
        import msvcrt

        stage = 'RESOLVE_WINDOWS_API'
        api = ctypes.WinDLL('kernel32', use_last_error=True)
        SIZE_T = ctypes.c_size_t
        ULONG_PTR = ctypes.c_size_t
        HANDLE = wintypes.HANDLE
        DWORD = wintypes.DWORD

        class STARTUPINFO(ctypes.Structure):
            _fields_ = [('cb', DWORD), ('lpReserved', wintypes.LPWSTR),
                        ('lpDesktop', wintypes.LPWSTR), ('lpTitle', wintypes.LPWSTR),
                        ('dwX', DWORD), ('dwY', DWORD), ('dwXSize', DWORD),
                        ('dwYSize', DWORD), ('dwXCountChars', DWORD),
                        ('dwYCountChars', DWORD), ('dwFillAttribute', DWORD),
                        ('dwFlags', DWORD), ('wShowWindow', wintypes.WORD),
                        ('cbReserved2', wintypes.WORD), ('lpReserved2', ctypes.c_void_p),
                        ('hStdInput', HANDLE), ('hStdOutput', HANDLE), ('hStdError', HANDLE)]

        class STARTUPINFOEX(ctypes.Structure):
            _fields_ = [('StartupInfo', STARTUPINFO), ('lpAttributeList', ctypes.c_void_p)]

        class PROCESS_INFORMATION(ctypes.Structure):
            _fields_ = [('hProcess', HANDLE), ('hThread', HANDLE),
                        ('dwProcessId', DWORD), ('dwThreadId', DWORD)]

        class BASIC_LIMIT(ctypes.Structure):
            _fields_ = [('PerProcessUserTimeLimit', ctypes.c_int64),
                        ('PerJobUserTimeLimit', ctypes.c_int64), ('LimitFlags', DWORD),
                        ('MinimumWorkingSetSize', SIZE_T), ('MaximumWorkingSetSize', SIZE_T),
                        ('ActiveProcessLimit', DWORD), ('Affinity', ULONG_PTR),
                        ('PriorityClass', DWORD), ('SchedulingClass', DWORD)]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in (
                'ReadOperationCount', 'WriteOperationCount', 'OtherOperationCount',
                'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]

        class EXTENDED_LIMIT(ctypes.Structure):
            _fields_ = [('BasicLimitInformation', BASIC_LIMIT), ('IoInfo', IO_COUNTERS),
                        ('ProcessMemoryLimit', SIZE_T), ('JobMemoryLimit', SIZE_T),
                        ('PeakProcessMemoryUsed', SIZE_T), ('PeakJobMemoryUsed', SIZE_T)]

        class ACCOUNTING(ctypes.Structure):
            _fields_ = [(name, ctypes.c_int64) for name in (
                'TotalUserTime', 'TotalKernelTime', 'ThisPeriodTotalUserTime',
                'ThisPeriodTotalKernelTime')] + [(name, DWORD) for name in (
                'TotalPageFaultCount', 'TotalProcesses', 'ActiveProcesses', 'TotalTerminatedProcesses')]

        def bind(name, args, returns):
            fn = getattr(api, name)
            fn.argtypes, fn.restype = args, returns
            return fn

        close = bind('CloseHandle', [HANDLE], wintypes.BOOL)
        current = bind('GetCurrentProcess', [], HANDLE)
        duplicate = bind('DuplicateHandle', [HANDLE, HANDLE, HANDLE, ctypes.POINTER(HANDLE), DWORD, wintypes.BOOL, DWORD], wintypes.BOOL)
        make_job = bind('CreateJobObjectW', [ctypes.c_void_p, wintypes.LPCWSTR], HANDLE)
        set_job = bind('SetInformationJobObject', [HANDLE, ctypes.c_int, ctypes.c_void_p, DWORD], wintypes.BOOL)
        query_job = bind('QueryInformationJobObject', [HANDLE, ctypes.c_int, ctypes.c_void_p, DWORD, ctypes.c_void_p], wintypes.BOOL)
        assign = bind('AssignProcessToJobObject', [HANDLE, HANDLE], wintypes.BOOL)
        terminate_job = bind('TerminateJobObject', [HANDLE, wintypes.UINT], wintypes.BOOL)
        terminate_process = bind('TerminateProcess', [HANDLE, wintypes.UINT], wintypes.BOOL)
        initialize_attrs = bind('InitializeProcThreadAttributeList', [ctypes.c_void_p, DWORD, DWORD, ctypes.POINTER(SIZE_T)], wintypes.BOOL)
        update_attrs = bind('UpdateProcThreadAttribute', [ctypes.c_void_p, DWORD, SIZE_T, ctypes.c_void_p, SIZE_T, ctypes.c_void_p, ctypes.c_void_p], wintypes.BOOL)
        delete_attrs = bind('DeleteProcThreadAttributeList', [ctypes.c_void_p], None)
        create = bind('CreateProcessW', [wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
                                      wintypes.BOOL, DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
                                      ctypes.POINTER(STARTUPINFOEX), ctypes.POINTER(PROCESS_INFORMATION)], wintypes.BOOL)
        resume = bind('ResumeThread', [HANDLE], DWORD)
        times = bind('GetProcessTimes', [HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
                                       ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME)], wintypes.BOOL)
        wait = bind('WaitForSingleObject', [HANDLE, DWORD], DWORD)
        exit_code = bind('GetExitCodeProcess', [HANDLE, ctypes.POINTER(DWORD)], wintypes.BOOL)

        def require(ok):
            if not ok:
                raise ctypes.WinError(ctypes.get_last_error())

        def observe():
            state = wait(process, 0)
            if state == 0:
                code = DWORD()
                require(exit_code(process, ctypes.byref(code)))
                result['actual_exit'] = int(code.value)
                cleanup['primary_exit_confirmed'] = True
            elif state != 258:
                raise ctypes.WinError(ctypes.get_last_error())
            if assigned:
                info = ACCOUNTING()
                require(query_job(job, 1, ctypes.byref(info), ctypes.sizeof(info), None))
                cleanup['active_processes_last_observed'] = int(info.ActiveProcesses)
                cleanup['job_idle_confirmed'] = info.ActiveProcesses == 0
            return cleanup['primary_exit_confirmed'] and (not assigned or cleanup['job_idle_confirmed'])

        stage = 'CREATE_EXCLUSIVE_JOB'
        job = make_job(None, None)
        require(job)
        handles.append(job)
        limits = EXTENDED_LIMIT()
        limits.BasicLimitInformation.LimitFlags = 0x00002000  # KILL_ON_JOB_CLOSE; no breakaway.
        require(set_job(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        cleanup['kill_on_job_close_configured'] = True

        stage = 'PREPARE_EXPLICIT_STD_HANDLES'
        if stdin is None:
            nul = open(os.devnull, 'rb')
        input_stream = nul if stdin is None else stdin
        inherited = []
        for stream in (input_stream, stdout, stderr):
            stream.flush()
            duplicated = HANDLE()
            require(duplicate(current(), HANDLE(msvcrt.get_osfhandle(stream.fileno())),
                              current(), ctypes.byref(duplicated), 0, True, 2))
            handles.append(duplicated.value)
            inherited.append(duplicated.value)
        size = SIZE_T()
        initialize_attrs(None, 1, 0, ctypes.byref(size))
        if size.value == 0:
            raise ctypes.WinError(ctypes.get_last_error())
        attribute_buffer = ctypes.create_string_buffer(size.value)
        require(initialize_attrs(attribute_buffer, 1, 0, ctypes.byref(size)))
        attribute_initialized = True
        inherited_array = (HANDLE * 3)(*inherited)
        require(update_attrs(attribute_buffer, 0, 0x00020002, ctypes.cast(inherited_array, ctypes.c_void_p),
                             ctypes.sizeof(inherited_array), None, None))
        startup = STARTUPINFOEX()
        startup.StartupInfo.cb = ctypes.sizeof(startup)
        startup.StartupInfo.dwFlags = 0x00000100  # STARTF_USESTDHANDLES
        startup.StartupInfo.hStdInput, startup.StartupInfo.hStdOutput, startup.StartupInfo.hStdError = inherited
        startup.lpAttributeList = ctypes.addressof(attribute_buffer)
        command = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
        environment = ctypes.create_unicode_buffer('\0'.join(k + '=' + env[k] for k in sorted(env, key=str.upper)) + '\0\0')
        pi = PROCESS_INFORMATION()
        check_cancel()
        stage = 'CREATE_SUSPENDED'
        # EXTENDED_STARTUPINFO_PRESENT is required for the explicit HANDLE_LIST.
        # No default NO_WINDOW, DETACHED_PROCESS or NEW_PROCESS_GROUP flag.
        flags = creation_flags | 0x00000004 | 0x00000400 | 0x00080000
        require(create(argv[0], command, None, None, True, flags, environment, str(cwd), ctypes.byref(startup), ctypes.byref(pi)))
        process = pi.hProcess
        handles.extend([pi.hProcess, pi.hThread])
        result['owned_child_pid'] = int(pi.dwProcessId)
        stage = 'READ_CREATION_TIME'
        creation, exited, kernel, user = (wintypes.FILETIME() for _ in range(4))
        require(times(process, ctypes.byref(creation), ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)))
        result['creation_time_100ns'] = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)
        stage = 'ASSIGN_SUSPENDED_CHILD'
        require(assign(job, process))
        assigned = True
        cleanup['assigned_before_resume'] = True
        emit_observation('assigned-before-resume')
        check_cancel()
        if time.monotonic() - started >= timeout:
            result['timed_out'] = True
        else:
            stage = 'RESUME_ASSIGNED_CHILD'
            prior = resume(pi.hThread)
            if prior == 0xFFFFFFFF:
                raise ctypes.WinError(ctypes.get_last_error())
            if prior != 1:
                raise RuntimeError('Unexpected suspended thread count: ' + str(prior))
            result['resumed'] = True
            emit_observation('resumed')
            stage = 'WAIT_PRIMARY_AND_JOB_IDLE'
            while not observe():
                check_cancel()
                emit_observation('live')
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    result['timed_out'] = True
                    break
                time.sleep(min(0.02, remaining))
    except BaseException as exc:
        record_error(exc)
    finally:
        result['stage'] = stage
        if process is not None and api is not None:
            try:
                needs_termination = result['timed_out'] or result['error'] is not None
                if needs_termination:
                    requested = 0xE0000308  # Deliberate termination request, NEVER an inferred observed exit.
                    cleanup['termination_code_requested'] = requested
                    if assigned:
                        cleanup['termination_requested'] = True
                        cleanup['termination_succeeded'] = bool(terminate_job(job, requested))
                        require(cleanup['termination_succeeded'])
                    else:
                        # Create succeeded but binding failed: thread was never resumed, no descendants exist.
                        cleanup['unassigned_suspended_child_termination_requested'] = True
                        cleanup['unassigned_suspended_child_termination_succeeded'] = bool(terminate_process(process, requested))
                        require(cleanup['unassigned_suspended_child_termination_succeeded'])
                    deadline = time.monotonic() + 5.0
                    while not observe() and time.monotonic() < deadline:
                        time.sleep(0.02)
                    if not cleanup['primary_exit_confirmed'] or (assigned and not cleanup['job_idle_confirmed']):
                        raise RuntimeError('Termination was requested; exit/job-idle unconfirmed after cleanup deadline')
                else:
                    observe()
            except BaseException as exc:
                cleanup['errors'].append(error_text(exc))
                record_error(exc)
        if attribute_initialized:
            try:
                delete_attrs(attribute_buffer)
            except BaseException as exc:
                cleanup['errors'].append(error_text(exc))
                record_error(exc)
        close_failed = False
        for handle in reversed(handles):
            try:
                if not close(handle):
                    raise ctypes.WinError(ctypes.get_last_error())
            except BaseException as exc:
                close_failed = True
                cleanup['errors'].append(error_text(exc))
                record_error(exc)
        if nul is not None:
            try:
                nul.close()
            except BaseException as exc:
                close_failed = True
                cleanup['errors'].append(error_text(exc))
                record_error(exc)
        cleanup['handles_closed'] = not close_failed
        result['elapsed_seconds'] = time.monotonic() - started
    return result
