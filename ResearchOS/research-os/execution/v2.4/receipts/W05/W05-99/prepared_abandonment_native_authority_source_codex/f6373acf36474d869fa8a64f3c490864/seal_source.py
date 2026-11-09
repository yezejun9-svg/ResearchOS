from pathlib import Path
import hashlib, json, difflib, re

R = Path("D:/作品集/ResearchOS/research-os")
B = R / "execution/v2.4/receipts/W05/W05-99"
N = B / "prepared_abandonment_native_authority_source_codex/f6373acf36474d869fa8a64f3c490864"
C = N / "candidate-root"
V = B / "prepared_run_abandonment_source_v3_codex/6e97da15b65146e5a6ef73a4804c9d12"
D = B / "prepared_abandonment_authority_migration_design_review_codex/762dfe06aa444fdc9e9c9f5a37f37c6b"
M = B / "prepared_abandonment_schema_upgrade_source_codex/e841e7fcddaa45ecb115f84df9827af2"
def pin(path):
    raw=path.read_bytes()
    return {"path":str(path),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
expected = [
    (D/"HDF.json","a2e8b723db1b65869748537b48433223851fb5f33b0fef58ce7f2604e99cb2c3",1864),
    (D/"MF.json","9f94602ee473c92775484881a188d552e5b669b50b54ce9ebe47dbc408177fa4",2066),
    (D/"review.json","1a28bbe4b250de303bd203eecf6bc331c1e088ba7db104db919f33d871c577c9",25023),
    (V/"HDF.json","1e9d2bd0f67ef4a12906181efaa780fe2889f7fb335b30576147f40f62eae138",9423),
    (V/"MF.json","cb9c9e0d8d1a30b35b5b22e6f3eb8b4ac949933e55f2e0798f8c9c8e8d1f9c28",17159),
    (R/"apps/control/main.go","9a519be38a1c09a819864073eedf0eaf9941c4c75f95ded0c3e89143012da9b1",12674),
]
inputs=[]
for path,sha,size in expected:
    actual=pin(path)
    if actual["sha256"]!=sha or actual["bytes"]!=size:
        write(N/"input-pin-failure.json",{"expected":{"path":str(path),"sha256":sha,"bytes":size},"actual":actual})
        raise SystemExit("INPUT_PIN_DRIFT")
    inputs.append(actual)
v3=json.loads((V/"MF.json").read_text(encoding="utf-8"))
verified=[]
for name,record in v3["members"].items():
    actual=pin(Path(record["path"]))
    if actual["sha256"]!=record["sha256"] or actual["bytes"]!=record["bytes"]:
        write(N/"input-pin-failure.json",{"member":name,"expected":record,"actual":actual})
        raise SystemExit("V3_MEMBER_DRIFT")
    verified.append(actual)
support=[]
for rel in ["AGENTS.md","adapters/runtime/data_root_windows.go","adapters/runtime/process_windows.go","ops/supervisor/control_authority_windows.go","ops/supervisor/release_drain_windows.go","ops/supervisor/control_fixture_windows.go","apps/control/drain_windows.go","internal/domain/backup_upgrade.go","internal/domain/contracts.go","internal/store/sqlite.go","go.mod"]:
    support.append(pin(R/rel))
source_files=sorted(p for p in C.rglob("*") if p.is_file())
source_refs={}
patches=[]
for path in source_files:
    relative=path.relative_to(C).as_posix()
    previous=V/"candidate-root"/relative if relative=="internal/domain/prepared_run_abandonment.go" else R/relative if relative=="apps/control/main.go" else None
    ref=pin(path)
    ref["previous_ref"]=pin(previous) if previous else None
    ref["base_kind"]="v3 Source" if relative=="internal/domain/prepared_run_abandonment.go" else "Main readonly" if previous else "NEW"
    source_refs[relative]=ref
    before=previous.read_text(encoding="utf-8").splitlines(keepends=True) if previous else []
    after=path.read_text(encoding="utf-8").splitlines(keepends=True)
    patches.extend(difflib.unified_diff(before,after,fromfile="a/"+relative,tofile="b/"+relative))
(N/"source-diff.patch").write_text("".join(patches),encoding="utf-8")
write(N/"base-refs.json",{"schema":"researchos.native-authority-base-refs.v1","inputs":inputs,"v3_manifest_members_verified":verified,"supporting_current_main":support,"source_refs":source_refs,"write_scope":str(N),"main_mutation":False,"v3_mutation":False,"existing_test_mutation":False})
texts={str(p.relative_to(C)):p.read_text(encoding="utf-8") for p in source_files}
testnames=[name for text in texts.values() for name in re.findall(r"func (Test[A-Za-z0-9_]+)\(",text)]
write(N/"source-static-evidence.json",{
    "schema":"researchos.native-authority-static-evidence.v1",
    "status":"STATIC_SOURCE_OBSERVATIONS_ONLY",
    "source_file_count":len(source_files),
    "test_files":[str(p.relative_to(C)) for p in source_files if p.name.endswith("_test.go")],
    "test_functions_authored":testnames,
    "go_gofmt_tests_native_model_sql_git_runs":0,
    "issuer_anchor_empty":'const enrolledIssuerPublicKeyHex = ""' in (C/"internal/recoveryauthority/types.go").read_text(encoding="utf-8"),
    "public_capability_fields":False,
    "source_overlay_requires":["v3 non-test core (or byte-identical v4 core)","independently accepted v4 tests, not copied here","separate schema-upgrade Source fixed domain entry"],
    "forbidden_targets_written":[],
    "tool_capture_gap":{"calls":2,"description":"First two read-only bootstrap exec calls were not put in functions.store. Original outputs are not reconstructed. Source hash verification below independently refreshes all authoritative inputs.","original_chunks":["c67fd6","3a04ef","fb6b30"],"captured_from_chunk":"1cdf7d","serialization_boundary":"original-source-construction-tool-io.json contains exact stored construction I/O through the seal script creation, excludes its own serialization and final sealing invocation to avoid self-reference."},
    "input_pin_drift":0,
    "negative_behavior_evidence":"Tests are authored only; no runtime PASS claimed.",
    "component_limit":"Signatures authorize exact current action with required CAS; historical witness does not claim past signatures, exact historical closure UTC or a pre-completed current state check."
})
members={str(p.relative_to(N)).replace("\\","/"):pin(p) for p in sorted(N.rglob("*")) if p.is_file() and p.name not in {"HDF.json","MF.json"}}
manifest={
    "schema":"researchos.prepared-native-authority-source-manifest.v1","sourceStatus":"EXECUTION_REPORTED","source_only":True,"formal":False,"execution_authority":False,"revision_root":str(N),"source_dir":str(C),
    "source_file_count":len(source_files),"member_count":len(members),"total_file_count_in_revision":len(members)+2,"members":members,"metadata_files_excluded":["HDF.json","MF.json"],"input_refs":inputs,"input_drift":0,
    "source_refs":source_refs,"goVerification":"NOT_RUN_BY_SOURCE_AUTHOR","productionAuthority":"UNPROVISIONED_DEFAULT_DENY",
    "composition_dependency":{"source_namespace":str(M),"candidate_root":str(M/"candidate-root"),"required_file":"internal/domain/backup_prepared_abandonment_upgrade_windows.go","required_symbol":"domain.ExecutePreparedAbandonmentSchemaUpgrade(context.Context,*sql.DB,recoveryauthority.MigrationToken,string,LocalUpgradeOptions) (Object,error)","manifest_ref":None,"status":"OTHER_WORKER_NOT_YET_SEALED; Root must resolve exact HDF/MF before complete-control build"}
}
write(N/"MF.json",manifest)
handoff={
    "schema":"researchos.prepared-native-authority-source-handoff.v1","sourceStatus":"EXECUTION_REPORTED","decision":"SOURCE_ONLY_UNPROVISIONED_ROOT_BUILD_NATIVE_TEST_REVIEW_REQUIRED","actor_id":"codex:/root/prepared_native_authority_impl",
    "model_selection":{"requested":"gpt-6-astra high","reason":"architecture/security/native authority; per project AGENTS","actual_runtime_model_independently_inspected":False},
    "formal":False,"execution_authority":False,"production_ready":False,"revision_root":str(N),"source_dir":str(C),"source_file_count":len(source_files),"manifest_member_count":len(members),"total_file_count_in_revision":len(members)+2,"manifest_ref":pin(N/"MF.json"),
    "base_refs_ref":pin(N/"base-refs.json"),"diff_ref":pin(N/"source-diff.patch"),"static_ref":pin(N/"source-static-evidence.json"),"contract_ref":pin(N/"contracts/native-authority.v1.json"),"tool_io_ref":pin(N/"original-source-construction-tool-io.json"),
    "input_refs":inputs,"v3previous_refs":[record for name,record in v3["members"].items() if name.startswith("candidate-root/")],
    "candidate_files":source_refs,"composition_dependency":manifest["composition_dependency"],
    "completed_source_components":["typed current HISTORICAL_EVIDENCE_ADOPTION preserving unknowns and lossless historical identities","raw historical Job/once/clock/stdstream and transitive source guard validation","unexported opaque default-zero-reject adoption Token and independent MigrationToken","Windows inherited purpose-separated HMAC pipe plus real OS peer/self PID/birth/SID and accepted image checks","source-pinned Ed25519 issuer verification, offline DPAPI provision and signed release/grant tools (unprovisioned)","new Root kill-on-close Job and lifetime-held file/image/source/raw guards; fresh DataRootLease","concrete private domain authority factory; current OWNER reauthenticated under original CAS","apps/control fixed pre-start maintenance composition; separate schema operation interface","focused source tests without v3/v4 test edits"],
    "remaining_gates":["Root Go formatting/build/tests including standalone enrollment, complete-control dependency composition, real native positive and negative flow","independent security/source review","real fresh issuer/root signer protected resources; newly reviewed Source anchor revision; accepted release binary/source pins and fresh operation grants","complete original raw evidence/backup/inventory lineage pins","separate schema24 migration acceptance/authorization before abandonment","current OWNER and original exact CAS/footprint conditions in an authorized execution"],
    "verification":{"source_inputs_raw_sha_and_size":"VERIFIED_BY_SEAL_SCRIPT","go_gofmt_native_tests_model_git_sql_services":"NOT_RUN","production_db_reads":0,"production_db_writes":0,"Main_writes":0,"old_source_writes":0,"private_execute_claim_reads":0,"vault_secret_reads":0},
    "capture_gap":json.loads((N/"source-static-evidence.json").read_text(encoding="utf-8"))["tool_capture_gap"],
    "STOP":"Source author stops here; this handoff is not acceptance, signing-key enrollment or production authority."
}
write(N/"HDF.json",handoff)
print(json.dumps({"HDF":pin(N/"HDF.json"),"MF":pin(N/"MF.json"),"source_file_count":len(source_files),"member_count":len(members),"total_file_count":len(members)+2,"test_functions_authored":testnames},ensure_ascii=False,indent=2))

