from pathlib import Path
import json,hashlib
B=Path(__file__).parent
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
old=B/'B-r3-independent-root-evidence-verification.json';x=old.read_bytes()
try:
 v=json.loads(x);issue=None
except json.JSONDecodeError as e:
 assert x.endswith(bytes([92,110]));v=json.loads(x[:-2]);issue={'type':'ROOT_GENERATOR_LITERAL_NEWLINE_JSON_BOUNDARY','detail':str(e),'trailing_bytes':list(x[-2:]),'old':ref(old),'native_exit_of_generation':0,'old_preserved':True,'not_Source_or_test_failure':True}
assert v['verified_count']==199 and not v['unresolved']
new=B/'B-r3-independent-root-evidence-verification-r2.json'
with new.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write(chr(10))
assert json.loads(new.read_bytes())==v
diag=B/'root-evidence-json-boundary-cp527.json'
with diag.open('x',encoding='utf8')as f:json.dump({'record':issue,'corrected':ref(new),'counter_record':1},f,ensure_ascii=False,indent=2);f.write(chr(10))
print(json.dumps({'corrected':ref(new),'diagnostic':ref(diag),'previous_issue':issue,'count':199},ensure_ascii=False))
