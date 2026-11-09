import sys
sys.dont_write_bytecode=True
import hashlib,json,types,re,os,subprocess,platform,signal,time,uuid
from datetime import datetime,timezone
from pathlib import Path
R=Path('D:\\作品集\\ResearchOS\\research-os');B=R/"execution/v2.4/receipts/W05/W05-99";O=Path('D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W09\\W09-99\\integration_codex\\w09c19-producer-1a11f08')
T=Path('D:\\作品集\\ResearchOS\\research-os\\.local\\worktrees\\w09c19-1a11f08')
ISO=Path('D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W09\\W09-99\\integration_codex\\w09c19-isolation-1a11f08')

def bind_canonical_input_vector(canonical,before,checkpoint_sha,checkpoint_bytes,checkpoint_revision,vector_path,vector_sha,vector_bytes):
 assert len(vector_sha)==64 and all(c in "0123456789abcdef" for c in vector_sha), "CANONICAL_VECTOR_HASH_FORMAT"
 assert type(vector_bytes) is int and 0<vector_bytes<=65536, "CANONICAL_VECTOR_SIZE"
 path=Path(vector_path)
 assert path.is_absolute(), "CANONICAL_VECTOR_ABSOLUTE_PATH"
 path=path.resolve(strict=True)
 assert path.name=="canonical-input-vector.json" and path.is_relative_to((R/"execution/v2.4/receipts/W09/W09-99").resolve()), "CANONICAL_VECTOR_NAMESPACE"
 with path.open("rb") as stream:raw=stream.read(vector_bytes+1)
 assert len(raw)==vector_bytes and hashlib.sha256(raw).hexdigest()==vector_sha, "CANONICAL_VECTOR_PIN"
 vector=json.loads(raw)
 assert isinstance(vector,dict) and set(vector)=={"schema","checkpoint_revision","refs"}, "CANONICAL_VECTOR_FIELDS"
 assert vector["schema"]=="researchos.w09-c19-canonical-input-vector.v1", "CANONICAL_VECTOR_SCHEMA"
 assert type(vector["checkpoint_revision"]) is int and vector["checkpoint_revision"]==checkpoint_revision and checkpoint_revision>0, "CANONICAL_VECTOR_REVISION"
 refs=vector["refs"]
 assert isinstance(refs,list) and len(refs)==4, "CANONICAL_VECTOR_EXACT_FOUR"
 fixed={str(p.resolve()):p for p in canonical};observed={}
 for ref in refs:
  assert isinstance(ref,dict) and set(ref)=={"path","sha256","bytes"}, "CANONICAL_REF_FIELDS"
  assert isinstance(ref["path"],str) and Path(ref["path"]).is_absolute(), "CANONICAL_REF_ABSOLUTE_PATH"
  key=str(Path(ref["path"]).resolve())
  assert key in fixed and key not in observed, "CANONICAL_REF_FIXED_UNIQUE_PATH"
  assert isinstance(ref["sha256"],str) and len(ref["sha256"])==64 and all(c in "0123456789abcdef" for c in ref["sha256"]), "CANONICAL_REF_HASH_FORMAT"
  assert type(ref["bytes"]) is int and 0<ref["bytes"]<=64*1024*1024, "CANONICAL_REF_SIZE"
  data=before[fixed[key]]
  assert len(data)==ref["bytes"] and hashlib.sha256(data).hexdigest()==ref["sha256"], "CANONICAL_REF_PIN"
  observed[key]={"path":key,"sha256":ref["sha256"],"bytes":ref["bytes"]}
 assert set(observed)==set(fixed), "CANONICAL_VECTOR_FIXED_SET"
 cp=observed[str(canonical[0].resolve())]
 assert cp["sha256"]==checkpoint_sha and cp["bytes"]==checkpoint_bytes, "CANONICAL_CHECKPOINT_ARGUMENTS"
 assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision, "CANONICAL_CHECKPOINT_REVISION"
 return {"path":str(path),"sha256":vector_sha,"bytes":vector_bytes},[observed[str(p.resolve())] for p in canonical]

def pin(p):
 p=Path(p).resolve();raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 expected={"path":ref["path"],"sha256":ref["sha256"].removeprefix("sha256:"),"bytes":ref["bytes"]}
 actual=pin(ref["path"]);expected["path"]=str(Path(expected["path"]).resolve())
 assert actual==expected,"exact Source reference mismatch"
 return actual
def save(name,value):
 with (O/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
 return pin(O/name)
def module(path,raw):
 path=Path(path).resolve();m=types.ModuleType("root_typed_"+path.stem);m.__file__=str(path);sys.modules[m.__name__]=m
 exec(compile(raw,str(path),"exec"),m.__dict__);return m
def members(ref):
 manifest=json.loads(Path(ref["path"]).read_bytes())
 values=manifest["members"];return list(values.values()) if isinstance(values,dict) else values
def unique(refs):
 result={}
 for ref in refs:
  ref=verify(ref);key=ref["path"].casefold()
  assert key not in result or result[key]==ref
  result[key]=ref
 return list(result.values())
assert len(sys.argv)==11, "usage: validate.py CHOICE_SHA256 CHOICE_BYTES CHECKPOINT_SHA256 CHECKPOINT_BYTES CHECKPOINT_REVISION ISOLATION_READY_SHA256 ISOLATION_READY_BYTES VECTOR_PATH VECTOR_SHA256 VECTOR_BYTES"
choice_path=Path(__file__).resolve().parent/"source.integration.choice.json"
choice_ref={"path":str(choice_path),"sha256":sys.argv[1],"bytes":int(sys.argv[2])}
verify(choice_ref);choice=json.loads(choice_path.read_bytes())
assert choice["schema"]=="researchos.root-w09-c19-integration-choice.v1" and choice["Root_source_adoption_only"] is True
isolation_ref=verify({"path":str(ISO/"isolation.ready.json"),"sha256":sys.argv[6],"bytes":int(sys.argv[7])})
isolation=json.loads(Path(isolation_ref["path"]).read_bytes())
assert isolation["status"]=="DETACHED_CANDIDATE_WORKTREE_READY_NO_SOURCE_OVERLAY"
assert Path(isolation["worktree_root"]).resolve()==T and Path(isolation["repository_root"]).resolve()==R
assert isolation["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and isolation["all_owned_jobs_closed"] is True
assert isolation["source_overlay"] is False and isolation["main_canonical_unchanged"] is True
sources={relative:verify(ref) for relative,ref in choice["sources"].items()}
assert len(sources)==6 and set(sources)==set(choice["exact_six_targets"])
input_refs=[verify(choice_ref),pin(__file__),isolation_ref]+[verify(ref) for ref in choice["base_driver_refs"]+choice["review_refs"]]
input_refs += [verify(ref) for ref in choice["original_input_refs"]]
new_tests=list(choice["selected_tests"]);review_refs=choice["review_refs"]
assert new_tests==["TestW09C19ChainInvalidation","TestW09C19ExplicitOriginAndUnknown"]
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
before={p:p.read_bytes() for p in canonical}
checkpoint_sha,checkpoint_bytes,checkpoint_revision=sys.argv[3],int(sys.argv[4]),int(sys.argv[5])
assert pin(canonical[0])["sha256"]==checkpoint_sha and pin(canonical[0])["bytes"]==checkpoint_bytes
assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision
vector_ref,canonical_refs=bind_canonical_input_vector(canonical,before,checkpoint_sha,checkpoint_bytes,checkpoint_revision,sys.argv[8],sys.argv[9],int(sys.argv[10]))
assert isolation["canonical_input_vector_ref"]==vector_ref, "ISOLATION_CANONICAL_VECTOR_MISMATCH"
assert not O.exists();O.mkdir()
canonical_pre_run_ref=save("canonical.pre-run.exact.json",dict(refs=canonical_refs,canonical_input_vector_ref=vector_ref,revision=checkpoint_revision,formal_acceptance=False))
main_before={R/n:(R/n).read_bytes() for n in sources if (R/n).is_file()}
main_before.update({R/n:(R/n).read_bytes() for n in ("go.mod","go.sum","internal/domain/store.go")})

gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
go=R/".local/tools/go1.27.1/go/bin/go.exe";git=Path("C:/Program Files/Git/cmd/git.exe")
for path,digest in ((Path(sys.executable),"cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"),(gp,"e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"),(hp,"6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"),(go,"d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"),(git,"da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f")):
 assert pin(path)["sha256"]==digest
input_refs.extend(list(sources.values())+[pin(p) for p in main_before]+[pin(p) for p in (gp,hp,go,git,Path(sys.executable),go.parent.parent/"VERSION",go.parent.parent/"src/go.mod")])

gm=module(gp,gp.read_bytes());helper=module(hp,hp.read_bytes())
input_refs += canonical_refs+[vector_ref,pin(R/"execution/project_identity.json")]
for mod in list(sys.modules.values()):
 for field in ("__file__","__cached__"):
  path=getattr(mod,field,None)
  if path and Path(path).is_file():input_refs.append(pin(path))
guard_raw=gp.read_bytes();assert hashlib.sha256(guard_raw).hexdigest()=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
input_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
input_refs=unique(input_refs);input_guard.acquire(input_refs)
helper=module(hp,input_guard.get_buffer(str(hp)))
runtime_guard=candidate_guard=compiler_guard=None
scratch=Path('D:\\作品集\\ResearchOS\\research-os\\.local\\w09c19-producer-env-1a11f08');assert not scratch.exists();scratch.mkdir()
for name in ("profile","temp"):(scratch/name).mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(go.parent)+";"+str(git.parent)+";C:/Windows/System32","PATHEXT":".COM;.EXE;.BAT;.CMD","USERPROFILE":str(scratch/"profile"),"LOCALAPPDATA":str(scratch/"profile"),"APPDATA":str(scratch/"profile"),"TEMP":str(scratch/"temp"),"TMP":str(scratch/"temp"),"GOROOT":str(go.parent.parent),"GOPATH":str(R/".local/gopath"),"GOCACHE":str(R/".local/gocache"),"GOENV":"off","GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GOWORK":"off","CGO_ENABLED":"0","GOFLAGS":"-mod=readonly -p=1","GOMAXPROCS":"2","RESEARCHOS_GO":str(go),"RESEARCHOS_TASK_ID":"W09","RESEARCHOS_CHECK_ID":"","RESEARCHOS_CASE_ID":"C19","RESEARCHOS_RETRIEVAL_MODE":"fixture","GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_GLOBAL":"NUL","GIT_TERMINAL_PROMPT":"0","GIT_OPTIONAL_LOCKS":"0"}
invocations=[];closed_jobs=[];formatted_ref=inventory_ref=overlay_ref=packet_ref=None

def invoke(label,argv,wall,cwd=None):
 cwd=str(cwd or T);out=O/(label+".stdout.raw");err=O/(label+".stderr.raw")
 result=None;exception=None
 try:
  with out.open("xb") as stdout,err.open("xb") as stderr:result=helper.run_owned(argv,cwd,env,stdout,stderr,wall,creation_flags=0x08000000)
 except BaseException as error:exception=repr(error)
 finally:
  receipt=save(label+".invocation.json",dict(argv=argv,cwd=cwd,public_environment=env,result=result,exception=exception,actual_native_exit=result.get("actual_exit") if result else None,stdout_ref=pin(out),stderr_ref=pin(err),external_model_provider_requests=0,original_trial_provider_requests=None,production_DB_writes=0))
 assert exception is None and result is not None
 invocations.append(receipt);cleanup=result["job_cleanup"]
 is_closed=not cleanup["errors"] and cleanup["active_processes_last_observed"]==0 and all(cleanup[key] for key in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"));closed_jobs.append(is_closed)
 print(json.dumps({"progress":label,"actual_native_exit":result["actual_exit"],"receipt_ref":receipt}),flush=True)
 assert is_closed and result["error"] is None
 return result
def success(label,argv,wall):
 result=invoke(label,argv,wall);assert result["actual_exit"]==0 and not result["timed_out"],label+" actual failed";return result
def closed(status,error=None):
 assert all(path.read_bytes()==raw for path,raw in before.items()) and all(path.read_bytes()==raw for path,raw in main_before.items())
 ref=save("validation.closed.json",dict(status=status,error=error,source_count=len(sources),source_overlay_ref=overlay_ref,exact_source_members_ref=formatted_ref,compiler_inventory_ref=inventory_ref,native_packet_ref=packet_ref,selected_tests=new_tests,expected_native_ids=choice["expected_native_ids"],formal_consumers="NOT_RUN_REGISTRY_UNBOUND",same_native_report_required_for_both_consumers=True,canonical_pre_run_ref=canonical_pre_run_ref,invocation_refs=invocations,all_owned_jobs_closed=all(closed_jobs),independent_Source_review_refs=review_refs,Main_canonical_unchanged=True,Main_adopted=False,original_trial_DB_touched=False,external_model_provider_requests=0,formal_acceptance=False))
 print(json.dumps({"closed_ref":ref,"status":status}),flush=True)

try:
 runtime_refs=unique([pin(p) for p in helper.runtime_resource_paths()])
 runtime_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);runtime_guard.acquire(runtime_refs)
 for relative,ref in sources.items():
  path=T/relative
  if path.is_file():assert path.read_bytes()==(R/relative).read_bytes()
  path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(input_guard.get_buffer(ref["path"]))
 overlay_ref=save("source-overlay.json",{"sources":sources,"Source_count":len(sources),"independent_source_reviews":review_refs,"Main_adopted":False})
 formatted=[pin(T/name) for name in sources];formatted_ref=save("exact.source-members.json",formatted)
 candidate_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);candidate_guard.acquire(formatted+[formatted_ref])
 success("compiler-input-list",[str(go),"list","-test","-deps","-compiled","-json","./internal/domain"],240)
 text=(O/"compiler-input-list.stdout.raw").read_text(encoding="utf-8")
 decoder=json.JSONDecoder();pos=0;packages=[];inputs={};embeds=[]
 fields=("GoFiles","CgoFiles","CFiles","CXXFiles","MFiles","HFiles","FFiles","SFiles","SwigFiles","SwigCXXFiles","SysoFiles","CompiledGoFiles","TestGoFiles","XTestGoFiles","EmbedFiles","TestEmbedFiles","XTestEmbedFiles")
 while pos<len(text):
  while pos<len(text) and text[pos].isspace():pos+=1
  if pos==len(text):break
  pkg,pos=decoder.raw_decode(text,pos);assert not pkg.get("Error") and not pkg.get("DepsErrors");packages.append(pkg.get("ImportPath"))
  if not pkg.get("Dir"):continue
  directory=Path(pkg["Dir"])
  for field in fields:
   for name in pkg.get(field,[]):
    path=Path(name);path=path if path.is_absolute() else directory/path;ref=pin(path);inputs[ref["path"]]=ref
    if field.endswith("EmbedFiles"):embeds.append({"package":pkg["ImportPath"],"field":field,"ref":ref})
 product={}
 for relative in ("apps/control","internal","adapters","evaluation","ops","migrations/sqlite","spec/v2.0/contracts"):
  directory=T/relative
  for path in directory.rglob("*"):
   assert not path.is_symlink()
   if path.is_file():ref=pin(path);product[ref["path"]]=ref
 for relative in ("go.mod","go.sum","execution/toolchains/locked.json","spec/v2.0/PACKAGE_MANIFEST.json"):ref=pin(T/relative);product[ref["path"]]=ref
 tools=[pin(p) for p in (go.parent.parent/"pkg/tool/windows_amd64").iterdir() if p.is_file()]
 inventory_ref=save("actual-compiler-input-inventory.json",{"package_count":len(packages),"packages":packages,"build_inputs":list(inputs.values()),"product_inventory":list(product.values()),"compiler_tool_refs":tools,"GoRef":pin(go),"actual_embed_files":embeds,"includes_actual_test_and_embed_inputs":True,"build_tag":None,"Root_SOURCE_COMPONENT_only":True})
 compiler_refs=unique(list(inputs.values())+list(product.values())+tools+[pin(go),inventory_ref])
 compiler_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);compiler_guard.acquire(compiler_refs)
 # This single owned Python process and every git/go child inherit the exclusive Job.
 # This new candidate has no prior producer directory. A failed run is archived by
 # its unique newly-created child, never by a mutable latest pointer.
 base=(T/"execution/receipts/W09/retrieval").resolve()
 assert not base.exists()
 result=invoke("w09-c19-producer",[str(Path(sys.executable)),"-I","-S","-B","-X","utf8",str(T/"ops/ci/retrieval.py")],420,T)
 created=list(base.iterdir()) if base.is_dir() else []
 assert len(created)==1 and created[0].is_dir() and not created[0].is_symlink()
 packet_dir=created[0].resolve();assert packet_dir.parent==base and re.fullmatch(r"run-[0-9a-f]{32}",packet_dir.name)
 # Preserve originals before evaluating any producer success claim; no latest/glob selection.
 archive=O/"native-packet";archive.mkdir()
 mapping=[]
 for path in sorted(packet_dir.rglob("*")):
  assert not path.is_symlink() and path.resolve().is_relative_to(packet_dir)
  if path.is_file():
   relative=path.relative_to(packet_dir);dest=archive/relative;dest.parent.mkdir(parents=True,exist_ok=True)
   with dest.open("xb") as stream:stream.write(path.read_bytes())
   a,b=pin(path),pin(dest);assert (a["sha256"],a["bytes"])==(b["sha256"],b["bytes"])
   mapping.append(dict(original_ref=a,archive_ref=b))
 report_path=packet_dir/"report.json";tool_path=packet_dir/"native-tool-run.json"
 packet_ref=save("native-packet.public-index.json",dict(run_id=packet_dir.name.removeprefix("run-"),original_report_ref=pin(report_path) if report_path.is_file() else None,original_tool_run_ref=pin(tool_path) if tool_path.is_file() else None,raw_copy_mapping=mapping,consumer_source_root=str(T),formal_acceptance=False,immutable_original_bytes=True))
 raw=(O/"w09-c19-producer.stdout.raw").read_text(encoding="utf-8")
 emitted=json.loads(raw)
 assert (T/emitted["report_reference"]).resolve()==report_path and (T/emitted["tool_run_reference"]).resolve()==tool_path
 report=json.loads(report_path.read_bytes());tool=json.loads(tool_path.read_bytes())
 assert result["actual_exit"]==0 and not result["timed_out"] and report["status"]=="PASS" and report["exit_code"]==0 and report["timed_out"] is False
 assert report["task_id"]=="W09" and report["check_id"] is None and report["case_id"]=="C19"
 assert report["formal_construction_acceptance"]=="NOT_RUN_POSTRUN_REVIEW_PENDING" and report["formal_case_accepted_delta"]==0
 assert report["selected_tests"]==new_tests and set(report["passed_tests"])==set(new_tests)
 expected_argv=[str(go),"test","-count=1","-json","-run","^(?:"+"|".join(new_tests)+")$","./internal/domain"]
 assert report["actual_invocation"]==tool["actual_invocation"]==expected_argv
 assert sorted(report["assertion_ids"])==choice["expected_native_ids"] and report["assertions"]==5 and report["owned_export"]["complete"] is True
 assert tool["report_sha256"]==pin(report_path)["sha256"] and tool["run_id"]==report["run_id"] and tool["native_exit_code"]==0
 assert all(pin(T/relative)["sha256"]==ref["sha256"] and pin(T/relative)["bytes"]==ref["bytes"] for relative,ref in sources.items())
 closed("C19_NATIVE_PRODUCER_PACKET_CLOSED_PENDING_INDEPENDENT_REVIEW")

except BaseException as error:
 if not (O/"validation.closed.json").exists():closed("FAILED_C19_LIST_OR_SINGLE_PRODUCER_CLOSED",repr(error))
 raise
finally:
 for guard,name in ((compiler_guard,"compiler"),(candidate_guard,"candidate"),(runtime_guard,"runtime"),(input_guard,"input")):
  if guard is not None:
   cleanup=guard.close();save(name+"-source-guard.cleanup.actual.json",cleanup)
   assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
