from pathlib import Path
import hashlib,json,difflib,re
R=Path("D:/作品集/ResearchOS/research-os")
B=R/"execution/v2.4/receipts/W05/W05-99"
N=B/"prepared_abandonment_native_authority_source_codex/b1599aaf259c435db5a0a5313ab0ea65"
P=B/"prepared_abandonment_native_authority_source_codex/f6373acf36474d869fa8a64f3c490864"
M=B/"prepared_abandonment_schema_upgrade_source_codex/e841e7fcddaa45ecb115f84df9827af2"
C=N/"candidate-root"
def pin(p):
    raw=p.read_bytes()
    return {"path":str(p),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def save(p,v):
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
provision=B/"integration_codex/recoveryauthority-key-provision-root-9b42b8e7072a40b1"
oldtest=B/"integration_codex/native-authority-unprovisioned-component-root-cb0935d7bf444f4f/validation.closed.json"
expected=[
(provision/"key-provision.closed.json","873953117beb0f5730674d130e49c18502b6e5821ea37f5658af3c80f1e7d5fe",2375),
(provision/"original-tool-io.json","007d9c9f615c115cbabd622cc60a945fb63ac7a5bd0ccdace35859ecc2bb3ada",1715),
(oldtest,"1dbcd356c92c5bcc5b58a4726a1b7b7d5855c31ea8226bdc037133fd57101061",4443)]
fresh=[]
for path,sha,size in expected:
    actual=pin(path)
    if actual["sha256"]!=sha or actual["bytes"]!=size:
        save(N/"seal-input-drift.json",{"expected":{"path":str(path),"sha256":sha,"bytes":size},"actual":actual})
        raise SystemExit("PUBLIC_PROOF_PIN_DRIFT")
    fresh.append(actual)
# Only public proof JSON is read. Never follow private_resource_ref.
proof=json.loads((provision/"key-provision.closed.json").read_text(encoding="utf-8"))
issuer=proof["keys"]["issuer"]["public_key_hex"]
if issuer!="936929c4ad26612ee75cc4ad5a6dc2d8c0f898bf974bb9c01e8e5140ee207bdf":
    raise SystemExit("PUBLIC_KEY_DIFFERS_FROM_ROOT_AUTHORIZATION")
if ('const enrolledIssuerPublicKeyHex = "'+issuer+'"') not in (C/"internal/recoveryauthority/types.go").read_text(encoding="utf-8"):
    raise SystemExit("SOURCE_PUBLIC_KEY_DIFFERS")
old=json.loads((P/"MF.json").read_text(encoding="utf-8"))
for name,ref in old["members"].items():
    actual=pin(Path(ref["path"]))
    if actual["sha256"]!=ref["sha256"] or actual["bytes"]!=ref["bytes"]:
        raise SystemExit("OLD_SOURCE_MUTATED")
refs={}; changed=[]; patch=[]
files=sorted(p for p in C.rglob("*") if p.is_file())
if len(files)!=20:raise SystemExit("SOURCE_COUNT_NOT_20")
for path in files:
    rel=path.relative_to(C).as_posix()
    previous=Path(old["source_refs"][rel]["path"])
    ref=pin(path); ref["previous_ref"]=pin(previous); refs[rel]=ref
    if path.read_bytes()!=previous.read_bytes():
        changed.append(rel)
        patch.extend(difflib.unified_diff(previous.read_text(encoding="utf-8").splitlines(keepends=True),path.read_text(encoding="utf-8").splitlines(keepends=True),fromfile="a/"+rel,tofile="b/"+rel))
wanted={"internal/recoveryauthority/native_windows.go","internal/recoveryauthority/native_windows_test.go","internal/recoveryauthority/types.go"}
if set(changed)!=wanted:raise SystemExit("UNEXPECTED_SOURCE_DELTA")
(N/"source-diff.patch").write_text("".join(patch),encoding="utf-8")
base=json.loads((N/"input-refs.json").read_text(encoding="utf-8"))
base["immutable_cp352_snapshot_ref"]=pin(N/"checkpoint.CP352.raw.json")
if base["immutable_cp352_snapshot_ref"]["sha256"]!="e128ec5e0a7aa8b7dad605fc3cd8889dc09f72d7b2ce0d1a864543c53328830d" or base["immutable_cp352_snapshot_ref"]["bytes"]!=3971419:
    raise SystemExit("IMMUTABLE_CP352_SNAPSHOT_DRIFT")
base["public_proof_refs"]=fresh
base["checkpoint_scope"]="CP352 hash observed and verified at constructor entry; canonical checkpoint is not reread or rewritten by this Source."
base["current_source_refs"]=refs
save(N/"base-refs.json",base)
tests=[name for p in files for name in re.findall(r"func (Test[A-Za-z0-9_]+)\(",p.read_text(encoding="utf-8"))]
static={
"schema":"researchos.native-authority-source-static.v2",
"source_only":True,
"source_count":20,"changed_source_count":3,"unchanged_source_count":17,
"changed_source_files":changed,
"actual_embed_inventory_ref":pin(N/"actual-embed-inventory.json"),
"actual_embed_directives_inspected":9,
"public_issuer_anchor":issuer,
"private_resource_refs_followed":False,
"test_functions_authored":tests,
"new_test_functions":["TestAuthoritySourceInventoryRequiresActualEmbeddedMarkdown","TestAuthoritySourceInventoryConservativelyRequiresAllEmbedCandidates"],
"new_tests_executed":False,
"old_24_node_validation":"Prior unprovisioned leaf only; not current-source proof.",
"go_gofmt_native_sql_git_provider_runs":0,
"failure_origin_refs":[pin(N/"failure-origin.766.json")],
"input_hash_verification":"Original source members and designated public provisioning proofs match; CP352 verified at constructor entry.",
"compiler_closure_claim":False,
"required_root_gate":"Fresh trusted build go list -deps -json covering actual EmbedFiles and compiled inputs plus module/toolchain provenance; listed local trees and optional vendor are conservative all-regular only.",
"tool_io_scope":"Complete current-turn stored reads/construction/correction input-output before log serialization. Failed JS parse input/result retained verbatim as failure766. Log serialization and self-pinning seal invocation excluded to avoid recursion."
}
save(N/"source-static-evidence.json",static)
dependency={
"source_namespace":str(M),"HDF_ref":pin(M/"HDF.json"),"MF_ref":pin(M/"MF.json"),
"required_symbol":"domain.ExecutePreparedAbandonmentSchemaUpgrade(context.Context,*sql.DB,recoveryauthority.MigrationToken,string,LocalUpgradeOptions) (Object,error)",
"status":"SEALED_SOURCE_DEPENDENCY; full control integration and fresh build still required"
}
members={p.relative_to(N).as_posix():pin(p) for p in sorted(N.rglob("*")) if p.is_file() and p.name not in {"HDF.json","MF.json"}}
mf={"schema":"researchos.prepared-native-authority-source-manifest.v2","sourceStatus":"EXECUTION_REPORTED","source_only":True,"formal":False,"execution_authority":False,"revision_root":str(N),"source_dir":str(C),"source_file_count":20,"member_count":len(members),"total_file_count_in_revision":len(members)+2,"members":members,"metadata_files_excluded":["HDF.json","MF.json"],"previous_source_HDF":pin(P/"HDF.json"),"previous_source_MF":pin(P/"MF.json"),"source_refs":refs,"input_refs":base["verified_inputs"]+fresh,"composition_dependency":dependency,"source_public_anchor":"ROOT_PROVISIONED_PUBLIC_KEY_PINNED_PENDING_ACCEPTANCE","goVerification":"NOT_RUN_BY_SOURCE_AUTHOR"}
save(N/"MF.json",mf)
hdf={"schema":"researchos.prepared-native-authority-source-handoff.v2","sourceStatus":"EXECUTION_REPORTED","decision":"SOURCE_ONLY_REAL_PUBLIC_ANCHOR_AND_CONSERVATIVE_INVENTORY_FIX_PENDING_FRESH_ROOT_VERIFICATION","actor_id":"codex:/root/prepared_native_authority_impl","formal":False,"execution_authority":False,"production_ready":False,"revision_root":str(N),"source_dir":str(C),"source_file_count":20,"changed_source_count":3,"unchanged_source_count":17,"manifest_member_count":len(members),"total_file_count_in_revision":len(members)+2,"manifest_ref":pin(N/"MF.json"),"source_refs":refs,"previous_source_HDF":pin(P/"HDF.json"),"previous_source_MF":pin(P/"MF.json"),"base_refs_ref":pin(N/"base-refs.json"),"diff_ref":pin(N/"source-diff.patch"),"static_ref":pin(N/"source-static-evidence.json"),"current_contract_ref":pin(N/"contracts/native-authority.v2.json"),"previous_contract_retained_only_as_lineage":pin(N/"contracts/native-authority.v1.json"),"actual_embed_inventory_ref":pin(N/"actual-embed-inventory.json"),"tool_io_ref":pin(N/"original-source-construction-tool-io.json"),"failure_origin_refs":[pin(N/"failure-origin.766.json")],"public_proof_refs":fresh,"issuer_public_key_hex":issuer,"root_adoption_public_key_requires_signed_release_enrollment":proof["keys"]["root-adoption"]["public_key_hex"],"composition_dependency":dependency,"completed_source_delta":["All regular files under seven fixed product trees required, including actual embedded markdown and unknown future suffixes/hidden/test-named inputs; links and special files reject.","Optional vendor subtree and present go.work/go.work.sum also required.","Actual embedded project rules omission/read-handle retention test plus six additional omission cases authored.","Root-authorized real issuer public key pinned; no private key file followed or generated; all other authority mechanisms unchanged."],"remaining_gates":["Root fresh format/build/test including actual go list -deps -json compiled/embed closure and external module/toolchain verification.","Fresh independent security/native review of changed source with real keys; old24nodes not current proof.","Complete native/control plus sealed migration integration.","Separately signed accepted release and distinct bounded grants/current OWNER/native lease/exact original-state gates before any production action."],"verification":{"Source_author_Go_gofmt_native_SQL_Git_provider_runs":0,"private_key_reads":0,"Main_canonical_oldSource_writes":0,"prior_24node_result_current_applicability":False},"STOP":"Sealed source-only handoff; no execution or self-acceptance authority."}
save(N/"HDF.json",hdf)
print(json.dumps({"HDF":pin(N/"HDF.json"),"MF":pin(N/"MF.json"),"source_file_count":20,"changed":changed,"member_count":len(members),"total_file_count":len(members)+2,"new_tests_run":False,"failure766_preserved":True},ensure_ascii=True))

