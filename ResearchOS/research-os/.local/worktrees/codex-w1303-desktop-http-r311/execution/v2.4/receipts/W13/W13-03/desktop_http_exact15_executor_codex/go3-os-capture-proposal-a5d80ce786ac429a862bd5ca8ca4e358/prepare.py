"""Receipt preparation only. Does not import the proposed runner or launch tests."""
from pathlib import Path
import ast
import hashlib
import json
import difflib

OUT = Path(__file__).resolve().parent
MAIN = Path('D:/作品集/ResearchOS/research-os')
WT = MAIN / '.local/worktrees/codex-w1303-desktop-http-r311'
BASE = MAIN / 'execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write(name, data):
    data = data.encode('utf-8') if isinstance(data, str) else data
    with (OUT / name).open('xb') as f:
        f.write(data)
    return {'path': (OUT/name).as_posix(), 'sha256': sha(data), 'bytes':len(data)}

base = BASE.read_bytes()
assert sha(base) == '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad'
write('windows_owned_process.original.py', base)
text = base.decode('utf-8').replace('\r\n', '\n')

def replace(old, new):
    global text
    assert text.count(old) == 1, old[:100]
    text = text.replace(old, new)

replace('import ctypes\n', 'import ctypes\nimport hashlib\nimport struct\n')
replace('    cleanup = result[\'job_cleanup\']\n', '''    result['debug_capture'] = {
        'mode': 'CREATE_OWN_CHILD_DEBUG_ONLY_THIS_PROCESS',
        'events': [], 'modules': [], 'exit_event_observed': False,
        'bounded_events': 4096, 'bounded_module_files': 256,
        'actual_loaded_file_handles_only': True, 'complete': False,
    }
    debug = result['debug_capture']
    loaded_files = []
    cleanup = result['job_cleanup']
''')
replace("        close = bind('CloseHandle', [HANDLE], wintypes.BOOL)\n", '''        if ctypes.sizeof(ctypes.c_void_p) != 8:
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
''')
replace('        def observe():\n', '''        def hash_loaded_file(handle):
            length = ctypes.c_int64()
            require(file_size(handle, ctypes.byref(length)))
            if not 0 < length.value <= 256 * 1024 * 1024:
                raise RuntimeError('Loaded module file size outside finite capture bound')
            require(seek_file(handle, 0, None, 0))
            digest = hashlib.sha256()
            buffer = ctypes.create_string_buffer(1024 * 1024)
            total = 0
            while total < length.value:
                count = DWORD()
                require(read_file(handle, buffer, min(len(buffer), length.value-total), ctypes.byref(count), None))
                if count.value == 0:
                    raise RuntimeError('Unexpected EOF in held loaded-module file')
                digest.update(buffer.raw[:count.value])
                total += count.value
            return {'sha256': digest.hexdigest(), 'bytes': total}

        def capture_file(raw_handle, event_code, image_base):
            if not raw_handle or raw_handle == 0xFFFFFFFFFFFFFFFF:
                raise RuntimeError('Actual load event has no readable file handle; capture is incomplete')
            original = HANDLE(raw_handle)
            try:
                if len(loaded_files) >= 256:
                    raise RuntimeError('Loaded-module capture limit exceeded')
                path_buffer = ctypes.create_unicode_buffer(32768)
                n = file_name(original, path_buffer, len(path_buffer), 0)
                if not n or n >= len(path_buffer):
                    raise ctypes.WinError(ctypes.get_last_error())
                retained = HANDLE()
                require(duplicate(current(), original, current(), ctypes.byref(retained), 0, False, 2))
                handles.append(retained.value)
                fact = {'event_code':event_code, 'image_base':image_base,
                        'path_from_actual_file_handle':path_buffer.value,
                        'before':hash_loaded_file(retained)}
                loaded_files.append((retained.value, fact))
                debug['modules'].append(fact)
                if sum(row['before']['bytes'] for row in debug['modules']) > 1024 * 1024 * 1024:
                    raise RuntimeError('Aggregate loaded module byte limit exceeded')
            finally:
                require(close(original))

        def pump(milliseconds, cleanup_mode=False):
            event = DEBUG_EVENT()
            if not wait_debug(ctypes.byref(event), milliseconds):
                error = ctypes.get_last_error()
                if error == 121:  # ERROR_SEM_TIMEOUT; no event, not a child failure.
                    return
                raise ctypes.WinError(error)
            status = 0x00010002  # DBG_CONTINUE for non-exception notifications.
            event_fact = {'code':int(event.code), 'pid':int(event.pid), 'tid':int(event.tid)}
            try:
                if event.pid != pi.dwProcessId:
                    raise RuntimeError('Debug event does not belong to the process we created')
                raw = bytes(event.u)
                if event.code == 1:
                    code = struct.unpack_from('<I', raw, 0)[0]
                    event_fact.update(exception_code=code, first_chance=struct.unpack_from('<I', raw, 152)[0])
                    # Only the initial debugger breakpoint is consumed. Other exceptions
                    # retain application/OS handling, including Go runtime exceptions.
                    if code == 0x80000003 and not any(e.get('initial_breakpoint') for e in debug['events']):
                        event_fact['initial_breakpoint'] = True
                    else:
                        status = 0x80010001  # DBG_EXCEPTION_NOT_HANDLED
                elif event.code in (3, 6):
                    hfile = struct.unpack_from('<Q', raw, 0)[0]
                    image_base = struct.unpack_from('<Q', raw, 24 if event.code == 3 else 8)[0]
                    if cleanup_mode:
                        if hfile and hfile != 0xFFFFFFFFFFFFFFFF:
                            require(close(HANDLE(hfile)))
                        event_fact['capture_omitted_during_failure_cleanup'] = True
                    else:
                        capture_file(hfile, int(event.code), image_base)
                elif event.code == 5:
                    debug['exit_event_observed'] = True
                    event_fact['actual_exit_event_code'] = struct.unpack_from('<I', raw, 0)[0]
            except BaseException as exc:
                record_error(exc)
            finally:
                # These IDs come only from the received owned event; never OpenProcess(PID).
                require(continue_debug(event.pid, event.tid, status))
                if len(debug['events']) < 4096:
                    debug['events'].append(event_fact)
                else:
                    record_error(RuntimeError('Debug event bound exceeded'))

        def observe():
''')
replace('flags = creation_flags | 0x00000004 | 0x00000400 | 0x00080000', 'flags = creation_flags | 0x00000004 | 0x00000400 | 0x00080000 | 0x00000002  # Fixed DEBUG_ONLY_THIS_PROCESS; no attach')
replace('                time.sleep(min(0.02, remaining))', '''                pump(min(20, max(1, int(remaining * 1000))))
                if result['error'] is not None:
                    raise RuntimeError('Actual module capture failed; stop this sole child')''')
replace('                        time.sleep(0.02)', '                        pump(20, cleanup_mode=True)')
replace('        if attribute_initialized:\n', '''        if process is not None and api is not None:
            try:
                for retained, fact in loaded_files:
                    fact['after'] = hash_loaded_file(HANDLE(retained))
                    if fact['after'] != fact['before']:
                        raise RuntimeError('Loaded module bytes changed on the retained file handle')
                debug['complete'] = bool(debug['modules']) and debug['exit_event_observed'] and result['error'] is None
            except BaseException as exc:
                cleanup['errors'].append(error_text(exc))
                record_error(exc)
        if attribute_initialized:
''')
text = text.replace('"""Receipt-only Windows child runner;', '"""PROPOSED, NOT EXECUTED: receipt-only Windows debug-event child runner;', 1)
ast.parse(text)
helper_ref = write('windows_debug_owned_process.py', text)
write('owned-helper-proposed.diff', ''.join(difflib.unified_diff(base.decode('utf-8').splitlines(True),text.splitlines(True),fromfile='r308/original',tofile='proposal/owned-debug')))
write('preparation.json', json.dumps({'status':'PREPARATION_ONLY_NOT_EXECUTED', 'original':{'path':BASE.as_posix(),'sha256':sha(base),'bytes':len(base)},'proposed_helper':helper_ref,'validation':'ast.parse only; no WinAPI invocation or child started'}, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(helper_ref,ensure_ascii=False))
