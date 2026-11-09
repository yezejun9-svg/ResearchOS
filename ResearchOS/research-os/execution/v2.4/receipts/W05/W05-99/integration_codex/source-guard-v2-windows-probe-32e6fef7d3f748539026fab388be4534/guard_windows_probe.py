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
events=[];guard=module.SourceReadGuard();closed=None
try:
 buffers=guard.acquire(refs)
 assert guard.get_buffer(str(a))==before_a and guard.get_buffer(str(b))==before_b
 assert a.read_bytes()==before_a and b.read_bytes()==before_b
 events.append({"name":"read_allowed_while_held","pass":True})
 for name,operation in [
  ("write_denied_while_held",lambda:a.write_bytes(b"FORBIDDEN")),
  ("delete_denied_while_held",lambda:a.unlink()),
  ("replace_denied_while_held",lambda:os.replace(replacement,a))]:
  try:operation()
  except OSError as error:
   observed=getattr(error,"winerror",None)
   events.append({"name":name,"observed_winerror":observed,"observed_errno":error.errno,"pass":observed==32})
   assert observed==32,name+": expected actual Windows sharing violation"
  else:raise AssertionError(name+": protected file mutation succeeded")
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

