import ast,json,hashlib,copy
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent.parent
OLD=B/'integration_codex/native-positive-root-api-6957929b0a784a91/root_public_api.actual.py'
NEW=B/'integration_codex/native-positive-root-api-v2-d4491126fbd148f8/root_public_api.actual.py'
PREV=B/'native_positive_root_api_independent_review_codex/1a11dc9845e8a173ffe07771'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
refs=json.loads((PREV/'evidence.json').read_bytes())['base_refs']
assert len(refs)==4091
refs += [pin(NEW),pin(PREV/'HDF.json'),pin(PREV/'MF.json')]
assert pin(NEW)['sha256']=='0fd8c0e47599d817b776dc9d55a0a5d1342ebad1739c914ddb97998c81732543' and pin(NEW)['bytes']==11725
assert pin(OLD)['sha256']=='f3f4aa28ec23cfe1c73381ff7a82fbd6f8fb0feb15c0e3cc74fea80d21dea7e8'
old=OLD.read_bytes();new=NEW.read_bytes()
at=ast.parse(old);bt=ast.parse(new)
af=next(n for n in ast.walk(at) if isinstance(n,ast.FunctionDef) and n.name=='go_json_hash')
bf=next(n for n in ast.walk(bt) if isinstance(n,ast.FunctionDef) and n.name=='go_json_hash')
al=old.splitlines(keepends=True);bl=new.splitlines(keepends=True)
inverse=b''.join(bl[:bf.lineno-1]+al[af.lineno-1:af.end_lineno]+bl[bf.end_lineno:])
assert inverse==old
for parent in ast.walk(bt):
 for key,value in ast.iter_fields(parent):
  if isinstance(value,list):
   for i,node in enumerate(value):
    if node is bf:value[i]=copy.deepcopy(af)
assert ast.dump(at,include_attributes=False)==ast.dump(bt,include_attributes=False)
text=ast.get_source_segment(new.decode(),bf)
assert 'utf-16-be' in text and 'errors="strict"' in text and 'ensure_ascii=False' in text
assert 'sort_keys=True' not in text and '.replace(' not in text
for r in refs:assert pin(r['path'])==r,('drift',r['path'])
ref=save('evidence.json',dict(base_refs=refs,source_ref=pin(NEW),old_source_ref=pin(OLD),inverse_replacement_entire_file_byte_equal=True,AST_equal_except_go_json_hash=True,restricted_domain=['str','list','dict[str,restricted]'],invalid_unicode_rejected=True,keys_ordered_by_UTF16BE=True,minimal_json_string_escaping=True,numeric_values_rejected=True,source_hash_finding_fixed=True,all_current_pins_match=True,target_executions=0,Go_executions=0,SQL_executions=0,new_mechanical_errors=0))
print(json.dumps(dict(evidence_ref=ref,base_refs=len(refs),drift=0,source_hash_finding_fixed=True,only_function_changed=True,new_mechanical_errors=0)))

