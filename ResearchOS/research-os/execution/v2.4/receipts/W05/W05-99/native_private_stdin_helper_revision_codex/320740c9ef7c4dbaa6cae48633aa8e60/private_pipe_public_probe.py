"""Public dummy-input probe for Root's independent private-pipe tests only."""
import ctypes
from ctypes import wintypes
import json
import msvcrt
import sys
import time

def main():
    mode = sys.argv[1]
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.GetFileType.argtypes = [wintypes.HANDLE]
    api.GetFileType.restype = wintypes.DWORD
    kind = int(api.GetFileType(wintypes.HANDLE(msvcrt.get_osfhandle(sys.stdin.fileno()))))
    data = bytearray(sys.stdin.buffer.read(4097))
    expected = b"A" * 4096 if mode == "maximum" else b"PUBLIC_DUMMY_PRIVATE_PIPE_TEST"
    valid = kind == 3 and data == expected
    for index in range(len(data)):
        data[index] = 0
    print(json.dumps({"scope": "PUBLIC_DUMMY_INPUT_ONLY", "file_type_pipe": kind == 3,
                      "read_all_reached_eof": True, "expected_public_input_matched": valid}), flush=True)
    if not valid:
        return 9
    if mode == "reject":
        return 7
    if mode == "timeout":
        time.sleep(60)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

