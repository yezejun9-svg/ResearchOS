import ast,json,hashlib,copy
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent.parent
OLD=B/'integration_codex/native-positive-root-api-v3-61a10e989dfd4c19/root_public_api.actual.py'
NEW=B/'integration_codex/native-positive-root-api-v4-7e971c417d4d4d2a/root_public_api.actual.py'
PREV=B/'native_positive_root_api_v3_independent_review_codex/1a11dcd93196ee5d1df782f6'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
refs=json.loads((PREV/'evidence.json').read_bytes())['base_refs'];assert len(refs)==4097
refs += [pin(NEW),pin(PREV/'HDF.json'),pin(PREV/'MF.json')]
assert pin(NEW)['sha256']=='60f0e6b119209511067904c55c0522accaa0d5689dfcaf54f5eef2173ab6c16e' and pin(NEW)['bytes']==14554
old=OLD.read_bytes();new=NEW.read_bytes();at=ast.parse(old);bt=ast.parse(new)
def inspect(t):return next(n for n in ast.walk(t) if isinstance(n,ast.If) and ast.unparse(n.test)=="action == 'inspect'")
af=inspect(at);bf=inspect(bt);al=old.splitlines(keepends=True);bl=new.splitlines(keepends=True)
assert b''.join(bl[:bf.lineno-1]+al[af.lineno-1:af.end_lineno]+bl[bf.end_lineno:])==old
for p in ast.walk(bt):
 for k,v in ast.iter_fields(p):
  if isinstance(v,list):
   for i,n in enumerate(v):
    if n is bf:v[i]=copy.deepcopy(af)
assert ast.dump(at,include_attributes=False)==ast.dump(bt,include_attributes=False)
s=ast.get_source_segment(new.decode(),bf)
required=['self._create(path,gm._GENERIC_READ,0x00000003,None,gm._OPEN_EXISTING,gm._FILE_ATTRIBUTE_NORMAL,None)','"immutable_source_claim"]=False','"FILE_SHARE_READ_WRITE_DELETE_DENIED"','api_factory=SQLiteReadShareAPI','reader_resources=unique([plain(snapshot_ref)]','database_guard.acquire(db_resources)','?mode=ro','PRAGMA query_only=ON','db.execute("BEGIN")','native_ids_before==native_ids_after==snap["measured_native_ids"]','data_version_before==data_version_after','primary_and_WAL_bytes_unchanged','database_cleanup=database_guard.close()','"source_reader":reader_cleanup,"live_database":database_cleanup','"immutable_database_claim":False']
for text in required:assert text in s,text
assert '"-shm"' not in s
assert "controller.release_fixture" not in s and "controller.sign_reviewed" not in s
for r in refs:assert pin(r['path'])==r,('drift',r['path'])
ref=save('evidence.json',dict(base_refs=refs,source_ref=pin(NEW),old_source_ref=pin(OLD),inverse_inspect_replacement_entire_file_byte_equal=True,AST_equal_outside_inspect=True,database_desired_access='GENERIC_READ',database_share_mode=3,delete_share_denied=True,source_runtime_snapshot_share_read_only=True,SQLite_mode_ro_query_only_transaction=True,identity_data_version_and_enumerated_raw_pin_stability_required=True,all_schema_and_typed_rows_still_read=True,reader_and_database_cleanup_saved_separately=True,immutable_database_claim=False,WAL_scope='Only WAL present when db_resources is collected. Newly appearing WAL is not separately enumerated/rejected.',no_auto_release=True,all_current_pins_match=True,SQL_executions=0,target_executions=0,new_mechanical_errors=0))
print(json.dumps(dict(evidence_ref=ref,base_refs=len(refs),drift=0,only_inspect_changed=True,live_sqlite_read_source_accepted=True,new_mechanical_errors=0)))

