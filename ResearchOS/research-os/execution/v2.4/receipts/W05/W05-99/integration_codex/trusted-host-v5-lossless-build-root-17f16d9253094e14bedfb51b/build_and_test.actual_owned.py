import sys
sys.dont_write_bytecode=True
import hashlib,json,types,uuid
from pathlib import Path
ROOT=Path("D:/作品集/ResearchOS/research-os");B=ROOT/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
SD=B/"mu_sdk_trusted_qualification_host_source_v5_codex/17e94063a8244fdfa69aefdbdf895cf6";SRC=SD/"staged-root-3896725ace2b4b2783334c313d548c4f";OLD=B/"mu_sdk_trusted_qualification_host_source_v4_codex/staged-root-69e7c3008fd968419f4d4072c3c8";DEST=O/"formatted-go-source"
names=("main.go","hostapi.go","prepare.go","execute.go","prepare_runtime.go","seed.template.json","profile.template.json","go.authority.template.json")
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 p=O/name
 with p.open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def module(path,raw):
 m=types.ModuleType("root_go_lossless_"+path.stem);m.__file__=str(path);exec(compile(raw,str(path),"exec"),m.__dict__);return m
mf=json.loads((SD/"MF.json").read_bytes());assert mf["changed_members"]==["execute.go"] and mf["sourceStatus"]=="EXECUTION_REPORTED" and not mf["permission_to_execute"]
for n,ref in mf["members"].items():
 assert pin(SRC/n)==dict(path=str(SRC/n),sha256=ref["sha256"],bytes=ref["bytes"])
 assert ref["same_as_v4"]==(n!="execute.go")
 if n!="execute.go":assert (SRC/n).read_bytes()==(OLD/n).read_bytes()
assert pin(SRC/"execute.go")["sha256"]=="b98763c60ef21ccf7931bda558bc044350a19fd409cad3ae113439e4b74fa68b"
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
go=ROOT/".local/tools/go1.27.1/go/bin/go.exe";fmt=go.with_name("gofmt.exe");test=O/"go-source/reader_contract_test.go"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad" and pin(go)["sha256"]=="d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
frozen=[pin(SRC/n) for n in names]+[pin(OLD/n) for n in names]+[pin(SD/n) for n in ("HDF.json","MF.json","source-diff.patch","static-test-evidence.json")]+[pin(gp),pin(hp),pin(go),pin(fmt),pin(test),pin(Path(__file__).resolve()),pin(ROOT/"execution/toolchains/locked.json")]
mainnames=("internal/host/vault.go","internal/host/host.go","apps/control/main.go","internal/domain/runtime_qualification.go","apps/cli/cli_stream.go","internal/domain/contracts.go","internal/canonical/jcs.go")
frozen += [pin(ROOT/n) for n in mainnames]
evidence_dir=B/"integration_codex/root-model-trial-v5-870ecc93e109c85ee985e1566ff/trial-output"
frozen += [pin(evidence_dir/n) for n in ("host-job.contract.json","host-job.probe.json")]
canonical=[ROOT/"execution/v2.4"/(x+".json") for x in ("checkpoint","path_ownership","step_state","commands")];canonbefore={p:p.read_bytes() for p in canonical}
assert json.loads(canonbefore[canonical[0]])["revision"]==349
gm=module(gp,gp.read_bytes());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(frozen)
helper=module(hp,guard.get_buffer(str(hp)));formatted_guard=None
temp=ROOT/".local"/("trusted-host-v5-lossless-build-"+uuid.uuid4().hex);temp.mkdir();(temp/"profile").mkdir();(temp/"temp").mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(go.parent)+";C:/Windows/System32;C:/Program Files/Git/cmd","PATHEXT":".COM;.EXE;.BAT;.CMD","USERPROFILE":str(temp/"profile"),"LOCALAPPDATA":str(temp/"profile"),"APPDATA":str(temp/"profile"),"TEMP":str(temp/"temp"),"TMP":str(temp/"temp"),"GOROOT":str(go.parent.parent),"GOPATH":str(ROOT/".local/gopath"),"GOCACHE":str(ROOT/".local/gocache"),"GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GOWORK":"off","CGO_ENABLED":"0","GOFLAGS":"-mod=readonly -p=1","GOMAXPROCS":"2"}
invocations=[]
def invoke(label,argv,timeout):
 out=O/(label+".stdout.raw");err=O/(label+".stderr.raw");result=None;exception=None
 save(label+".intent.json",dict(argv=argv,cwd=str(ROOT),public_environment=env,wall_seconds=timeout,target_host_executions=0,provider_requests=0))
 try:
  with out.open("xb") as stdout,err.open("xb") as stderr:result=helper.run_owned(argv,str(ROOT),env,stdout,stderr,timeout,creation_flags=0x08000000)
 except BaseException as e:exception=repr(e)
 finally:
  receipt=save(label+".invocation.json",dict(argv=argv,cwd=str(ROOT),result=result,exception=exception,actual_native_exit=result.get("actual_exit") if result else None,stdout_ref=pin(out),stderr_ref=pin(err),target_host_executions=0,provider_requests=0));invocations.append(receipt)
 assert exception is None and result is not None and result["actual_exit"]==0 and result["error"] is None and not result["timed_out"],label+" native failed"
 cleanup=result["job_cleanup"];assert not cleanup["errors"] and cleanup["active_processes_last_observed"]==0 and all(cleanup[k] is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 return receipt
try:
 DEST.mkdir(exist_ok=False)
 for n in names:
  with (DEST/n).open("xb") as f:f.write(guard.get_buffer(str(SRC/n)))
 with (DEST/test.name).open("xb") as f:f.write(guard.get_buffer(str(test)))
 gofiles=[str(DEST/n) for n in names if n.endswith(".go")]
 invoke("format",[str(fmt),"-w",*gofiles,str(DEST/test.name)],30)
 formatted_refs=[pin(DEST/n) for n in names]+[pin(DEST/test.name)];source_manifest=save("formatted.source-members.json",formatted_refs)
 formatted_guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);formatted_guard.acquire(formatted_refs+[source_manifest])
 invoke("reader-test",[str(go),"test","-count=1","-json",*gofiles,str(DEST/test.name)],180)
 events=[json.loads(line) for line in (O/"reader-test.stdout.raw").read_text(encoding="utf-8").splitlines() if line]
 tests={e["Test"]:e["Action"] for e in events if "Test" in e and e["Action"] in ("pass","fail","skip")}
 assert tests and all(a=="pass" for a in tests.values()) and len(tests)==27,(len(tests),tests)
 binary=temp/"trusted-qualification-host.exe"
 invoke("compile",[str(go),"build","-trimpath","-o",str(binary),*gofiles],180)
 assert all(p.read_bytes()==body for p,body in canonbefore.items()) and all(pin(ref["path"])==ref for ref in frozen+formatted_refs)
 closed=save("reader-validation.closed.json",dict(status="ACTUAL_GO_READER_TESTS_AND_COMPILE_PASSED_SOURCE_ONLY",source_namespace=str(SRC),formatted_namespace=str(DEST),source_members_ref=source_manifest,binary_ref=pin(binary),invocation_refs=invocations,go_test_pass_names=sorted(tests),go_test_pass_count=len(tests),actual_failed_trial_evidence_inputs=2,invalid_numeric_structure_cases=18,positive_decimal_cases=3,pin_corruption_cases=2,all_owned_jobs_closed=True,canonical_unchanged=True,old_source_unchanged=True,target_host_executions=0,provider_requests=0,formal_acceptance=False,runtime_qualification=False))
 print(json.dumps(dict(closed_ref=closed,binary_ref=pin(binary),owned_native_jobs=3,go_tests=len(tests),target_host_executions=0,provider_requests=0)),flush=True)
finally:
 if formatted_guard is not None:save("formatted-source-guard.cleanup.actual.json",formatted_guard.close())
 save("input-source-guard.cleanup.actual.json",guard.close())

