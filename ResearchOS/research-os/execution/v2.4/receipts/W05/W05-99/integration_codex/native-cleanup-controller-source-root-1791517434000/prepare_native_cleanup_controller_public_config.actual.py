import sys
sys.dont_write_bytecode=True
import json,hashlib,types,uuid,sqlite3,struct,collections,subprocess,queue,threading,datetime,ctypes
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
A=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-cleanup-compile-source-root-1791516889000")
V=B/"native_controller_retained_window_revision_codex/ctl4-1a11e7f5205729390aaee9f47b28ce6"
Z=B/"native_ctl4_n12_independent_review_codex/cn-20261009-source-review"
OLD=B/"integration_codex/native-migration-positive-ttl-root-26c5c890ef5144d4/native-harness.public.config.json"
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
op=B/"native_migration_atomic_publication_revision_codex/1a11d9c912f7c13799a37e93/windows_owned_observed.py"
ctl=V/"root_native_migration_controller.py"
BP=B/"native_python_broker_temp_env_revision_codex/7bc2467624af477a8d55e0595ec4a7c2"
BR=B/"native_python_broker_temp_env_independent_review_codex/9e4f389d093d4ea58eb5ec06e102876d"
PU=B/"integration_codex/python-broker4-public-units-root-1791512710000/revision-explicit-binary-handles"
def plain(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def ref(p):
 q=plain(p);q["sha256"]="sha256:"+q["sha256"];return q
def verify(v):
 q=plain(v["path"]);assert q["sha256"]==v["sha256"].removeprefix("sha256:") and q["bytes"]==v["bytes"];return q
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
 return ref(O/n)
def module(p,raw):
 p=Path(p).resolve();m=types.ModuleType("root_t8_public_"+p.stem);m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(raw,str(p),"exec"),m.__dict__);return m
assert plain(ctl)["sha256"]=="e7538c580d2e07217512e036e00272b3be94cb11551ace6885cc46316a67b3b3"
assert plain(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert plain(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
assert plain(op)["sha256"]=="fe102f02de5aa966945ef88218e412f1988509168705d03a8660dab8b282d4e3"
assert plain(Path(sys.executable))["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
assert plain(V/"HDF.json")["sha256"]=="9b335e2099575e3737b038ba212315bf4d4f1e2311614961d20bf8770cc578cc"
assert plain(V/"MF.json")["sha256"]=="14a6d3df02728fcc2b675658d4c2247a66f07d271826fd7bbe54c0ac7ad2de03"
assert plain(Z/"HDF.json")["sha256"]=="32ddc6d38de6708304127045f738adac3959d9c225b0aec35e8666dacdd51412"
assert plain(Z/"MF.json")["sha256"]=="122de2bf58c17ec8a05a8fd7bcd3d79580c7bf3a8576e6740004a0d1241ca8a2"
assert json.loads((Z/"HDF.json").read_bytes())["CTL4_decision"]=="SOURCE_ACCEPTED_PENDING_FRESH_CONFIG_AND_ROOT_ACTUAL"
assert plain(A/"validation.closed.json")["sha256"]=="cb2459bafde88bf99ab33bd34212fd2986e93e287fab1ad940437be9e3531d67"
actual=json.loads((A/"validation.closed.json").read_bytes())
assert actual["status"]=="NATIVE_CLEANUP43_FOUR_PROGRAMS_TAGGED_TEST_AND32_LEAVES_PASS_COMPONENT_ONLY_NATIVE_ACTUAL_PENDING"
assert actual["unit_pass_count"]==35 and actual["unit_fail_count"]==actual["unit_skip_count"]==0 and actual["native_migration_cases_executed"]==0
assert plain(OLD)["sha256"]=="6f9cef908f962c22f7b8b1fce8e938b83d10c84dfacf919c7a7420996e74389a"
cm=module(ctl,ctl.read_bytes());gm=module(gp,gp.read_bytes());original=module(hp,hp.read_bytes());observed=module(op,op.read_bytes())
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
before=[plain(p) for p in canonical]
assert len(sys.argv)==4, "usage: checkpoint_SHA checkpoint_BYTES checkpoint_REV"
assert before[0]["sha256"]==sys.argv[1] and before[0]["bytes"]==int(sys.argv[2]) and json.loads(canonical[0].read_bytes())["revision"]==int(sys.argv[3])
bootstrap_refs=[plain(p) for p in (gp,hp,op,ctl,OLD,Path(sys.executable),Path(__file__),*canonical,R/"execution/project_identity.json")]
for d in (V,Z):
 bootstrap_refs += [plain(d/"HDF.json"),plain(d/"MF.json")]
 members=json.loads((d/"MF.json").read_bytes())["members"];members=members.values() if isinstance(members,dict) else members
 bootstrap_refs += [verify(v) for v in members]
bootstrap_refs += [verify(actual["compiler_input_inventory_ref"]),plain(A/"validation.closed.json"),plain(A/"tagged-test-binary-compile.invocation.json"),plain(A/"broker-temp-unit-results.json")]
assert plain(BP/"root_only_native_broker.py")["sha256"]=="70b8eba1de168849d041488ac9268da60fd2ae8a059cc9518e9dc93d0cd4b87c"
assert plain(BP/"HDF.json")["sha256"]=="ed0f388870aef974f9577e6d5146637d5a1a77ce6b22c57e989227654de05824"
assert plain(BP/"MF.json")["sha256"]=="deab5d3bb0fc512c37808a4dcd9b66d370dcd0c1ae14b84e1949fcfdb915ebdc"
assert plain(BR/"HDF.json")["sha256"]=="7c0ad0872da573a5a6948b2c6e7d55a438e57e3cc2ba65b70329e9cea6dd2518"
assert plain(BR/"MF.json")["sha256"]=="8edd94cc087bf2f042fcec9a892f04687eb0898dc67c683e2fe710f85cbf58bb"
assert plain(PU/"validation.closed.json")["sha256"]=="9f9d17cfdcea867bf03bd1404ec1bd8b1824229add2a2b03d107c0ce2cb6c318"
unit_results=json.loads((PU/"units.results.json").read_bytes());assert unit_results["pass_count"]==17 and unit_results["fail_count"]==unit_results["skip_count"]==0
for d in (BP,BR):
 bootstrap_refs += [plain(d/"HDF.json"),plain(d/"MF.json")]
 members=json.loads((d/"MF.json").read_bytes())["members"];members=members.values() if isinstance(members,dict) else members
 bootstrap_refs += [verify(v) for v in members]
bootstrap_refs += [plain(BP/"root_only_native_broker.py"),plain(PU/"validation.closed.json"),plain(PU/"units.results.json"),plain(PU/"units.invocation.json"),plain(PU/"input-source-guard.cleanup.actual.json"),plain(PU/"runtime-source-guard.cleanup.actual.json")]
for m in list(sys.modules.values()):
 for field in ("__file__","__cached__"):
  p=getattr(m,field,None)
  if p and Path(p).is_file():bootstrap_refs.append(plain(p))
bootstrap_refs += [plain(p) for p in original.runtime_resource_paths()]
phase_source=B/"root_native_concrete_phase_helpers_revision_codex/nhr1-1a11e7f5205729390aaee9f47b28ce6"
phase_review=B/"root_native_concrete_helpers_independent_review_codex/nhr1r-20261009-source-review"
assert plain(phase_source/"HDF.json")["sha256"]=="151045d795d4ac73a7e00f74a290f051583f11582017c608ac8a526c6051b328"
assert plain(phase_source/"MF.json")["sha256"]=="f545b924574565a8141bc5a42761cee6f2b1efca5b08b3dea418f0a30a0ec5c5"
assert plain(phase_review/"HDF.json")["sha256"]=="4e4702c5f27e365b8bfc16d73226bd5a5f9fb53a70e9064b4659d44aaf357c6b"
assert plain(phase_review/"MF.json")["sha256"]=="e116cb0ec170d1248c03747df76ae38ed9ef408a61f0a450c2aa521f349c3fc7"
for d in (phase_source,phase_review):
 bootstrap_refs += [plain(d/"HDF.json"),plain(d/"MF.json")]
 m=json.loads((d/"MF.json").read_bytes())["members"];m=m.values() if isinstance(m,dict) else m
 bootstrap_refs += [verify(v) for v in m]
bootstrap_refs=list({v["path"].casefold():v for v in bootstrap_refs}.values())
bootstrap=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);bootstrap.acquire(bootstrap_refs)
fullguard=None
try:
 assert bootstrap.get_buffer(str(ctl.resolve()))==ctl.read_bytes()
 inventory_path=Path(actual["compiler_input_inventory_ref"]["path"]);inventory=json.loads(bootstrap.get_buffer(str(inventory_path.resolve())))
 build_path=A/"tagged-test-binary-compile.invocation.json";build=json.loads(bootstrap.get_buffer(str(build_path.resolve())))
 assert build["actual_native_exit"]==0
 hc=json.loads(bootstrap.get_buffer(str(OLD.resolve())))
 hc["CaseID"]="t12cl149d6f49321"
 hc["BuildRoot"]=actual["current_source_root"];hc["OutputDirectory"]=str((O/"harness-facts").resolve())
 for key,label in (("RootProgram","maintenance-root-build"),("ControlProgram","control-build"),("BackupProgram","backup-build"),("EnrollmentProgram","enrollment-build")):
  p=verify(actual["binary_refs"][label]);hc[key]={"role":hc[key]["role"],**p,"sha256":"sha256:"+p["sha256"]}
 assert not Path(hc["OutputDirectory"]).exists()
 broker_source=verify(plain(BP/"root_only_native_broker.py"));hc["BrokerSource"]={"role":"broker-source",**broker_source,"sha256":"sha256:"+broker_source["sha256"]}
 assert set(hc["BrokerSource"])=={"role","path","sha256","bytes"}
 hc_ref=save("native-harness.public.config.json",hc)
 cfg={"Schema":"researchos.root-native-migration-controller.v1","ControllerDirectory":str((O/"controller-runtime").resolve()),"ControllerSource":ref(ctl),"HarnessConfig":hc_ref,"TestProgram":ref(actual["binary_refs"]["tagged-test-harness"]["path"]),"ObservedOwnedHelper":ref(op),"OriginalOwnedHelper":ref(hp),"SourceReadGuard":ref(gp),"CompilerInventory":ref(inventory_path),"BuildInvocation":ref(build_path)}
 frozen={}
 def add(v):
  q=verify(v);q["sha256"]="sha256:"+q["sha256"];key=q["path"].casefold();assert key not in frozen or frozen[key]==q;frozen[key]=q
 for v in cfg.values():
  if isinstance(v,dict):add(v)
 for key in ("RootProgram","ControlProgram","BackupProgram","EnrollmentProgram","PythonProgram","BrokerSource","PrivateStdinHelper"):add(hc[key])
 for v in inventory["build_inputs"]+inventory["product_inventory"]+inventory["compiler_tool_refs"]:add(v)
 add(inventory["GoRef"])
 for v in bootstrap_refs:add(v)
 go=Path(inventory["GoRef"]["path"]);add(ref(go.parent.parent/"VERSION"));add(ref(go.parent.parent/"src/go.mod"))
 add(actual["official_test2json_ref"])
 scratch=R/".local"/"native-cleanup-controller-env-1791517434000"
 (scratch/"temp").mkdir(parents=True,exist_ok=False);(scratch/"profile").mkdir()
 env={k:v for k,v in build["public_environment"].items() if k in cm.ENV_KEYS}
 for key in ("TEMP","TMP","RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT"):env[key]=str((scratch/"temp").resolve())
 for key in ("USERPROFILE","LOCALAPPDATA","APPDATA"):env[key]=str((scratch/"profile").resolve())
 assert env["RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT"]==env["TEMP"]==env["TMP"]
 cfg["FrozenInputs"]=list(frozen.values());cfg["Environment"]=env
 cfg_ref=save("controller.public.config.json",cfg)
 fullguard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);fullguard.acquire([{"path":v["path"],"sha256":v["sha256"].removeprefix("sha256:"),"bytes":v["bytes"]} for v in cfg["FrozenInputs"]]+[verify(cfg_ref)])
 c=cm.context(cfg_ref)
 assert c["cfg"]==cfg and c["hc"]==hc and c["hc"]["Case"]=="positive-replay"
 assert before==[plain(p) for p in canonical]
 assert not Path(cfg["ControllerDirectory"]).exists() and not Path(hc["OutputDirectory"]).exists()
 out=save("controller-config.prepared.json",dict(schema="researchos.root-native-controller-public-configuration-prepared.v1",status="FRESH_CTL4_CLEANUP_BROKER4_PROOF_CONTEXT_VALIDATED_NO_NATIVE_LAUNCH",config_ref=cfg_ref,harness_config_ref=hc_ref,frozen_input_count=len(frozen),selected_compiler_input_count=len(inventory["build_inputs"]),product_input_count=len(inventory["product_inventory"]),compiler_tool_count=len(inventory["compiler_tool_refs"]),GoRef_explicitly_frozen=True,official_test2json_ref=actual["official_test2json_ref"],public_temp_binding=env["TEMP"],source_review_refs=[ref(Z/"HDF.json"),ref(Z/"MF.json"),ref(BR/"HDF.json"),ref(BR/"MF.json")],broker_source_ref=ref(BP/"root_only_native_broker.py"),broker_public17_units_ref=ref(PU/"validation.closed.json"),compile_ref=ref(A/"validation.closed.json"),canonical_unchanged_refs=before,no_automatic_sign_or_approval=True,native_cases_executed=0,Owner_credential_reads=0,private_key_reads=0,issuer_signatures=0,original_trial_DB_writes=0,provider_requests=0,formal_acceptance=False))
 print(json.dumps({"prepared_ref":out,"config_ref":cfg_ref,"frozen_input_count":len(frozen)}),flush=True)
finally:
 for g,n in ((fullguard,"config-input"),(bootstrap,"bootstrap")):
  if g:
   cleanup=g.close();save(n+"-source-guard.cleanup.actual.json",cleanup);assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
