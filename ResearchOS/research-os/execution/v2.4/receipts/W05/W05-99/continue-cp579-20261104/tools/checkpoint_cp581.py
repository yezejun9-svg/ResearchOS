import hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def put(path,value):
    tmp=path.with_name(path.name+'.new');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,path)
cpfile=root/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw)
assert cp['revision']==580 and len(cp['failure_counters'])==2327
assert not (out/'checkpoint.cp580.before-integration.json').exists()
integration=json.loads((out/'integration.json').read_bytes())
dispatch=json.loads((out/'main-dispatch-verification.json').read_bytes())
assert dispatch['status']=='PASS_DEVELOPMENT_NEGATIVE_CHECKS'
assert all(row['interpretation_matches'] for row in dispatch['rows'])
assert (root/'execution/v2.4/step_state.json').read_bytes()==(out/'step_state.before.json').read_bytes()
(out/'checkpoint.cp580.before-integration.json').write_bytes(raw)
now=datetime.now(timezone.utc).isoformat()
initial=cp['failure_counters'][:]
diagnostics=[]
for path,key in [('routing-author/diagnostics.json','records'),('host-author/diagnostics.json','events'),('readiness-author/diagnostic-index.v2.json',None),('reviews/integration-review.json','diagnostics')]:
    doc=json.loads((out/path).read_bytes())
    if key:events=doc[key]
    elif isinstance(doc,list):events=doc
    else:events=[e for e in doc['previous_round']+doc['current_round'] if 'diagnostic' in e or any(word in e.get('status','') for word in ['ERROR','FAIL','BLOCK','DENIED'])]
    for index,event in enumerate(events):
        diagnostics.append({'origin_key':f'20261104|continue-cp579|{path}|{index}','at':now,'attempts':1,'status':'PRESERVED_DEVELOPMENT_OR_TOOL_DIAGNOSTIC','detail':event,'source_ref':{'path':str((out/path).relative_to(root)),'sha256':sha(out/path)},'counter_reset':False})
for chunk,exitcode,detail in [
    ('86ed6e',0,'Default sandbox Git permission denied on D:; checkpoint read itself succeeded but unbounded output was truncated. Elevated 23ebec confirmed actual HEAD and protected tracked status. No mutation.'),
    ('337122',1,'Read-only rg guessed absent package tools/dispatch.py; actual execution/command_dispatcher/dispatch.py subsequently found.'),
    ('a1dc60',0,'Batched read included absent repo/tools path; task_packet source read completed.'),
    ('ceb849',0,'Batched rg included absent apps/desktop/build-development.mjs; main source read completed.'),
    ('bbe743',1,'Read-only rg guessed absent apps/desktop/build.mjs; actual build-development.py subsequently found.'),
    ('007713',1,'Expected pending integration-review receipt was not yet present during a read-only check. No operation was replayed and no product action occurred.'),
    ('d81bc0/25b111',0,'Known local endpoint GET /api/tags under elevated context returned SocketException ConnectionRefused. Metadata-only, inference0, credentialfalse. Resource gap only, not runtime failure or new model qualification.')]:
    diagnostics.append({'origin_key':'20261104|continue-cp579|root|'+chunk,'at':now,'attempts':1,'status':'READONLY_TOOL_OR_RESOURCE_DIAGNOSTIC','tool_chunk':chunk,'exit':exitcode,'detail':detail,'counter_reset':False})
known={r.get('origin_key') for r in initial}
for record in diagnostics:
    assert record['origin_key'] not in known
    cp['failure_counters'].append(record);known.add(record['origin_key'])
assert cp['failure_counters'][:len(initial)]==initial
put(out/'diagnostic-import.json',{'before':len(initial),'after':len(cp['failure_counters']),'prefix_preserved':True,'imported':diagnostics,'mixed_development_and_tool_diagnostics_not_native_product_failure_count':True})
refs={}
for relative in ['integration.json','main-dispatch-verification.json','reviews/routing-review.json','reviews/host-review.json','reviews/integration-review.json','host-author/source-manifest.json','routing-author/author-summary.json','readiness-author/READINESS.v2.md','readiness-author/diagnostic-index.v2.json','local-model-resource.json','local-model-resource-elevated.json','task-packet-after-integration-result.json']:
    refs[relative]={'path':str((out/relative).relative_to(root)),'sha256':sha(out/relative)}
cp['expected_previous_revision']=580;cp['revision']=581;cp['updated_at']=now;cp['updated_by']='codex:/root'
cp['superseded_cp580_control_fields']={'head':cp.get('head'),'current_Main_HEAD':cp.get('current_Main_HEAD'),'current_Main_tree':cp.get('current_Main_tree'),'next_command':cp.get('next_command')}
cp['head']=integration['main_head'];cp['current_Main_HEAD']=integration['main_head'];cp['current_Main_tree']=integration['main_tree']
cp['current_effective_formal_status']['current_head']=integration['main_head'];cp['current_effective_formal_status']['needs_rederive_after_source_change']=True
next_command='Read continue-cp579-20261104/RESUME.json and readiness-author/READINESS.v2.md. Use the frozen task selector; next source scope may expose task --prompt through the existing authenticated session/goal CLI path after strict parsing. Ordinary LIVE delivery checker, fresh trusted workspace selection, current runtime qualification and reachable local model are still required. Do not replay consumed scopes or reset counters.'
resume={'schema':'researchos.cp581-resume.v1','checkpoint_revision':581,'status':'COMPATIBILITY_FIXES_INTEGRATED_LIVE_DELIVERY_OPEN','main_head':integration['main_head'],'main_tree':integration['main_tree'],'source_files_integrated':17,'registry_revision':41,'reviews':refs,'current_card':'W05-99','formal_accepted':0,'formal_required':42,'formal_increment':0,'all_22_parents_accepted':False,'failure_records':len(cp['failure_counters']),'counter_reset':False,'step_state_unchanged':True,'native_calls_this_scope':0,'provider_inference_calls_this_scope':0,'local_metadata_gets':'Root default1 + root elevated1 + readiness agent1, each inference0; exact receipts/transcripts retained.','remaining':['Current Mu formal LIVE driver for W05 selectors is absent; preflight is deliberately BLOCKED/NOT_RUN.','Ordinary LIVE Goal business acceptance remains unavailable outside the existing planning exception.','First-use workspace requires genuine trusted chooser, not fabricated selection_ref.','Fresh instance needs current qualification and purpose-bound authorization.','Declared local model endpoint 127.0.0.1:11435 refused connection at the recorded elevated probe.'],'next':next_command}
put(out/'RESUME.json',resume)
cp['next_command']=next_command
cp['current_implementation']={'status':resume['status'],'at':now,'resume_ref':str((out/'RESUME.json').relative_to(root)),'integration_ref':refs['integration.json'],'formal_increment':0,'active_construction_owners':[]}
for kind,record in zip(['W05_ROUTING_COMPAT','SHARED_HOST_DISCOVERY_COMPAT'],integration['records']):
    cp['workers'].append({'step_id':'W05-99','slice_id':kind,'owner':'codex:/root/workbench_builder' if kind=='W05_ROUTING_COMPAT' else 'codex:/root/resume_audit','worktree':record['worktree'],'state':'INDEPENDENT_SOURCE_REVIEWED_AND_INTEGRATED_NOT_FORMAL_ACCEPTANCE','main_source_head':integration['main_head'],'integration_ref':refs['integration.json']})
cp['blocked_resources'].append({'resource_id':'CURRENT_MU_W05_FORMAL_LIVE_DRIVER','status':'IMPLEMENTATION_GAP','blocks':['W05-G02','W05-H08','W05-P01','W05-U02','A04'],'evidence':refs['main-dispatch-verification.json'],'recorded_at':now,'other_branches_remain_eligible':True})
cp['blocked_resources'].append({'resource_id':'CURRENT_DECLARED_LOCAL_MODEL_11435','status':'CONNECTION_REFUSED_AT_PROBE','blocks':['Fresh local model qualification and model task only'],'evidence':refs['local-model-resource-elevated.json'],'recorded_at':now,'other_branches_remain_eligible':True})
assert cpfile.read_bytes()==raw
put(cpfile,cp)
handoff=root/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=handoff.read_bytes();(out/'handoff.cp580.before-integration.md').write_bytes(old)
prefix=('# Current resume CP581\n\nRead execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104/RESUME.json. W05 selector/locked-Python repair and CLI/Desktop owned-host discovery compatibility were independently reviewed and integrated. Source tests and fail-closed dispatcher probes are development evidence; no native/model inference or formal acceptance. Main '+integration['main_head']+'. Registry41. All prior failure records retained; ordinary LIVE delivery, trusted first-use selection and current model qualification remain open. Full goal unfinished: formal0/42, not all22parents.\n\n').encode()
tmp=handoff.with_name(handoff.name+'.cp581.new');tmp.write_bytes(prefix+old);os.replace(tmp,handoff)
print(json.dumps({'checkpoint':581,'main_head':integration['main_head'],'failure_records':len(cp['failure_counters']),'formal_increment':0}))
