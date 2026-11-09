import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
T=R/".local/worktrees/codex-w0599-schema24-fixture-748db574d1db4c6b";S=B/"prepared_abandonment_native_authority_source_codex/b1599aaf259c435db5a0a5313ab0ea65";C=B/"prepared_run_abandonment_source_v4_codex/f1cd47ca0f9544bfbe94b51a80d7c492";M=B/"prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6";F=B/"schema22_public_fixture_bridge_revision_codex/378a514e11f9417fab091937a9d2421c";H=B/"integration_codex/schema22-fixture-helper-build-root-8aa628d3038b4cd0";L=B/"historical14_observation_revision_codex/14a0241966034992a6f931518140a1f5"
X=B/"schema24_current_fixture_revision_codex/e43b3af533177e02749afc2b8112814e"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 actual=pin(ref["path"]);assert actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"];return actual
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def module(p,raw):
 m=types.ModuleType("root_historical_regression_"+p.stem);m.__file__=str(p);exec(compile(raw,str(p),"exec"),m.__dict__);return m
expected={S:("d0053e330004e062fa123976f83b5d92cf4945e6fcaa36a9c7b2e35e7a54f20a","a745b96158ee7e5c42e5e2b8a732decb36cbb569b0d52f1692e311bc958dd6b6"),C:("16034d64a0e95c9697a1afda1fa1babcdaa79652c3e9e3847503fc5b87896565","fc99c790329ebf190adb04e6b7243c3c3c375f9bb361a3173c910b55b0a45733"),M:("36e752205a2ab01f4402cf5e3dcfa5bdf643e3a7d15cc95e5cfea70da94ec840","bf995d940591a336ae3219afc0f5f1c6e8ad14f5bb39000da5bfeab6c5b38ba8"),F:("a16f917a8f0986e665d33a05f4113d15a882bd55e809040ee68208cb9356a0f7","f6ccd1049969c37985ec58f890fb0e3e153f790433bcba03fa1d2a8a1ecd8ab3")}
expected[L]=("f7b2d77b029c6f530480ea9fc3a7940cba4cfcc12c29f7592405acbf96c2d45f","a8c61268b83cf0c086e9148bb1ac59493ea450b59b8b27af1e45e28e658e460e")
expected[X]=("118be301fb67efa575cf4156cf54c30882264937136c4363ef30413e6076d38b","6c98d5ee592aa3f2cef7d0ea2e4c22edd1818d83eb0f93b9bd9e657ece348c35")
for d,(h,m) in expected.items():assert pin(d/"HDF.json")["sha256"]==h and pin(d/"MF.json")["sha256"]==m
manifests=[json.loads((d/"MF.json").read_bytes()) for d in (C,S,M,F,L,X)]
refs=[verify(ref) for mf in manifests for ref in mf["members"].values()]+[verify(ref) for mf in manifests[3:] for ref in mf["base_refs"]]
sources={};overlap={}
for d,mf in zip((C,S,M,F,L,X),manifests):
 for n,ref in mf["members"].items():
  if not n.startswith("candidate-root/"):continue
  target=n.removeprefix("candidate-root/")
  if target in sources:overlap[target]=dict(previous_ref=sources[target],superseding_ref=ref)
  sources[target]=ref
assert len(sources)==41 and list(overlap)==["internal/domain/prepared_run_abandonment.go","internal/domain/backup_configuration_upgrade_test.go","internal/domain/backup_historical14_resume_test.go","internal/domain/backup_upgrade_test.go"]
main_files=["go.mod","go.sum","apps/control/main.go","internal/domain/store.go","internal/domain/runtime_coordinator_windows.go","internal/domain/backup_migration.go","internal/domain/backup.go","internal/domain/backup_upgrade.go","internal/domain/backup_host_configuration.go","internal/domain/backup_configuration_upgrade_test.go","internal/domain/backup_upgrade_test.go"];main_files+=["internal/domain/backup_command_queue_test.go","internal/domain/backup_host_configuration_test.go","internal/domain/client_configuration_test.go"];main_before={R/n:(R/n).read_bytes() for n in main_files}
for n in sources:
 target=T/n
 if n in main_files:assert target.read_bytes()==main_before[R/n]
 else:assert not target.exists()
for n in ("go.mod","go.sum"):assert (T/n).read_bytes()==main_before[R/n]
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")];before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==354
helper_validation=json.loads((H/"validation.closed.json").read_bytes());assert helper_validation["status"]=="FROZEN_SCHEMA22_HELPER_TEST_PACKAGE_COMPILED_COMPONENT_ONLY" and helper_validation["all_owned_jobs_closed"]
helper_binary=verify(helper_validation["binary_ref"]);helper_root=Path(helper_validation["staged_source_root"]);helper_inputs=json.loads((H/"formatted.source-members.json").read_bytes());assert len(helper_inputs)==504
refs+=[verify(ref) for ref in helper_inputs]+[pin(H/n) for n in ("validation.closed.json","original-tool-io.json","formatted.source-members.json")]+[helper_binary]
resources={
 "RESEARCHOS_CONFIGURATION_OLD_CONTROL":(B/"host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a/old22-control.exe","0cba028c2f8222bef5000a292b1d52346eb534f026f0ee34b4bf55e8a6f033e6"),
 "RESEARCHOS_CONFIGURATION_TARGET_PROGRAM":(B/"main_configuration_composition_independent_review_codex/c34b6453-73e7-42ad-8ac0-511231cf78ab/programs/main-backup23.exe","87038bfe098bdf8da46d554ef35ca957cafd482f0f8bdd3d654c4c0243ec9268"),
 "RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL":(B/"host_configuration_upgrade_executor_codex/handoff-5375496dd2b24206b5db17fc9bc358c3/historical14-control.exe","aeda2d5eff0028529eaa53e9f5cc91fbcd668842577315eb744bd5f066834032")}
for path,sha in resources.values():assert pin(path)["sha256"]==sha;refs.append(pin(path))
oldroot=B/"host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a/frozen_source";old_files=[ref for ref in manifests[3]["base_refs"] if Path(ref["path"]).is_relative_to(oldroot)];assert len(old_files)==502;refs+=[verify(ref) for ref in old_files]
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py";go=R/".local/tools/go1.27.1/go/bin/go.exe";fmt=go.with_name("gofmt.exe")
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad" and pin(go)["sha256"]=="d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
refs+=[pin(p) for p in main_before]+[pin(T/"go.mod"),pin(T/"go.sum"),pin(gp),pin(hp),pin(go),pin(fmt),pin(Path(__file__).resolve())]+[pin(d/n) for d in (S,C,M,F,L,X) for n in ("HDF.json","MF.json")];review_config=json.loads((O/"source-review.accepted.json").read_text(encoding="utf-8"));assert Path(review_config["source_namespace"])==X and review_config["source_review_accepted"]
refs+=[verify(ref) for ref in review_config["review_refs"]]+[pin(O/"source-review.accepted.json")]
parent=B/"integration_codex/prepared-historical-regression-v3-root-0a452eccf5be423b";assert pin(parent/"validation.closed.json")["sha256"]=="36df9a817c132fa4a32920e478c5fbbd011d93282aedf4916ce71a2eb07ef3c3"
parent_tests=json.loads((parent/"validation.closed.json").read_bytes())["test_actions"]["actions"];assert len(parent_tests)==199
refs+=[pin(parent/"validation.closed.json")]
refs=list({r["path"]:r for r in refs}.values())
gm=module(gp,gp.read_bytes());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(refs);helper=module(hp,guard.get_buffer(str(hp)));candidate=None
scratch=R/".local/schema24-fixture-targeted-env-62c53c29ad6e4788";scratch.mkdir(parents=True,exist_ok=False);(scratch/"profile").mkdir();(scratch/"temp").mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(go.parent)+";C:/Windows/System32;C:/Program Files/Git/cmd","PATHEXT":".COM;.EXE;.BAT;.CMD","USERPROFILE":str(scratch/"profile"),"LOCALAPPDATA":str(scratch/"profile"),"APPDATA":str(scratch/"profile"),"TEMP":str(scratch/"temp"),"TMP":str(scratch/"temp"),"GOROOT":str(go.parent.parent),"GOPATH":str(R/".local/gopath"),"GOCACHE":str(R/".local/gocache"),"GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GOWORK":"off","CGO_ENABLED":"0","GOFLAGS":"-mod=readonly -p=1","GOMAXPROCS":"2"}
invocations=[]
def invoke(label,argv,wall):
 out=O/(label+".stdout.raw");err=O/(label+".stderr.raw");result=None;exception=None
 try:
  with out.open("xb") as stdout,err.open("xb") as stderr:result=helper.run_owned(argv,str(T),env,stdout,stderr,wall,creation_flags=0x08000000)
 except BaseException as e:exception=repr(e)
 finally:
  receipt=save(label+".invocation.json",dict(argv=argv,cwd=str(T),public_environment=env,result=result,exception=exception,actual_native_exit=result.get("actual_exit") if result else None,stdout_ref=pin(out),stderr_ref=pin(err),provider_requests=0,production_db_writes=0));invocations.append(receipt)
 assert exception is None and result and not result["timed_out"] and result["error"] is None
 c=result["job_cleanup"];assert not c["errors"] and c["active_processes_last_observed"]==0 and all(c[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 print(json.dumps(dict(progress=label,actual_native_exit=result["actual_exit"],receipt_ref=receipt)),flush=True)
 return result
def closed(status,failed=None,tests=None,binary=None):
 assert all(p.read_bytes()==raw for p,raw in before.items()) and all(p.read_bytes()==raw for p,raw in main_before.items())
 ref=save("validation.closed.json",dict(status=status,failed_step=failed,invocation_refs=invocations,source_overlay_ref=overlay,formatted_source_ref=formatted_ref if "formatted_ref" in globals() else None,test_actions=tests,binary_ref=binary,all_owned_jobs_closed=True,main_canonical_unchanged=True,issuer_anchor_provisioned_separate_native_component=True,complete_control_built_in_this_regression=False,migration_dependency_source_sealed=True,production_db_writes=0,provider_requests=0,formal_acceptance=False))
 print(json.dumps(dict(closed_ref=ref,status=status,provider_requests=0)),flush=True)

env.update({k:str(v[0]) for k,v in resources.items()})
env.update(RESEARCHOS_GO=str(go),RESEARCHOS_CONFIGURATION_OLD_ROOT=str(oldroot),RESEARCHOS_CONFIGURATION_SCHEMA22_HELPER=helper_binary["path"],RESEARCHOS_CONFIGURATION_SCHEMA22_HELPER_SHA256="sha256:"+helper_binary["sha256"],RESEARCHOS_CONFIGURATION_SCHEMA22_HELPER_ROOT=str(helper_root))
try:
 for n,ref in sources.items():
  target=T/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(guard.get_buffer(str(Path(ref["path"]))))
 overlay=save("source-overlay.json",dict(core_manifest_ref=pin(C/"MF.json"),native_manifest_ref=pin(S/"MF.json"),migration_manifest_ref=pin(M/"MF.json"),schema22_bridge_manifest_ref=pin(F/"MF.json"),historical14_observation_manifest_ref=pin(L/"MF.json"),sources=sources,overlap=overlap,source_count=41,schema24_fixture_manifest_ref=pin(X/"MF.json"),schema24_fixture_source_independent_refs=review_config["review_refs"],Main_adopted=False))
 result=invoke("format",[str(fmt),"-w",*[str(T/n) for n in sources if n.endswith(".go")]],45)
 if result["actual_exit"]!=0:closed("FAILED_FORMAT_NATIVE_CLOSED","format");raise AssertionError("historical regression composite gofmt failed")
 targets=[pin(T/n) for n in sources];formatted_ref=save("formatted.source-members.json",targets)
 candidate=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);candidate.acquire(targets+[formatted_ref])
 test=invoke("prepared-and-historical-backup-regression",[str(go),"test","-count=1","-json","-timeout=585s","-run","^Test(PreparedUpgrade|PreparedRunAbandonment|W17Upgrade|W18|ConfigurationUpgrade|ClientQueue|ClientConfiguration|HandlerRejectedSessionPublicBackupReplay)","./internal/domain"],600)
 events=[json.loads(l) for l in (O/"prepared-and-historical-backup-regression.stdout.raw").read_text(encoding="utf-8").splitlines() if l.startswith("{")];actions={e["Test"]:e["Action"] for e in events if "Test" in e and e["Action"] in ("pass","fail","skip")}
 started={e["Test"] for e in events if e.get("Action")=="run" and "Test" in e};assert started==set(actions) and set(parent_tests).issubset(actions)
 tests=dict(actions=actions,all_started_have_terminal=True,parent199_test_names_preserved=True,pass_count=sum(v=="pass" for v in actions.values()),fail_count=sum(v=="fail" for v in actions.values()),skip_count=sum(v=="skip" for v in actions.values()),model_or_SDK_execution_claim=False,historical_FIXTURE_PHASE_injections_retained=True)
 if test["actual_exit"]!=0 or not actions or any(v!="pass" for v in actions.values()):closed("FAILED_PREPARED_AND_HISTORICAL_REGRESSION_NATIVE_CLOSED","prepared-and-historical-backup-regression",tests);raise AssertionError("historical backup regression failed")
 closed("SCHEMA24_CURRENT_FIXTURES_AND_PREPARED_HISTORICAL_TARGETED_PASSED_COMPONENT_ONLY",tests=tests)
finally:
 if candidate is not None:
  c=candidate.close();save("candidate-source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
 c=guard.close();save("input-source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
