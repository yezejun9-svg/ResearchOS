"""Only short, local Python process-tree fixtures; never network or product IO."""
import ctypes
from ctypes import wintypes
import os
import subprocess
import sys
import time

mode = sys.argv[1]
if mode == "leaf":
    print("OWNED_LEAF_STARTED", os.getpid(), flush=True)
    time.sleep(float(sys.argv[2]))
    print("OWNED_LEAF_EXIT", flush=True)
elif mode == "normal-tree":
    print("OWNED_ROOT_STARTED", os.getpid(), flush=True)
    child = subprocess.Popen([sys.executable, "-I", "-S", "-X", "utf8", __file__, "leaf", ".08"], stdin=subprocess.DEVNULL, stdout=sys.stdout, stderr=sys.stderr)
    assert child.wait(timeout=2) == 0
    print("OWNED_ROOT_EXIT", flush=True)
elif mode in ("timeout-tree", "parent-exit-tree"):
    child = subprocess.Popen([sys.executable, "-I", "-S", "-X", "utf8", __file__, "leaf", "20"], stdin=subprocess.DEVNULL, stdout=sys.stdout, stderr=sys.stderr)
    print("OWNED_LONG_CHILD_CREATED", child.pid, flush=True)
    if mode == "parent-exit-tree": os._exit(0)
    time.sleep(20)
elif mode == "grace-event":
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    event = int(os.environ["OWNED_VERIFICATION_STOP_EVENT"])
    print("OWNED_GRACE_WAIT", flush=True)
    if kernel.WaitForSingleObject(event, 5000) != 0: raise SystemExit(9)
    print("OWNED_GRACE_EXIT", flush=True)
elif mode == "output-limit":
    sys.stdout.write("X" * 8192); sys.stdout.flush()
    time.sleep(20)
else: raise SystemExit(8)
