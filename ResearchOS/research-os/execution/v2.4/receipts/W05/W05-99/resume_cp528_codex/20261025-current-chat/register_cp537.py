import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;O=N/'continuation-cp537'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix() if p.is_relative_to(R.resolve()) else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write(chr(10))
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp537.pending')
 with q.open('xb')as f:f.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==536 and ow['revision']==322 and len(cp['failure_counters'])==2117
res=read(N/'React-Main-integration-result.json');base=read(N/'React-Main-integration-baseline.json');prior=read(N/'continuation-cp536/RESUME.current.json')
assert res['status']=='REVIEWED_SOURCE_INTEGRATED_AND_EXACT_STAGED_BUILD_VERIFIED' and res['formal_increment']==0
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda *x:subprocess.check_output(git+list(x),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==res['Main_HEAD'] and g('rev-parse','HEAD^{tree}').decode().strip()==res['Main_tree']
assert not g('diff','--cached','--name-only')
assert g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==base['dirty_paths']
for x in base['dirty_files']:
 p=R/x['relative_path'];assert p.is_file()==x['exists']
 if x['exists']:assert ref(p)['sha256']==x['sha256']
for x in base['protected_source']+base['original_dist_refs']+res['staged_build_refs']:
 assert ref(Path(x['path']))['sha256']==x['sha256']
for number in ['030-react-main-preflight','031-react-main-fast-forward','032-react-main-after-ff','033-react-main-staged-build','034-react-main-integration-verify']:
 d=read(N/(number+'.recipe.result.json'));assert d['native_exit']==0
c57_ref=prior['active_source_cards'][0];assert ref(R/c57_ref['path'])['sha256']==c57_ref['sha256']
assert res['C57_base_commit_unchanged']=='085b4711afe0c1288448b174eef24ecd5af0551b'
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
completion={'schema':'researchos.React-Main-integration-completion.v1','at':now,'status':'INDEPENDENTLY_REVIEWED_SOURCE_INTEGRATED_LOCALLY','prior_Main_HEAD':res['prior_Main_HEAD'],'current_Main_HEAD':res['Main_HEAD'],'current_Main_tree':res['Main_tree'],'integration_result_ref':ref(N/'React-Main-integration-result.json'),'scope_ref':ref(N/'continuation-cp536/React-Main-integration-scope.json'),'source_adoption_ref':prior['react_source_adopted_ref'],'command_result_refs':[ref(N/(x+'.recipe.result.json'))for x in ['030-react-main-preflight','031-react-main-fast-forward','032-react-main-after-ff','033-react-main-staged-build','034-react-main-integration-verify']],'preservation':{'dirty20_byte_preserved_before_checkpoint_update':True,'protected9_unchanged':True,'old_dist33_unchanged':True,'staged3_equal_reviewed_candidate':True,'Root_checkpoint_ownership_handoff_updates':'Intentional after preservation verification; not source changes'},'current_C57_scope_ref':c57_ref,'C57_base_commit':res['C57_base_commit_unchanged'],'original_runtime_instance_switched':False,'native_packaged_Desktop':'NOT_RUN','formal_increment':0,'failure_records_preserved':2117}
new(O/'React-Main-integration-completed.json',completion)
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v115',at=now,checkpoint_revision=537,ownership_revision=323,head=res['Main_HEAD'],current_Main_HEAD=res['Main_HEAD'],current_Main_tree=res['Main_tree'],prior_Main_HEAD_before_react_integration=res['prior_Main_HEAD'],react_Main_integration_status=completion['status'],react_Main_integration_result_ref=ref(O/'React-Main-integration-completed.json'),failure_records_preserved=2117)
resume['next_command']='Continue C57 implementation on immutable Source43 base085b4711 in its owned worktree; complete historical maintenance transaction/boot fixtures, freeze author manifest then independent review. Main React14 now exactly integrated at7d1e3ff with identical stagedbundle; preserve dirty20/protected9/old33dist and original runtime/data. Formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=537,expected_previous_revision=536,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'],current_Main_HEAD=res['Main_HEAD'],current_Main_tree=res['Main_tree'])
cp['work_in_progress'].update(current_chat_continuation_cp537=rr,react_Main_integration_result_ref=ref(O/'React-Main-integration-completed.json'))
cp['evidence_index'].append({'kind':'REACT_SOURCE14_REVIEWED_MAIN_FF_AND_IDENTICAL_STAGED_BUNDLE','ref':rr,'formal_increment':0})
ow.update(revision=323,expected_previous_revision=322,updated_at=now,updated_by='codex:/root')
ow['special_paths']['react_Main_integration'].update(state='COMPLETED_EXACT_LOCAL_FF_AND_STAGED_BUILD',evidence_ref=ref(O/'React-Main-integration-completed.json'),current_Main_HEAD=res['Main_HEAD'])
ow['special_paths']['react_frontend_source'].update(state='FROZEN_SOURCE_ACCEPTED_AND_INTEGRATED_IN_MAIN')
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as f:f.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+chr(10)).encode())
swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+chr(10)).encode())
swap(hp,raw[hp],('# Current verified continuation CP537'+chr(10)*2+'Read '+rr['path']+' first. Reviewed React14 integrated in Main7d1e3ff; stagedbundle byte-identical, originaldist33 and protected9 retained. Original dirty20 preserved before these intentional Root checkpoint updates. C57 active on immutable Source43 base085b. Original runtime not switched. Formal0/42/all22open, mixedrecords2117.'+chr(10)*2).encode()+raw[hp])
assert sp.read_bytes()==raw[sp] and cp['failure_counters']==read(O/'checkpoint.before.raw.json')['failure_counters']
print(json.dumps({'checkpoint':537,'ownership':323,'mixed_records':2117,'current_Main_HEAD':res['Main_HEAD'],'resume':rr,'integration_completion':ref(O/'React-Main-integration-completed.json')},ensure_ascii=False))
