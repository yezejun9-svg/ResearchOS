"""Root-only synthetic fixture broker; importing starts no process.

The public request identifies an independently reviewed executable and helper.
Current Owner bytes arrive only over an inherited Windows stdin pipe. No path,
argument, environment entry, output or receipt contains this private input.
"""
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import json
import msvcrt
import os
from pathlib import Path
import sys

def raw_pin(path):
    data = path.read_bytes()
    return {"path": str(path), "sha256": "sha256:" + hashlib.sha256(data).hexdigest(), "bytes": len(data)}

def require_pin(pin):
    if not isinstance(pin, dict) or set(pin) != {"role", "path", "sha256", "bytes"}:
        raise ValueError("public pin shape")
    path = Path(pin["path"])
    if not path.is_absolute() or not path.is_file() or str(path.resolve()).casefold() != str(path).casefold():
        raise ValueError("public pin path")
    actual = raw_pin(path)
    if actual["sha256"] != pin["sha256"] or actual["bytes"] != pin["bytes"]:
        raise ValueError("public pin changed")
    return path

def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, separators=(",", ":"))
        stream.flush()
        os.fsync(stream.fileno())

def read_private_pipe():
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.GetFileType.argtypes = [wintypes.HANDLE]
    api.GetFileType.restype = wintypes.DWORD
    if api.GetFileType(wintypes.HANDLE(msvcrt.get_osfhandle(sys.stdin.fileno()))) != 3:
        raise ValueError("broker requires real private stdin pipe")
    value = bytearray(4097)
    count = 0
    try:
        while count < len(value):
            view = memoryview(value)[count:]
            try:
                received = sys.stdin.buffer.readinto(view)
            finally:
                view.release()
            if not received:
                break
            count += received
        if not 1 <= count <= 4096:
            raise ValueError("broker private input size")
        del value[count:]
        return value
    except BaseException:
        for index in range(len(value)):
            value[index] = 0
        raise

def main():
    private_input = None
    output = None
    try:
        if len(sys.argv) != 2:
            raise ValueError("one public request path required")
        request_path = Path(sys.argv[1])
        if not request_path.is_absolute() or request_path.stat().st_size > 1024 * 1024:
            raise ValueError("public request path/size")
        request = json.loads(request_path.read_text(encoding="utf-8"))
        expected = {"Schema", "Program", "Arguments", "CWD", "Environment",
                    "OutputDirectory", "TimeoutSeconds", "PrivateStdinHelper"}
        if set(request) != expected or request["Schema"] != "researchos.synthetic-native-broker.v1":
            raise ValueError("public request schema")
        program = require_pin(request["Program"])
        helper_path = require_pin(request["PrivateStdinHelper"])
        output = Path(request["OutputDirectory"])
        if not output.is_absolute() or output.parent != request_path.parent or output.exists():
            raise ValueError("fresh sibling output directory required")
        if set(request["Environment"]) != {"SystemRoot", "WINDIR"}:
            raise ValueError("native environment must be the fixed public pair")
        if not isinstance(request["Arguments"], list) or not all(isinstance(v, str) for v in request["Arguments"]):
            raise ValueError("public arguments required")
        output.mkdir(parents=False, exist_ok=False)
        spec = importlib.util.spec_from_file_location("reviewed_owned_private_stdin", helper_path)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        private_input = read_private_pipe()
        with (output / "stdout.raw").open("xb") as stdout, (output / "stderr.raw").open("xb") as stderr:
            result = helper.run_owned_private_stdin(
                [str(program)] + request["Arguments"], request["CWD"], request["Environment"],
                stdout, stderr, request["TimeoutSeconds"], private_input, creation_flags=0x08000000)
        closed = result["job_cleanup"]
        complete = (result["actual_exit"] is not None and result["error"] is None and not result["timed_out"]
                    and result["resumed"] and closed["assigned_before_resume"]
                    and closed["primary_exit_confirmed"] and closed["job_idle_confirmed"]
                    and closed["active_processes_last_observed"] == 0
                    and closed["handles_closed"] and not closed["errors"]
                    and result["private_stdin"]["input_buffer_cleared"] and not any(private_input))
        write_new(output / "invocation.json", {
            "Schema": "researchos.synthetic-native-broker-result.v1",
            "PublicRequest": raw_pin(request_path), "Result": result,
            "Stdout": raw_pin(output / "stdout.raw"), "Stderr": raw_pin(output / "stderr.raw"),
            "PrivateInputPersisted": False, "ActualLifetimeClosed": complete,
            "NativeAuthorityAcceptance": False})
        print(json.dumps({"output_directory": str(output), "actual_lifetime_closed": complete,
                          "native_authority_acceptance": False}), flush=True)
        return 0 if complete else 1
    except BaseException as exc:
        # Exception text can originate in an input decoder. Do not echo it.
        if output is not None and output.is_dir() and not (output / "broker-error.json").exists():
            write_new(output / "broker-error.json", {"error_type": type(exc).__name__,
                      "private_input_persisted": False, "native_authority_acceptance": False})
        print(json.dumps({"broker_failed": True, "error_type": type(exc).__name__}), file=sys.stderr, flush=True)
        return 1
    finally:
        if private_input is not None:
            for index in range(len(private_input)):
                private_input[index] = 0

if __name__ == "__main__":
    raise SystemExit(main())

