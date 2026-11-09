from pathlib import Path
import hashlib,json
p=Path(__file__).parent
cache=p/"__pycache__"
if cache.exists():
 assert cache.resolve().parent==p.resolve() and not cache.is_symlink()
 for f in cache.iterdir():
  assert f.is_file() and f.suffix==".pyc" and f.resolve().parent==cache.resolve()
  f.unlink()
 cache.rmdir()
def pin(f):
 raw=f.read_bytes();return {"path":str(f),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def put(n,v):
 with (p/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p/n)
e=json.loads((p/"pe-and-catalog-evidence.json").read_bytes())
add=[e["conhost"]["file_ref"],*e["new_direct_dependency_pins"]]
assert len(add)==6
summary=put("exact-resource-delta.json",{"schema":"researchos.desktop58-conhost-exact-static-delta.v1","base_counts":e["original_counts"],"additions_to_catalog_and_runtime":add,"static_images_add":[e["conhost"]["file_ref"]],"conditional_new_counts":{"resource_catalog_files":23874,"runtime_files":1303,"compiler_files":22138,"static_images":17},"conditions":"Counts apply only to the listed six new distinct paths; future source/metadata overlay path changes require recomputation.","api_set_contract_count":99,"explicit_system32_read_count":9,"recursive_pe_or_os_loaded_closure_proven":False,"actual_execution_authorized":False,"source_acceptance":False,"formal_increment":0})
files=[pin(f) for f in sorted(p.iterdir()) if f.is_file()]
m=put("manifest.json",{"schema":"researchos.public-review-manifest.v1","count":len(files),"entries":files,"self_excluded":True})
h=put("handoff.json",{"schema":"researchos.desktop58-conhost-resource-diagnostic-handoff.v1","decision":"RESOURCE_GAP_CONFIRMED_NEW_INPUT_REQUIRED","report_ref":pin(p/"report.json"),"evidence_ref":pin(p/"pe-and-catalog-evidence.json"),"resource_delta_ref":summary,"manifest_ref":m,"new_failure_count":0,"native_target_executed":False,"status":"STOPPED"})
print(json.dumps({"report_ref":pin(p/"report.json"),"manifest_ref":m,"handoff_ref":h,"resource_delta_ref":summary},ensure_ascii=False))

