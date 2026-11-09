import ast,copy,hashlib,json,types
from pathlib import Path,PureWindowsPath
O=Path(__file__).resolve().parent
rows=json.loads((O/"intake.json").read_bytes())["rows"]
def raw(n):
 r=next(x for x in rows if Path(x["source_ref"]["path"]).name==n)
 return Path(r["snapshot_ref"]["path"]).read_bytes()
source=ast.parse(raw("canonical_transactions.py"));controller=ast.parse(raw("controller.py"))
files={};directories=set();events=[];handles={};locks={};fault={};journal_writes=[]
class MemPath:
 def __init__(self,p):self.p=str(PureWindowsPath(str(p)))
 def __str__(self):return self.p
 def __truediv__(self,p):return MemPath(str(PureWindowsPath(self.p)/str(p)))
 def __eq__(self,p):return isinstance(p,MemPath) and PureWindowsPath(self.p)==PureWindowsPath(p.p)
 def __hash__(self):return hash(PureWindowsPath(self.p))
 def is_absolute(self):return PureWindowsPath(self.p).is_absolute()
 def is_dir(self):return self.p in directories
 def mkdir(self):
  if self.p in directories:raise FileExistsError(self.p)
  directories.add(self.p);events.append(["mkdir",self.p])
class Number:
 def __init__(self,v=0):self.value=v if v is not None else 0
class Handle(Number):
 def __init__(self,v=0):super().__init__((2**64-1) if v==-1 else v)
class Buffer:
 def __init__(self,x):
  self.raw=b"\x00"*x if isinstance(x,int) else bytes(x)+b"\x00"
class UnicodeBuffer:
 def __init__(self,n):self.value="";self.length=n
 def __len__(self):return self.length
class Function:
 def __init__(self,fn):self.fn=fn
 def __call__(self,*args):return self.fn(*args)
root=MemPath("D:/作品集/ResearchOS/research-os")
paths=(root/"execution/v2.4/checkpoint.json",root/"execution/v2.4/path_ownership.json")
journal_dir=MemPath("D:/review-only/phase")
def file_pin(p):
 b=files[str(p)];return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def json_bytes(v):return (json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode()
def exclusive(p,b):
 p=str(p)
 if p in files:raise FileExistsError(p)
 files[p]=b;journal_writes.append(p);events.append(["journal",p]);return {"path":p,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
counter={"next_handle":100,"tx":0}
def create(path,access,share,security,disposition,flags,template):
 events.append(["CreateFileW",path,access,share,disposition])
 if path in locks:return 2**64-1
 if path not in files:return 2**64-1
 if fault.get("second_open") and path==str(paths[1]):return 2**64-1
 counter["next_handle"]+=1;h=counter["next_handle"];handles[h]={"path":path,"offset":0};locks[path]=h;return h
def close(h):
 events.append(["CloseHandle",h])
 if fault.get("close") and h==min(handles):return 0
 p=handles.pop(h)["path"];locks.pop(p);return 1
def size(h,num):
 events.append(["GetFileSizeEx",h,"locks",len(locks)]);num.value=len(files[handles[h]["path"]]);return 1
def seek(h,pos,unused,origin):handles[h]["offset"]=pos;return 1
def read(h,buf,count,got,unused):
 p=handles[h]["path"];offset=handles[h]["offset"];data=files[p][offset:offset+count];buf.raw=data+b"\x00"*(count-len(data));got.value=len(data);handles[h]["offset"]+=len(data);return 1
def write(h,buf,count,done,unused):
 p=handles[h]["path"];events.append(["WriteFile",p,count,"locks",len(locks)])
 if fault.get("write_ownership") and p==str(paths[1]):return 0
 old=files[p];offset=handles[h]["offset"];data=buf.raw[:count];files[p]=old[:offset]+data+old[offset+len(data):];handles[h]["offset"]+=len(data);done.value=len(data);return 1
def end(h):
 p=handles[h]["path"];files[p]=files[p][:handles[h]["offset"]];return 1
def flush(h):events.append(["FlushFileBuffers",h]);return 1
def final_path(h,out,length,flags):out.value=handles[h]["path"];return len(out.value)
kernel=types.SimpleNamespace(**{n:Function(f) for n,f in {"CreateFileW":create,"CloseHandle":close,"GetFileSizeEx":size,"SetFilePointerEx":seek,"ReadFile":read,"WriteFile":write,"SetEndOfFile":end,"FlushFileBuffers":flush,"GetFinalPathNameByHandleW":final_path}.items()})
ct=types.SimpleNamespace(WinDLL=lambda *a,**k:kernel,c_void_p=Handle,c_longlong=Number,POINTER=lambda x:x,byref=lambda x:x,create_string_buffer=Buffer,create_unicode_buffer=UnicodeBuffer,get_last_error=lambda:32,WinError=lambda code:RuntimeError("simulated WinError "+str(code)))
wt=types.SimpleNamespace(DWORD=Number,BOOL=Number,LPCWSTR=str,LPWSTR=str)
def next_uuid():counter["tx"]+=1;return types.SimpleNamespace(hex=str(counter["tx"]).zfill(32))
env={"Path":MemPath,"ROOT":root,"PATHS":paths,"MAX_BYTES":16*1024*1024,"ctypes":ct,"wintypes":wt,"os":types.SimpleNamespace(name="nt"),"uuid":types.SimpleNamespace(uuid4=next_uuid),"json":json,"hashlib":hashlib,"exclusive":exclusive}
names={"pin_raw","encoded","update_pair"}
exec(compile(ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),"<selected-canonical-AST-all-OS-calls-memory-stubbed>","exec"),env)
uuid="a"*32
cp0={"head":"adc460c2138528f163f7fdab5e8d81dde157b7fb","current_step_id":"W05-99","revision":342,"work_in_progress":{"mu_sdk_active_run_uuid":uuid}}
ow0={"revision":168,"card_path_bindings":{"W05-99":{"subtasks":{"mu_sdk_trial":{"run_uuid":uuid,"state":"ACTIVE_ISOLATED_PHASE"}}}}}
def reset():
 files.clear();directories.clear();events.clear();handles.clear();locks.clear();fault.clear();journal_writes.clear()
 directories.add(str(journal_dir));files[str(paths[0])]=json_bytes(cp0);files[str(paths[1])]=json_bytes(ow0)
def require(ok,msg):
 if not ok:raise RuntimeError(msg)
def exclusive_json(p,v):return exclusive(p,json_bytes(v))
cenv={"Path":MemPath,"ROOT":root,"SOURCE_COMMIT":cp0["head"],"pin":file_pin,"stamp":lambda:"2026-10-08T00:00:00Z","require":require,"exclusive_json":exclusive_json,"module":lambda *a:types.SimpleNamespace(update_pair=env["update_pair"]),"CANONICAL_TRANSACTION_REF":{"stub":"immutable module source pin already verified"}}
exec(compile(ast.Module(body=[n for n in controller.body if isinstance(n,ast.FunctionDef) and n.name in ("cleanup_confirmed","close_canonical_lease","activate_canonical_lease")],type_ignores=[]),"<controller-lease-pure-AST-only>","exec"),cenv)
good={"actual_exit":0,"timed_out":False,"error":None,"job_cleanup":{"errors":[],"active_processes_last_observed":0,"primary_exit_confirmed":True,"job_idle_confirmed":True,"handles_closed":True}}
results=[]
reset()
def transform(cp,ow):
 events.append(["transform_locks",len(locks)])
 blocked=create(str(paths[0]),0x40000000,0,None,3,0x80,None)==2**64-1
 events.append(["concurrent_open_denied",blocked]);cp["revision"]+=1;ow["revision"]+=1;return cp,ow
refs=[file_pin(p) for p in paths];env["update_pair"](refs,transform,journal_dir,"activate")
results.append({"case":"BOTH_EXCLUSIVE_HANDLES_HELD_THROUGH_READ_COMPARE_WRITE","matches_expected":all(e[-1]==2 for e in events if e[0] in ("GetFileSizeEx","WriteFile")) and ["transform_locks",2] in events and ["concurrent_open_denied",True] in events and not locks,"events":copy.deepcopy(events),"OS_semantics":"Mandatory sharing behavior modeled; not actual Windows proof"})
reset();refs=[file_pin(p) for p in paths];changed=json.loads(files[str(paths[0])]);changed["revision"]+=1;files[str(paths[0])]=json_bytes(changed);before=dict(files);error=None
try:env["update_pair"](refs,lambda a,b:(a,b),journal_dir,"activate")
except RuntimeError as exc:error=str(exc)
results.append({"case":"STALE_EXPECTED_BYTES_REJECTED_UNDER_LOCK","matches_expected":error is not None and files==before and not locks,"error":error,"events":copy.deepcopy(events)})
reset();fault["second_open"]=True;before=dict(files);error=None
try:env["update_pair"]([file_pin(p) for p in paths],lambda a,b:(a,b),journal_dir,"activate")
except RuntimeError as exc:error=str(exc)
results.append({"case":"SECOND_LOCK_FAILURE_MAKES_NO_WRITES","matches_expected":error is not None and files==before and not locks,"error":error,"events":copy.deepcopy(events)})
reset();before=dict(files);error=None
def bad_transform(a,b):raise RuntimeError("independent transform failure")
try:env["update_pair"]([file_pin(p) for p in paths],bad_transform,journal_dir,"activate")
except RuntimeError as exc:error=str(exc)
results.append({"case":"TRANSFORM_FAILURE_MAKES_NO_WRITES","matches_expected":error is not None and files==before and not locks,"error":error})
reset();fault["write_ownership"]=True;error=None
try:cenv["close_canonical_lease"]({"run_uuid":uuid},journal_dir,good,None)
except RuntimeError as exc:error=str(exc)
after_cp=json.loads(files[str(paths[0])]);after_ow=json.loads(files[str(paths[1])]);partial=[json.loads(b) for p,b in files.items() if p.endswith("failed.partial.json")]
results.append({"case":"CLOSE_SECOND_WRITE_FAILURE_SHOULD_KEEP_RECONCILIATION_GUARD","matches_expected":after_cp["work_in_progress"]["mu_sdk_active_run_uuid"]==uuid,"error":error,"checkpoint_active_uuid":after_cp["work_in_progress"]["mu_sdk_active_run_uuid"],"ownership_state":after_ow["card_path_bindings"]["W05-99"]["subtasks"]["mu_sdk_trial"]["state"],"partial_receipt":partial,"locks_released":not locks})
# No automatic retry is executed by the candidate; this explicit hypothetical next admission tests the guard.
fault.clear();newid="b"*32
doc={"run_uuid":newid,"root_registration":{"synthetic":"new registration"},"data_root":"D:/isolated"}
admission_error=None
try:cenv["activate_canonical_lease"](doc,{"synthetic":"lease"},file_pin(paths[0]),file_pin(paths[1]),journal_dir)
except RuntimeError as exc:admission_error=str(exc)
results.append({"case":"NEW_ADMISSION_AFTER_UNRECONCILED_PARTIAL_CLOSE_SHOULD_REJECT","matches_expected":admission_error is not None,"error":admission_error,"checkpoint_active_uuid":json.loads(files[str(paths[0])])["work_in_progress"]["mu_sdk_active_run_uuid"],"scope":"explicit second invocation in memory with fresh current refs, not a candidate automatic retry"})
reset();fault["close"]=True;error=None
try:env["update_pair"]([file_pin(p) for p in paths],lambda a,b:(a,b),journal_dir,"activate")
except RuntimeError as exc:error=str(exc)
results.append({"case":"CLOSE_HANDLE_FAILURE_PROPAGATES","matches_expected":error is not None and "close failure" in error,"error":error,"held_handle_count":len(locks)})
report={"schema":"researchos.independent-v3-canonical-controls.v1","cases":results,"WinAPI_calls":0,"real_canonical_access":False,"actual_candidate_entry_invoked":False,"selected_functions_exercised":["update_pair","close_canonical_lease","activate_canonical_lease"],"all_files_and_journals":"in-memory only; real file paths used merely as map keys","new_tool_failures":0}
(O/"canonical-controls.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"cases":len(results),"mismatches":[r["case"] for r in results if not r["matches_expected"]],"WinAPI_calls":0,"real_writes":0},ensure_ascii=False))

