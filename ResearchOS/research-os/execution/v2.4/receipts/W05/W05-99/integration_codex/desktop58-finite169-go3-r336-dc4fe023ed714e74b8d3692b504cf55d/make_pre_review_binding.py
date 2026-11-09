import sys, json, hashlib, runpy
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(r"D:/作品集/ResearchOS/research-os")
BASE=Path(__file__).resolve().parent
q=json.loads((BASE/'root-construction.parameters.desktop58.json').read_bytes())
inputs=json.loads((BASE/'root-inputs.desktop58.pre-review.json').read_bytes())
r=q['builder_source_ref'];p=Path(r['path']);b=p.read_bytes()
assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
assert inputs['before']==[335,163,580] and inputs['after']==[336,164,603]
out=BASE/'binding.pre-review.json'
assert not out.exists()
args=[]
for key in ('scope_template_ref','runtime_resources_ref','compiler_resources_ref','current43_authority_ref','origin_cut_ref','canonical_before_ref','source_inputs_ref','metadata_code_refs_ref','failure_prefix430_ref','desktop_values_ref','toolchain_lock_ref'):
    args+=['--'+key.replace('_','-'),json.dumps(inputs[key],ensure_ascii=False)]
args+=['--controller-review-ref','null']
for key in ('before','after','main_git','public_environment'):
    args+=['--'+key.replace('_','-'),json.dumps(inputs[key],ensure_ascii=False)]
for key in ('run_uuid','registration_namespace','controller_review_path','new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root'):
    args+=['--'+key.replace('_','-'),inputs[key]]
args+=['--output',str(out)]
sys.argv=[str(p)]+args
runpy.run_path(str(p),run_name='__main__')
raw=out.read_bytes()
print(json.dumps({'binding_ref':{'path':str(out),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'final_controller_review_ref_bound':False,'actual_candidate_calls':0,'canonical_writes':0},ensure_ascii=False))

