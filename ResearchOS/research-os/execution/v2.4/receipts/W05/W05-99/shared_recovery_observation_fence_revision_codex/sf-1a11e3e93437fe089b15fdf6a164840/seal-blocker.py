import pathlib,json,hashlib
N=pathlib.Path(__file__).parent
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def js(name,obj):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=True,indent=2);f.write('\n')
data=json.loads((N/'source-input.json').read_text(encoding='utf-8'))
initial=json.loads((N/'sourceguard.initial.json').read_text(encoding='utf-8'))['refs']
checks=[]
for expected in initial:
 actual=pin(pathlib.Path(expected['path']));assert expected==actual,expected['path']
 checks.append({'before':expected,'after':actual,'equal':True})
for name in data['files']:assert (N/'frozen-inputs/T6'/name).read_bytes()==(pathlib.Path(data['t6'])/name).read_bytes()
for name in data['publicDriver']:assert (N/'frozen-inputs/modernc-sqlite-v1.60.1'/pathlib.Path(name).name).read_bytes()==pathlib.Path(name).read_bytes()
assert not (N/'candidate-root').exists()
js('sourceguard.final.json',{'all_declared_inputs_unchanged':True,'count':len(checks),'checks':checks,'frozen_copies_byte_equal':True,'candidate_files':0,'main_canonical_T6_oldSource_write':False})
members={}
for p in sorted(N.rglob('*')):
 if p.is_file() and p.name not in {'MF.json','HDF.json'}:members[p.relative_to(N).as_posix()]=pin(p)
js('MF.json',{'schema':'researchos.shared-recovery-fence-blocker-manifest.v1','status':'SOURCE_BLOCKED','authority':'NONE','formal_acceptance':False,'members':members,'exclusions':['HDF.json','MF.json'],'final_seal_result':'external actual tool result; no self-reference'})
h={'schema':'researchos.shared-recovery-fence-blocker-handoff.v1','status':'SOURCE_BLOCKED','repair_implemented':False,'candidate_files':0,'actor_id':'codex:/root/command_queue_impl','namespace':str(N),'authority':'NONE','self_approved':False,'formal_acceptance':False,'production_ready':False,
'manifest_ref':pin(N/'MF.json'),'manifest_member_count':len(members),'report_ref':pin(N/'report.md'),'cases_ref':pin(N/'planned-cases.json'),'case_status':'PLANNED_NOT_EXECUTED','static_blocker_ref':pin(N/'static-blocker-evidence.json'),'sourceguard_initial_ref':pin(N/'sourceguard.initial.json'),'sourceguard_final_ref':pin(N/'sourceguard.final.json'),'original_reads_ref':pin(N/'original-read-tool-io.json'),'freeze_io_ref':pin(N/'freeze-tool-io.json'),
'mechanical_failures':[{'ordinal':870,'actualOuter':1,'actualPython':None,'native':None,'ref':pin(N/'failure-origin.870.json')},{'ordinal':872,'actualOuter':1,'actualPython':None,'native':None,'ref':pin(N/'failure-origin.872.json')}],'failure_counter_reset':False,'external_Root_871_not_duplicated':True,
'blocking_condition':'Direct shared trigger replacement changes populated schema24 startup guard and historical source21/22/23 schema templates. Root selected separate compatibility route; no permission escalation requested.',
'root_authorization':'FULL_IMPLEMENTATION_ALREADY_AUTHORIZED; engineering branch separation only',
'root_next':['independent review of bounded blocker evidence','preserve exact historical trigger/template inputs and design authorized compatible restore/upgrade route','implement failclosed current-epoch/time/body/receipt/native validation in separately scoped candidate','run discriminating SQLite/Go tests and independent actual review'],
'epoch_fact':'runtime_observations.epoch INTEGER; no proven cause of prior ACK failures claimed',
'actions':{'Go_parser_build_test_gofmt':False,'SQL_native_model':False,'private_credential_read':False,'Main_canonical_T6_oldSource_write':False,'production_schema_contract_migration_write':False},
'fresh_native_positive':'OPEN_PENDING_ROOT_RESOURCE','overall_goal_blocked':False,'STOP':True}
js('HDF.json',h)
for p in members.values():assert pin(pathlib.Path(p['path']))==p
print(json.dumps({'HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json'),'members':len(members),'sourceguard':h['sourceguard_final_ref'],'failures':h['mechanical_failures'],'status':h['status'],'candidate_files':0,'STOP':True}))

