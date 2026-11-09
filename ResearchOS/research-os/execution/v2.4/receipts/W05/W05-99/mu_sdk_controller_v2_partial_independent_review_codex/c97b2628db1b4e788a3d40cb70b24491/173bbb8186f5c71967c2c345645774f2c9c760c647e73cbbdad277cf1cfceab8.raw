"""Execute the reviewed SDK precheck and phase in one assigned Python PID."""
import sys
sys.dont_write_bytecode = True
import hashlib, json, os, types
from pathlib import Path

def pinned(pin):
    path = Path(pin["path"])
    if not path.is_absolute() or not path.is_file():
        raise RuntimeError("absolute existing pin required")
    raw = path.read_bytes()
    if len(raw) != pin["bytes"] or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
        raise RuntimeError("pinned input changed")
    return path, raw

def main():
    if len(sys.argv) != 2:
        raise RuntimeError("usage: phase_worker.py ABSOLUTE_INPUT.json")
    input_path = Path(sys.argv[1])
    if not input_path.is_absolute():
        raise RuntimeError("absolute phase input required")
    input_raw = input_path.read_bytes()
    doc = json.loads(input_raw)
    runner_pin = doc["root_registration"]
    _, registration_raw = pinned(runner_pin)
    registration = json.loads(registration_raw)
    runner_path, runner_raw = pinned(registration["source_ref"])
    phase = doc["phase"]
    if phase not in ("bootstrap", "execute"):
        raise RuntimeError("unsupported phase")
    engine = types.ModuleType("reviewed_mu_sdk_trial_engine")
    engine.__file__ = str(runner_path)
    exec(compile(runner_raw, str(runner_path), "exec"), engine.__dict__)
    original_argv = sys.argv[:]
    try:
        for command in ("precheck-" + phase, phase):
            if input_path.read_bytes() != input_raw:
                raise RuntimeError("phase input changed between precheck and execute")
            pinned(registration["source_ref"])
            sys.argv = [str(runner_path), command, str(input_path)]
            engine.main()
            print(json.dumps({"root_phase_worker_pid": os.getpid(),
                              "completed_command": command,
                              "entry_in_same_pid": True}), flush=True)
    finally:
        sys.argv = original_argv

if __name__ == "__main__":
    main()
