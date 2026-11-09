"""Narrow non-author review of repaired path preflight; no real OS API calls."""
from pathlib import Path
import ast, builtins, ctypes, difflib, hashlib, hmac, json, ntpath, re, types, __future__
from ctypes import wintypes
O=Path(__file__).resolve().parent
P=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99")
S=P/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9"
OLD=P/"source_read_guard_codex/68ac03921c9c4efd821c178dd934e16e"
PRIOR=P/"source_read_guard_independent_review_codex/f3211e5e62ff4af392f358ac79093492"
def meta(p,raw=None):
 if raw is None:raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def put(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
mf=meta(S/"manifest.json");assert (mf["sha256"],mf["bytes"])==("323244fa61d59d2b6ff04d67705dcc621bb7c317cfe057752761966f704cd07f",2422)
manifest=json.loads((S/"manifest.json").read_bytes())
refs=manifest["source_files"]+[mf,manifest["derived_from_v1_manifest"]]
prior_m=meta(PRIOR/"manifest.json");assert prior_m["sha256"]=="af86bc6d863629e7aff773d33d5b57db5da05187ba88f366f5e86ade882dfc05"
prior_doc=json.loads((PRIOR/"manifest.json").read_bytes())
for item in prior_doc["files"]:
 actual=meta(Path(item["path"]));assert actual["sha256"]==item["sha256"] and actual["bytes"]==item["bytes"]
refs += [prior_m]+[item for item in prior_doc["files"] if Path(item["path"]).name in ["controls.json","REVIEW.md","HANDOFF.md"]]
refs += [dict(path=str(OLD/"source_read_guard.py"),sha256="e61a1b078a40b7d8bda1116944c42e0ddd37644ad5689917a164b6c5d67d9c96",bytes=10646)]
intake=[]
for ref in refs:
 p=Path(ref["path"]);raw=p.read_bytes();x=meta(p,raw)
 assert x["sha256"]==ref["sha256"] and x["bytes"]==ref["bytes"],p
 dest=O/"snapshots"/p.relative_to(P);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);x["snapshot"]=str(dest.relative_to(O));intake.append(x)
oldraw=(OLD/"source_read_guard.py").read_bytes();newraw=(S/"source_read_guard.py").read_bytes()
oldtree,newtree=ast.parse(oldraw),ast.parse(newraw)
def keep(node):
 if isinstance(node,ast.FunctionDef) and node.name=="_canonical":return False
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {"_LOCAL_DRIVE","_DOS_DEVICE"} for t in node.targets):return False
 return True
assert ast.dump(ast.Module(body=[n for n in oldtree.body if keep(n)],type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=[n for n in newtree.body if keep(n)],type_ignores=[]),include_attributes=False)
for name in ["_Win32API","SourceReadGuard"]:
 oldnode=next(n for n in oldtree.body if isinstance(n,ast.ClassDef) and n.name==name);newnode=next(n for n in newtree.body if isinstance(n,ast.ClassDef) and n.name==name)
 assert ast.get_source_segment(oldraw.decode(),oldnode)==ast.get_source_segment(newraw.decode(),newnode)
(O/"reviewer.v1-to-v2.diff").write_text("".join(difflib.unified_diff(oldraw.decode().splitlines(True),newraw.decode().splitlines(True),fromfile="v1/source_read_guard.py",tofile="v2/source_read_guard.py")),encoding="utf-8",newline="")
# Full module loaded only with allowlisted imports and a ctypes proxy.
def denied(*a,**k):raise AssertionError("real OS API forbidden")
proxy=types.SimpleNamespace(**{n:getattr(ctypes,n) for n in ["c_void_p","c_longlong","POINTER","byref","create_unicode_buffer","create_string_buffer"]})
proxy.wintypes=wintypes;proxy.WinDLL=denied;proxy.get_last_error=lambda:123
mods={"ctypes":proxy,"hashlib":hashlib,"hmac":hmac,"ntpath":ntpath,"re":re,"__future__":__future__}
def importer(name,*a,**k):
 if name not in mods:raise AssertionError("unexpected import")
 return mods[name]
safe=dict(vars(builtins));safe["__import__"]=importer
for name in ["open","eval","exec","compile","input"]:safe.pop(name,None)
ns={"__name__":"independent_guard_v2_memory","__builtins__":safe}
exec(compile(newtree,"reviewed_guard_v2.py","exec"),ns);Guard=ns["SourceReadGuard"]
data=b"guard-v2-memory-only"
def pin(path):return dict(path=path,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
negative_paths=[
 "//server/share/a.py","//?/C:/guard/one.py","//./C:/guard/one.py",
 "\\\\server\\share\\a.py","\\\\?\\C:\\guard\\one.py","\\\\.\\C:\\guard\\one.py",
 "C:relative.py","/root/one.py","1:/one.py","CC:/one.py",
 "C:/guard/a.py:stream","C:/guard/../one.py","C:/guard/./one.py","C:/guard//one.py",
 "C://guard/one.py","C:/guard/one.py.","C:/guard/one.py ",
 "C:/guard/CON","C:/guard/COM1.txt","C:/guard/LPT¹.log",
 "C:/guard/a"+chr(0)+".py","C:/guard/a"+chr(10)+".py","C:/",
]
results=[]
for path in negative_paths:
 invoked=[]
 def factory():invoked.append(True);raise AssertionError("factory reached for rejected path")
 guard=Guard(api_factory=factory)
 try:guard.acquire([pin(path)])
 except ValueError:pass
 else:raise AssertionError("path accepted:"+repr(path))
 ob=guard.close();assert not invoked and ob["failure"]["stage"]=="preflight" and ob["closed"] and ob["retained_handles_count"]==0
 results.append(dict(path=path,status="REJECTED_BEFORE_API",factory_calls=0,open_calls=0,observation=ob))
class FakeAPI:
 def __init__(self,final_override=None):self.events=[];self.paths={};self.final_override=final_override
 def open_read_shared_read(self,path):
  handle=len(self.paths)+1;self.paths[handle]=path;self.events.append(["open",path]);return handle
 def final_path(self,handle):return self.final_override or "\\\\?\\"+ntpath.normpath(self.paths[handle])
 def size(self,handle):return len(data)
 def read_exact(self,handle,size):self.events.append(["read",handle]);return data
 def close(self,handle):self.events.append(["close",handle]);self.paths.pop(handle)
positive_paths=["C:/guard/one.py","C:\\guard\\one.py","c:/GUARD/one.py","D:/作品集/Guard 空间/源文件.py","D:\\作品集\\Guard 空间\\源文件.py"]
positive=[]
for path in positive_paths:
 api=FakeAPI();g=Guard(api_factory=lambda:api);g.acquire([pin(path)])
 assert g.get_buffer(path) is data;ob=g.close();assert ob["closed"] and ob["verification"]=="PASSED"
 positive.append(dict(path=path,status="VERIFIED_WITH_MEMORY_API",opens=len([e for e in api.events if e[0]=="open"])))
api=FakeAPI();g=Guard(per_file_cap=len(data),total_cap=len(data),api_factory=lambda:api)
g.acquire([pin("C:/guard/one.py"),pin("c:\\GUARD\\one.py")])
assert len([e for e in api.events if e[0]=="open"])==1;assert g.close()["closed"]
boundary=[]
for actual in ["C:/unapproved/one.py","\\\\?\\UNC\\server\\share\\one.py"]:
 api=FakeAPI(final_override=actual);g=Guard(api_factory=lambda:api)
 try:g.acquire([pin("C:/guard/one.py")])
 except ValueError:pass
 else:raise AssertionError("final path mismatch accepted")
 ob=g.close();assert ob["closed"] and ob["failure"]["stage"]=="GetFinalPathNameByHandleW" and not any(e[0]=="read" for e in api.events)
 boundary.append(dict(final_path=actual,status="REJECTED_BEFORE_READ_AND_CLOSED"))
prior_controls=json.loads((PRIOR/"controls.json").read_bytes())
assert len(prior_controls["checks"])==28
put("intake.json",dict(status="PASS_EXACT_PINS",files=intake,prior_manifest_full_members_rechecked=len(prior_doc["files"])))
put("controls.json",dict(schema="researchos.source-read-guard-v2-independent-controls.v1",decision="PASS_SOURCE_ONLY",R1="CLOSED_IN_SOURCE_AND_MEMORY_SUBSTITUTE",negative_preflight=results,positive_local_paths=positive,duplicate_same_pin_one_open=True,final_handle_boundary=boundary,unchanged_AST_except=["_canonical","_LOCAL_DRIVE","_DOS_DEVICE"],unchanged_adapter_and_lifecycle_class_text=True,reused_prior_controls=28,real_winapi_calls=0,provider_requests=0,candidate_target_file_reads=0,scope="New path controls only; prior28 outcomes reused under exact lifecycle/adapter class identity. No candidate real OS adapter initialization or native execution."))
print(json.dumps(dict(decision="PASS_SOURCE_ONLY",negative_preflight=len(results),positive_local_paths=len(positive),duplicate_control=1,final_handle_boundary=len(boundary),prior_controls_reused=28,real_winapi_calls=0,provider_requests=0)))

