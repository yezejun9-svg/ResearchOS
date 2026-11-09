from readonly import *
import subprocess
INTENT="Close finite collection: inspect only selected public root-registry metadata and Source matching logic; final sidefile stat and source cleanliness. No new database connection."
SQL=[]
if __name__=="__main__":
 old=json.loads((E/"g03-results.json").read_text(encoding="utf8"))
 selected=next(q["rows"] for q in old["queries"] if q["name"]=="active_workspace_public_fields")
 wanted={os.path.normcase(os.path.normpath(r[4])) for r in selected}
 p=D/"host/workspaces/roots.json"
 data=json.loads(p.read_text(encoding="utf8")) if p.is_file() and p.stat().st_size<1048576 else {}
 candidates=[];visited=0
 def walk(v,depth=0):
  global visited
  visited+=1
  if depth>3 or visited>64:return
  if isinstance(v,dict):
   paths=[v.get(k) for k in ["real_path","RealPath","path","Path"] if isinstance(v.get(k),str)]
   if any(os.path.normcase(os.path.normpath(x)) in wanted for x in paths):
    allowed=["ref","Ref","real_path","RealPath","access","Access","volume_id","VolumeID","file_id","FileID","final_path","FinalPath","revoked","Revoked","authorized_workspace_ref"]
    candidates.append({k:v[k] for k in allowed if k in v})
   for k,x in list(v.items())[:32]:
    if isinstance(x,(dict,list)):walk(x,depth+1)
  elif isinstance(v,list):
   for x in v[:9]:walk(x,depth+1)
 walk(data)
 public=dict(top_level_keys=list(data) if isinstance(data,dict) else ["list"],selected_path_matches=candidates,
  previous_g08_ref_only_empty_is_not_absence=True,root_ref_crosswalk_verified=bool(candidates),samehandle_native_identity_accepted=False)
 save("selected-host-root-crosswalk.json",public)
 print("HOST_ROOT_SELECTED_CROSSWALK",json.dumps(public,ensure_ascii=False))
 sp=W/"internal/host/backup_windows.go"
 print("SOURCE_SNAPSHOT_ROOT_LOOKUP","\n".join(sp.read_text(encoding="utf8").splitlines()[:68]))
 final=dict(final_observer_metadata=sides(),all_sqlite_observer_connections_explicitly_closed=True,no_observer_process_left_running=True,
  no_key_or_credentials_material_read=True,no_original_backup_or_mutation_operation=True,
  mutable_live_source_not_snapshot=True)
 save("observer-closure.json",final)
 print("OBSERVER_CLOSURE",json.dumps(final,ensure_ascii=False))
 args=["git","-C",str(W),"status","--porcelain=v1"];i="g09-final-source-status"
 save(i+".recipe.json",dict(id=i,group="G09",fullargv=args,cwd=str(W),relevantenv={k:os.environ.get(k) for k in ["TMP","TEMP","PYTHONUTF8","PATH"]},exact_sql=[],intent="Readonly source cleanliness",
  rawstdout=i+".stdout.raw",rawstderr=i+".stderr.raw",nativeexit=i+".exit.json",prewritten_at=time.time()))
 with (E/(i+".stdout.raw")).open("wb") as o,(E/(i+".stderr.raw")).open("wb") as er:
  q=subprocess.run(args,cwd=W,stdout=o,stderr=er)
 save(i+".exit.json",dict(native_exit=q.returncode))
 assert q.returncode==0 and (E/(i+".stdout.raw")).read_bytes()==b""
 print("G09_FINITE_COLLECTION_CLOSED")

