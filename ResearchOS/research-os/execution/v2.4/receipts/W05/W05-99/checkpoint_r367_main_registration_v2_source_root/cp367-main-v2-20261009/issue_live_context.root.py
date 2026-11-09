import hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
N=Path(__file__).resolve().parent/'root-postseal-live-950-20261009'
def ref(p,sha=None,size=None):
 p=Path(p).resolve(strict=True);raw=p.read_bytes();v={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
 if sha is not None:assert v['sha256']==sha and v['bytes']==size
 return v
def save(name,v):
 with (N/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return ref(N/name)
facts=json.loads((Path(__file__).resolve().parent/'checkpoint.execution.facts.json').read_bytes())
assert facts['highest_observed_ordinal']==947 and facts['next_failure_ordinal']==948
origin948=ref(B/'restored21_session_runtime_caller_source_codex/r21v2caller-20261009-02/original-failure.948.json','87066617f8c62ebfc76cc542f4f57196321dd309fbdf2f3d2b1aa050cef6cb50',1244)
origin949=ref(B/'checkpoint_r367_main_registration_v2_independent_review_codex/cp367v2r-01a11fad/failure-read.original-tool-io.json','4ef8f7c8ed41bf734b8df8f9c3c3c302df866ff94f957f0c14d6601c38136d2d',22413)
review=ref(B/'checkpoint_r367_main_registration_v2_independent_review_codex/cp367v2r-01a11fad/HDF.json','4bb022d282498db9225fbb1b544753b73f1ba11223281424155e79e5a462e4ba',3827)
assert json.loads(Path(review['path']).read_bytes())['decision']=='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_LIVE_CONTEXT_VALIDATION'
stamp=datetime.now(timezone.utc).isoformat()
N.mkdir(exist_ok=False)
mapping=save('failure-origin.949.registration.root.json',{'schema':'researchos.root-original-failure-registration.v1','issued_by':'codex:/root','created_utc':stamp,'ordinal':949,'origin_ref':origin949,'chunk_id':'b7b538','actual_outer_exit':1,'actual_python_exit':None,'actual_native_exit':None,'actual_model_exit':None,'original_calls':1,'replay':False,'counter_reset':False,'source_review_ref':review,'sealed_origin_ordinal_NULL_preserved':True})
ctx=save('live-context.actual.root.json',{'schema':'researchos.root-postseal-live-diagnostic-context.v1','issued_by':'codex:/root','created_utc':stamp,'source_cutoff':{'highest_ordinal':947,'next_failure_ordinal':948},'next_original_failure_ordinal':950,'pending':[{'ordinal':948,'origin_ref':origin948,'description':'A21 caller v2 Source apply_patch expected context not found; full original tool IO retained, all numeric exits NULL, no Main/Canon/product call.'},{'ordinal':949,'origin_ref':origin949,'description':'CP367 v2 independent Source review readonly query b7b538 appended a nonexistent filename; observed outer exit1, Python/Native/model NULL; no writes or replay. Root ordinal949 registration is separate and original sealed NULL preserved.'}]})
print(json.dumps({'live_context_ref':ctx,'failure949_registration_ref':mapping,'postseal_source_review_ref':review,'actual_source_cutoff_next':948,'next_original_failure_ordinal_live':950},ensure_ascii=False))
