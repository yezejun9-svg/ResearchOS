import sys
sys.dont_write_bytecode=True
import json, hashlib, types, uuid
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99"
O=Path(__file__).resolve().parent
A=B/"integration_codex/native-harness43-compile-unit-root-c16a0730cf914bc5"
P=B/"integration_codex/native-migration-positive-root-73df768bc70b4f64"
I=B/"integration_codex/controller-atomic-publication-root-2e926de963bc46f2/source-input.reviewed.json"
def plain(path):
 path=Path(path).resolve();raw=path.read_bytes()
 return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def ref(path):
 v=plain(path);v["sha256"]="sha256:"+v["sha256"];return v
def save(name,value):
 with (O/name).open("xb") as stream:stream.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return ref(O/name)
def module(path):
 path=Path(path).resolve();name="root_config_"+path.stem
 m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m
 exec(compile(path.read_bytes(),str(path),"exec"),m.__dict__);return m
meta=json.loads(I.read_bytes());assert meta["atomic_publication_source_accepted"] and not meta["native_or_owner_accepted"]
ctl=Path(meta["controller_ref"]["path"]);assert plain(ctl)==meta["controller_ref"]
cm=module(ctl)
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
op=ctl.parent/"windows_owned_observed.py"
assert plain(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert plain(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
assert plain(op)["sha256"]=="fe102f02de5aa966945ef88218e412f1988509168705d03a8660dab8b282d4e3"
gm=module(gp);original=module(hp);observed=module(op)
actual=json.loads((A/"validation.closed.json").read_bytes())
assert actual["unit_pass_count"]==25 and actual["unit_fail_count"]==actual["unit_skip_count"]==0
assert actual["native_migration_cases_executed"]==0
hcpath=P/"native-harness.public.config.json"
assert plain(hcpath)["sha256"]=="ef404512f197dda8223526af9f301fa922b54a84416e43094f79202e70f9fd32"
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
for value in meta["review_refs"]:add(value)
scratch=R/".local"/("native-positive-controller-env-"+uuid.uuid4().hex)
(scratch/"temp").mkdir(parents=True);(scratch/"profile").mkdir()
env={k:v for k,v in build["public_environment"].items() if k in cm.ENV_KEYS}
for key in ("TEMP","TMP"):env[key]=str((scratch/"temp").resolve())
for key in ("USERPROFILE","LOCALAPPDATA","APPDATA"):env[key]=str((scratch/"profile").resolve())
cfg["FrozenInputs"]=list(frozen.values());cfg["Environment"]=env
config_ref=save("controller.public.config.json",cfg)
before=[plain(R/"execution/v2.4"/(n+".json")) for n in ("checkpoint","path_ownership","step_state","commands")]
# Pure context validation proves all selected compiler/product/runtime paths are
# represented. It starts no child, reads no credential, and creates no approvals.
c=cm.context(config_ref)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire([dict(path=p["path"],sha256=p["sha256"].removeprefix("sha256:"),bytes=p["bytes"]) for p in cfg["FrozenInputs"]])
finally:
 cleanup=guard.close();save("config-input-source-guard.cleanup.actual.json",cleanup)
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
assert before==[plain(p["path"]) for p in before]
assert not Path(cfg["ControllerDirectory"]).exists() and not Path(hc["OutputDirectory"]).exists()
receipt=save("controller-config.prepared.json",{"schema":"researchos.root-native-controller-public-configuration-prepared.v1",
 "status":"PUBLIC_POSITIVE_CONTROLLER_CONFIGURATION_VALIDATED_NOT_EXECUTED","config_ref":config_ref,
 "frozen_input_count":len(frozen),"selected_compiler_input_count":len(inventory["build_inputs"]),
 "product_input_count":len(inventory["product_inventory"]),"compiler_tool_count":len(inventory["compiler_tool_refs"]),"GoRef_explicitly_frozen":True,
 "supersedes_pure_public_config_ref":{"path":str((B/"integration_codex/native-positive-controller-config-root-0b1ce17e94d14864/controller.public.config.json").resolve()),"sha256":"sha256:a501379943aa41fb13b19d4220a2eadd3aff5177935b1174ef4af3e5c17b1b34","bytes":1086219},
 "canonical_unchanged_refs":before,"controller_source_review_refs":meta["review_refs"],
 "native_cases_executed":0,"Owner_credential_reads":0,"private_key_reads":0,"issuer_signatures":0,
 "original_trial_DB_writes":0,"provider_requests":0,"formal_acceptance":False})
print(json.dumps({"prepared_ref":receipt,"config_ref":config_ref,"frozen_input_count":len(frozen)}))
