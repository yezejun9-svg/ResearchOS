"""Retain original1089; correct only actual finite guard document fields."""
import hashlib,json,types
from pathlib import Path
D=Path(__file__).resolve().parent
original=D/'review_delta.py';raw=original.read_bytes()
assert len(raw)==15558 and hashlib.sha256(raw).hexdigest()=='5ba40745c8fbb36775d953631f58638fee27400bd43b7ab3070d2f8a4a609c87'
text=raw.decode()
old="all(v['closed'] and v['retained_handles_count']==0 and not v['errors'] for v in (source_guard,control_guard))"
new="all(v['schema']=='researchos.finite-source-guard.v1' and v['all_handles_closed'] is True and v['retained_handles']==0 and v['live_Canon_handles']==0 and all(x['end_identity_bytes_equal'] is True for x in v['records']) for v in (source_guard,control_guard))"
assert text.count(old)==1
text=text.replace(old,new,1)
assert text.count("'independent-delta-Source-guard.closed.json'")==1
text=text.replace("'independent-delta-Source-guard.closed.json'","'continuation-delta-Source-guard.closed.json'",1)
module=types.ModuleType('Task76_continuation_no_products');module.__file__=str(original)
exec(compile(text,str(original)+' [preserved1089 minimal guard-field continuation]','exec'),module.__dict__)
note=module.note
def persist_note(name,passed,**detail):
 note(name,passed,**detail)
 with (D/'continuation-checks-progress.jsonl').open('ab') as stream:
  stream.write((json.dumps(module.checks[-1],ensure_ascii=False,allow_nan=False)+'\n').encode())
module.note=persist_note
module.main()
