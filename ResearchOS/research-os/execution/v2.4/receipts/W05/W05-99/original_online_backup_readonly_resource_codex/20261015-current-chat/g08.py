from readonly import *
import subprocess,hashlib
INTENT="Selected public Host owner/root registry metadata, exact historical package public-file metadata, and readonly ICACLS/fsutil auxiliary identity; no credential/vault/key payload."
SQL=[]
def aux(i,args):
 rec=dict(id=i,group="G08",fullargv=list(map(str,args)),cwd=str(W),relevantenv={k:os.environ.get(k) for k in ["TMP","TEMP","PYTHONUTF8","PATH"]},
  exact_sql=[],intent="Readonly native auxiliary metadata; not accepted same-handle identity proof",
  rawstdout=i+".stdout.raw",rawstderr=i+".stderr.raw",nativeexit=i+".exit.json",prewritten_at=time.time())
 save(i+".recipe.json",rec)
 with (E/(i+".stdout.raw")).open("wb") as o,(E/(i+".stderr.raw")).open("wb") as er:p=subprocess.run(list(map(str,args)),cwd=W,stdout=o,stderr=er,timeout=10)
 save(i+".exit.json",dict(native_exit=p.returncode,classification="READONLY_RESULT" if not p.returncode else "EXPECTED_OR_UNSUPPORTED_NATIVE_DENIAL_NO_ESCALATION"))
 return dict(id=i,native_exit=p.returncode,stdout=(E/(i+".stdout.raw")).read_bytes().decode("mbcs",errors="replace"))
if __name__=="__main__":
 prior=json.loads((E/"g03-results.json").read_text(encoding="utf8"))
 rows=next(q["rows"] for q in prior["queries"] if q["name"]=="active_workspace_public_fields")
 workspace=Path(rows[0][4]) if rows else None
 public={}
 hp=D/"host/host_state.json"
 if hp.is_file() and hp.stat().st_size<=65536:
  data=json.loads(hp.read_text(encoding="utf8"))
  allowed=["Version","PrincipalRef","PrincipalID","HostInstanceID","version","principal_ref","principal_id","host_instance_id"]
  public["host_identity"]={k:data[k] for k in allowed if k in data}
 else:public["host_identity"]="UNKNOWN_NOT_READ"
 rp=D/"host/workspaces/roots.json"
 if rp.is_file() and rp.stat().st_size<=1048576:
  data=json.loads(rp.read_text(encoding="utf8"));rs=data.get("Roots",data.get("roots",[]))
  selected=[]
  for row in rs:
   if row.get("ref") in [r[0] for r in rows]:
    selected.append({k:row.get(k) for k in ["ref","real_path","access","volume_id","file_id","final_path","revoked"]})
  public["registered_selected_roots"]=selected
 else:public["registered_selected_roots"]="UNKNOWN_NOT_READ"
 public["host_files_metadata"]=[metadata(p) for p in [hp,rp,D/"host",D/"host/credentials",D/"discovery.json"]]
 old=R/"execution/v2.4/receipts/W05/W05-99/qualification_official_entry_resource_map_codex/20261015-current-chat"
 binding=json.loads((old/"actual-activation-binding.json").read_text(encoding="utf8"))
 package=Path(binding["cwd"]).parents[1]
 rels=["apps/desktop/package.json","apps/desktop/main/lib/host.js","apps/desktop/resources/control/researchos-control.exe","apps/desktop/resources/control/runtime-verifier.exe","apps/desktop/resources/control/runtime-verifier-installation.json","apps/desktop/resources/control/runtime/mu-worker.mjs.build.json","apps/desktop/resources/control/runtime/node.exe","apps/desktop/resources/control/runtime/mu-worker.mjs"]
 public["package_metadata_historical_route_not_current_process"]=[metadata(package/r) for r in rels]
 public["historical_package_root"]=str(package)
 scripts={}
 for rel in ["apps/desktop/main/lib/host.js"]:
  pp=package/rel;sp=W/rel
  if pp.is_file() and sp.is_file():scripts[rel]=dict(package_sha256=pin(pp)["sha256"],source_sha256=pin(sp)["sha256"])
 public["public_route_script_pins"]=scripts
 public["public_asset_manifests"]={}
 for rel in ["apps/desktop/resources/control/runtime-verifier-installation.json","apps/desktop/resources/control/runtime/mu-worker.mjs.build.json"]:
  pp=package/rel
  if pp.is_file() and pp.stat().st_size<=32768:public["public_asset_manifests"][rel]=json.loads(pp.read_text(encoding="utf8"))
 sysdir=Path(os.environ["SystemRoot"])/"System32";ic=sysdir/"icacls.exe";fs=sysdir/"fsutil.exe"
 public["native_aux_binary_pins"]=[pin(ic),pin(fs)]
 targets=[D,DB]+([workspace] if workspace else [])
 public["native_aux"]=[]
 for n,p in enumerate(targets):
  public["native_aux"].append(aux("g08-acl-"+str(n),[ic,p]))
  public["native_aux"].append(aux("g08-fileid-"+str(n),[fs,"file","queryfileid",p]))
 public["G01"]="UNKNOWN_NO_INDEPENDENTLY_ACCEPTED_SAMEHANDLE_128BIT_HELPER; stdstat/fsutil outputs auxiliary only"
 public["key_usability"]="UNKNOWN_NO_KEY_PATH_OR_CONTENT_READ_NO_KEY_CREATED"
 public["backup_destination"]="UNKNOWN_NO_TARGET_SELECTED_OR_CREATED"
 public["restore_authority"]="NOT_GRANTED"
 public["actual_deployment_config_equivalence"]="UNKNOWN_HISTORICAL_ROUTE_AND_PUBLIC_FILES_DO_NOT_PROVE_CURRENT_PROCESS_CONFIG"
 save("host-deployment-native-metadata.json",public);print(json.dumps(public,ensure_ascii=False))

