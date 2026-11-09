"""Freeze C-only date patch; no runtime/SDK/GUI/model invocation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, difflib
ROOT=Path(__file__).resolve().parent
OLD=ROOT.with_name("product-v1-real-electron-harness-prepare-revision-03")
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def row(p): return {"path":p.relative_to(ROOT).as_posix(),"sha256":digest(p),"bytes":p.stat().st_size}
def write(name,data):
    with (ROOT/name).open("x",encoding="utf-8",newline="\n") as out:
        json.dump(data,out,ensure_ascii=False,indent=2); out.write("\n")
for name in ["FROZEN.json","MANIFEST.json","ARCHIVE_FILES.json"]:
    if (ROOT/name).exists(): raise SystemExit("ALREADY_FROZEN")
baseline=json.loads((ROOT/"BASELINE.json").read_text(encoding="utf-8"))
if digest(OLD/"FROZEN.json")!=baseline["freeze3_sha256"]: raise SystemExit("OLD_FREEZE_DRIFT")
for item in baseline["baseline_files"]:
    if digest(OLD/item["path"])!=item["sha256"]: raise SystemExit("OLD_BASELINE_DRIFT:"+item["path"])
for name in ["real-electron-flow.mjs","preparation-purechecks.mjs","path-evidence-purechecks.ps1","ui8-selector-purechecks.mjs","SELECTOR_BINDING.json"]:
    if digest(ROOT/name)!=digest(OLD/name): raise SystemExit("NON_DATE_CODE_CHANGE:"+name)
old=(OLD/"choose-owned-folder.ps1").read_text(encoding="utf-8")
new=(ROOT/"choose-owned-folder.ps1").read_text(encoding="utf-8")
start=new.index("function Convert-NativeDeadlineUtc(")
end=new.index("function Convert-UiaAbsolutePath(",start)
reverse=new[:start]+new[end:]
reverse=reverse.replace("# These functions are pure string/evidence predicates.","# These three functions are pure string/evidence predicates.")
reverse=reverse.replace("$identity = Get-Content -LiteralPath $identityFile -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String",
                        "$identity = Get-Content -LiteralPath $identityFile -Raw -Encoding UTF8 | ConvertFrom-Json")
reverse=reverse.replace("$actionDeadline = Convert-NativeDeadlineUtc $identity.action_deadline_utc",
                        "$actionDeadline = [DateTimeOffset]::Parse($identity.action_deadline_utc).UtcDateTime")
if reverse.encode("utf-8")!=(OLD/"choose-owned-folder.ps1").read_bytes():
    raise SystemExit("DATE_PATCH_REVERSAL_NOT_BYTE_EXACT_STOP")
(ROOT/"helper.diff").write_text("".join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile="freeze03/choose-owned-folder.ps1",tofile="freeze04/choose-owned-folder.ps1")),encoding="utf-8")
scope_path=ROOT/"scope.template.json"
scope=json.loads(scope_path.read_text(encoding="utf-8"))
if scope["status"]!="NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_AND_SUPERVISION": raise SystemExit("EXECUTION_SCOPE_NOT_EDITABLE")
scope["harness"]={"runner_sha256":digest(ROOT/"real-electron-flow.mjs"),"folder_helper_sha256":digest(ROOT/"choose-owned-folder.ps1")}
scope["playwright"]["inventory_path"]=str(ROOT/"SDK_INVENTORY.json")
scope["native_picker"]["deadline_wire"]="STRICT_ORIGINAL_UTC_STRING_YYYY_MM_DD_THH_MM_SS_FFF_Z_INVARIANT"
scope_path.write_text(json.dumps(scope,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
files=[row(p) for p in sorted(ROOT.rglob("*")) if p.is_file()]
write("MANIFEST.json",{"schema":"researchos.real-electron-controller.revision04-manifest/1","files":files})
write("FROZEN.json",{"schema":"researchos.real-electron-controller.revision04-freeze/1","revision":4,
    "status":"DATE_SOURCE_FIX_PREPARED_PENDING_INDEPENDENT_REVIEW_NOT_RUN",
    "frozen_at":datetime.now(timezone.utc).isoformat(),"construction_frozen":True,"source_modification_permitted":False,
    "manifest_sha256":digest(ROOT/"MANIFEST.json"),"scope_sha256":digest(scope_path),
    "source_sha256":{n:digest(ROOT/n) for n in ["real-electron-flow.mjs","choose-owned-folder.ps1"]},
    "baseline_sha256":digest(ROOT/"BASELINE.json"),"freeze3_unchanged":True,
    "runner_same_as_freeze3":True,"reverse_only_date_patch_equals_freeze3_bytes":True,
    "new_checks":{"date_pure_passed":36,"actual_timezone_reproduction_exit":0,"helper_ast_in_date_test_exit":0},
    "old_path_owner_payment_cancel_selector_checks_reused_not_recounted":True,
    "helper_entrypoint":0,"sdk_imports":0,"add_type":0,"uia":0,"gui":0,"native":0,"model":0,
    "formal_increment":0,"product_increment":0,"counter_reset":False,
    "runtime_admission":"NOT_GRANTED_BY_AUTHOR",
    "pending":["Independent narrow date re-review","Fresh Root real execution scope and existing outer exact Job","Real GUI/UIA/model retry NOT_RUN"]})
archive=[row(p) for p in sorted(ROOT.rglob("*")) if p.is_file()]
write("ARCHIVE_FILES.json",{"root":str(ROOT),"files":archive,"file_count":len(archive),
    "total_bytes":sum(p["bytes"] for p in archive),"excluded":["none; no SDK copy/cache/dist"]})
print(json.dumps({"status":"FROZEN_REVISION04_DATE_ONLY_NOT_RUN","freeze_sha256":digest(ROOT/"FROZEN.json"),
    "manifest_sha256":digest(ROOT/"MANIFEST.json"),"archive_sha256":digest(ROOT/"ARCHIVE_FILES.json"),
    "scope_sha256":digest(scope_path),"source_sha256":{n:digest(ROOT/n) for n in ["real-electron-flow.mjs","choose-owned-folder.ps1"]},
    "files":len(archive),"bytes":sum(p["bytes"] for p in archive)}))
