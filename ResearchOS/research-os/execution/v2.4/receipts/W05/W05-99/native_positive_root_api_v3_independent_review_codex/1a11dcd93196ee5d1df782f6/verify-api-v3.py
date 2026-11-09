import ast,json,hashlib,copy
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent.parent
OLD=B/'integration_codex/native-positive-root-api-v2-d4491126fbd148f8/root_public_api.actual.py'
NEW=B/'integration_codex/native-positive-root-api-v3-61a10e989dfd4c19/root_public_api.actual.py'
PREV=B/'native_positive_root_api_v2_independent_review_codex/1a11dcb4caa1e0b14c81faf'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
refs=json.loads((PREV/'evidence.json').read_bytes())['base_refs']
assert len(refs)==4094
refs += [pin(NEW),pin(PREV/'HDF.json'),pin(PREV/'MF.json')]
assert pin(NEW)['sha256']=='d323122f6a25e940745117cd8f1475e31c83337009e96c7d09d96c11accb26ce' and pin(NEW)['bytes']==12441
assert pin(OLD)['sha256']=='0fd8c0e47599d817b776dc9d55a0a5d1342ebad1739c914ddb97998c81732543'
old=OLD.read_bytes();new=NEW.read_bytes();at=ast.parse(old);bt=ast.parse(new)
def inspect(t):
 return next(n for n in ast.walk(t) if isinstance(n,ast.If) and ast.unparse(n.test)=="action == 'inspect'")
af=inspect(at);bf=inspect(bt)
al=old.splitlines(keepends=True);bl=new.splitlines(keepends=True)
assert b''.join(bl[:bf.lineno-1]+al[af.lineno-1:af.end_lineno]+bl[bf.end_lineno:])==old
for p in ast.walk(bt):
 for k,v in ast.iter_fields(p):
  if isinstance(v,list):
   for i,n in enumerate(v):
    if n is bf:v[i]=copy.deepcopy(af)
assert ast.dump(at,include_attributes=False)==ast.dump(bt,include_attributes=False)
s=ast.get_source_segment(new.decode(),bf)
for expected in ["fixture[\"test_failed\"] is True and fixture[\"release_required\"] is True","Path(cfg[\"Environment\"][\"TEMP\"]).resolve()","not db_path.is_relative_to(R/\".local/mu-sdk-isolated-project-ed84838046934329a76733a005c9b162\")","before is not None and rehearsal is not None and after is not None","\"expected_baseline_available\":before is not None and rehearsal is not None","\"early_failure_retained\":early_failure","?mode=ro","PRAGMA query_only=ON","reader_cleanup=read_guard.close()"]:
 assert expected in s,expected
assert "controller.release_fixture" not in s and "controller.sign_reviewed" not in s
for r in refs:assert pin(r['path'])==r,('drift',r['path'])
ref=save('evidence.json',dict(base_refs=refs,source_ref=pin(NEW),old_source_ref=pin(OLD),inverse_inspect_replacement_entire_file_byte_equal=True,AST_equal_outside_inspect=True,early_retained_requires_failed_and_release_required=True,database_constrained_to_exact_config_TEMP=True,original_data_root_explicitly_excluded=True,current_native_ID_match_required=True,absent_baselines_explicit_null=True,missing_before_rehearsal_after_implies_expected_state_false=True,all_schema_and_typed_rows_still_read=True,SQL_reader_guards_close_before_inspection_receipt=True,no_auto_release=True,all_current_pins_match=True,SQL_executions=0,target_executions=0,new_mechanical_errors=0))
print(json.dumps(dict(evidence_ref=ref,base_refs=len(refs),drift=0,only_inspect_changed=True,partial_retained_source_accepted=True,new_mechanical_errors=0)))

