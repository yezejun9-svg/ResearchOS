import ast,copy,hashlib,json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).parent
Q=N.parents[1]/"native_grant_archive_request_builder_source_codex/gqb-1a11ee4f162766098eda3028b0679f2"
def module(path,name):
 raw=path.read_bytes();m=types.ModuleType(name);m.__file__=str(path)
 exec(compile(raw,str(path),"exec"),m.__dict__);return m
m=module(N/"native_grant_public_pin_archive.py","bounded_archive")
b=module(Q/"root_build_grant_archive_request.py","request_builder")
results=[]
def expect(name,fn,reject=False):
 try:fn()
 except (ValueError,TypeError,KeyError,OSError) as e:
  assert reject,(name,type(e).__name__)
  results.append({"name":name,"result":"PASS","rejected":type(e).__name__})
 else:
  assert not reject,name
  results.append({"name":name,"result":"PASS"})
def yes(v):assert v
def boundaries(mod,function,label):
 savedPath,savedCanonical=mod.Path,mod.canonical
 opened=[];reads=[];closed=[];state={}
 class Stream:
  def __enter__(self):return self
  def __exit__(self,*args):closed.append(True)
  def read(self,n):
   reads.append(n)
   if state.get("io_error"):raise OSError("synthetic read failure")
   return b"a"*min(state["actual"],n)
 class P:
  def __init__(self,p):self.p=p
  def open(self,mode):
   assert mode=="rb";opened.append(mode);return Stream()
 mod.Path=P;mod.canonical=lambda p:p.lower()
 def run(size,actual,wrong=False,io_error=False):
  opened.clear();reads.clear();closed.clear();state.update(actual=actual,io_error=io_error)
  ref={"path":"D:/fixture/public.json","sha256":"sha256:"+hashlib.sha256(b"a"*size).hexdigest() if type(size) is int and 0<=size<1024 else "sha256:"+"a"*64,"bytes":size}
  if wrong:ref["sha256"]="sha256:"+"0"*64
  try:
   out=function(ref)
   assert out==b"a"*size
  finally:
   if opened:
    assert reads==[size+1] and closed==[True]
   else:assert not reads and not closed
 for tag,size,actual,reject,wrong in [
  ("empty",0,0,False,False),("exact",5,5,False,False),("short",5,4,True,False),
  ("one_extra",5,6,True,False),("virtual_huge",5,10**12,True,False),
  ("empty_plus_one",0,1,True,False),("wrong_hash",5,5,True,True),
  ("cap_request_short",128*1024*1024,0,True,False),
  ("bool",True,0,True,False),("float",5.0,0,True,False),
  ("negative",-1,0,True,False),("above_cap",128*1024*1024+1,0,True,False)]:
  expect(label+"_"+tag,lambda s=size,a=actual,w=wrong:run(s,a,w),reject)
 expect(label+"_read_error_closes",lambda:run(5,0,io_error=True),True)
 mod.Path,mod.canonical=savedPath,savedCanonical
boundaries(m,m.read_ref,"archive")
boundaries(b,b.bounded_read,"builder")
archive_count=len(results)
original_canonical=m.canonical
m.canonical=lambda p:original_canonical(p,False)
def rp(role,path,sha=None,size=5):
 return {"role":role,"path":path,"sha256":sha or "sha256:"+"a"*64,"bytes":size}
temp="D:/fixture/temp"
cfg={"Environment":{"TEMP":temp}}
hc={"OutputDirectory":"D:/fixture/harness","BackupProgram":rp("backup-program","D:/resident/backup.exe"),
 "ControlProgram":rp("control-program","D:/resident/control.exe")}
opt={"Plan":m.PLAN,"SourceRoot":temp+"/source","TargetRoot":temp+"/target","Snapshot":temp+"/snapshot",
 "Destination":temp+"/restore","KeyFile":"D:/private/NEVER_FOLLOW"}
pins=[rp("source-program",hc["BackupProgram"]["path"]),rp("target-program",hc["ControlProgram"]["path"])]
for role in sorted(m.inventory_roles()):
 prefix,name=role.split(":",1);root=opt["SourceRoot" if prefix=="source-inventory" else "TargetRoot"]
 v=m.INVENTORY[name];pins.append(rp(role,root+"/"+name,v["sha256"],v["bytes"]))
alias=copy.deepcopy(next(p for p in pins if p["role"]==m.ALIAS_TARGET));alias["role"]="migration-sql";pins.insert(0,alias)
backup=rp("encrypted-backup-manifest",opt["Snapshot"]+"/manifest.json")
rehearsal=rp("isolated-restore-rehearsal",opt["Destination"]+"/prepared-abandonment-rehearsal.json")
pins += [backup,rehearsal,rp("encrypted-backup-payload:state.sqlite.enc",opt["Snapshot"]+"/state.sqlite.enc")]
pins += [rp("fixture-evidence:"+x,hc["OutputDirectory"]+"/"+x) for x in
 ("before.rows.json","fixture.public.json","00-rehearsal/invocation.json","00-rehearsal/stdout.raw","00-rehearsal/stderr.raw")]
payload={"schema":"researchos.recovery-migration-grant.v1","purpose":"RESEARCHOS_PREPARED_SCHEMA23_TO24_V1",
 "stage":"APPLY_ORIGINAL","binding":{"plan_id":m.PLAN,"backup":backup,"rehearsal":rehearsal},
 "options":opt,"pins":pins,"private_meta":{"NEVER_FOLLOW":18446744073709551615}}
manifest={"files":[{"name":"state.sqlite"}],"private_ref":"NEVER_FOLLOW"}
original=copy.deepcopy(payload)
entries=b.select_full(m,payload,cfg,hc,manifest,b.FULL_FLAG)
expect("full_60_unique_entries",lambda:yes(len(entries)==60 and len({x["path"] for x in entries})==60))
expect("source28_target29",lambda:yes(sum(x["role"].startswith("source-inventory:") for x in entries)==28 and sum(x["role"].startswith("target-inventory:") for x in entries)==29))
expect("alias_not_copied_twice",lambda:yes(all(x["role"]!="migration-sql" for x in entries)))
expect("raw_pins_exact_fields",lambda:yes(all(set(x)=={"role","path","sha256","bytes"} for x in entries)))
expect("payload_original_refs_unchanged",lambda:yes(payload==original))
expect("private_metadata_not_in_entries",lambda:yes("NEVER_FOLLOW" not in json.dumps(entries)))
expect("requires_explicit_full_flag",lambda:b.select_full(m,payload,cfg,hc,manifest,""),True)
expect("reject_near_match_flag",lambda:b.select_full(m,payload,cfg,hc,manifest,"--select-full"),True)
expect("missing_manifest_cipher",lambda:b.select_full(m,payload,cfg,hc,{"files":[]} ,b.FULL_FLAG),True)
expect("wrong_manifest_cipher",lambda:b.select_full(m,payload,cfg,hc,{"files":[{"name":"other"}]},b.FULL_FLAG),True)
expect("duplicate_manifest_name",lambda:b.select_full(m,payload,cfg,hc,{"files":[{"name":"state.sqlite"},{"name":"state.sqlite"}]},b.FULL_FLAG),True)
expect("reject_manifest_traversal",lambda:b.select_full(m,payload,cfg,hc,{"files":[{"name":"../private"}]},b.FULL_FLAG),True)
mutated=copy.deepcopy(payload);mutated["pins"][0]["bytes"]+=1
expect("alias_pin_conflict",lambda:b.select_full(m,mutated,cfg,hc,manifest,b.FULL_FLAG),True)
mutated2=copy.deepcopy(payload);mutated2["pins"].append(copy.deepcopy(mutated2["pins"][1]))
expect("duplicate_grant_role",lambda:b.select_full(m,mutated2,cfg,hc,manifest,b.FULL_FLAG),True)
mutated3=copy.deepcopy(payload);mutated3["pins"].pop(3)
expect("missing_fixed_inventory",lambda:b.select_full(m,mutated3,cfg,hc,manifest,b.FULL_FLAG),True)
source=(Q/"root_build_grant_archive_request.py").read_text(encoding="utf-8")
tree=ast.parse(source)
expect("no_unbounded_reads_in_builder",lambda:yes(".read_bytes(" not in source and ".read()" not in source))
expect("one_exclusive_request_write_site",lambda:yes(source.count('.open("xb")')==1))
expect("no_archive_run_or_child_process",lambda:yes("m.run(" not in source and "m.main(" not in source and "subprocess" not in source and ".mkdir(" not in source))
expect("precise_uint64_decode",lambda:yes(m.decode(b'{"n":18446744073709551615}')["n"]==18446744073709551615))
m.canonical=original_canonical
for folder,name,items in [(N,"bounded-controls.results.json",results[:26]),(Q,"builder-controls.results.json",results)]:
 with (folder/name).open("xb") as f:f.write((json.dumps({"schema":"researchos.pure-source-controls.v1","controls":items,
  "count":len(items),"actual_archive_main":False,"actual_builder_main":False,"actual_compose":False,
  "actual_win32_guard":False,"SQL_API_Go_private_model":False},indent=2)+"\n").encode())
print("GPA_BOUNDARY_AND_BUILDER_CONTROLS_OK "+json.dumps({"boundary":26,"total":len(results),"native_exit":None}))

