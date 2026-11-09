import sqlite3,json,time,os
from pathlib import Path
from urllib.parse import quote
from collector import E,R,W,D,DB,S,scope,save,pin
def metadata(p):
 try:
  st=p.lstat()
  return dict(path=str(p),exists=True,size=st.st_size,mtime_ns=st.st_mtime_ns,ctime_ns=st.st_ctime_ns,mode=st.st_mode,attributes=getattr(st,"st_file_attributes",None),native_aux_64bit_fileindex=st.st_ino,is_symlink=p.is_symlink())
 except OSError as e:return dict(path=str(p),exists=False,error=type(e).__name__,winerror=getattr(e,"winerror",None))
def sides():return [metadata(p) for p in [D,DB,Path(str(DB)+"-wal"),Path(str(DB)+"-shm")]]
def query_group(group,sql):
 before=sides();t0=time.time();uri="file:"+quote(str(DB.resolve()).replace("\\","/"),safe="/:")+"?mode=ro&cache=private"
 # Explicit URI is pinned in prewritten recipe; no immutable, store.Open or Host.New.
 db=sqlite3.connect(uri,uri=True,timeout=3)
 results=[];start=time.monotonic()
 try:
  db.execute("PRAGMA query_only=ON")
  db.set_progress_handler(lambda: 1 if time.monotonic()-start>10 else 0,1000)
  for item in sql:
   q=item["sql"];params=item.get("params",[])
   assert q.lstrip().upper().startswith(("SELECT ","PRAGMA "))
   cur=db.execute(q,params)
   rows=cur.fetchmany(item.get("row_cap",256)+1)
   if len(rows)>item.get("row_cap",256):raise RuntimeError("query row cap exceeded: "+item["name"])
   results.append(dict(name=item["name"],columns=[x[0] for x in cur.description] if cur.description else [],rows=rows))
 finally:db.close()
 out=dict(group=group,uri=uri,query_only=True,observer_closed=True,started_at=t0,finished_at=time.time(),before=before,after=sides(),queries=results)
 save(group+"-results.json",out);print(json.dumps(out,ensure_ascii=False))
 return out

