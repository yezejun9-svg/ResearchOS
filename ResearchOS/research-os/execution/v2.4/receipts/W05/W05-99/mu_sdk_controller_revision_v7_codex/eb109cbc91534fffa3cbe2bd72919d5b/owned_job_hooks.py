"""Root-owned Windows Job hook. Importing this file starts no process."""
import hashlib, types
from pathlib import Path
BASE = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py")
BASE_SHA = "6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
BASE_BYTES = 18901
SIGNATURE = "def run_owned(argv, cwd, env, stdout, stderr, timeout, stdin=None, creation_flags=0):"
ASSIGNED = "        cleanup['assigned_before_resume'] = True\n"

def load_hooked_owned_process():
    raw = BASE.read_bytes()
    if len(raw) != BASE_BYTES or hashlib.sha256(raw).hexdigest() != BASE_SHA:
        raise RuntimeError("pinned owned-process base changed")
    text = raw.decode("utf-8")
    if text.count(SIGNATURE) != 1 or text.count(ASSIGNED) != 1:
        raise RuntimeError("owned-process exact hook locations changed")
    text = text.replace(SIGNATURE, SIGNATURE[:-2] + ", before_resume=None):")
    hook = """        if before_resume is not None:
            before_resume({
                'process_handle': int(pi.hProcess), 'thread_handle': int(pi.hThread),
                'job_handle': int(job), 'runner_pid': int(pi.dwProcessId),
                'creation_time_100ns': result['creation_time_100ns'],
                'started_monotonic': started, 'absolute_deadline_monotonic': started + timeout,
                'assigned_before_resume': cleanup['assigned_before_resume'],
                'kill_on_job_close_configured': cleanup['kill_on_job_close_configured'],
                'resumed': False,
            })
"""
    text = text.replace(ASSIGNED, ASSIGNED + hook)
    module = types.ModuleType("root_owned_before_resume")
    module.__file__ = str(BASE)
    exec(compile(text, str(BASE) + "::root-before-resume", "exec"), module.__dict__)
    return module

def run_owned_hooked(argv, cwd, env, stdout, stderr, timeout, before_resume, stdin=None, creation_flags=0):
    if not callable(before_resume):
        raise ValueError("a reviewed before-resume callback is required")
    return load_hooked_owned_process().run_owned(
        argv, cwd, env, stdout, stderr, timeout, stdin=stdin,
        creation_flags=creation_flags, before_resume=before_resume)
