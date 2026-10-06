"""SYNTHETIC_NOT_PRODUCT: actual unchanged v1 field guard compatibility."""
from pathlib import Path
import importlib.util,json,hashlib,sys
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
required=('schema','scope','task_id','step_id','executor_id','verifier_id','issued_at','acceptance_baseline_ref','evidence_index_ref','current_context_ref','owned_case_verdicts','parent_gate_verdicts','open_blockers','construction_decision')
value={k:None for k in required}
value.update(collection_completion_ref={'path':'SYNTHETIC_COMPLETION','sha256':'a'*64},collection_source_order_review='VERIFIED_EXCLUSIVE_RUN_BEFORE_PREPROOF_PREPUBLISH_FINALLY_AFTER_AND_FINAL_EXIT')
rows=[]
for i,name in enumerate(['execution/v2.4/formal_case_index.py','execution/v2.4/receipts/W04/W04-99/formal_validator_codex/validate.py']):
 p=ROOT/name;raw=p.read_bytes();spec=importlib.util.spec_from_file_location('review_v1_guard_'+str(i),p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;exec(compile(raw,str(p),'exec'),m.__dict__)
 try:m.fields(value,required,('supersedes_review_refs','supersession_reason'),label='independent review')
 except Exception as exc:rows.append({'reader':name,'sha256':hashlib.sha256(raw).hexdigest(),'actual_result':'REFUSED','exception':type(exc).__name__,'code':getattr(exc,'code',None),'detail':str(exc)})
 else:raise RuntimeError('Expected actual v1 refusal absent')
out={'classification':'SYNTHETIC_NOT_PRODUCT','finding':'Helper-required review additions are forbidden by actual unchanged v1 readers','results':rows,'source_changes':0}
with (OUT/'schema_conflict_repro.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(out,ensure_ascii=False))
