import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
C=B/"integration_codex/native-harness43-compile-unit-root-c16a0730cf914bc5"
T=R/".local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2"
V=B/"native_migration_harness_error_revision_codex/e57c696eaf418862f0eb721ec8c8"
U=B/"native_private_stdin_helper_revision_codex/320740c9ef7c4dbaa6cae48633aa8e60"
K=B/"integration_codex/recoveryauthority-key-provision-root-9b42b8e7072a40b1"
CASE=R/".local/native-migration-case-positive-replay-43d8129a6c904f5c"
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(r):
 a=pin(r["path"]);assert a["sha256"]==r["sha256"] and a["bytes"]==r["bytes"];return a
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
 return pin(p)
def rawpin(role,p):
 a=pin(p);return dict(role=role,path=a["path"],sha256="sha256:"+a["sha256"],bytes=a["bytes"])
assert pin(C/"validation.closed.json")["sha256"]=="83f63ea38fc0af3b97cb5fb33000c9c98abe4cb048ee516c364f02dc142540d8"
v=json.loads((C/"validation.closed.json").read_bytes());assert v["unit_pass_count"]==25 and v["unit_fail_count"]==v["unit_skip_count"]==0 and v["native_migration_cases_executed"]==0
assert Path(v["current_source_root"])==T
refs=[verify(r) for r in v["binary_refs"].values()]+[verify(v["formatted_source_ref"]),verify(v["compiler_input_inventory_ref"])]
broker=V/"root_only_native_broker.py";private_helper=U/"windows_owned_private_stdin.py";python=Path(sys.executable)
assert pin(broker)["sha256"]=="5f3b4e957d85aeb091a2a801d72bcbf2afb2135c42e0a0a86fc740ff9f99750e"
assert pin(private_helper)["sha256"]=="4654730495d3777c8bf63540a0f5795b17ff14a45e93d6cd915e2e2846213a3c"
assert pin(python)["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
public_key=(K/"root-adoption.stdout.public.raw").read_text(encoding="utf-8").strip()
assert public_key=="d5d735ecd3296beb4ee68d59da4f7503d7db34b310e0642d9f8b19c5c454e4b5"
assert (K/"issuer.stdout.public.raw").read_text(encoding="utf-8").strip()=="936929c4ad26612ee75cc4ad5a6dc2d8c0f898bf974bb9c01e8e5140ee207bdf"
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
refs+=[pin(p) for p in (gp,broker,private_helper,python,K/"root-adoption.stdout.public.raw",K/"issuer.stdout.public.raw",C/"validation.closed.json",Path(__file__).resolve())]
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==355
assert not CASE.exists() and CASE.resolve().is_relative_to((R/".local").resolve()) and not (O/"facts").exists()
m=types.ModuleType("root_public_config_guard");m.__file__=str(gp);exec(compile(gp.read_bytes(),str(gp),"exec"),m.__dict__)
guard=m.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(refs)
try:
 (CASE/"programs").mkdir(parents=True,exist_ok=False)
 copies={}
 for label,name in (("maintenance-root-build","recovery-root.exe"),("control-build","control.exe"),("backup-build","backup.exe"),("enrollment-build","recovery-enrollment.exe")):
  ref=v["binary_refs"][label];p=CASE/"programs"/name
  with p.open("xb") as f:f.write(guard.get_buffer(str(Path(ref["path"]))))
  a=pin(p);assert a["sha256"]==ref["sha256"] and a["bytes"]==ref["bytes"];copies[label]=dict(original_ref=ref,case_ref=a)
 cfg=dict(Schema="researchos.synthetic-native-migration-config.v1",Case="positive-replay",CaseID="73df768bc70b4f64",OutputDirectory=str(O/"facts"),BuildRoot=str(T),RootSigningPublicKey=public_key,RootProgram=rawpin("root-program",CASE/"programs/recovery-root.exe"),ControlProgram=rawpin("control-program",CASE/"programs/control.exe"),BackupProgram=rawpin("backup-program",CASE/"programs/backup.exe"),EnrollmentProgram=rawpin("enrollment-program",CASE/"programs/recovery-enrollment.exe"),PythonProgram=rawpin("python-program",python),BrokerSource=rawpin("broker-source",broker),PrivateStdinHelper=rawpin("private-stdin-helper",private_helper))
 config=save("native-harness.public.config.json",cfg)
 assert all(p.read_bytes()==r for p,r in before.items())
 proof=save("public-config.prepared.json",dict(status="PUBLIC_POSITIVE_CONFIG_AND_FOUR_CASE_PROGRAMS_PREPARED_NO_NATIVE_EXECUTION",configuration_ref=config,compiled_test_binary_ref=v["binary_refs"]["tagged-test-harness"],required_test_cwd=str(T/"internal/domain"),program_copies=copies,source43_compilation_ref=pin(C/"validation.closed.json"),case_root=str(CASE),output_directory_created=False,issuer_private_key_accessed=False,root_adoption_private_sidecar_created=False,issuer_signatures_created=0,original_trial_db_writes=0,external_model_provider_requests=0,formal_acceptance=False))
 print(json.dumps(dict(prepared_ref=proof,configuration_ref=config,native_executions=0)),flush=True)
finally:
 c=guard.close();save("input-source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
