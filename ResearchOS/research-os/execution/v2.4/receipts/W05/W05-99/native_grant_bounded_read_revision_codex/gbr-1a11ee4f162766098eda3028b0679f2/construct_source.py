import ast,difflib,hashlib,json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).parent
B=N.parents[1]
O=B/"native_grant_public_pin_archive_source_codex/gpa-1a11ee4f162766098eda3028b0679f2"
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":"sha256:"+hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def emit(name,v):
 with (N/name).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
inputs=[pin(O/x) for x in ("native_grant_public_pin_archive.py","HDF.json","MF.json","calling-contract.md")]
assert inputs[0]["sha256"]=="sha256:baad4ec59c1ed4451ad8d054f6800f7f8c3e8a4836d004adf367f0d667782ef4" and inputs[0]["bytes"]==23856
old=(O/"native_grant_public_pin_archive.py").read_bytes()
a='    raw = Path(value["path"]).read_bytes()\n    require(len(raw) == value["bytes"] and digest(raw) == value["sha256"], "input pin mismatch")'
b='    with Path(value["path"]).open("rb") as stream:\n        raw = stream.read(value["bytes"] + 1)\n    require(len(raw) == value["bytes"], "input pin mismatch")\n    require(digest(raw) == value["sha256"], "input pin mismatch")'
s=old.decode();assert s.count(a)==1;s=s.replace(a,b)
assert s.count(b)==1 and s.replace(b,a).encode()==old
prior=ast.parse(old);new=ast.parse(s)
pa=[ast.dump(x,include_attributes=False) for x in prior.body if not isinstance(x,ast.FunctionDef) or x.name!="read_ref"]
na=[ast.dump(x,include_attributes=False) for x in new.body if not isinstance(x,ast.FunctionDef) or x.name!="read_ref"]
assert pa==na
(N/"native_grant_public_pin_archive.py").write_text(s,encoding="utf-8",newline="\n")
(N/"bounded-read.patch").write_text("".join(difflib.unified_diff(old.decode().splitlines(True),s.splitlines(True),fromfile="GPA/read_ref",tofile="GPA-R01/read_ref")),encoding="utf-8",newline="\n")
emit("exact-inverse.json",{"old_helper_ref":inputs[0],"new_helper_ref":pin(N/"native_grant_public_pin_archive.py"),
 "old":a,"new":b,"whole_file_byte_inverse":True,"all_other_AST_nodes_identical":True})
assert [pin(Path(x["path"])) for x in inputs]==inputs
emit("guard.final.json",{"before":inputs,"after":inputs,"all_unchanged":True,"source_only":True,"actual_win32_guard":False})
print("GPA_BOUNDED_SOURCE_OK "+json.dumps(pin(N/"native_grant_public_pin_archive.py"),ensure_ascii=True))

