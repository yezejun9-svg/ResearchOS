"""Freeze only this C revision; no product/runtime execution or D writes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parent
OLD = ROOT.with_name("product-v1-real-electron-harness-prepare")
def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()
def row(file):
    return {"path": file.relative_to(ROOT).as_posix(), "sha256": digest(file), "bytes": file.stat().st_size}
def write(name, data):
    with (ROOT/name).open("x", encoding="utf-8", newline="\n") as target:
        json.dump(data,target,ensure_ascii=False,indent=2)
        target.write("\n")

for name in ["FROZEN.json","MANIFEST.json","ARCHIVE_FILES.json"]:
    if (ROOT/name).exists():
        raise SystemExit("ALREADY_FROZEN_DO_NOT_REWRITE")
baseline = json.loads((ROOT/"BASELINE.json").read_text(encoding="utf-8"))
if digest(OLD/"FROZEN.json") != baseline["freeze1_sha256"] or digest(OLD/"MANIFEST.json") != baseline["freeze1_manifest_sha256"]:
    raise SystemExit("OLD_FREEZE_DRIFT")
for item in baseline["baseline_files"]:
    if digest(OLD/item["path"]) != item["sha256"]:
        raise SystemExit("OLD_SOURCE_DRIFT:"+item["path"])
scope_file = ROOT/"scope.template.json"
scope = json.loads(scope_file.read_text(encoding="utf-8"))
if scope["status"] != "NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_AND_SUPERVISION":
    raise SystemExit("DO_NOT_MODIFY_EXECUTION_SCOPE")
scope["windows"]["powershell"] = "C:/Users/yqyyds/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe"
scope["windows"]["powershell_sha256"] = "362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139"
scope["windows"]["shell_policy"] = "NORMAL_EXISTING_POLICY_NO_OVERRIDE"
scope["playwright"]["inventory_path"] = str(ROOT/"SDK_INVENTORY.json")
scope["harness"] = {"runner_sha256":digest(ROOT/"real-electron-flow.mjs"),
                    "folder_helper_sha256":digest(ROOT/"choose-owned-folder.ps1")}
scope["native_picker"] = {"automation":"REAL_OWNED_SHELL_UIA_ONLY","runtime_verified":False,
    "operator_fallback":False,"final_path_proof":"AT_LEAST_ONE_RELIABLE_ABSOLUTE_VALUE_ALL_ABSOLUTE_VALUES_CONSISTENT",
    "failure_cleanup":"REVALIDATE_EXACT_OWNED_HWND_THEN_NORMAL_IDCANCEL_ELSE_ROOT_JOB_UNKNOWN"}
scope["payment_policy"] = {"required_actual_host_authentication":{"state":"LOGGED_IN","kind":"chatgpt"},
    "check_before_submission":"FRESH_HOST_CAPABILITIES_NOT_SCOPE_ASSERTION",
    "api_key_other_unprobed":"BLOCK_NO_LOGIN_OR_PAID_FALLBACK"}
scope_file.write_text(json.dumps(scope,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
files = [row(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
write("MANIFEST.json",{"schema":"researchos.real-electron-controller.revision02-manifest/1","files":files})
write("FROZEN.json",{"schema":"researchos.real-electron-controller.revision02-freeze/1",
    "revision":2,"status":"PREPARED_NOT_RUN_PENDING_INDEPENDENT_REVIEW",
    "frozen_at":datetime.now(timezone.utc).isoformat(),
    "construction_frozen":True,"source_modification_permitted":False,
    "manifest_sha256":digest(ROOT/"MANIFEST.json"),"scope_sha256":digest(scope_file),
    "source_sha256":{name:digest(ROOT/name) for name in ["real-electron-flow.mjs","choose-owned-folder.ps1"]},
    "pure_test_source_sha256":{name:digest(ROOT/name) for name in ["preparation-purechecks.mjs","path-evidence-purechecks.ps1"]},
    "baseline_sha256":digest(ROOT/"BASELINE.json"),"freeze1_unchanged":True,
    "prior_review_sha256":baseline["review_sha256"],"counter_reset":False,
    "checks":{"node_pure":21,"path_pure":21,"node_syntax_exit":0,"helper_ast_in_normal_pwsh7":"0"},
    "runner_invocations":0,"helper_body":0,"sdk_imports":0,"add_type":0,"uia":0,"gui":0,"native":0,"model":0,
    "formal_increment":0,"product_increment":0,
    "runtime_admission":"NOT_GRANTED_BY_AUTHOR",
    "pending":["Independent re-review of revised safety source",
       "Root final integrated source/bundle/new execution scope/external exact Job",
       "Real UIA absolute-path availability and actual GUI/model/cleanup remain NOT_RUN"]})
archive = [row(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
write("ARCHIVE_FILES.json",{"root":str(ROOT),"files":archive,"file_count":len(archive),
    "total_bytes":sum(p["bytes"] for p in archive),"excluded":["none; no SDK copy/cache/builddist"]})
print(json.dumps({"status":"FROZEN_REVISION_02_NOT_RUN","freeze_sha256":digest(ROOT/"FROZEN.json"),
    "manifest_sha256":digest(ROOT/"MANIFEST.json"),"archive_sha256":digest(ROOT/"ARCHIVE_FILES.json"),
    "scope_sha256":digest(scope_file),"source_sha256":{n:digest(ROOT/n) for n in ["real-electron-flow.mjs","choose-owned-folder.ps1"]},
    "files":len(archive),"bytes":sum(p["bytes"] for p in archive)}))
