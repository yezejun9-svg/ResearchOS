import sys
sys.dont_write_bytecode=True
import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
N=Path(__file__).resolve().parent
CV=W/'w09_c19_consumer_v7_caller_source_codex/consv7-1a11f5e'
NR=W/'w09c19_v7_actual_independent_review_codex/review-37dedbd890c44a93975558f2851d8675'
CR=W/'w09_c19_consumer_v7_independent_review_codex/cv7r-01a11f6b'
PRODUCER=W/'integration_codex/w09c19v7-producer-1a11f30'
def require(value,label):
 if not value:raise ValueError(label)
def ref(path):
 path=Path(path).resolve(strict=True);raw=path.read_bytes()
 return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def pinned(path,sha,size):
 result=ref(path);require(result['sha256']==sha and result['bytes']==size,'PIN:'+str(path));return result
def read(value):
 require(isinstance(value,dict) and set(value)=={'path','sha256','bytes'},'REF_SCHEMA')
 require(ref(value['path'])==value,'CURRENT_REF')
 return json.loads(Path(value['path']).read_bytes())
def save(name,value):
 path=N/name
 with path.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return ref(path)
def verify_members(value):
 doc=read(value);members=doc['members']
 if isinstance(members,dict):members=list(members.values())
 require(isinstance(members,list),'MEMBERS_LIST')
 for member in members:read_bytes_ref(member)
 return len(members)
def read_bytes_ref(value):
 require(isinstance(value,dict) and set(value)=={'path','sha256','bytes'},'MEMBER_REF_SCHEMA')
 require(ref(value['path'])==value,'MEMBER_REF')
 return value
def main():
 contract_ref=pinned(CV/'calling-contract.json','8ca6e8aa69565da72c0dd5f0a71673af36a02a2b148730762d109afdd5472cf3',12042)
 contract=read(contract_ref)
 source_ref=pinned(CV/'run_c19_consumers.actual_owned.py','28cb94dfd8e941afd5d292e26a931047097e93265c3b8c98f37b2e39ec73b9f5',22088)
 require(source_ref==contract['source_caller_ref'],'SOURCE_CALLER_CONTRACT')
 native_hdf=pinned(NR/'HDF.json','d6adce580965b6d8c607a5176a45043dbfb445a51d7d50d5a7f2195b89dcaa16',5552)
 native_mf=pinned(NR/'MF.json','511830b94ffdd4059727d09bc240e02acb6976b5ee7f50ff1ac9f320cd3f4218',17590)
 caller_hdf=pinned(CR/'HDF.json','a2997039d4d26b1a1d5447e2f6176cee55234df541e2e795cf6394465d519d25',3358)
 caller_mf=pinned(CR/'MF.json','a6def124972f8aa5e41485869aa96c436eadcbb5f1a6a460bb919a190a62044d',4269)
 native=read(native_hdf);caller=read(caller_hdf)
 require(native['actual_fixture_decision']=='QUALIFIED' and native['consumer_readiness']=='QUALIFIED_PENDING_ROOT_ACTUAL_CONSUMPTION','NEW_NATIVE_QUALIFICATION')
 require(native['actor_id']=='codex:/root/native_temp_independent_review' and not native['formal_acceptance'] and not native['consumer_executed'],'NATIVE_NONAUTHOR_BOUNDARY')
 require(native['manifest_ref']==native_mf and caller['manifest_ref']==caller_mf and caller['candidate_ref']==source_ref,'REVIEW_BINDINGS')
 require(caller['status']=='SOURCE_ACCEPTED_PENDING_NEW_PRODUCER_QUALIFICATION_AND_ROOT_SCOPE' and caller['formal_case_accepted_delta']==0,'CALLER_SOURCE_REVIEW')
 member_counts={'producer_review':verify_members(native_mf),'caller_review':verify_members(caller_mf)}
 closed_ref=pinned(PRODUCER/'validation.closed.json','305551f1fa3c4a2bd5f04795fcff205a66038de4c16d861aa619a3a42ae09384',4271)
 closed=read(closed_ref);packet_ref=read_bytes_ref(closed['native_packet_ref']);packet=read(packet_ref)
 report_ref=read_bytes_ref(native['original_report_ref']);tool_ref=read_bytes_ref(native['native_tool_run_ref'])
 require(packet['original_report_ref']==report_ref and packet['original_tool_run_ref']==tool_ref,'PACKET_NATIVE_REVIEW_EQUAL')
 report=read(report_ref);tool=read(tool_ref)
 require(report['run_id']==native['original_run_id']==tool['run_id'] and report['status']=='PASS' and report['exit_code']==0,'ACTUAL_NEW_RUN')
 vector_ref=pinned(N/'canonical-input-vector.json','1dfed486c4cd91f043dd48bd6b6eef46dc06ca52bce9339289c6e5cb13dcffda',983)
 vector=read(vector_ref);require(set(vector)=={'schema','checkpoint_revision','refs'} and vector['checkpoint_revision']==366,'CP366_VECTOR')
 for item in vector['refs']:read_bytes_ref(item)
 pre=read(closed['canonical_pre_run_ref']);require(pre['canonical_input_vector_ref']==vector_ref and pre['refs']==vector['refs'],'PRODUCER_VECTOR_CURRENT')
 require(read(next(item for item in vector['refs'] if Path(item['path']).name=='path_ownership.json'))['revision']==170,'OW170')
 copies=native['candidate_copy_refs'];require(len(copies)==3,'EXACT_THREE_MODE_COPIES')
 common=read_bytes_ref(copies[0]);require(common['sha256']==native['mode_review_ref']['sha256'] and common['bytes']==native['mode_review_ref']['bytes'],'COMMON_COPY_BYTES')
 common_doc=read(common);require(common_doc['decision']=='QUALIFIED' and common_doc['run_id']==report['run_id'],'COMMON_QUALIFIED_CURRENT')
 modes=[]
 for route,decision_ref,original_ref in zip(contract['route_order'],copies[1:],native['route_specific_decision_refs']):
  decision_ref=read_bytes_ref(decision_ref);decision=read(decision_ref)
  require((decision_ref['sha256'],decision_ref['bytes'])==(original_ref['sha256'],original_ref['bytes']),'MODE_COPY_BYTES')
  require(decision['decision']=='QUALIFIED' and decision['route']==route and decision['run_id']==report['run_id'],'EXACT_QUALIFIED_ROUTE')
  rel=decision['independent_review_ref'];candidate=Path(contract['scope_fixed_values']['candidate_root'])
  require(read_bytes_ref({'path':str(candidate/rel['path']),'sha256':rel['sha256'],'bytes':rel['bytes']})==common,'SAME_COMMON_REVIEW')
  modes.append({'route':route,'decision_ref':decision_ref,'independent_review_ref':common})
 guards=[ref(path) for path in contract['producer_guard_cleanup_paths']]
 for item in guards:
  guard=read(item);require(guard['closed'] is True and guard['errors']==[] and guard['retained_handles_count']==0,'PRODUCER_GUARD_CLOSED')
 request={'schema':contract['request_schema'],'producer_closed_ref':closed_ref,'native_packet_ref':packet_ref,'report_ref':report_ref,'tool_run_ref':tool_ref,'producer_review_handoff_ref':native_hdf,'producer_review_manifest_ref':native_mf,'caller_review_handoff_ref':caller_hdf,'caller_review_manifest_ref':caller_mf,'canonical_vector_ref':vector_ref,'modes':modes,'producer_guard_cleanup_refs':guards}
 scope={'schema':contract['scope_schema'],**contract['scope_fixed_values']}
 for field in contract['scope_binding_fields_equal_request']:scope[field]=request[field]
 require(set(scope)==set(contract['scope_required_fields']),'EXACT_SCOPE_FIELDS')
 require(not Path(scope['consumer_receipt_root']).exists() and not Path(scope['consumer_environment_root']).exists(),'FRESH_CONSUMER_ROOTS')
 scope_ref=save('component-consumer.scope.root.json',scope);request['root_consumer_scope_ref']=scope_ref
 require(set(request)==set(contract['request_required_fields']),'EXACT_REQUEST_FIELDS')
 request_ref=save('component-consumer.request.root.json',request)
 ready=save('component-consumer.ready.root.json',{'status':'ROOT_SCOPE_REQUEST_READY_FOR_TWO_COMPONENT_CONSUMERS','scope_ref':scope_ref,'request_ref':request_ref,'source_caller_ref':source_ref,'producer_review_ref':native_hdf,'caller_review_ref':caller_hdf,'member_counts':member_counts,'canonical_vector_ref':vector_ref,'producer_run_id':report['run_id'],'formal_delta':0,'Main_adopted':False,'new_provider_requests':0})
 print(json.dumps({'ready_ref':ready,'scope_ref':scope_ref,'request_ref':request_ref,'formal_delta':0,'actual_consumers_executed':False}),flush=True)
if __name__=='__main__':main()

