# W09 RECEIPT-ONLY PROPOSAL. Not imported/executed in preparation.
# Derived from pinned b60c8826 debug helper. New tree mode requires independent review.
# Captures all debug descendants only after actual membership in this created Job.
"""PROPOSED, NOT EXECUTED: receipt-only Windows debug-event child runner; importing this module starts no process.

The caller owns stdout/stderr, raw receipts, tool pins and the decision to stop.
An unnamed, non-inherited Job owns exactly this suspended child and descendants.
No PID lookup, taskkill, shell, breakaway flag or pre-existing Job is used.
"""

import ctypes
import hashlib
import struct
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


def run_owned(argv, cwd, env, stdout, stderr, timeout, expected_image, allowed_images, allowed_module_files, process_cap, stdin=None, creation_flags=0):
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
    result['debug_capture'] = {
        'mode': 'CREATE_OWN_JOB_DEBUG_PROCESS_TREE',
        'events': [], 'modules': [], 'exit_event_observed': False,
        'bounded_events': 131072, 'bounded_module_files': 32768,
        'actual_loaded_file_handles_only': True, 'complete': False,
    }
    debug = result['debug_capture']
    debug.update(create_process_count=0, exit_process_count=0, initial_breakpoint_count=0,
                 exit_event_code=None, total_processes_last_observed=None,
                 debugger_thread_process_handles='OS debug-engine lifetime until matching exit continuation; not explicitly owned duplicates')
    loaded_files = []
    def image_key(value):
        value = str(value)
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
        return str(Path(value).resolve()).casefold()

    processes = {}
    generations = []
    debug['process_generations'] = generations  # Live partial observations, including failures.
    debug['pending_failure_event'] = None
    cleanup = result['job_cleanup']
    started = time.monotonic()
    capture_deadline = None

    def deadline_check(deadline, phase):
        if time.monotonic() >= deadline:
            result['timed_out'] = True
            raise TimeoutError(phase + ' deadline exceeded')
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
        if not isinstance(expected_image, dict) or set(expected_image) != {'sha256', 'bytes'}:
            raise ValueError('Pinned executable digest and byte size required')
        if type(process_cap) is not int or not 1 <= process_cap <= 2048:
            raise ValueError('process_cap outside reviewed bound')
        if not isinstance(allowed_images, list) or not allowed_images or len(allowed_images) > 64:
            raise ValueError('explicit finite executable image set required')
        image_pins = {}
        for row in allowed_images:
            if set(row) != {'path','sha256','bytes'}:
                raise ValueError('exact image pin fields required')
            key = image_key(row['path'])
            if key in image_pins:
                raise ValueError('duplicate executable path pin')
            image_pins[key] = {'sha256':row['sha256'],'bytes':row['bytes']}
        if image_pins.get(image_key(argv[0])) != expected_image:
            raise ValueError('primary executable not exactly included in allowed set')
        if not isinstance(allowed_module_files,list) or not allowed_module_files or len(allowed_module_files)>200000:
            raise ValueError('Explicit module/runtime file universe required')
        module_pins = {image_key(r['path']): {'sha256':r['sha256'],'bytes':r['bytes']} for r in allowed_module_files}
        module_pins.update(image_pins)
        capture_deadline = started + timeout
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

        if ctypes.sizeof(ctypes.c_void_p) != 8:
            raise RuntimeError('This proposed event decoder requires Windows x64')

        class DEBUG_UNION(ctypes.Union):
            _fields_ = [('alignment', ctypes.c_uint64 * 20)]

        class DEBUG_EVENT(ctypes.Structure):
            _fields_ = [('code', DWORD), ('pid', DWORD), ('tid', DWORD), ('u', DEBUG_UNION)]

        if DEBUG_EVENT.u.offset != 16 or ctypes.sizeof(DEBUG_EVENT) != 176:
            raise RuntimeError('Unexpected x64 DEBUG_EVENT layout')
        wait_debug = bind('WaitForDebugEvent', [ctypes.POINTER(DEBUG_EVENT), DWORD], wintypes.BOOL)
        continue_debug = bind('ContinueDebugEvent', [DWORD, DWORD, DWORD], wintypes.BOOL)
        file_name = bind('GetFinalPathNameByHandleW', [HANDLE, wintypes.LPWSTR, DWORD, DWORD], DWORD)
        file_size = bind('GetFileSizeEx', [HANDLE, ctypes.POINTER(ctypes.c_int64)], wintypes.BOOL)
        seek_file = bind('SetFilePointerEx', [HANDLE, ctypes.c_int64, ctypes.POINTER(ctypes.c_int64), DWORD], wintypes.BOOL)
        read_file = bind('ReadFile', [HANDLE, ctypes.c_void_p, DWORD, ctypes.POINTER(DWORD), ctypes.c_void_p], wintypes.BOOL)
        close = bind('CloseHandle', [HANDLE], wintypes.BOOL)
        current = bind('GetCurrentProcess', [], HANDLE)
        duplicate = bind('DuplicateHandle', [HANDLE, HANDLE, HANDLE, ctypes.POINTER(HANDLE), DWORD, wintypes.BOOL, DWORD], wintypes.BOOL)
        make_job = bind('CreateJobObjectW', [ctypes.c_void_p, wintypes.LPCWSTR], HANDLE)
        set_job = bind('SetInformationJobObject', [HANDLE, ctypes.c_int, ctypes.c_void_p, DWORD], wintypes.BOOL)
        query_job = bind('QueryInformationJobObject', [HANDLE, ctypes.c_int, ctypes.c_void_p, DWORD, ctypes.c_void_p], wintypes.BOOL)
        assign = bind('AssignProcessToJobObject', [HANDLE, HANDLE], wintypes.BOOL)
        in_job = bind('IsProcessInJob', [HANDLE, HANDLE, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL)
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

        def hash_loaded_file(handle, deadline):
            deadline_check(deadline, 'module hash')
            length = ctypes.c_int64()
            require(file_size(handle, ctypes.byref(length)))
            if not 0 < length.value <= 256 * 1024 * 1024:
                raise RuntimeError('Loaded module file size outside finite capture bound')
            require(seek_file(handle, 0, None, 0))
            digest = hashlib.sha256()
            buffer = ctypes.create_string_buffer(1024 * 1024)
            total = 0
            while total < length.value:
                deadline_check(deadline, 'module hash')
                count = DWORD()
                require(read_file(handle, buffer, min(len(buffer), length.value-total), ctypes.byref(count), None))
                if count.value == 0:
                    raise RuntimeError('Unexpected EOF in held loaded-module file')
                digest.update(buffer.raw[:count.value])
                total += count.value
                deadline_check(deadline, 'module hash')
            return {'sha256': digest.hexdigest(), 'bytes': total}

        def capture_file(raw_handle, event_code, image_base, process_id):
            if not raw_handle or raw_handle == 0xFFFFFFFFFFFFFFFF:
                raise RuntimeError('Actual load event has no readable file handle; capture is incomplete')
            original = HANDLE(raw_handle)
            try:
                if len(loaded_files) >= 32768:
                    raise RuntimeError('Loaded-module capture limit exceeded')
                path_buffer = ctypes.create_unicode_buffer(32768)
                n = file_name(original, path_buffer, len(path_buffer), 0)
                if not n or n >= len(path_buffer):
                    raise ctypes.WinError(ctypes.get_last_error())
                retained = HANDLE()
                require(duplicate(current(), original, current(), ctypes.byref(retained), 0, False, 2))
                handles.append(retained.value)
                fact = {'event_code':event_code, 'image_base':image_base, 'pid':process_id,
                        'creation_time_100ns':processes[process_id]['creation_time_100ns'],
                        'path_from_actual_file_handle':path_buffer.value,
                        'before':hash_loaded_file(retained, capture_deadline)}
                if module_pins.get(image_key(path_buffer.value)) != fact['before']:
                    raise RuntimeError('Actual loaded module outside frozen runtime universe')
                if event_code == 3:
                    loaded_image_key = image_key(path_buffer.value)
                    if image_pins.get(loaded_image_key) != fact['before']:
                        raise RuntimeError('Actual CREATE_PROCESS file path/bytes outside pinned executable set')
                    processes[process_id]['image'] = fact
                    if process_id == pi.dwProcessId and fact['before'] != expected_image:
                        raise RuntimeError('Primary image mismatch')
                loaded_files.append((retained.value, fact))
                debug['modules'].append(fact)
                if sum(row['before']['bytes'] for row in debug['modules']) > 128 * 1024 * 1024 * 1024:
                    raise RuntimeError('Aggregate loaded module byte limit exceeded')
            finally:
                require(close(original))

        def pump(milliseconds, cleanup_mode=False):
            event = DEBUG_EVENT()
            if not wait_debug(ctypes.byref(event), milliseconds):
                error = ctypes.get_last_error()
                if error == 121:
                    return
                raise ctypes.WinError(error)
            status = 0x00010002
            event_fact = {'code':int(event.code), 'pid':int(event.pid), 'tid':int(event.tid)}
            event_owned = event.pid in processes and not processes[event.pid]['exit_continued']
            raw = bytes(event.u)
            event_file = struct.unpack_from('<Q', raw, 0)[0] if event.code in (3, 6) else 0
            try:
                if event.code not in (1, 2, 3, 4, 5, 6, 7, 8):
                    raise RuntimeError('RIP or unsupported debug event: ' + str(event.code))
                if event.code == 3:
                    if event.pid in processes and not processes[event.pid]['exit_continued']:
                        raise RuntimeError('Duplicate live CREATE_PROCESS')
                    if len(generations) >= process_cap:
                        raise RuntimeError('Executable process budget exhausted')
                    ph = HANDLE(struct.unpack_from('<Q',raw,8)[0])
                    membership = wintypes.BOOL()
                    require(in_job(ph, job, ctypes.byref(membership)))
                    if not membership.value:
                        raise RuntimeError('Debug child not a member of the actual exclusive Job')
                    event_owned = True  # Actual IsProcessInJob succeeded while event is held.
                    retained_process = HANDLE()
                    require(duplicate(current(), ph, current(), ctypes.byref(retained_process), 0, False, 2))
                    handles.append(retained_process.value)
                    c, e, k, u = (wintypes.FILETIME() for _ in range(4))
                    require(times(retained_process, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)))
                    identity = (int(c.dwHighDateTime)<<32)|int(c.dwLowDateTime)
                    if event.pid == pi.dwProcessId and identity != result['creation_time_100ns']:
                        raise RuntimeError('Primary creation identity mismatch')
                    proc = {'pid':int(event.pid),'primary_tid':int(event.tid),'creation_time_100ns':identity,
                            'held_process_handle':retained_process.value,'job_membership_observed':True,
                            'initial_breakpoint_count':0,'exit_event_code':None,'exit_continued':False,'independent_exit':None}
                    processes[event.pid] = proc
                    generations.append(proc)
                    debug['create_process_count'] += 1
                    event_fact['process_generation'] = len(generations)
                elif event.pid not in processes or processes[event.pid]['exit_continued']:
                    raise RuntimeError('Unknown process generation or event after EXIT continuation')
                proc = processes[event.pid]
                if event.code == 2:
                    event_fact['debug_thread_handle'] = struct.unpack_from('<Q',raw,0)[0]
                    # These debug-engine handles are closed by Windows on matching EXIT
                    # continuation. Keep only CreateProcessW handles in our close list.
                if event.code == 1:
                    code = struct.unpack_from('<I', raw, 0)[0]
                    first = struct.unpack_from('<I', raw, 152)[0]
                    event_fact.update(exception_code=code, first_chance=first,
                                      address=struct.unpack_from('<Q',raw,16)[0])
                    if first not in (0, 1):
                        raise RuntimeError('Invalid exception first-chance flag')
                    # The first first-chance breakpoint on the primary thread after
                    # CREATE_PROCESS is treated as the loader handshake. Record the
                    # address; this is an explicit debug-mode assumption, not attestation.
                    if code == 0x80000003 and first == 1 and event.tid == proc['primary_tid'] and proc['initial_breakpoint_count'] == 0:
                        proc['initial_breakpoint_count'] = 1
                        debug['initial_breakpoint_count'] += 1
                        event_fact['initial_breakpoint'] = True
                    else:
                        status = 0x80010001
                if event.code in (3, 6):
                    image_base = struct.unpack_from('<Q', raw, 24 if event.code == 3 else 8)[0]
                    if cleanup_mode:
                        event_fact['capture_omitted_during_failure_cleanup'] = True
                    else:
                        owned_file = event_file
                        event_file = 0  # capture_file finally owns this handle from here.
                        capture_file(owned_file, int(event.code), image_base, int(event.pid))
                elif event.code == 5:
                    debug['exit_process_count'] += 1
                    proc['exit_event_code'] = struct.unpack_from('<I', raw, 0)[0]
                    event_fact['actual_exit_event_code'] = proc['exit_event_code']
                    if event.pid == pi.dwProcessId:
                        debug['exit_event_observed'] = True
                        debug['exit_event_code'] = proc['exit_event_code']
            except BaseException as exc:
                record_error(exc)
            finally:
                try:
                    if event_file and event_file != 0xFFFFFFFFFFFFFFFF:
                        require(close(HANDLE(event_file)))
                except BaseException as exc:
                    record_error(exc)
                finally:
                    if len(debug['events']) >= 131072:
                        record_error(RuntimeError('Debug event bound exceeded'))
                    failed = result['error'] is not None or result['timed_out']
                    may_continue = not failed
                    if failed:
                        pending = dict(event_fact, continuation_status=status, owned_event=event_owned)
                        debug['pending_failure_event'] = pending
                        # Never release an unqualified image/module before killing its owned Job.
                        try:
                            if not assigned:
                                raise RuntimeError('Failed event has no assigned exclusive Job')
                            cleanup['termination_code_requested'] = 0xE0000308
                            cleanup['termination_requested'] = True
                            cleanup['termination_succeeded'] = bool(terminate_job(job, 0xE0000308))
                            require(cleanup['termination_succeeded'])
                            event_fact['job_terminated_before_continue'] = True
                            may_continue = event_owned
                        except BaseException as exc:
                            record_error(exc)
                    try:
                        if may_continue:
                            require(continue_debug(event.pid, event.tid, status))
                            event_fact['continued'] = True
                            debug['pending_failure_event'] = None
                            if event.code == 5 and event.pid in processes:
                                processes[event.pid]['exit_continued'] = True
                        else:
                            event_fact['continued'] = False
                    except BaseException as exc:
                        record_error(exc)
                    finally:
                        if len(debug['events']) < 131072:
                            debug['events'].append(event_fact)

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
                debug['total_processes_last_observed'] = int(info.TotalProcesses)
                if info.TotalProcesses > process_cap:
                    record_error(RuntimeError('Actual Job total processes exceeds reviewed cap'))
                cleanup['active_processes_last_observed'] = int(info.ActiveProcesses)
                cleanup['job_idle_confirmed'] = info.ActiveProcesses == 0
            return cleanup['primary_exit_confirmed'] and (not assigned or cleanup['job_idle_confirmed']) and debug['exit_event_observed']

        stage = 'CREATE_EXCLUSIVE_JOB'
        job = make_job(None, None)
        require(job)
        handles.append(job)
        limits = EXTENDED_LIMIT()
        limits.BasicLimitInformation.LimitFlags = 0x00002000  | 0x00000008  # KILL_ON_JOB_CLOSE plus ACTIVE_PROCESS; no breakaway.
        limits.BasicLimitInformation.ActiveProcessLimit = min(process_cap, 16)
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
        stage = 'CREATE_SUSPENDED'
        # EXTENDED_STARTUPINFO_PRESENT is required for the explicit HANDLE_LIST.
        # No default NO_WINDOW, DETACHED_PROCESS or NEW_PROCESS_GROUP flag.
        flags = creation_flags | 0x00000004 | 0x00000400 | 0x00080000 | 0x00000001  # Fixed DEBUG_PROCESS tree; no attach/breakaway
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
            stage = 'WAIT_PRIMARY_AND_JOB_IDLE'
            while not observe():
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    result['timed_out'] = True
                    break
                pump(min(20, max(1, int(remaining * 1000))))
                if result['error'] is not None:
                    raise RuntimeError('Actual module capture failed; stop this sole child')
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
                    pending = debug['pending_failure_event']
                    if pending is not None:
                        if not assigned or not cleanup.get('termination_succeeded') or not pending['owned_event']:
                            raise RuntimeError('Held failed debug event cannot be safely continued')
                        require(continue_debug(pending['pid'], pending['tid'], pending['continuation_status']))
                        pending['cleanup_continued_after_job_termination'] = True
                        if pending['code'] == 5 and pending['pid'] in processes:
                            processes[pending['pid']]['exit_continued'] = True
                        debug['pending_failure_event'] = None
                    deadline = time.monotonic() + 5.0
                    while not observe() and time.monotonic() < deadline:
                        pump(20, cleanup_mode=True)
                    if not cleanup['primary_exit_confirmed'] or (assigned and not cleanup['job_idle_confirmed']):
                        raise RuntimeError('Termination was requested; exit/job-idle unconfirmed after cleanup deadline')
                else:
                    observe()
            except BaseException as exc:
                cleanup['errors'].append(error_text(exc))
                record_error(exc)
        if process is not None and api is not None:
            try:
                finalization_deadline = time.monotonic() + 25.0
                result['evidence_finalization_timeout_seconds'] = 25
                if result['error'] is not None or result['timed_out']:
                    raise RuntimeError('Evidence finalization incomplete after earlier failure; no success')
                for retained, fact in loaded_files:
                    fact['after'] = hash_loaded_file(HANDLE(retained), finalization_deadline)
                    if fact['after'] != fact['before']:
                        raise RuntimeError('Loaded module bytes changed on the retained file handle')
                for proc in generations:
                    ph = HANDLE(proc['held_process_handle'])
                    if wait(ph, 0) != 0:
                        raise RuntimeError('Process generation exit not independently signaled')
                    code = DWORD()
                    require(exit_code(ph, ctypes.byref(code)))
                    proc['independent_exit'] = int(code.value)
                    if proc['independent_exit'] != proc['exit_event_code'] or not proc['exit_continued']:
                        raise RuntimeError('Process generation exit/continuation disagreement')
                    if proc['initial_breakpoint_count'] != 1:
                        raise RuntimeError('Missing initial loader handshake')
                debug['process_generations'] = generations
                debug['complete'] = (bool(debug['modules']) and len(generations) == debug['create_process_count']
                    == debug['exit_process_count'] == debug['total_processes_last_observed']
                    and debug['exit_event_code'] == result['actual_exit'] and result['error'] is None
                    and not result['timed_out'])
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
        closed_owned = 0
        cleanup['explicit_owned_handle_count'] = len(handles)
        for handle in reversed(handles):
            try:
                if not close(handle):
                    raise ctypes.WinError(ctypes.get_last_error())
                closed_owned += 1
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
        cleanup['explicit_owned_handles_remaining'] = len(handles)-closed_owned
        cleanup['explicit_owned_handle_close_successes'] = closed_owned
        cleanup['handles_closed'] = not close_failed and len(handles)==closed_owned
        result['elapsed_seconds'] = time.monotonic() - started
    return result
