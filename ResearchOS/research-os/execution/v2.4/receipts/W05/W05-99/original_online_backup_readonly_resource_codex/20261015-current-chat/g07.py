from readonly import *
import stat
INTENT="Bounded native metadata-only active-workspace metrics. Stop at first production limit, reparse, error, or 10-second budget; no file content and no followed known reparse."
SQL=[]
if __name__=="__main__":
 prior=json.loads((E/"g03-results.json").read_text(encoding="utf8"))
 queries={q["name"]:q for q in prior["queries"]}
 count=queries["active_workspace_count_exact_opsbackup"]["rows"][0][0]
 selected=queries["active_workspace_public_fields"]["rows"]
 limits=dict(roots=8,files=4096,dirs=4096,total_bytes=256<<20,file_bytes=16<<20,path_bytes=4096)
 totals=dict(files=0,dirs=0,total_bytes=0,entries=0,max_file_bytes=0)
 records=[];outcome="WITHIN_LIMITS_METADATA_ONLY";started=time.monotonic()
 if count>8:outcome="EXCEEDS_ROOT_LIMIT"
 else:
  for row in selected:
   root=Path(row[4]);record=dict(workspace_ref=row[0],root=str(root),root_metadata=metadata(root),outside_data_root=not root.is_relative_to(D),not_backup_destination_qualified=True)
   records.append(record)
   todo=[root];stop=None
   while todo and stop is None:
    current=todo.pop()
    try:
     st=current.lstat()
     if getattr(st,"st_file_attributes",0)&0x400 or stat.S_ISLNK(st.st_mode):
      stop=dict(reason="REPARSE_NOT_FOLLOWED",path=str(current));break
     with os.scandir(current) as it:
      for entry in it:
       if time.monotonic()-started>10:
        stop=dict(reason="BOUNDED_TIME_LIMIT",path=str(current));break
       ep=Path(entry.path);s=entry.stat(follow_symlinks=False);totals["entries"]+=1
       if getattr(s,"st_file_attributes",0)&0x400 or stat.S_ISLNK(s.st_mode):
        stop=dict(reason="REPARSE_NOT_FOLLOWED",path=str(ep));break
       rel=ep.relative_to(root).as_posix()
       if len(rel.encode("utf8"))>limits["path_bytes"]:stop=dict(reason="EXCEEDS_PATH_LIMIT",path=str(ep));break
       if stat.S_ISDIR(s.st_mode):
        totals["dirs"]+=1
        if totals["dirs"]>limits["dirs"]:stop=dict(reason="EXCEEDS_DIR_LIMIT",path=str(ep));break
        todo.append(ep)
       elif stat.S_ISREG(s.st_mode):
        totals["files"]+=1;totals["total_bytes"]+=s.st_size;totals["max_file_bytes"]=max(totals["max_file_bytes"],s.st_size)
        if totals["files"]>limits["files"]:stop=dict(reason="EXCEEDS_FILE_COUNT",path=str(ep));break
        if s.st_size>limits["file_bytes"]:stop=dict(reason="EXCEEDS_SINGLE_FILE_BYTES",path=str(ep),bytes=s.st_size);break
        if totals["total_bytes"]>limits["total_bytes"]:stop=dict(reason="EXCEEDS_TOTAL_BYTES",path=str(ep));break
       else:stop=dict(reason="NONREGULAR_ENTRY",path=str(ep));break
    except OSError as er:
     stop=dict(reason="ACCESS_OR_NATIVE_METADATA_ERROR",path=str(current),error=type(er).__name__,winerror=getattr(er,"winerror",None))
   record["stop"]=stop;record["full_tree_completed"]=stop is None
   if stop:
    outcome=stop["reason"];break
 out=dict(group="G07",active_count=count,limits=limits,observed_lower_bounds=totals,outcome=outcome,workspaces=records,
          elapsed_seconds=time.monotonic()-started,no_contents_read=True,no_known_reparse_followed=True,
          no_same_handle_128bit_acceptance=True,path_race_continuity_unproved=True,total_tree_metrics_complete=all(x["full_tree_completed"] for x in records) and len(records)==count)
 save("workspace-limits.json",out);print(json.dumps(out,ensure_ascii=False))

