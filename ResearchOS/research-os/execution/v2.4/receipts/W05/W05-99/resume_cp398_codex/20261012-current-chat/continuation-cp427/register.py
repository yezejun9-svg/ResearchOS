import copy, datetime, hashlib, json, os, pathlib, subprocess
ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT = pathlib.Path(__file__).resolve().parent
CANON = ROOT / 'execution/v2.4'
paths = [CANON/'checkpoint.json', CANON/'path_ownership.json', CANON/'HANDOFF_RESUME_PACK.md']
before = {p:p.read_bytes() for p in paths}
cp = json.loads(before[paths[0]].decode('utf-8-sig'))
ow = json.loads(before[paths[1]].decode('utf-8-sig'))
assert cp['revision'] == 426 and ow['revision'] == 214
state = (CANON/'step_state.json').read_bytes()
old_failures = copy.deepcopy(cp['failure_counters'])
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
def ref(p):
    raw=p.read_bytes()
    return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def receipt(name):
    return CANON/'receipts/W05/W05-99'/name/'20261012-current-chat'
def write_new(p,d):
    assert not p.exists(),str(p)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
review=ref(receipt('product_coding_client_review_codex')/'independent-review.json')
assert review['sha256']=='77025b69305065815deb1b8d4f4f9949f8d4801eaa76f0f526f7ffbf276e41c1'
assessment=ref(receipt('product_coding_client_repair_v2_scope_assessment_codex')/'scope-repair-assessment.json')
assert assessment['sha256']=='97a4e04175a805ef2d7246e0011076ce109e5734a9df2ba458980b94fb3d995d'
original_scope=json.loads((OUT.parent/'continuation-cp424/coding-client-scope.json').read_text(encoding='utf-8-sig'))
scope_paths=['apps/desktop/main/main.js','apps/desktop/main/lib/desktop-management.js','apps/desktop/main/lib/ipc.js','apps/desktop/preload/preload.js','apps/web/src/workbench.jsx','tests/ui/desktop/desktop-management-boundary.test.mjs','tests/ui/desktop/coding-authorization-boundary.test.mjs','tests/ui/continuity/coding_authorization_driver.mjs']
scope={'schema':'researchos.coding-client-causal-repair-scope.v2','at':now,'step_id':'W05-99',
       'owner':'codex:/root/coding_client_repair_v2','worktree':'.local/worktrees/w05-product-coding-client-repair-v2-20261012',
       'base_commit':'eb7f712d21268c87f9af9428048313c9361c52d6','paths':scope_paths,
       'original_rejected_review_ref':review,'independent_scope_assessment_ref':assessment,
       'model':'gpt-6-sol','reasoning_effort':'high','reason_for_model':'Four bound causal client defects with exact eight-path scope; independent acceptance remains ASTRA.',
       'required_repairs':['W05-CODING-CLIENT-001 privileged exact frozen scope consent before original CONFIRM, cancellation zero frame/effect, post-await context/pending revalidation.',
                           'W05-CODING-CLIENT-002 shared pending/uncertain barrier before any retirement/mutation, preserve original late terminal status.',
                           'W05-CODING-CLIENT-003 retain original PREPARE operation/result across UI context change; no orphaned request or replacement prepare.',
                           'W05-CODING-CLIENT-004 STATUS committed config reconciles original V2 views exactly once on success; failed readonly refresh can safely retry.'],
       'limits':['Only original eight client paths; no first-use five, Core, Native3, schema, target CLI or Canon edits.',
                 'Preserve rejected EB7F bytes/bundle/manifest, original failures and all qualification/coding/SHUTDOWN barriers.',
                 'No live models, tools, root GUI, credentials, Owner synthesis, paid calls or tunnels.',
                 'Full fresh source-bound build before frozen final candidate; coordinate build window with other Source writer.',
                 'Independent review before Main integration; source/fixture not whole-product or formal acceptance.'],
       'formal_increment':0,'parent_acceptance':False}
write_new(OUT/'coding-client-repair-scope.json',scope); sr=ref(OUT/'coding-client-repair-scope.json')
cp.update(revision=427,expected_previous_revision=426,updated_at=now,updated_by='codex:/root')
ow.update(revision=215,expected_previous_revision=214,updated_at=now,updated_by='codex:/root')
ow['path_lease_transfers'].append({'at':now,'actor':'codex:/root','new_owner':scope['owner'],
    'new_subtask':'W05-99/normal_product_explicit_coding_profile_client_repair_v2',
    'new_worktree':scope['worktree'],'paths':scope_paths,'scope_ref':sr,'kind':'NEW_CAUSAL_REPAIR_OF_FROZEN_REJECTED_EB7F'})
cp['work_in_progress'].update(coding_client_status='EB7F_FOUR_BOUND_COUNTEREXAMPLES_REQUEST_CHANGES_NEW_EXACT8_REPAIR',
    coding_client_independent_review_ref=review,coding_client_repair_scope_ref=sr,
    native_first_use_actual_state='CAUSAL_RETRY01_NORMALLY_CLOSED_BOTH_PIDS_ABSENT_ORIGINAL_DATA_PRESERVED')
# New normalized UTC identity evidence caused a different safe-close input; the first diagnostic never sent WM_CLOSE.
closure=ref(receipt('normal_desktop_first_use_causal_retry01_codex')/'normal-window-close.intent.json')
ps="Get-CimInstance Win32_Process -Filter 'ProcessId = 57044 OR ProcessId = 55208' | Select-Object ProcessId | ConvertTo-Json"
result=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,text=True,encoding='utf-8')
assert result.returncode==0 and not result.stdout.strip()
write_new(OUT/'closed-process-observation.json',{'at':now,'pids':[57044,55208],'cim_exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'normal_close_ref':closure,'forced_termination':False,'model_calls':0,'data_reset':False})
for item in cp['side_effects_pending']:
    if item.get('kind')=='OWNED_NORMAL_DESKTOP_FIRST_USE_CAUSAL_RETRY01_ZERO_MODEL_HOST':
        item.update(state='NORMAL_WINDOW_CLOSE_EXITED_BOTH_PIDS_RECHECKED',exited=True,closure_ref=ref(OUT/'closed-process-observation.json'))
for finding in ['001','002','003','004']:
    cp['failure_counters'].append({'origin_key':'current-chat-20261012|W05-CODING-CLIENT-'+finding,
        'attempts':1,'status':'INDEPENDENT_BOUND_COUNTEREXAMPLE_SOURCE_FIXTURE_REQUEST_CHANGES',
        'counter_reset':False,'evidence_ref':review,'actual_models':0})
cp['failure_counters'].append({'origin_key':'current-chat-20261012|safe-close-date-serialization-assertion',
    'attempts':1,'status':'DIAGNOSTIC_ASSERTION_BEFORE_WM_CLOSE_NORMALIZED_UTC_NEW_INPUT_SUCCEEDED',
    'counter_reset':False,'evidence_ref':closure,'tool_chunk':'8d2769','actual_models':0})
cp['next_command']='Finish firstuse5 repair/bound build then independent review and actual Native firstuse using original data; parallel coding client exact8 repairs four frozen bound counterexamples, serialize full builds. No models until explicit original qualification consent. 0/42 formal/all22 parents open.'
resume={'schema':'researchos.current-chat-resume.v23','at':now,'checkpoint_revision':427,'ownership_revision':215,
    'head':cp['head'],'project_id':cp['project_id'],'current_step_id':'W05-99','accepted_formal_cases':0,
    'required_formal_cases':42,'required_parent_tasks':22,'failure_records_preserved':len(cp['failure_counters']),
    'goal_status':'ACTIVE','coding_repair_scope_ref':sr,'coding_review_ref':review,
    'firstuse_source_owner':'codex:/root/w05_main24','coding_source_owner':scope['owner'],'active_source_limit':2,
    'original_data_preserved':True,'closed_desktop_pids':[53188,57044],'closed_control_pids':[61168,55208],
    'owned_ollama_pid':60952,'real_models_this_preparation':0,'phone_user_answer':'USE_REAL_PHONE_WHEN_PRODUCT_PAIRING_READY',
    'phone_ready':False,'next_command':cp['next_command']}
write_new(OUT/'RESUME.current.json',resume)
cp['artifacts'].extend([review,assessment,sr,ref(OUT/'closed-process-observation.json'),ref(OUT/'RESUME.current.json')])
cp['work_in_progress']['current_chat_resume_ref']=ref(OUT/'RESUME.current.json')
assert cp['failure_counters'][:len(old_failures)]==old_failures
assert cp['no_progress_rounds']==json.loads(before[paths[0]].decode('utf-8-sig'))['no_progress_rounds']
for p,name in zip(paths,['checkpoint.before.raw.json','ownership.before.raw.json','HANDOFF.before.raw.md']):
    assert not (OUT/name).exists();(OUT/name).write_bytes(before[p]);assert p.read_bytes()==before[p]
assert (CANON/'step_state.json').read_bytes()==state
handoff=('# Current verified continuation CP427\n\nRead `'+ref(OUT/'RESUME.current.json')['path']+'` first. '
    'Both original and causal retry Desktop instances exited normally, original data retained. Firstuse5 and codingrepair8 are disjoint active Source branches; rejected EB7F and all failure counters remain preserved. '
    'Formal0/42 and all22 parent obligations open.\n\n').encode()+before[paths[2]]
for p,raw in [(paths[0],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode()),(paths[1],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode()),(paths[2],handoff)]:
    tmp=p.with_name(p.name+'.cp427.tmp');assert not tmp.exists();tmp.write_bytes(raw);os.replace(tmp,p)
print(json.dumps({'checkpoint':427,'ownership':215,'scope':sr,'resume':ref(OUT/'RESUME.current.json'),'preserved_failures':len(old_failures),'new_records':5,'formal_increment':0},ensure_ascii=False))
