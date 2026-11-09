from pathlib import Path
import hashlib,json,types
D=Path(__file__).resolve().parent
SUP=Path(r'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99\full_w09_current_resource_readonly_codex\new-current-resource-readonly-20261010-01\review_support.py')
assert hashlib.sha256(SUP.read_bytes()).hexdigest()=='567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s=types.ModuleType('support');s.__file__=str(SUP);exec(compile(SUP.read_bytes(),str(SUP),'exec'),s.__dict__);s.D=D
pair=s.capture('60b15e',1,1,1261)
prefix=json.loads((D/'independent-metadata-checks.json').read_bytes());guard=json.loads((D/'source-review-guard.closed.json').read_bytes())
assert len(prefix['checks'])==prefix['passed']==11 and all(x['passed'] for x in prefix['checks'])
assert guard['closed'] and guard['retained_handles_count']==0 and not guard['errors']
record=s.write('original1261.evidence.json',dict(original_ordinal=1261,actual_chunk_id='60b15e',actual_outer_exit=1,actual_Python_exit=1,actual_Native_exit=None,actual_Go_exit=None,actual_SQL_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,actual_TP_exit=None,raw_ref=pair['raw_ref'],binding_ref=pair['binding_ref'],original_script_ref=s.pin(D/'review_source.source.py'),successful_prefix_ref=s.pin(D/'independent-metadata-checks.json'),actual_finally_guard_ref=s.pin(D/'source-review-guard.closed.json'),successful_prefix_count=11,guards_closed=True,product_calls=0))
print(json.dumps(dict(**pair,evidence_ref=record,prefix_ref=s.pin(D/'independent-metadata-checks.json'),guard_ref=s.pin(D/'source-review-guard.closed.json')),ensure_ascii=False))
