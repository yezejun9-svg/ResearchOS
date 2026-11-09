"""Independent AST and memory-only review. All candidate OS entrypoints are replaced."""
from pathlib import Path
import ast, builtins, ctypes, hashlib, hmac, json, ntpath, re, types, __future__
from ctypes import wintypes
O=Path(__file__).resolve().parent
S=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/source_read_guard_codex/68ac03921c9c4efd821c178dd934e16e")
def meta(p,raw):
 return {"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def put(n,obj):(O/n).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
mfraw=(S/"manifest.json").read_bytes()
assert hashlib.sha256(mfraw).hexdigest()=="099113490f7f894f0bcdc23e3d92ce31de1e4d4cac4883ec0dbc31d24f8f0a7c" and len(mfraw)==1899
manifest=json.loads(mfraw);refs=[]
for ref in manifest["source_files"]+[meta(S/"manifest.json",mfraw)]:
 p=Path(ref["path"]);raw=p.read_bytes();x=meta(p,raw)
 assert (x["sha256"],x["bytes"])==(ref["sha256"],ref["bytes"])
 dest=O/"snapshots"/p.name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw);x["snapshot"]=dest.relative_to(O).as_posix();refs.append(x)
raw=(S/"source_read_guard.py").read_bytes();tree=ast.parse(raw,filename="reviewed_source_read_guard.py")
allowed={"__future__","ctypes","hashlib","hmac","ntpath","re"}
assert all((node.module if isinstance(node,ast.ImportFrom) else alias.name) in allowed for node in ast.walk(tree) if isinstance(node,(ast.Import,ast.ImportFrom)) for alias in (node.names if isinstance(node,ast.Import) else [None]))
assert not any(isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in {"open","exec","eval","compile","__import__"} for node in ast.walk(tree))
calls={"real_winapi":0,"candidate_target_reads":0,"fake_windll_loads":0}
def denied_dll(*a,**kw):raise AssertionError("real DLL loading forbidden")
proxy=types.SimpleNamespace(**{n:getattr(ctypes,n) for n in ["c_void_p","c_longlong","POINTER","byref","create_unicode_buffer","create_string_buffer"]})
proxy.wintypes=wintypes;proxy.WinDLL=denied_dll;proxy.get_last_error=lambda:123
modules={"ctypes":proxy,"hashlib":hashlib,"hmac":hmac,"ntpath":ntpath,"re":re,"__future__":__future__}
def restricted_import(name,*a,**kw):
 if name not in modules:raise AssertionError("unexpected import:"+name)
 return modules[name]
safe=dict(vars(builtins));safe["__import__"]=restricted_import
for n in ["open","eval","exec","compile","input"]:safe.pop(n,None)
ns={"__name__":"independent_memory_guard","__builtins__":safe}
exec(compile(tree,"reviewed_source_read_guard.py","exec"),ns)
Guard=ns["SourceReadGuard"];checks=[];findings=[]
def ok(name,detail=None):checks.append({"name":name,"status":"PASS","detail":detail})
def pin(path,data):return {"path":path,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)}
A="C:/guard/one.py";B="C:/guard/two.py";x=b"alpha";y=b"bravo"
class FakeAPI:
 def __init__(self,rows=None):
  self.rows={ntpath.normcase(ntpath.normpath(p)):v for p,v in (rows or {A:x,B:y}).items()}
  self.events=[];self.handles={};self.seq=100;self.closed=[];self.size_count={}
  self.fail_open_at=0;self.open_count=0;self.final_override={};self.size_override={};self.read_override={};self.fail_read=set();self.close_fail={}
 def open_read_shared_read(self,path):
  self.open_count+=1;self.events.append(["open",path])
  if self.open_count==self.fail_open_at:raise OSError(5,"injected open")
  self.seq+=1;self.handles[self.seq]=ntpath.normcase(ntpath.normpath(path));return self.seq
 def final_path(self,h):
  key=self.handles[h];self.events.append(["final",h]);return self.final_override.get(key,key)
 def size(self,h):
  key=self.handles[h];n=self.size_count.get(h,0);self.size_count[h]=n+1;self.events.append(["size",h])
  value=self.size_override.get(key,len(self.rows[key]))
  return value[n] if isinstance(value,list) else value
 def read_exact(self,h,size):
  key=self.handles[h];self.events.append(["read",h,size])
  if key in self.fail_read:raise OSError(30,"injected read")
  return self.read_override.get(key,self.rows[key])
 def close(self,h):
  self.events.append(["close",h]);n=self.close_fail.get(h,0)
  if n:
   self.close_fail[h]=n-1;raise OSError(6,"injected close")
  self.closed.append(h);self.handles.pop(h,None)
def make(api,**kw):
 count=[]
 def factory():count.append(True);return api
 return Guard(api_factory=factory,**kw),count
f=FakeAPI();g,factory_calls=make(f)
assert not factory_calls and f.events==[];ok("constructor_no_API_effects")
refs1=[pin(A,x),pin(B,y),pin("c:\\guard\\ONE.py",x)]
buffers=g.acquire(refs1)
assert len(buffers)==2 and g.get_buffer(A) is x and g.get_buffer(B) is y
assert f.open_count==2 and len([e for e in f.events if e[0]=="read"])==2
ok("one_held_handle_and_one_verified_buffer_per_normalized_pin")
try:g.acquire(refs1)
except RuntimeError:pass
else:raise AssertionError("one-shot")
obs=g.close();assert obs["closed"] and obs["retained_handles_count"]==0 and not obs["errors"] and not g.buffers
assert all(e["closed"] for e in obs["entries"]);json.dumps(obs)
ok("one_shot_close_and_JSON_safe_observation")
preflight=[
 ("empty",[]),("extra_key",[dict(pin(A,x),extra=True)]),
 ("digest_prefix",[dict(pin(A,x),sha256="sha256:"+hashlib.sha256(x).hexdigest())]),
 ("negative_size",[dict(pin(A,x),bytes=-1)]),("bool_size",[dict(pin(A,x),bytes=True)]),
 ("drive_relative",[pin("C:one.py",x)]),("no_drive",[pin("/one.py",x)]),
 ("backslash_UNC",[pin("\\\\server\\share\\one.py",x)]),
 ("backslash_device",[pin("\\\\?\\C:\\guard\\one.py",x)]),
 ("conflicting_duplicate",[pin(A,x),pin(A,y)]),
 ("per_file_cap",[pin(A,b"123456789")]),
 ("total_cap",[pin(A,x),pin(B,y),pin("C:/guard/three.py",b"extra")]),
]
for name,reference in preflight:
 api=FakeAPI();guard,fc=make(api,per_file_cap=8,total_cap=10)
 try:guard.acquire(reference)
 except (ValueError,TypeError):pass
 else:raise AssertionError("preflight accepted "+name)
 ob=guard.close();assert not fc and not api.events and ob["closed"] and ob["failure"]["stage"]=="preflight"
 ok("preflight_"+name)
for caps in [(True,10),(8,False),(0,10),(8,7),(1.0,10)]:
 try:Guard(per_file_cap=caps[0],total_cap=caps[1])
 except ValueError:pass
 else:raise AssertionError("caps")
ok("constructor_caps")
api=FakeAPI({A:b"",B:y});guard,_=make(api);guard.acquire([pin(A,b""),pin(B,y)]);ob=guard.close();assert ob["verification"]=="PASSED";ok("zero_byte_exact_file")
for fault,expected_stage in [("hash","SHA256"),("open","CreateFileW"),("final","GetFinalPathNameByHandleW"),("size","GetFileSizeEx"),("read","ReadFile"),("growth","ReadFile"),("short","ReadFile")]:
 api=FakeAPI();key=ntpath.normcase(ntpath.normpath(B))
 if fault=="hash":api.read_override[key]=b"other"
 if fault=="open":api.fail_open_at=2
 if fault=="final":api.final_override[key]="C:/unapproved/other.py"
 if fault=="size":api.size_override[key]=6
 if fault=="read":api.fail_read.add(key)
 if fault=="growth":api.size_override[key]=[5,6]
 if fault=="short":api.read_override[key]=b"four"
 guard,_=make(api)
 try:guard.acquire([pin(A,x),pin(B,y)])
 except (ValueError,OSError):pass
 else:raise AssertionError(fault)
 ob=guard.close();assert not api.handles and not guard.buffers and ob["closed"] and ob["verification"]=="FAILED" and ob["failure"]["stage"]==expected_stage
 assert len(api.closed)==(1 if fault=="open" else 2)
 ok("partial_failure_"+fault,{"closed_handles":len(api.closed),"stage":expected_stage})
api=FakeAPI();guard,_=make(api);guard.acquire([pin(A,x),pin(B,y)]);api.close_fail[101]=1
first=guard.close();assert not first["closed"] and first["retained_handles_count"]==1 and len(first["errors"])==1 and 101 in api.handles and 102 not in api.handles
second=guard.close();assert second["closed"] and second["retained_handles_count"]==0 and len(second["errors"])==1 and all(e["closed"] for e in second["entries"])
assert second["verification"]=="PASSED";ok("close_retry_retains_historical_error_but_true_current_all_closed",{"first":first,"second":second})
api=FakeAPI();api.close_fail[101]=2;guard,_=make(api);guard.acquire([pin(A,x)])
ob1=guard.close();ob2=guard.close();assert not ob1["closed"] and not ob2["closed"] and ob2["retained_handles_count"]==1 and len(ob2["errors"])==2
ob3=guard.close();assert ob3["closed"] and len(ob3["errors"])==2;ok("repeated_close_failure_retains_exact_handle")
api=FakeAPI();api.read_override[ntpath.normcase(ntpath.normpath(B))]=b"other";api.close_fail[101]=1;guard,_=make(api)
try:guard.acquire([pin(A,x),pin(B,y)])
except ValueError:pass
else:raise AssertionError("partial expected")
assert guard._entries[0]["handle"]==101 and not guard._entries[0]["closed"]
ob=guard.close();assert ob["closed"] and ob["verification"]=="FAILED" and ob["failure"]["stage"]=="SHA256" and len(ob["errors"])==1
ok("partial_acquire_failure_preserves_original_failure_and_retries_close")
# Reproduce preflight defects with a fake API only. No network or device is opened.
for path in ["//server/share/a.py","//?/C:/guard/one.py","//./C:/guard/one.py"]:
 api=FakeAPI({path:x});guard,fc=make(api)
 try:guard.acquire([pin(path,x)])
 except (ValueError,OSError) as exc:outcome=type(exc).__name__
 else:outcome="accepted"
 ob=guard.close()
 assert fc and api.open_count==1
 findings.append({"id":"R1","input_path":path,"observed":"preflight accepted and fake API open called","factory_calls":len(fc),"open_count":api.open_count,"outcome":outcome,"closed":ob["closed"],"native_calls":0})
# Run the concrete ctypes adapter against Python callables, never a DLL.
class Fn:
 def __init__(self,callback):self.callback=callback
 def __call__(self,*args):return self.callback(*args)
class Kernel:
 def __init__(self):
  self.create_args=[];self.pos=0;self.payload=b"abc";self.close_args=[]
  self.CreateFileW=Fn(self.create);self.GetFinalPathNameByHandleW=Fn(self.final);self.GetFileSizeEx=Fn(self.size);self.ReadFile=Fn(self.read);self.CloseHandle=Fn(self.close)
 def create(self,*args):self.create_args.append(args);return 7
 def final(self,h,buf,cap,flags):
  value="\\\\?\\C:\\guard\\one.py";buf.value=value;return len(value)
 def size(self,h,out):ctypes.cast(out,ctypes.POINTER(ctypes.c_longlong)).contents.value=len(self.payload);return 1
 def read(self,h,buf,amount,out,over):
  chunk=self.payload[self.pos:self.pos+amount];self.pos+=len(chunk);ctypes.memmove(buf,chunk,len(chunk));ctypes.cast(out,ctypes.POINTER(wintypes.DWORD)).contents.value=len(chunk);return 1
 def close(self,h):self.close_args.append(h);return 1
kernel=Kernel()
def fake_dll(*args,**kw):calls["fake_windll_loads"]+=1;return kernel
proxy.WinDLL=fake_dll
native=ns["_Win32API"]();h=native.open_read_shared_read(A)
assert kernel.create_args[0]==(A,0x80000000,1,None,3,0x80,None)
assert ns["_final_path"](native.final_path(h))=="C:\\guard\\one.py"
assert native.size(h)==3 and native.read_exact(h,3)==b"abc";native.close(h);assert kernel.close_args==[7]
ok("concrete_adapter_exact_share_read_only_flags_via_memory_functions")
assert calls["real_winapi"]==calls["candidate_target_reads"]==0
put("intake.json",{"status":"PASS_EXACT_PINS","files":refs})
put("controls.json",{"decision":"REQUEST_CHANGES","checks":checks,"reproduced_findings":findings,"counts":calls,"provider_requests":0,"native_jobs":0,"main_or_canonical_writes":0,"scope":"Candidate AST loaded with allowlisted imports and ctypes proxy; acquire calls only memory substitutes. Fake DLL adapter exercises ctypes argument wiring using Python functions, not Windows."})
print(json.dumps({"decision":"REQUEST_CHANGES","passed_controls":len(checks),"reproduced_preflight_inputs":len(findings),"real_winapi_calls":0,"target_reads":0,"provider_requests":0}))

