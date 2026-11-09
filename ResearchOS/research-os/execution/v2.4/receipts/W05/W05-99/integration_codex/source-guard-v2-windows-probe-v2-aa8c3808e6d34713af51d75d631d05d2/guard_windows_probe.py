import sys
sys.dont_write_bytecode=True
import ctypes,hashlib,json,os,types
from ctypes import wintypes
from pathlib import Path
OUT=Path(__file__).resolve().parent
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def checked(ref):
 p=Path(ref["path"]);b=p.read_bytes()
 assert {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}==ref
 return p,b
def save(n,obj):
 p=OUT/n
 with p.open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
doc=json.loads(Path(sys.argv[1]).read_bytes())
_,review_raw=checked(doc["review_ref"]);review=json.loads(review_raw)
assert review["decision"]=="PASS_SOURCE_ONLY" and review["reviewer"]=="codex:/root/w05_merge_review"
assert review["source_ref"]==doc["guard_ref"]
guard_path,guard_raw=checked(doc["guard_ref"])
module=types.ModuleType("independently_reviewed_source_guard_actual_probe");module.__file__=str(guard_path)
exec(compile(guard_raw,str(guard_path),"exec"),module.__dict__)
fixture=Path(doc["fixture_directory"])
a=fixture/"中文 evidence.py";b=fixture/"other source.json";replacement=fixture/"replacement.py"
before_a=b"guard witness: source file stays exact\n";before_b=b'{"guard":"source-only"}\n'
a.write_bytes(before_a);b.write_bytes(before_b);replacement.write_bytes(b"replacement must not land\n")
refs=[pin(a),pin(b),doc["python_ref"]]
kernel=ctypes.WinDLL("kernel32",use_last_error=True)
H=ctypes.c_void_p;D=wintypes.DWORD
create=kernel.CreateFileW;create.argtypes=[wintypes.LPCWSTR,D,D,H,D,D,H];create.restype=H
delete=kernel.DeleteFileW;delete.argtypes=[wintypes.LPCWSTR];delete.restype=wintypes.BOOL
move=kernel.MoveFileExW;move.argtypes=[wintypes.LPCWSTR,wintypes.LPCWSTR,D];move.restype=wintypes.BOOL
close_handle=kernel.CloseHandle;close_handle.argtypes=[H];close_handle.restype=wintypes.BOOL
def raw_writer_open():
 handle=create(str(a),0x40000000,1,None,3,0x80,None)
 if handle==H(-1).value or not handle:return False,ctypes.get_last_error()
 assert close_handle(handle)
 return True,None
def raw_delete():
 ok=bool(delete(str(a)));return ok,None if ok else ctypes.get_last_error()
def raw_replace():
 ok=bool(move(str(replacement),str(a),1));return ok,None if ok else ctypes.get_last_error()
events=[];guard=module.SourceReadGuard();closed=None
try:
 buffers=guard.acquire(refs)
 assert guard.get_buffer(str(a))==before_a and guard.get_buffer(str(b))==before_b
 assert a.read_bytes()==before_a and b.read_bytes()==before_b
 events.append({"name":"read_allowed_while_held","pass":True})
 for name,operation in [
  ("write_denied_while_held",raw_writer_open),
  ("delete_denied_while_held",raw_delete),
  ("replace_denied_while_held",raw_replace)]:
  succeeded,observed=operation()
  events.append({"name":name,"actual_win32_succeeded":succeeded,"observed_winerror":observed,"pass":not succeeded and observed==32})
  assert not succeeded and observed==32,name+": expected raw Win32 ERROR_SHARING_VIOLATION"
 assert a.read_bytes()==before_a and b.read_bytes()==before_b
 events.append({"name":"protected_inputs_unchanged","pass":True,"source_refs":refs})
finally:
 closed=guard.close()
 close_ref=save("guard.cleanup.actual.json",closed)
assert closed["closed"] is True and closed["retained_handles_count"]==0 and closed["errors"]==[]
assert closed["verification"]=="PASSED" and all(e["closed"] and e["verified"] and e["final_path_match"] for e in closed["entries"])
a.write_bytes(b"write after ownership ends\n")
assert a.read_bytes()==b"write after ownership ends\n"
events.append({"name":"write_allowed_after_close","pass":True})
kernel=ctypes.WinDLL("kernel32",use_last_error=True)
kernel.GetCurrentProcess.argtypes=[];kernel.GetCurrentProcess.restype=ctypes.c_void_p
kernel.IsProcessInJob.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.POINTER(wintypes.BOOL)];kernel.IsProcessInJob.restype=wintypes.BOOL
member=wintypes.BOOL()
assert kernel.IsProcessInJob(kernel.GetCurrentProcess(),None,ctypes.byref(member))
assert bool(member.value)
events.append({"name":"actual_probe_pid_is_job_member","pass":True})
proof=save("guard.windows.actual.json",{"schema":"researchos.source-read-guard-root-windows-probe.v1",
 "actor":"codex:/root","status":"PASS_PRIVATE_WINDOWS_TARGET_SCOPE_ONLY","actual_pid":os.getpid(),
 "actual_any_job_membership":bool(member.value),"review_ref":doc["review_ref"],"source_ref":doc["guard_ref"],
 "cleanup_ref":close_ref,"events":events,"expected_negative_sharing_errors_are_controls":True,
 "provider_requests":0,"target_host_executions":0,"canonical_writes":0,"runtime_qualification":False,"formal_acceptance":False})
print(json.dumps({"proof_ref":proof,"actual_pid":os.getpid(),"status":"PASS_PRIVATE_WINDOWS_TARGET_SCOPE_ONLY"}),flush=True)

