"""Freeze narrow C UI8-selector revision; do not launch/import any runtime."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, difflib
ROOT = Path(__file__).resolve().parent
OLD = ROOT.with_name("product-v1-real-electron-harness-prepare-revision-02")
def digest(file): return hashlib.sha256(file.read_bytes()).hexdigest()
def row(file): return {"path":file.relative_to(ROOT).as_posix(),"sha256":digest(file),"bytes":file.stat().st_size}
def write(name,data):
    with (ROOT/name).open("x",encoding="utf-8",newline="\n") as target:
        json.dump(data,target,ensure_ascii=False,indent=2); target.write("\n")
for name in ["FROZEN.json","MANIFEST.json","ARCHIVE_FILES.json"]:
    if (ROOT/name).exists(): raise SystemExit("ALREADY_FROZEN")
baseline=json.loads((ROOT/"BASELINE.json").read_text(encoding="utf-8"))
if digest(OLD/"FROZEN.json")!=baseline["freeze2_sha256"]: raise SystemExit("OLD_FREEZE_DRIFT")
for item in baseline["baseline_files"]:
    if digest(OLD/item["path"])!=item["sha256"]: raise SystemExit("OLD_SOURCE_DRIFT")
for name in ["choose-owned-folder.ps1","preparation-purechecks.mjs","path-evidence-purechecks.ps1"]:
    if digest(ROOT/name)!=digest(OLD/name): raise SystemExit("NOT_UI_ONLY_REVISION:"+name)
old=(OLD/"real-electron-flow.mjs").read_text(encoding="utf-8")
new=(ROOT/"real-electron-flow.mjs").read_text(encoding="utf-8")
for start,end in [("const requireThat = ","const inside = "),("function safeText(","function inventory(")]:
    if old[old.index(start):old.index(end,old.index(start))]!=new[new.index(start):new.index(end,new.index(start))]:
        raise SystemExit("PURE_HELPER_SOURCE_CHANGED")
(ROOT/"runner.diff").write_text("".join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile="freeze2/real-electron-flow.mjs",tofile="freeze3/real-electron-flow.mjs")),encoding="utf-8")
scope_file=ROOT/"scope.template.json"
scope=json.loads(scope_file.read_text(encoding="utf-8"))
if scope["status"]!="NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_AND_SUPERVISION": raise SystemExit("EXECUTION_SCOPE_NOT_EDITABLE")
ui={"apps/web/src/workbench.jsx":"e0f4c6db45757b0f506b950fb5eb004de7358f1667cbaf876ab5addee7eadd19",
    "apps/web/src/screens.jsx":"d7405a7bf396b97907dca9ac4bf9182295fba5251b9766e276a67f9ef6b573be"}
pins={item["path"]:item["sha256"] for item in scope["source"]["pins"]}
pins.update(ui)
scope["source"]["pins"]=[{"path":name,"sha256":value} for name,value in pins.items()]
scope["source"]["pin_status"]="UI8_SELECTOR_TARGET_UPDATED_OTHER_FIELDS_REQUIRE_ROOT_FINAL_INTEGRATED_REBIND"
scope["selector_binding"]={"source_head":baseline["source_head"],"bundle_manifest_sha256":baseline["bundle_manifest_sha256"],"source_sha256":ui}
scope["harness"]={"runner_sha256":digest(ROOT/"real-electron-flow.mjs"),"folder_helper_sha256":digest(ROOT/"choose-owned-folder.ps1")}
scope["playwright"]["inventory_path"]=str(ROOT/"SDK_INVENTORY.json")
scope_file.write_text(json.dumps(scope,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
files=[row(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
write("MANIFEST.json",{"schema":"researchos.real-electron-controller.revision03-manifest/1","files":files})
write("FROZEN.json",{"schema":"researchos.real-electron-controller.revision03-freeze/1","revision":3,
    "status":"PREPARED_UI8_SELECTOR_NOT_RUN_PENDING_INDEPENDENT_REVIEW","frozen_at":datetime.now(timezone.utc).isoformat(),
    "construction_frozen":True,"source_modification_permitted":False,"manifest_sha256":digest(ROOT/"MANIFEST.json"),
    "scope_sha256":digest(scope_file),"source_sha256":{n:digest(ROOT/n) for n in ["real-electron-flow.mjs","choose-owned-folder.ps1"]},
    "baseline_sha256":digest(ROOT/"BASELINE.json"),"selector_binding_sha256":digest(ROOT/"SELECTOR_BINDING.json"),
    "helper_same_as_freeze2":True,"prior_pure_functions_byte_identical":True,"prior_pure_results_not_recounted":True,
    "new_checks":{"ui8_selector_fragment_pure":6,"node_syntax_exit":0},
    "source_selector_target":baseline["source_head"],"bundle_selector_target":baseline["bundle_manifest_sha256"],
    "runner_invocations":0,"sdk_imports":0,"helper_body":0,"add_type":0,"uia":0,"gui":0,"native":0,"model":0,
    "formal_increment":0,"product_increment":0,"counter_reset":False,
    "runtime_admission":"NOT_GRANTED_BY_AUTHOR","pending":["Independent revision03 review","Root final actual source/bundle/fresh execution scope and outer exact Job","Real UIA/GUI/Codex remain NOT_RUN"]})
archive=[row(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
write("ARCHIVE_FILES.json",{"root":str(ROOT),"files":archive,"file_count":len(archive),
    "total_bytes":sum(r["bytes"] for r in archive),"excluded":["none; no SDK copy/cache/dist"]})
print(json.dumps({"status":"FROZEN_REVISION03_NOT_RUN","freeze_sha256":digest(ROOT/"FROZEN.json"),
    "manifest_sha256":digest(ROOT/"MANIFEST.json"),"archive_sha256":digest(ROOT/"ARCHIVE_FILES.json"),
    "scope_sha256":digest(scope_file),"source_sha256":{n:digest(ROOT/n) for n in ["real-electron-flow.mjs","choose-owned-folder.ps1"]},
    "files":len(archive),"bytes":sum(p["bytes"] for p in archive)}))
