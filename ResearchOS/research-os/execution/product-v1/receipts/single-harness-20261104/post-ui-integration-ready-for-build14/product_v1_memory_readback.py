"""Read-only Windows commit/physical memory snapshot; no process manipulation."""
import ctypes,json
from ctypes import wintypes
class MEMORYSTATUSEX(ctypes.Structure):
 _fields_=[('dwLength',wintypes.DWORD),('dwMemoryLoad',wintypes.DWORD),('ullTotalPhys',ctypes.c_ulonglong),('ullAvailPhys',ctypes.c_ulonglong),('ullTotalPageFile',ctypes.c_ulonglong),('ullAvailPageFile',ctypes.c_ulonglong),('ullTotalVirtual',ctypes.c_ulonglong),('ullAvailVirtual',ctypes.c_ulonglong),('ullAvailExtendedVirtual',ctypes.c_ulonglong)]
value=MEMORYSTATUSEX();value.dwLength=ctypes.sizeof(value)
api=ctypes.WinDLL('kernel32',use_last_error=True).GlobalMemoryStatusEx;api.argtypes=[ctypes.POINTER(MEMORYSTATUSEX)];api.restype=wintypes.BOOL
if not api(ctypes.byref(value)):raise ctypes.WinError(ctypes.get_last_error())
print(json.dumps(dict(memory_load_percent=value.dwMemoryLoad,total_physical_bytes=value.ullTotalPhys,available_physical_bytes=value.ullAvailPhys,total_commit_limit_bytes=value.ullTotalPageFile,available_commit_bytes=value.ullAvailPageFile,process_or_os_changes=0)))
