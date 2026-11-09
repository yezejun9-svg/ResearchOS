import pathlib,json,hashlib
N=pathlib.Path(__file__).parent
def pin(p):
 b=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def js(name,obj):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=True,indent=2);f.write('\n')
data=json.loads((N/'source-input.json').read_text(encoding='utf-8'))
initial=json.loads((N/'sourceguard.initial.json').read_text(encoding='utf-8'))['pins']
checks=[]
for expected in initial:
 actual=pin(pathlib.Path(expected['path']))
 assert actual==expected,expected['path']
 checks.append({'before':expected,'after':actual,'equal':True})
js('sourceguard.final.json',{'all_unchanged':True,'inputs':len(checks),'checks':checks,'canonical_Root_state_in_scope':False})
rel='internal/domain/client_protocol_control_windows_test.go'
base=(N/'base-root'/rel).read_bytes()
candidate=(N/'candidate-root'/rel).read_bytes()
replacement=json.loads((N/'source-replacement.json').read_text(encoding='utf-8'))
old,new=replacement['old'].encode(),replacement['new'].encode()
assert candidate.count(new)==1 and candidate.replace(new,old,1)==base
assert base.count(old)==1
before=base.split(old);after=candidate.split(new)
assert before==after
assert candidate.count(b'func Test')==base.count(b'func Test')==3
assert candidate.count(b'ACKNOWLEDGED')==base.count(b'ACKNOWLEDGED')-1
js('final-static-checks.json',{'exact_inverse':True,'outside_body_byte_equal':True,'test_names_preserved':3,'only_legacy_ACK_expectation_replaced':True,'sourceguard_closed':True,'Go_compile_test':False,'SQL_native_model':False,'self_approved':False})
members={}
for p in sorted(N.rglob('*')):
 if p.is_file() and p.name not in {'MF.json','HDF.json'}:members[p.relative_to(N).as_posix()]=pin(p)
js('MF.json',{'schema':'researchos.expired-writer-attach-source-manifest.v1','authority':'NONE','formal_acceptance':False,'members':members,'exclusions':['MF.json','HDF.json'],'seal_tool_result':'external actual tool result'})
hdf={'schema':'researchos.expired-writer-attach-source-handoff.v1','status':'SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL','namespace':str(N),'candidate_root':str(N/'candidate-root'),'actor_id':'codex:/root/command_queue_impl','authority':'NONE','self_approved':False,'formal_acceptance':False,'production_ready':False,
'manifest_ref':pin(N/'MF.json'),'manifest_member_count':len(members),'source_ref':pin(N/'candidate-root'/rel),'base_copy_ref':pin(N/'base-root'/rel),'original_T6_ref':data['t6']+'/'+rel,'diff_ref':pin(N/'test.patch'),'replacement_ref':pin(N/'source-replacement.json'),'sourceguard_initial_ref':pin(N/'sourceguard.initial.json'),'sourceguard_final_ref':pin(N/'sourceguard.final.json'),'report_ref':pin(N/'report.md'),'static_ref':pin(N/'final-static-checks.json'),
'input_packages':data['packages'],'required_ATT3_production':pin(pathlib.Path(data['att3'])/'candidate-root/internal/domain/client_protocol.go'),'Q5_review':'NOT_ASSUMED_ACCEPTED_NO_NEW_HELPER_DEPENDENCY',
'actions':{'Go_gofmt_parser_compile_test':False,'SQL_native_model':False,'Main_canonical_T6_old_Source_write':False,'production_write':False},
'mechanical_failures':[{'ordinal':853,'actualOuter':1,'actualPython':None,'native':None,'ref':pin(N/'failure-origin.853.json')},{'ordinal':854,'actualOuter':0,'actualPython':None,'native':None,'ref':pin(N/'failure-origin.854.json')},{'ordinal':855,'actualOuter':None,'actualPython':None,'native':None,'process_created':False,'ref':pin(N/'failure-origin.855.json')}],
'failure_counter_reset':False,'positive_test_actual':'OPEN_PENDING_ROOT_EXECUTION','restore_fresh_positive':'BLOCKED_PENDING_ROOT_RESOURCE','scope':'one existing test body only; old assertions preserved; no response mutation',
'root_required':['independent Source review','fresh approved ATT3/Q5/separate legacy Source composition','actual compile and strict original test execution with real process exit and closure evidence'],'STOP':True}
js('HDF.json',hdf)
for ref in members.values():
 assert pin(pathlib.Path(ref['path']))==ref
print(json.dumps({'HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json'),'members':len(members),'source':hdf['source_ref'],'sourceguard':hdf['sourceguard_final_ref'],'failures':hdf['mechanical_failures'],'STOP':True}))

