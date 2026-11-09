import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;O=N/'continuation-cp538';E=R/'execution/v2.4/receipts/W05/W05-99'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix()if p.is_relative_to(R.resolve())else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write(chr(10))
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp538.pending')
 with q.open('xb')as f:f.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==537 and ow['revision']==323 and len(cp['failure_counters'])==2117
parent=N/'continuation-cp533/C57-source-scope.json';ps=read(parent);six=ps['source_groups']['boot_production_and_tests'];assert len(six)==6
w=Path(ps['worktree']);assert all(not(w/p).exists()for p in six)
prior=read(N/'continuation-cp537/RESUME.current.json')
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];assert subprocess.check_output(git+['rev-parse','HEAD'],cwd=R).decode().strip()==prior['current_Main_HEAD']
for x in read(N/'selector-live-verification.json')['protected_source']:assert ref(Path(x['path']))['sha256']==x['sha256']
cleanup=E/'react_workbench_redesign_codex/20261025-current-chat/PREVIEW-CLEANUP-SUPPLEMENT.json';cl=read(cleanup)
assert ref(cleanup)['sha256']=='cb21133d88a7c33dd91cb8faa0ae3284a03a6d7403cdcc969e2a9638d1eba35c'
for x in cl['preserved_original_files']:assert ref(cleanup.parent/x['path'])['sha256']==x['sha256']
assert cl['stop']['wait_returned']and cl['stop']['native_exit']is None and not cl['post_stop']['process_exists']
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
scope={'schema':'researchos.C57-boot6-disjoint-subdelegation.v1','at':now,'status':'REGISTERED_SOURCE_IMPLEMENTATION','parent_scope_ref':ref(parent),'owner':'codex:/root/c57_boot6_builder_20261025','parent_integrator':'codex:/root/c57_maintenance_builder_20261025','model':'gpt-6-sol','reasoning_effort':'high','model_choice_reason':'Project AGENTS nontrivial bounded implementation; fixed adopted boot contract and exact6 disjoint files','worktree':str(w),'base_commit':ps['base_commit'],'base_tree':ps['base_tree'],'source_allowlist':six,'source_preimages':'ALL_ABSENT_VERIFIED_BEFORE_DELEGATION','own_receipts':str(E/'qualification_recovery_boundary_boot6_codex/20261025-current-chat'),'own_temporary_root':str(R/'.local/qualification-recovery-boundary-boot6-20261025-tmp'),'own_ascii_native_fixture_root':'C:/Users/yqyyds/.codex/researchos-fixture-cache/qualification-recovery-boundary-boot6-20261025','fixed_input_refs':[ref(E/'qualification_recovery_boot_supplement_architecture_codex/20261015-current-chat/BOOT-C-ARCHITECTURE.md'),ref(E/'qualification_recovery_boot_supplement_architecture_codex/20261015-current-chat/C-boot-exact-scope.json'),ref(E/'resume_cp398_codex/20261015-current-chat/continuation-cp521/boot-proposal-adopted-limits.json')],'precedence':'Latest CP533 parent adopted constraints and CP521 limits override historical not-issued/not-accepted words. Already authorized source; do not repeat old architecture loops.','coordination':['Parent confirmed six files untouched and yields only these6; parent owns remaining51 and combined integration/commit.','Same worktree deliberately shared by disjoint files; no git add/commit/reset/clean/rebase, no broad gofmt. Keep others changes and do not inspect original DB/runtime.','Freeze concrete opaque CurrentQuiescence API immediately with parent before Host wiring; private state, exact-held-lease/generation/operation/plan/identity binding and native handles retained until actual outer transaction completion. No JSON/bool/rawhandle capability.','Go tests/build own package initially. Coordinate any parent host integration needed; never edit remaining51. All commands recipe/rawstdout/rawstderr/nativeexit; preserve failures.','Native disposable fixtures only inside owned explicit paths; no original ACL/OS ancestor/reboot/account/shared process changes; unavailable privileged/distinctSID/fullrestart branches are explicit nonacceptance limits.','Only fixed plan/arm/observe/status/disarm-request phase CLI; nonWindows failclosed; no ordinary Core mode or arbitrary paths/SQL; arm gate includes independently accepted native+source+onlinebackup and trusted management proof.','Deliver meaningful pure/native tests, exact6 hashes/diff, append-only ledger/receipts, actual vs unavailable proof matrix; no self acceptance. Parent creates final combined commit after freeze.'],'formal_increment':0,'source_edit_authority':True,'original_data_or_process_authority':False,'actual_STOP_fence_restart_authority':False,'owned_disposable_fixture_authority':True}
new(O/'C57-boot6-source-subscope.json',scope)
record={'origin_key':'20261025|cp538-react-preview-exit-not-captured','attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':'Owned preview stopped after exact PID/starttime/argv validation; WaitForExit true and PID/port absent. Native ExitCode null remains NOT_CAPTURED, no numeric exit invented; original streams and frozen seals unchanged.','evidence_ref':ref(cleanup),'counter_reset':False}
cp['failure_counters'].append(record);assert len(cp['failure_counters'])==2118
new(O/'new-records-ledger.json',{'distinct_mixed_records':1,'records':[record],'product_failure_count':False})
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v116',at=now,checkpoint_revision=538,ownership_revision=324,failure_records_preserved=2118,C57_boot6_subscope_ref=ref(O/'C57-boot6-source-subscope.json'),react_preview_cleanup_ref=ref(cleanup))
resume['active_source_cards']=[ref(parent),ref(O/'C57-boot6-source-subscope.json')]
resume['active_source_path_partition']={'C57_parent':51,'boot_subtask':6,'overlap':0,'combined':57}
resume['next_command']='C57 parent implements51 while registered boot6 worker implements disjoint6 on same085b worktree; freeze opaque interface before wiring, preserve all existing changes. Parent integrates and freezes57 then Root independent review. MainReact7d integrated/stagedexact; original runtime/data unchanged. Formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=538,expected_previous_revision=537,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp538=rr,C57_boot6_subscope_ref=ref(O/'C57-boot6-source-subscope.json'))
cp['evidence_index'].append({'kind':'C57_DISJOINT_BOOT6_IMPLEMENTATION_DELEGATED_AND_PREVIEW_CLEANUP_LIMIT_RETAINED','ref':rr,'formal_increment':0})
ow.update(revision=324,expected_previous_revision=323,updated_at=now,updated_by='codex:/root')
ow['special_paths']['C57_maintenance_source'].update(state='IMPLEMENTING_EXCLUSIVE51_WITH_BOOT6_SUBDELEGATED',exclusive_source_paths=[p for p in ps['source_allowlist']if p not in six],subdelegation_ref=ref(O/'C57-boot6-source-subscope.json'))
ow['special_paths']['C57_boot6_source']={'owner':scope['owner'],'state':'REGISTERED','scope_ref':ref(O/'C57-boot6-source-subscope.json'),'exclusive_source_paths':six,'write_scope':[scope['own_receipts'],scope['own_temporary_root'],scope['own_ascii_native_fixture_root']]+[str(w/p)for p in six],'source_edit_authority':True,'original_data_or_process_authority':False}
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as f:f.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+chr(10)).encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+chr(10)).encode())
swap(hp,raw[hp],('# Current verified continuation CP538'+chr(10)*2+'Read '+rr['path']+' first. C57 source57 divided into parent51 plus disjointboot6 worker; exactbase085b. ReviewedReactMain7d integrated/stagedexact, previewstopped with nativeexitNOT_CAPTURED preserved. Original data/processes unchanged. Formal0/42/all22open, mixedrecords2118.'+chr(10)*2).encode()+raw[hp])
assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':538,'ownership':324,'mixed_records':2118,'boot6_scope':ref(O/'C57-boot6-source-subscope.json'),'resume':rr},ensure_ascii=False))
