from pathlib import Path
import hashlib,json,stat,sys,ast
OUT=Path(__file__).parent
sys.path.insert(0,str(OUT))
from pe_reader import parse_pe
ROOT=Path("D:/作品集/ResearchOS/research-os")
REG=ROOT/"execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-b4d53db07f1e4ab8b9c0b37e291a6da5"
inputs=[]
def ref(path):
 raw=path.read_bytes();return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def read(path):
 raw=path.read_bytes();inputs.append({"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
 return json.loads(raw)
def load(r):
 raw=Path(r["path"]).read_bytes()
 assert len(raw)==r["bytes"] and hashlib.sha256(raw).hexdigest()==r["sha256"]
 inputs.append(r);return json.loads(raw)
def put(name,v):
 with (OUT/name).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return ref(OUT/name)
def key(path):return str(Path(path)).casefold()
def inspect(path,parse=True):
 for p in (path,*path.parents):
  s=p.lstat()
  assert not (s.st_file_attributes&0x400) and not p.is_symlink() and not p.is_junction()
 assert path.resolve(strict=True)==path
 before=ref(path);result={"file_ref":before,"canonical_path":str(path.resolve()),"actual_loaded_proven":False}
 if parse:result["pe"]=parse_pe(path.read_bytes())
 after=ref(path);assert before==after
 result["before_after_equal"]=True
 return result
scope=read(REG/"scope_registration.json")
catalog=load(scope["resource_catalog_ref"]);runtime=load(scope["runtime_resources_ref"]);compiler=load(scope["compiler_resources_ref"])
result=read(Path(scope["output_root"])/"result.json")
assert inputs[-1]["sha256"]=="6b18d5f2daa214b0d722d579e2b01f52dbd3a1493106ca66988a2508bfde0ed0"
debug=result["last_child_result"]["debug_capture"]
rejected=debug["rejected_load_facts"]
assert len(rejected)==1
fact=rejected[0]
actual_path=fact["path_from_actual_file_handle"]
assert actual_path.casefold().endswith("\\windows\\system32\\conhost.exe")
file=Path("C:/Windows/System32/conhost.exe")
pe=inspect(file)
assert pe["file_ref"]["sha256"]=="e449bce01f275cd08f3d4e64bb73b3b43ae845a0dbdb3e6131426e66537705e5"
assert pe["file_ref"]["bytes"]==1003520
rows={"resource_catalog":{key(r["path"]):r for r in catalog["files"]},"runtime_files":{key(r["path"]):r for r in runtime["files"]},"compiler_files":{key(r["path"]):r for r in compiler["files"]},"process_images":{key(r["path"]):r for r in catalog["images"]}}
def coverage(path):return {name:items.get(key(path)) for name,items in rows.items()}
edges=[]
for kind in ("imports","delay_imports"):
 for name in pe["pe"][kind]:
  assert Path(name).name==name and "/" not in name and "\\" not in name
  edge={"kind":kind,"import_name":name}
  if name.casefold().startswith(("api-ms-win-","ext-ms-win-")):
   edge["status"]="API_SET_CONTRACT_UNRESOLVED_STATIC_NAME_ONLY"
  else:
   p=Path("C:/Windows/System32")/name
   if p.is_file():
    info=inspect(p,parse=False);edge.update(status="EXPLICIT_SYSTEM32_FILE_READ_NOT_LOADER_RESOLUTION",file=info,coverage=coverage(p))
   else:edge["status"]="NO_EXPLICIT_SYSTEM32_FILE_UNKNOWN"
  edges.append(edge)
missing={}
for e in edges:
 if "file" in e:
  pin=e["file"]["file_ref"]
  if e["coverage"]["resource_catalog"] is None or e["coverage"]["runtime_files"] is None:missing[key(pin["path"])]=pin
ctor=ROOT/"execution/v2.4/receipts/W13/W13-03/desktop58_windows_resource_capture_source_revision_codex/3aff012b57924a41a233cb9e162cfc0d/construct_root_inputs.desktop58.wldp.proposed.py"
ct=ctor.read_bytes();assert hashlib.sha256(ct).hexdigest()=="9f64bd96b11ea017656e1262b0caaede1cf295ee5e75dd689751439a868834a7"
inputs.append(ref(ctor))
assert (REG/"construct_root_inputs.desktop58.wldp.py").read_bytes()==ct
conhost_coverage=coverage(file)
detail=put("pe-and-catalog-evidence.json",{"schema":"researchos.desktop58-conhost-pe-resource-diagnostic.v1","actual_rejected_fact":fact,"conhost":pe,"conhost_old_coverage":conhost_coverage,"direct_edges":edges,"new_direct_dependency_pins":list(missing.values()),"original_counts":{"resource_catalog":len(catalog["files"]),"runtime_files":len(runtime["files"]),"compiler_files":len(compiler["files"]),"process_images":len(catalog["images"])},"all_input_refs":inputs,"static_only":True,"os_probe_executed":False,"candidate_executed":False})
report=put("report.json",{"schema":"researchos.desktop58-conhost-resource-independent-diagnostic.v1","reviewer":"codex:/root/w05_merge_review","decision":"RESOURCE_GAP_CONFIRMED_NEW_INPUT_REQUIRED","evidence_ref":detail,"actual_rejected_file_ref":pe["file_ref"],"actual_rejected_generation":fact["process_generation"],"actual_scope_ref":inputs[0],"constructor_ref":ref(ctor),"resource_change":{"resource_catalog_files":"Add conhost.exe and explicitly resolved direct/delay dependency candidates absent from existing catalog, using fresh exact before/after pins.","runtime_files":"Add conhost.exe and missing dependency candidates to constructor runtime overlay; its hardcoded premetadata identity count 1283 must change with the exact reviewed addition list.","process_images":"Add conhost.exe to Root q.static_image_refs and catalog.images. DLLs belong in files/runtime only. Adding only images passes neither helper's module check nor full runtime declaration.","compiler_files":"No compiler toolchain-tree change required: this is an explicit OS runtime overlay, not a Go compiler-source member.","constructor_source":"Existing wldp-specific required keys and exact-one report/count cannot consume arbitrary conhost additions. Use a new narrow constructor/source proposal with explicit reviewed conhost ref and dependency evidence; never overwrite old q/catalog/scope."},"caps":{"old_static_images":16,"new_static_images_if_only_conhost_exe":17,"controller_static_bound":60,"helper_total_image_bound":64,"current_generated_artifact_images":3,"declared_future_aliases":20,"maximum_declared_total_after_addition":40,"image_cap_unchanged":True,"process_cap":scope["process_cap"],"active_job_processes":scope["active_job_processes"],"actual_failed_generations":805,"scope_process_cap_not_exceeded_by_count":805<=scope["process_cap"],"top_native_HTTP_wall_budgets":"unchanged; static resource addition is not authorization to expand calls/time/process limits"},"limitations":["PE import names are static references, not actual loaded DLL proof or full loader resolution.","API-set contracts, forwarded exports and dynamic LoadLibrary targets remain UNKNOWN; this diagnostic performs no recursive Windows tree scan.","The prior run remains failed/capture incomplete. No posthoc union or retry of that exact input is qualified.","A new Root scope/CAS/unique grant and independent review are required before another once-only execution."],"new_failure_count":0,"source_acceptance":False,"formal_increment":0})
print(json.dumps({"report_ref":report,"evidence_ref":detail,"imports":len(pe["pe"]["imports"]),"delay_imports":len(pe["pe"]["delay_imports"]),"named_system32":[e["import_name"] for e in edges if "file" in e],"missing_direct_files":list(missing.values()),"conhost_old_membership":{k:v is not None for k,v in conhost_coverage.items()}},ensure_ascii=False))

