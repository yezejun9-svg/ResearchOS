import pathlib,json,hashlib
N=pathlib.Path(__file__).parent
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def js(name,obj):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=True,indent=2);f.write('\n')
data=json.loads((N/'source-input.json').read_text(encoding='utf-8'))
checks=[]
for expected in json.loads((N/'sourceguard.initial.json').read_text(encoding='utf-8'))['refs']:
 actual=pin(pathlib.Path(expected['path']));assert actual==expected,expected['path']
 checks.append({'before':expected,'after':actual,'equal':True})
rel='internal/domain/client_protocol_attach_contract_windows_test.go'
base=(N/'base-root'/rel).read_bytes();new=(N/'candidate-root'/rel).read_text(encoding='utf-8')
for replacement in reversed(data['replacements']):new=new.replace(replacement['new'],replacement['old'],1)
assert new.encode('utf-8')==base
for name in data['directT9']:assert (N/'contract-inputs/T9'/name).read_bytes()==(pathlib.Path(data['t9'])/name).read_bytes()
js('sourceguard.final.json',{'all_declared_inputs_unchanged':True,'inputs':len(checks),'checks':checks,'contract_copies_byte_equal':True,'exact_inverse':True,'canonical_Root_state_excluded':True})
members={}
for p in sorted(N.rglob('*')):
 if p.is_file() and p.name not in {'HDF.json','MF.json'}:members[p.relative_to(N).as_posix()]=pin(p)
js('MF.json',{'schema':'researchos.attach-contract-fixture-revision-manifest.v1','authority':'NONE','formal_acceptance':False,'members':members,'exclusions':['MF.json','HDF.json'],'seal_tool_result':'external actual tool result'})
h={'schema':'researchos.attach-contract-fixture-revision-handoff.v1','status':'SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL','actor_id':'codex:/root/command_queue_impl','namespace':str(N),'candidate_root':str(N/'candidate-root'),'candidate_files':1,'production_files':0,'authority':'NONE','self_approved':False,'formal_acceptance':False,'production_ready':False,
'manifest_ref':pin(N/'MF.json'),'manifest_member_count':len(members),'source_ref':pin(N/'candidate-root'/rel),'base_ref':pin(N/'base-root'/rel),'diff_ref':pin(N/'two-fixtures.patch'),'replacement_ref':pin(N/'source-replacements.json'),'contract_ref':pin(N/'contract-mapping.json'),'report_ref':pin(N/'report.md'),'static_ref':pin(N/'static-preservation.json'),'sourceguard_final_ref':pin(N/'sourceguard.final.json'),
'ATT3_HDF':{'path':data['att3']+'/HDF.json',**data['hdf']},'ATT3_MF':{'path':data['att3']+'/MF.json',**data['mf']},'prior_actual_ref':pin(N/'prior-actual-failures.json'),
'preservation':{'five_Test_names':True,'all_original_case_names':True,'outside_two_case_blocks_byte_equal':True,'negative_purposes_preserved':True,'common_rejection_assertion_unchanged':True,'CHECK_and_protocol_error_whitelist_unchanged':True,'nil_decode_never_passed_to_Execute':True},
'mechanical_failures':[{'ordinal':876,'actualOuter':1,'actualPython':None,'native':None,'ref':pin(N/'failure-origin.876.json')},{'ordinal':878,'actualOuter':None,'actualPython':None,'native':None,'process_started':False,'ref':pin(N/'failure-origin.878.json')},{'ordinal':882,'actualOuter':1,'actualPython':1,'native':None,'ref':pin(N/'failure-origin.882.json'),'failed_script_ref':pin(N/'construct-source.failed.882.py')}],
'failure_counter_reset':False,'actions':{'Go_AST_parser_compile_test_gofmt':False,'SQL_native_model':False,'Main_canonical_T6_T9_oldSource_write':False},'new_actual':'PENDING_ROOT','shared_fence_packet':'UNCHANGED_SOURCE_BLOCKED','root_next':['independent Source review','fresh approved composition and actual original five attach groups'],'STOP':True}
js('HDF.json',h)
for ref in members.values():assert pin(pathlib.Path(ref['path']))==ref
print(json.dumps({'HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json'),'members':len(members),'source':h['source_ref'],'guard':h['sourceguard_final_ref'],'failures':h['mechanical_failures'],'STOP':True}))

