import sys
sys.dont_write_bytecode=True
import json, hashlib, types, uuid
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99"
O=Path(__file__).resolve().parent
A=B/"integration_codex/native-ttl-compile-root-458f017f3c294bb6"
P=B/"integration_codex/native-migration-positive-ttl-root-26c5c890ef5144d4"
I=B/"integration_codex/controller-atomic-publication-root-2e926de963bc46f2/source-input.reviewed.json"
def plain(path):
 path=Path(path).resolve();raw=path.read_bytes()
 return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def ref(path):
 v=plain(path);v["sha256"]="sha256:"+v["sha256"];return v
def save(name,value):
 with (O/name).open("xb") as stream:stream.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return ref(O/name)
def module(path,raw):
 path=Path(path).resolve();name="root_config_"+path.stem
 m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m
 exec(compile(raw,str(path),"exec"),m.__dict__);return m
meta_raw=I.read_bytes();assert hashlib.sha256(meta_raw).hexdigest()=="68d8f7a0b97e7d2c969e9047fcc99ef0ec1610a4b9dd191b2548c528c8467531"
meta=json.loads(meta_raw);assert meta["atomic_publication_source_accepted"] and not meta["native_or_owner_accepted"]
ctl=Path(meta["controller_ref"]["path"]);assert plain(ctl)==meta["controller_ref"]
assert plain(ctl)["sha256"]=="14cba01f91b7d9f322243c0df041a29337c422f72ea96214337047522dec8c83" and plain(ctl)["bytes"]==40404
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
op=ctl.parent/"windows_owned_observed.py"
assert plain(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
assert plain(op)["sha256"]=="fe102f02de5aa966945ef88218e412f1988509168705d03a8660dab8b282d4e3"
guard_raw=gp.read_bytes()
assert hashlib.sha256(guard_raw).hexdigest()=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert plain(Path(sys.executable))["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
gm=module(gp,guard_raw)
bootstrap_refs=[plain(p) for p in (gp,hp,op,ctl,I,Path(sys.executable),Path(__file__).resolve())]
for mod in list(sys.modules.values()):
 for field in ("__file__","__cached__"):
  path=getattr(mod,field,None)
  if path and Path(path).is_file():bootstrap_refs.append(plain(path))
bootstrap_refs=list({v["path"].casefold():v for v in bootstrap_refs}.values())
bootstrap=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
bootstrap.acquire(bootstrap_refs)
assert bootstrap.get_buffer(str(I.resolve()))==meta_raw
try:
 original=module(hp,bootstrap.get_buffer(str(hp.resolve())))
 cm=module(ctl,bootstrap.get_buffer(str(ctl.resolve())))
 observed=module(op,bootstrap.get_buffer(str(op.resolve())))
 actual=json.loads((A/"validation.closed.json").read_bytes())
 assert actual["status"]=="NATIVE_TTL43_FOUR_PROGRAMS_AND_TAGGED_TEST_COMPILED_COMPONENT_ONLY_NATIVE_ACTUAL_PENDING" and actual["unit_pass_count"]==actual["unit_fail_count"]==actual["unit_skip_count"]==0
 assert actual["native_migration_cases_executed"]==0
 hcpath=P/"native-harness.public.config.json"
 assert plain(hcpath)["sha256"]=="6f9cef908f962c22f7b8b1fce8e938b83d10c84dfacf919c7a7420996e74389a"
 hc=json.loads(hcpath.read_bytes());assert hc["Case"]=="positive-replay"
 assert not Path(hc["OutputDirectory"]).exists()
 inventory_path=Path(actual["compiler_input_inventory_ref"]["path"])
 assert plain(inventory_path)==actual["compiler_input_inventory_ref"]
 inventory=json.loads(inventory_path.read_bytes())
 build_path=A/"tagged-test-binary-compile.invocation.json";build=json.loads(build_path.read_bytes())
 test_path=Path(actual["binary_refs"]["tagged-test-harness"]["path"])
 assert plain(test_path)==actual["binary_refs"]["tagged-test-harness"]
 cfg={"Schema":"researchos.root-native-migration-controller.v1",
      "ControllerDirectory":str((O/"controller-runtime").resolve()),
      "ControllerSource":ref(ctl),"HarnessConfig":ref(hcpath),"TestProgram":ref(test_path),
      "ObservedOwnedHelper":ref(op),"OriginalOwnedHelper":ref(hp),"SourceReadGuard":ref(gp),
      "CompilerInventory":ref(inventory_path),"BuildInvocation":ref(build_path)}
 frozen={}
 def add(value):
  v={"path":str(Path(value["path"]).resolve()),"sha256":"sha256:"+value["sha256"].removeprefix("sha256:"),"bytes":value["bytes"]}
  k=v["path"].casefold()
  assert k not in frozen or frozen[k]==v
  frozen[k]=v
 for key,value in cfg.items():
  if isinstance(value,dict):add(value)
 for key in ("RootProgram","ControlProgram","BackupProgram","EnrollmentProgram","PythonProgram","BrokerSource","PrivateStdinHelper"):add(hc[key])
 for value in inventory["build_inputs"]+inventory["product_inventory"]+inventory["compiler_tool_refs"]:add(value)
 add(inventory["GoRef"])
 for path in original.runtime_resource_paths():add(ref(path))
 for m in list(sys.modules.values()):
  if getattr(m,"__file__",None) and Path(m.__file__).is_file():add(ref(m.__file__))
  if getattr(m,"__cached__",None) and Path(m.__cached__).is_file():add(ref(m.__cached__))
 for path in (Path(__file__),I,A/"validation.closed.json"):add(ref(path))
 for value in bootstrap_refs:add(value)
 add(ref(Path(sys.executable)))
 for value in meta["review_refs"]:add(value)
 scratch=R/".local"/("native-ttl-controller-env-"+uuid.uuid4().hex)
 (scratch/"temp").mkdir(parents=True);(scratch/"profile").mkdir()
 old_cfg_path=B/"integration_codex/native-positive-controller-config-v2-root-0da7b5a0b3f84a13/controller.public.config.json"
 old_cfg_raw=old_cfg_path.read_bytes();assert hashlib.sha256(old_cfg_raw).hexdigest()=="9d561a6be761ebb2e61bb72a7bee22b07e188cee3877105827f4ca48ba6928fc"
 old_env_keys=set(json.loads(old_cfg_raw)["Environment"])
 add(ref(old_cfg_path))
 env={k:v for k,v in build["public_environment"].items() if k in old_env_keys}
 for key in ("TEMP","TMP"):env[key]=str((scratch/"temp").resolve())
 for key in ("USERPROFILE","LOCALAPPDATA","APPDATA"):env[key]=str((scratch/"profile").resolve())
 cfg["FrozenInputs"]=list(frozen.values());cfg["Environment"]=env
 config_ref=save("controller.public.config.json",cfg)
 before=[plain(R/"execution/v2.4"/(n+".json")) for n in ("checkpoint","path_ownership","step_state","commands")]
 # Pure context validation proves all selected compiler/product/runtime paths are
 # represented. It starts no child, reads no credential, and creates no approvals.
 guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
 try:
  guard.acquire([dict(path=p["path"],sha256=p["sha256"].removeprefix("sha256:"),bytes=p["bytes"]) for p in cfg["FrozenInputs"]])
  assert guard.get_buffer(str(ctl.resolve()))==bootstrap.get_buffer(str(ctl.resolve()))
  c=cm.context(config_ref)
 finally:
  cleanup=guard.close();save("config-input-source-guard.cleanup.actual.json",cleanup)
  assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
 assert before==[plain(p["path"]) for p in before]
 assert not Path(cfg["ControllerDirectory"]).exists() and not Path(hc["OutputDirectory"]).exists()
 receipt=save("controller-config.prepared.json",{"schema":"researchos.root-native-controller-public-configuration-prepared.v1",
  "status":"PUBLIC_POSITIVE_CONTROLLER_CONFIGURATION_VALIDATED_NOT_EXECUTED","config_ref":config_ref,
  "frozen_input_count":len(frozen),"selected_compiler_input_count":len(inventory["build_inputs"]),
  "product_input_count":len(inventory["product_inventory"]),"compiler_tool_count":len(inventory["compiler_tool_refs"]),"GoRef_explicitly_frozen":True,
  "old_positive_attempt_config_not_reused":True,
  "canonical_unchanged_refs":before,"controller_source_review_refs":meta["review_refs"],
  "native_cases_executed":0,"Owner_credential_reads":0,"private_key_reads":0,"issuer_signatures":0,
  "original_trial_DB_writes":0,"provider_requests":0,"formal_acceptance":False})
 print(json.dumps({"prepared_ref":receipt,"config_ref":config_ref,"frozen_input_count":len(frozen)}))

finally:
 bootstrap_cleanup=bootstrap.close();save("bootstrap-source-guard.cleanup.actual.json",bootstrap_cleanup)
 assert bootstrap_cleanup["closed"] and not bootstrap_cleanup["errors"] and bootstrap_cleanup["retained_handles_count"]==0
