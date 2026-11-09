import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
N=Path(__file__).resolve().parent;C=N.parent.parent/'w09_c19_caller_source_codex/w09c19-1a11f08'
def pin(p):
 raw=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,x):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
checks=json.loads((N/'checks.json').read_bytes())
assert checks['all_pass'] and checks['count']==563 and checks['inputs']==153
for v in json.loads((N/'input-pins.json').read_bytes()):assert pin(Path(v['path']))==v,v['path']
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal.json','seal.original-tool-io.json','postseal.original-tool-io.json')]
save('MF.json',{'schema':'researchos.independent-review-manifest.v1','members':members,'member_count':len(members)})
save('HDF.json',{'schema':'researchos.w09-c19-caller-independent-source-review.v1','status':'SOURCE_ACCEPTED_PENDING_ROOT_SCOPE_REGISTRATION_AND_ACTUAL','candidate_handoff_ref':pin(C/'handoff.json'),'candidate_manifest_ref':pin(C/'manifest.json'),'calling_contract_ref':pin(C/'root-calling-contract.json'),'report_ref':pin(N/'report.md'),'manifest_ref':pin(N/'MF.json'),'checks_ref':pin(N/'checks.json'),'input_pins_ref':pin(N/'input-pins.json'),'guard_ref':pin(N/'sourceguard.final.json'),'delta_ref':pin(N/'independent-delta.json'),'synthetic_order_control_ref':pin(N/'order-bridge-control.json'),'check_count':563,'input_count':153,'original_six_source_byte_identical':True,'complete_caller_forward_inverse':True,'five_fresh_paths_absent':True,'canonical_revision':364,'four_canonical_unchanged':True,'formal_consumers':'NOT_RUN_REGISTRY_UNBOUND','execution_grant':False,'Main_adopted':False,'formal_acceptance':False,'formal42_new_acceptance':0,'actual_Git_Go_SQL_producer_product_native_API_private_model':False,'formal_consumer_main_executed':False,'new_mechanical_failures':[],'author_existing_origin921_retained':True,'Root_only_registration_actual_and_canonical':True,'STOP_FINAL':True})
print(json.dumps({'HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json')}))

