import sys
sys.dont_write_bytecode=True
import json,hashlib,types,uuid
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
A=B/"integration_codex/native-harness43-compile-unit-root-c16a0730cf914bc5"
def pin(path):
 path=Path(path).resolve();raw=path.read_bytes()
 return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 with (O/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return pin(O/name)
def module(path):
 path=Path(path).resolve();m=types.ModuleType("root_test2json_"+path.stem);m.__file__=str(path);sys.modules[m.__name__]=m
 exec(compile(path.read_bytes(),str(path),"exec"),m.__dict__);return m
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
go=R/".local/tools/go1.27.1/go/bin/go.exe";GOROOT=go.parent.parent
assert pin(go)["sha256"]=="d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
assert pin(sys.executable)["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
assert (GOROOT/"VERSION").read_text(encoding="utf-8").splitlines()[0]=="go1.27.1"
parent=json.loads((A/"actual-tagged-compiler-input-inventory.json").read_bytes())
assert pin(go)==parent["GoRef"]
gm=module(gp);helper=module(hp)
base=[pin(p) for p in (gp,hp,go,GOROOT/"VERSION",GOROOT/"src/go.mod",Path(__file__),Path(sys.executable),R/"go.mod",R/"go.sum",A/"actual-tagged-compiler-input-inventory.json")]
base+=parent["compiler_tool_refs"]
base+=[pin(p) for p in helper.runtime_resource_paths()]
base+=[pin(m.__file__) for m in list(sys.modules.values()) if getattr(m,"__file__",None) and Path(m.__file__).is_file()]
base=list({str(Path(p["path"]).resolve()).casefold():p for p in base}.values())
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(base)
selected_guard=None;binary_guard=None
before=[pin(R/"execution/v2.4"/(n+".json")) for n in ("checkpoint","path_ownership","step_state","commands")]
scratch=R/".local"/("official-test2json-resource-"+uuid.uuid4().hex)
for n in ("temp","profile","programs"):(scratch/n).mkdir(parents=True,exist_ok=False)
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe",
"PATH":str(go.parent)+";C:/Windows/System32","PATHEXT":".COM;.EXE;.BAT;.CMD",
"GOROOT":str(GOROOT),"GOPATH":str(R/".local/gopath"),"GOCACHE":str(R/".local/gocache"),
"GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GOWORK":"off","GOENV":"off",
"CGO_ENABLED":"0","GOFLAGS":"-mod=readonly -p=1","GOMAXPROCS":"2"}
for k in ("TEMP","TMP"):env[k]=str(scratch/"temp")
for k in ("USERPROFILE","LOCALAPPDATA","APPDATA"):env[k]=str(scratch/"profile")
invocations=[]
def invoke(label,argv,timeout):
 out=O/(label+".stdout.raw");err=O/(label+".stderr.raw")
 with out.open("xb") as stdout,err.open("xb") as stderr:
  result=helper.run_owned(argv,str(R),env,stdout,stderr,timeout,creation_flags=0x08000000)
 receipt=save(label+".invocation.json",dict(argv=argv,cwd=str(R),public_environment=env,result=result,actual_native_exit=result["actual_exit"],stdout_ref=pin(out),stderr_ref=pin(err)))
 invocations.append(receipt)
 j=result["job_cleanup"]
 assert not j["errors"] and j["active_processes_last_observed"]==0 and all(j[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 assert result["actual_exit"]==0 and result["error"] is None and not result["timed_out"]
 print(json.dumps({"stage":label,"actual_native_exit":result["actual_exit"]}),flush=True)
try:
 invoke("official-stdlib-tool-selected-inputs",[str(go),"list","-deps","-compiled","-json","cmd/test2json"],240)
 raw=(O/"official-stdlib-tool-selected-inputs.stdout.raw").read_text(encoding="utf-8")
 decoder=json.JSONDecoder();position=0;packages=[];inputs={};embeds=[]
 fields=("GoFiles","CgoFiles","CFiles","CXXFiles","MFiles","HFiles","FFiles","SFiles","SwigFiles","SwigCXXFiles","SysoFiles","CompiledGoFiles","EmbedFiles")
 while position<len(raw):
  while position<len(raw) and raw[position].isspace():position+=1
  if position==len(raw):break
  pkg,position=decoder.raw_decode(raw,position);assert not pkg.get("Error") and not pkg.get("DepsErrors")
  packages.append(pkg["ImportPath"])
  if not pkg.get("Dir"):continue
  directory=Path(pkg["Dir"])
  for field in fields:
   for name in pkg.get(field,[]):
    path=Path(name);path=path if path.is_absolute() else directory/path
    ref=pin(path);inputs[ref["path"].casefold()]=ref
    if field=="EmbedFiles":embeds.append(ref)
 assert "cmd/test2json" in packages and "cmd/internal/test2json" in packages
 inventory=save("selected-official-compiler-inputs.json",dict(package_count=len(packages),packages=packages,selected_file_fields=fields,selected_input_count=len(inputs),build_inputs=list(inputs.values()),actual_embed_refs=embeds,GoRef=pin(go),compiler_tool_refs=parent["compiler_tool_refs"],GOROOT_version_ref=pin(GOROOT/"VERSION"),GOROOT_module_ref=pin(GOROOT/"src/go.mod"),upstream_source="Bundled pinned Go1.27.1 standard cmd/test2json; no custom reporter implementation."))
 selected_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);selected_guard.acquire(list(inputs.values())+[inventory])
 executable=scratch/"programs/test2json.exe"
 invoke("official-test2json-build",[str(go),"build","-trimpath","-buildvcs=false","-o",str(executable),"cmd/test2json"],300)
 binary=pin(executable)
 binary_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);binary_guard.acquire([binary])
 assert pin(executable)==binary
 assert before==[pin(p["path"]) for p in before]
 receipt=save("resource-build.closed.json",dict(status="OFFICIAL_TEST2JSON_COMPILED_TWO_OWNED_JOBS_CLOSED_NOT_EXECUTED",binary_ref=binary,compiler_inventory_ref=inventory,invocation_refs=invocations,base_input_refs=base,canonical_unchanged_refs=before,all_two_owned_jobs_closed=True,tool_executions=0,provider_requests=0,private_key_reads=0,original_trial_DB_writes=0,formal_acceptance=False))
 print(json.dumps({"closed_ref":receipt,"binary_ref":binary}),flush=True)
finally:
 for name,g in (("binary",binary_guard),("selected",selected_guard),("base",guard)):
  if g is not None:
   cleanup=g.close();save(name+"-source-guard.cleanup.actual.json",cleanup)
   assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
