import sys
sys.dont_write_bytecode=True
import json,hashlib,types
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
C=B/"integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4/controller.public.config.json"
def pin_raw(path,raw):
 return dict(path=str(Path(path).resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def pin(path):
 path=Path(path).resolve();return pin_raw(path,path.read_bytes())
def plain(ref):
 assert set(ref)=={"path","sha256","bytes"}
 return dict(path=ref["path"],sha256=ref["sha256"].removeprefix("sha256:"),bytes=ref["bytes"])
def checked(ref,raw):
 assert pin_raw(ref["path"],raw)==plain(ref),"fixed source reference mismatch before execution"
 return raw
def save(name,value):
 with (O/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return pin(O/name)
def module_raw(ref,raw):
 raw=checked(ref,raw);path=Path(ref["path"]).resolve()
 m=types.ModuleType("root_serve_"+path.stem);m.__file__=str(path);sys.modules[m.__name__]=m
 exec(compile(raw,str(path),"exec"),m.__dict__);return m
def unique(refs):
 out={}
 for p in refs:
  key=str(Path(p["path"]).resolve()).casefold()
  assert key not in out or out[key]==p,"conflicting exact source pins"
  out[key]=p
 return list(out.values())
def runtime_pins():
 refs=[]
 for m in list(sys.modules.values()):
  for field in ("__file__","__cached__"):
   path=getattr(m,field,None)
   if path and Path(path).is_file():refs.append(pin(path))
 return refs
config_raw=C.read_bytes()
config_plain=pin_raw(C,config_raw)
assert config_plain["sha256"]=="5f956dd27e9818b5e8ffa043d04317ea37d028c5d9dac3ffb241c22a2b0549c5" and config_plain["bytes"]==1095627
cfg=json.loads(config_raw)
config_ref={**config_plain,"sha256":"sha256:"+config_plain["sha256"]}
assert cfg["Schema"]=="researchos.root-native-migration-controller.v1"
fixed_python=pin(Path(sys.executable))
assert fixed_python["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b" and fixed_python["bytes"]==106328
guard_ref=cfg["SourceReadGuard"]
gm=module_raw(guard_ref,checked(guard_ref,Path(guard_ref["path"]).read_bytes()))
refs=unique([plain(p) for p in cfg["FrozenInputs"]]+[config_plain,pin(__file__),fixed_python]+runtime_pins())
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
guard.acquire(refs)
runtime_guard=None
action=sys.argv[1]
assert action in ("poll","snapshot","sign","publish","inspect","release","stop")
try:
 assert guard.get_buffer(str(C))==config_raw
 assert guard.get_buffer(guard_ref["path"])==checked(guard_ref,guard.get_buffer(guard_ref["path"]))
 controller=module_raw(cfg["ControllerSource"],guard.get_buffer(cfg["ControllerSource"]["path"]))
 helper=module_raw(cfg["OriginalOwnedHelper"],guard.get_buffer(cfg["OriginalOwnedHelper"]["path"]))
 c=controller.context(config_ref);assert c["hc"]["Case"]=="positive-replay"
 additional=unique([pin(p) for p in helper.runtime_resource_paths()]+runtime_pins())
 existing={p["path"].casefold():p for p in refs}
 for p in additional:
  if p["path"].casefold() in existing:assert existing[p["path"].casefold()]==p
 additional=[p for p in additional if p["path"].casefold() not in existing]
 if additional:
  runtime_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
  runtime_guard.acquire(additional)
 output={"action":action,"config_ref":config_ref,"formal_acceptance":False}
 if action=="poll":
  output["observation_ref"]=controller.poll(config_ref)
 elif action=="snapshot":
  output["snapshot_ref"]=controller.snapshot(config_ref)
 elif action=="stop":
  output["request_ref"]=controller.stop(config_ref)
 elif action in ("sign","publish","release"):
  approval_path=Path(sys.argv[2]).resolve()
  assert approval_path.is_file() and approval_path.is_relative_to(R/"execution/v2.4/receipts")
  approval_ref={"path":str(approval_path),"sha256":sys.argv[3],"bytes":int(sys.argv[4])}
  checked(approval_ref,approval_path.read_bytes())
  if action=="sign":
   key_manifest=B/"integration_codex/recoveryauthority-key-provision-root-9b42b8e7072a40b1/key-provision.closed.json"
   key_raw=key_manifest.read_bytes()
   key_ref=pin_raw(key_manifest,key_raw)
   assert key_ref["sha256"]=="873953117beb0f5730674d130e49c18502b6e5821ea37f5658af3c80f1e7d5fe" and key_ref["bytes"]==2375
   key_guard=gm.SourceReadGuard()
   try:
    key_guard.acquire([key_ref])
    metadata=json.loads(key_guard.get_buffer(str(key_manifest)))
    issuer_path=metadata["keys"]["issuer"]["private_resource_ref"]["path"]
    output["signing_receipt_ref"]=controller.sign_reviewed(config_ref,approval_ref,issuer_path)
    issuer_path=""
   finally:
    issuer_path=""
    key_cleanup=key_guard.close()
   assert key_cleanup["closed"] and not key_cleanup["errors"]
   output["key_metadata_guard_cleanup"]=key_cleanup
   output["private_path_recorded"]=False
  elif action=="publish":
   output["published_ref"]=controller.publish_signed(config_ref,approval_ref)
  else:
   output["published_ref"]=controller.release_fixture(config_ref,approval_ref)
 elif action=="inspect":
  import sqlite3,struct,collections
  snapshot_path=Path(sys.argv[2]).resolve()
  snapshot_ref={"path":str(snapshot_path),"sha256":sys.argv[3],"bytes":int(sys.argv[4])}
  checked(snapshot_ref,snapshot_path.read_bytes())
  snap=controller.decode(controller.read_ref(snapshot_ref))
  assert snap["config_ref"]==config_ref and snap["phase"]=="fixture-retained" and snap["case"]=="positive-replay"
  fixture=controller.decode(controller.read_ref(snap["fixture_public_ref"]))
  early_failure=Path(snap["fixture_public_ref"]["path"]).name=="06-fixture-retained.ready.json"
  if early_failure:
   assert fixture["test_failed"] is True and fixture["release_required"] is True
   fixture={"database":fixture["database"],"root":str(Path(fixture["database"]).parent)}
  else:
   assert fixture["synthetic"] is True and fixture["formal"] is False and fixture["production_db_writes"]==0
  db_path=Path(fixture["database"]).resolve()
  assert db_path.is_relative_to(Path(cfg["Environment"]["TEMP"]).resolve()) and db_path.is_file()
  assert not db_path.is_relative_to(R/".local/mu-sdk-isolated-project-ed84838046934329a76733a005c9b162")
  assert snap["measured_native_ids"]=={"root":controller.native_file_id(fixture["root"],True),"database":controller.native_file_id(str(db_path),False)}
  def quote(name):return '"'+name.replace('"','""')+'"'
  def digest(raw):return "sha256:"+hashlib.sha256(raw).hexdigest()
  def go_json_hash(value):
   # Actual contracts.Hash uses canonical.JSON/JCS, not Go Marshal's HTML escaping.
   # This data domain contains only arrays, objects with string keys, and strings.
   def canonical(v):
    if type(v) is str:
     v.encode("utf-16-be",errors="strict")
     return v
    if type(v) is list:return [canonical(item) for item in v]
    if type(v) is dict:
     assert all(type(key) is str for key in v)
     keys=sorted(v,key=lambda key:key.encode("utf-16-be",errors="strict"))
     return {key:canonical(v[key]) for key in keys}
    raise ValueError("outside restricted JCS schema/typed-row domain")
   text=json.dumps(canonical(value),ensure_ascii=False,separators=(",",":"),allow_nan=False)
   return digest(text.encode("utf-8",errors="strict"))
  def row_hash(values):
   encoded=bytearray()
   for value in values:
    if value is None:typ,raw=b"N",b""
    elif type(value) is int:typ,raw=b"I",str(value).encode("ascii")
    elif type(value) is float:typ,raw=b"F",struct.pack(">d",value)
    elif type(value) is str:typ,raw=b"T",value.encode("utf-8")
    elif type(value) is bytes:typ,raw=b"B",value
    else:raise ValueError("unexpected SQLite storage class")
    encoded.extend(typ+struct.pack(">Q",len(raw))+raw)
   return digest(encoded)
  db_resources=[pin(db_path)]
  db_resources.extend(pin(p) for p in (Path(str(db_path)+"-wal"),) if p.is_file())
  class SQLiteReadShareAPI(gm._Win32API):
   def open_read_shared_read(self,path):
    handle=self._create(path,gm._GENERIC_READ,0x00000003,None,gm._OPEN_EXISTING,gm._FILE_ATTRIBUTE_NORMAL,None)
    if handle in (None,gm._INVALID_HANDLE_VALUE):raise self._error("CreateFileW live SQLite read")
    return handle
  class SQLiteIdentityGuard(gm.SourceReadGuard):
   def close(self):
    observation=super().close()
    observation["schema"]="researchos.retained-sqlite-read-share-observation.v1"
    observation["share_mode"]="FILE_SHARE_READ_WRITE_DELETE_DENIED"
    observation["immutable_source_claim"]=False
    observation["existing_SQLite_writer_handles_permitted"]=True
    return observation
  database_guard=SQLiteIdentityGuard(per_file_cap=256*1024*1024,total_cap=512*1024*1024,api_factory=SQLiteReadShareAPI)
  reader_resources=unique([plain(snapshot_ref)]+[pin(p) for p in helper.runtime_resource_paths()]+runtime_pins())
  read_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
  db=None
  try:
   read_guard.acquire(reader_resources)
   database_guard.acquire(db_resources)
   native_ids_before={"root":controller.native_file_id(fixture["root"],True),"database":controller.native_file_id(str(db_path),False)}
   db=sqlite3.connect(db_path.as_uri()+"?mode=ro",uri=True,detect_types=0)
   db.execute("PRAGMA query_only=ON")
   data_version_before=db.execute("PRAGMA data_version").fetchone()[0]
   db.execute("BEGIN")
   schema_rows=[list(row) for row in db.execute("SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_master ORDER BY type,name")]
   table_names=[row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
   rows={}
   for name in table_names:
    cursor=db.execute("SELECT * FROM "+quote(name)+" LIMIT 0")
    columns=[item[0] for item in cursor.description];cursor.close()
    projection=",".join("CASE WHEN 1 THEN "+quote(col)+" END" for col in columns)
    values=db.execute("SELECT "+projection+" FROM "+quote(name))
    rows[name]={"columns":columns,"row_digests":sorted(row_hash(row) for row in values)}
   versions=[row[0] for row in db.execute("SELECT version FROM schema_migrations ORDER BY version")]
   db.rollback()
   data_version_after=db.execute("PRAGMA data_version").fetchone()[0]
   db.close();db=None
   native_ids_after={"root":controller.native_file_id(fixture["root"],True),"database":controller.native_file_id(str(db_path),False)}
   primary_and_WAL_bytes_unchanged=all(pin(ref["path"])==ref for ref in db_resources)
   assert native_ids_before==native_ids_after==snap["measured_native_ids"] and data_version_before==data_version_after and primary_and_WAL_bytes_unchanged
   before_ref=next((p for p in snap["evidence_refs"] if Path(p["path"]).name=="before.rows.json"),None)
   after_ref=next((p for p in snap["evidence_refs"] if Path(p["path"]).name=="after.rows.json"),None)
   rehearsal_ref=next((p for p in snap["evidence_refs"] if Path(p["path"]).name=="rehearsal.public.json"),None)
   before=controller.decode(controller.read_ref(before_ref)) if before_ref else None
   rehearsal=controller.decode(controller.read_ref(rehearsal_ref)) if rehearsal_ref else None
   after=controller.decode(controller.read_ref(after_ref)) if after_ref else None
   invariants={}
   for name,old in (before or {}).items():
    current=rows.get(name)
    if name=="schema_migrations":
     old_count=collections.Counter(old["row_digests"])
     new_count=collections.Counter(current["row_digests"]) if current else collections.Counter()
     invariants[name]=current is not None and current["columns"]==old["columns"] and all(new_count[h]>=count for h,count in old_count.items()) and len(current["row_digests"])==len(old["row_digests"])+1
    else:invariants[name]=current==old
   schema_sha=go_json_hash(schema_rows)
   expected_state=before is not None and rehearsal is not None and after is not None and all(invariants.values()) and versions==list(range(1,25)) and set(rows)-set(before)=={"runtime_prepared_abandonments"} and rows["runtime_prepared_abandonments"]["row_digests"]==[] and schema_sha==rehearsal["target_schema_sha256"] and rows==after
   inspection={"schema":"researchos.root-native-whole-fixture-inspection.v1","config_ref":config_ref,"snapshot_ref":snapshot_ref,"fixture_read_complete":True,"whole_row_schema_review_complete":True,"private_credentials_recorded":False,"private_raw_rows_recorded":False,"synthetic_only":True,"database_share_mode":"READ_WRITE_SHARED_DELETE_DENIED","immutable_database_claim":False,"transaction_snapshot_complete":True,"data_version_before":data_version_before,"data_version_after":data_version_after,"primary_and_WAL_bytes_unchanged":primary_and_WAL_bytes_unchanged,"database_ref":pin(db_path),"native_ids":snap["measured_native_ids"],"sqlite_schema_sha256":schema_sha,"expected_target_schema_sha256":rehearsal["target_schema_sha256"] if rehearsal else None,"expected_baseline_available":before is not None and rehearsal is not None,"early_failure_retained":early_failure,"schema_object_count":len(schema_rows),"typed_rows":rows,"typed_rows_sha256":go_json_hash(rows),"before_ref":before_ref,"after_ref":after_ref,"schema_versions":versions,"original_table_invariants":invariants,"expected_state_matches":expected_state,"formal_acceptance":False}
  finally:
   if db is not None:db.close()
   reader_cleanup=read_guard.close()
   database_cleanup=database_guard.close()
   save("inspection-reader-guards-"+__import__("uuid").uuid4().hex+".json",{"source_reader":reader_cleanup,"live_database":database_cleanup})
  assert database_cleanup["closed"] and not database_cleanup["errors"] and database_cleanup["retained_handles_count"]==0
  assert reader_cleanup["closed"] and not reader_cleanup["errors"] and reader_cleanup["retained_handles_count"]==0
  inspection["reader_guard_cleanup"]=reader_cleanup
  inspection["database_guard_cleanup"]=database_cleanup
  output["inspection_ref"]=save("inspection-positive.json",inspection)
  output["expected_state_matches"]=inspection["expected_state_matches"]
 output_ref=save("api-"+action+"-"+__import__("uuid").uuid4().hex+".json",output)
 print(json.dumps(output,ensure_ascii=True),flush=True)
 print(json.dumps({"root_api_receipt_ref":output_ref}),flush=True)
finally:
 cleanups=[]
 if runtime_guard is not None:cleanups.append(runtime_guard.close())
 cleanups.append(guard.close())
 save("api-guard-cleanup-"+__import__("uuid").uuid4().hex+".json",{"guards":cleanups})
 assert all(p["closed"] and not p["errors"] and p["retained_handles_count"]==0 for p in cleanups)
