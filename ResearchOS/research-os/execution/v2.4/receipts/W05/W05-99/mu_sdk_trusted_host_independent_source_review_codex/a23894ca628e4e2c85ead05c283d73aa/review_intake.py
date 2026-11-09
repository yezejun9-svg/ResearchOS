from pathlib import Path
import hashlib, json
ROOT=Path("D:/作品集/ResearchOS/research-os")
OUT=Path(__file__).resolve().parent
SOURCE=ROOT/"execution/v2.4/receipts/W05/W05-99/mu_sdk_trusted_qualification_host_source_codex/991a41da6cb146d9a5fae91c438f6d07"
def meta(p,raw):
 return {"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def write(name,obj):
 (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
manifest_raw=(SOURCE/"manifest.json").read_bytes()
manifest=json.loads(manifest_raw)
refs=manifest["source_files"]+manifest["current_source_evidence"]
additional=["internal/domain/contracts.go","internal/domain/store.go","internal/domain/orchestration.go","internal/domain/runtime_dispatch.go","internal/domain/acceptance.go","internal/domain/runtime_model_verification.go","internal/host/runtime_tools_windows.go","adapters/runtime/bridge_windows.go","go.mod","execution/v2.4/receipts/W05/W05-99/mu_sdk_job_observer_revision_v2_codex/099b315944fa42e393af8d9190e7c14e/mu_sdk_job_observer.v2.proposed.py","execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v8_source_codex/8251b1ed21754f7cbd6c2f8e7ff574eb/mu_sdk_trial.v8.proposed.py"]
items=[]
for ref in refs:
 p=Path(ref["path"]);raw=p.read_bytes();actual=meta(p,raw)
 actual["author_pin_matches"]=actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"]
 assert actual["author_pin_matches"],str(p)
 relative=p.relative_to(ROOT);dest=OUT/"snapshots"/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 actual["snapshot"]=dest.relative_to(OUT).as_posix();items.append(actual)
for rel in additional:
 p=ROOT/rel;raw=p.read_bytes();dest=OUT/"snapshots"/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 item=meta(p,raw);item["snapshot"]=dest.relative_to(OUT).as_posix();items.append(item)
dest=OUT/"snapshots"/(SOURCE/"manifest.json").relative_to(ROOT);dest.write_bytes(manifest_raw)
items.append(dict(meta(SOURCE/"manifest.json",manifest_raw),snapshot=dest.relative_to(OUT).as_posix()))
write("intake.json",{"schema":"researchos.independent-host-source-intake.v1","status":"PASS_PIN_IDENTITY_ONLY","author_refs_checked":len(refs),"additional_refs":len(additional),"source_manifest":meta(SOURCE/"manifest.json",manifest_raw),"files":items,"executed_candidate":False,"go_compiler":"NOT_RUN_BY_REVIEWER","native_host":"NOT_RUN_BY_REVIEWER","provider":"NOT_RUN_BY_REVIEWER"})
# Static evidence controls inspect text only; do not import/execute candidate code.
main=(SOURCE/"main.go").read_text(encoding="utf-8")
prepare=(SOURCE/"prepare.go").read_text(encoding="utf-8")
execute=(SOURCE/"execute.go").read_text(encoding="utf-8")
observer=(ROOT/additional[-2]).read_text(encoding="utf-8")
v8=(ROOT/additional[-1]).read_text(encoding="utf-8")
checks={
"go_pin_checked_then_path_reopened":execute.index("verifyPin(p)") < execute.index("verifyGOEvidence(a,v)") and "raw,err:=os.ReadFile(p.Path)" in execute and "return domain.Decode(raw)" in execute,
"profile_reopened_after_seed_hash":"exactDigest(v.p,v.h)" in main and "os.ReadFile(s.ProfileFile)" in prepare and "os.ReadFile(s.NodeExecutable)" in prepare and "os.ReadFile(s.BundleFile)" in prepare,
"workspace_constraints_disjoint":"[]string{s.RepoRoot,s.DataRoot,s.ReadOnlyVaultDir}" in main and "workspace.is_relative_to(data)" in observer and 'data.is_relative_to(repo / ".local")' in observer,
"policy_values_disagree":'policy["max_calls"]=2;policy["max_read_bytes"]=65536' in prepare and 'policy.get("max_calls") == 1' in v8 and 'policy.get("max_read_bytes") == 4096' in v8,
"prepare_state_check_outside_lease":prepare.index("os.Stat(statePath(s))") < prepare.index("openEnvironment(ctx,s)"),
}
assert all(checks.values())
write("static-evidence-controls.json",{"status":"PASS_STATIC_EVIDENCE_LOCATIONS_ONLY","checks":checks,"meaning":"Confirms cited text only; scheduling and runtime consequences are source reasoning, not executed reproduction."})
print(json.dumps({"status":"PASS_METADATA_AND_STATIC_LOCATIONS","author_refs":len(refs),"additional_refs":len(additional),"controls":len(checks)}))

