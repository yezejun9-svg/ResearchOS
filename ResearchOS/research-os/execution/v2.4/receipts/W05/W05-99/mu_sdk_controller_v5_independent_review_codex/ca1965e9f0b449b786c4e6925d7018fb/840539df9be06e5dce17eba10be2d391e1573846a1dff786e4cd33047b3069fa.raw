"""Development-only PID/Job witness; no SDK, product or provider operation."""
import sys
sys.dont_write_bytecode = True
import ctypes, json, os, time
from pathlib import Path
def main():
    if len(sys.argv) != 2:
        raise RuntimeError("absolute witness output required")
    output = Path(sys.argv[1])
    if not output.is_absolute() or output.exists():
        raise RuntimeError("fresh absolute witness output required")
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.GetCurrentProcess.restype = ctypes.c_void_p
    k.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
    k.IsProcessInJob.restype = ctypes.c_int
    assigned = ctypes.c_int()
    if not k.IsProcessInJob(k.GetCurrentProcess(), None, ctypes.byref(assigned)) or not assigned.value:
        raise RuntimeError("probe outside Job")
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"schema": "researchos.mu-sdk-controller-development-probe.v1",
                   "pid": os.getpid(), "inside_job": True, "monotonic_tick": time.monotonic(),
                   "external_provider_requests": 0, "sdk_entry_executed": False}, stream)
    print("CURRENT_PID_JOB_PROBE_PASSED", flush=True)
if __name__ == "__main__":
    main()
