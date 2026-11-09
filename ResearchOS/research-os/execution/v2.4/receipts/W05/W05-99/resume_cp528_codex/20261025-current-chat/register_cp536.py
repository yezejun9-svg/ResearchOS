import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;O=N/'continuation-cp536';E=R/'execution/v2.4/receipts/W05/W05-99';A=E/'react_workbench_redesign_codex/20261025-current-chat';V=E/'react_workbench_independent_review_codex/20261025-current-chat';W=R/'.local/worktrees/react-workbench-redesign-20261025'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix()if p.is_relative_to(R.resolve())else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write(chr(10))
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp536.pending');q.write_bytes(v);assert p.read_bytes()==b;os.replace(q,p)
for name,count in [('React-author-root-verification-r2.json',543),('React-independent-root-verification-r2.json',195)]:
 v=read(N/name);assert v['verified_count']==count and not v['unresolved']
 for x in v['verified_refs']:assert ref(Path(x['path']))['sha256']==x['sha256']
review=read(V/'REVIEW.json');assert review['verdict']=='NO_BLOCKING_FINDINGS'and not review['findings']
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']];raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p);assert cp['revision']==535 and ow['revision']==321 and len(cp['failure_counters'])==2105
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda cwd,*a:subprocess.check_output(git+list(a),cwd=cwd)
base='4f4023c956f84d65743f39ce77d6c8899a21ada1';head='7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e';tree='de59625ee5c1d360c741c95ec3f84b6f2764bb0e'
assert g(R,'rev-parse','HEAD').decode().strip()==base and not g(R,'diff','--cached','--name-only');dirty=g(R,'diff','--name-only','-z').decode().strip(chr(0)).split(chr(0));assert len(dirty)==20
for x in read(N/'selector-live-verification.json')['protected_source']:assert ref(Path(x['path']))['sha256']==x['sha256']
assert g(W,'rev-parse','HEAD').decode().strip()==head and not g(W,'status','--porcelain=v1','--untracked-files=all')
scope=read(N/'continuation-cp534/react-workbench-redesign-source14-scope.json');assert not(set(dirty)&set(scope['source_allowlist']))
for x in scope['baseline_source']:
 p=Path(x['path']);p=p if p.is_absolute()else R/p;assert ref(p)['sha256']==x['sha256']
baseline_paths={str((R/x['path']).resolve())if not Path(x['path']).is_absolute()else str(Path(x['path']).resolve())for x in scope['baseline_source']}
for path in scope['source_allowlist']:
 p=R/path
 if str(p.resolve())not in baseline_paths:assert not p.exists(),str(p)
subprocess.check_call(git+['merge-base','--is-ancestor',base,head],cwd=R)
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat();prior=read(N/'continuation-cp535/RESUME.current.json')
adopt={'schema':'researchos.React-source14-limited-source-adoption.v1','status':'SOURCE_AND_BOUNDED_UI_ACCEPTED_FOR_EXACT_LOCAL_INTEGRATION','at':now,'commit':head,'tree':tree,'actual_changed_paths':read(A/'SOURCE14-SEAL.json')['actual_changed_paths'],'author_seal':ref(A/'SOURCE14-SEAL.json'),'author_supplement_seal':ref(A/'SOURCE14-SUPPLEMENT-SEAL.json'),'independent_review':ref(V/'REVIEW.json'),'independent_seal':ref(V/'FINAL-SEAL.json'),'root_verifications':[ref(N/'React-author-root-verification-r2.json'),ref(N/'React-independent-root-verification-r2.json')],'verification_matrix':review['matrix'],'limits':review['limits'],'native_packaged_Desktop':'NOT_RUN','Main_integrated':False,'original_data_or_process_authority':False,'formal_increment':0}
new(O/'React-source14-limited-source-adopted.json',adopt)
integration={'schema':'researchos.React-source14-Main-local-integration.v1','owner':'codex:/root','status':'REGISTERED_AFTER_INDEPENDENT_REVIEW','expected_Main_HEAD':base,'target_commit':head,'target_tree':tree,'source_adoption_ref':ref(O/'React-source14-limited-source-adopted.json'),'allowed_source_paths':scope['source_allowlist'],'actual_change_paths':adopt['actual_changed_paths'],'git_operation':['git','-c','maintenance.auto=false','-c','gc.auto=0','merge','--ff-only','--no-edit',head],'build_output_root':str(R/'.local/react-main-integration-20261025'),'build_output':str(R/'.local/react-main-integration-20261025/web-dist'),'build_tool':'C:/nvm4w/nodejs/node.exe','production_dist_preservation':str(R/'apps/web/dist'),'requirements':['Before FF, snapshot exact current Main HEAD/index/dirty paths and bytes or absence, source preimages, original dist hashes and protected9. No overwrite of unexpected source paths or untracked collisions.','Perform only exact fast-forward to reviewed commit, with no stash/reset/clean/rebase/push. Verify HEAD/tree, all12source pins, dirty20 unchangedbyte state and protected9 after. No original Core/Desktop/data/API/provider action.','Build reviewed frontend from Main into a new task-owned staged outDir, never overwrite or empty existing apps/web/dist. Verify new build hashes against accepted candidate dist, and currentMain CI patterns bind new components/testfiles. Existing fullMain dirtyGo tests are preserved and are not claimed clean.','Record each actual Git/build/verification command with argv/cwd/env/rawstreams/nativeexit. Do not repeat independent UI suites when source and resulting bundle hashes are exact.','After integration, advance checkpoint current_Main_HEAD to new commit, but keep Source43/C57 immutable historical base085b and originalMain4f references unchanged. C57 remains in own worktree. Formal0/42/all22open unchanged.'],'authority':'User-authorized reversible local source implementation/integration after independent review, no production-instance switch','formal_increment':0}
new(O/'React-Main-integration-scope.json',integration)
items=[]
for x in read(N/'React-author-root-verification-r2.json')['recorded_command_results']:
 if x['exit']!=0:items.append({'id':'react-author-'+Path(x['path']).parent.name,'detail':x,'evidence_ref':ref(Path(x['path']))})
led=[json.loads(x)for x in(V/'LEDGER.jsonl').read_text(encoding='utf8').splitlines()if x.strip()]
for x in led:
 if x.get('status')in ['FAIL','NOT_PRESENT']:items.append({'id':'react-review-'+x['kind'],'detail':x,'evidence_ref':ref(V/'LEDGER.jsonl')})
items.append({'id':'react-review-initial-seal-ledger-drift','detail':read(V/'SEAL-EMISSION-DIAGNOSTIC.json'),'evidence_ref':ref(V/'SEAL-EMISSION-DIAGNOSTIC.json')})
items.extend([{'id':'root025-patch-format-assumption','detail':'Root compared abbreviated-index Git diff against valid full-index author artifact and failed;026 proves exact full-index equality,027 verification corrected without author/source edits.','evidence_ref':ref(N/'025-react-author-verification.recipe.result.json')},{'id':'root028-relative-manifest-key','detail':'Root generic ref walker stripped directory from full relative manifest keys, so verification was incomplete.029 uses full keys and verifies all189 independent entries and supplement. Prior report retained.','evidence_ref':ref(N/'028-react-independent-verification.recipe.result.json')},{'id':'root028-display-truncation','detail':'Large incorrect-unresolved list truncated display;raw retained,029 compact verification resolves actual refs.','evidence_ref':ref(N/'028-react-independent-verification.recipe.result.json')}])
assert len(items)==12;new(O/'new-records-ledger.json',{'distinct_mixed_records':12,'records':items,'product_failure_count':False,'expected_service_terminate_exit1':'Preserved in author/reviewer stop receipts, not unexpected failures'})
before=list(cp['failure_counters'])
for x in items:cp['failure_counters'].append({'origin_key':'20261025|cp536-'+x['id'],'attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':x['detail'],'evidence_ref':x['evidence_ref'],'counter_reset':False})
assert cp['failure_counters'][:2105]==before and len(cp['failure_counters'])==2117
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v114',at=now,checkpoint_revision=536,ownership_revision=322,failure_records_preserved=2117,react_source_adopted_ref=ref(O/'React-source14-limited-source-adopted.json'),react_Main_integration_scope_ref=ref(O/'React-Main-integration-scope.json'),current_Main_HEAD=base,expected_Main_after_react_integration=head,react_author_and_independent_ledger_import='DONE_CP536')
resume['next_command']='Root execute exact reviewed React fast-forward to7d1e3ff after snapshot, preserve dirty20/protected9/originaldist, build into new stagedoutDir and verify exactbundle. Then register newcurrent MainHEAD. C57 source continues on085b4711. Originaldata/processes untouched; formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=536,expected_previous_revision=535,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp536=rr,react_Main_integration_scope_ref=ref(O/'React-Main-integration-scope.json'));cp['evidence_index'].append({'kind':'REACT_SOURCE14_INDEPENDENTLY_ADOPTED_EXACT_MAIN_INTEGRATION_REGISTERED','ref':rr,'formal_increment':0})
ow.update(revision=322,expected_previous_revision=321,updated_at=now,updated_by='codex:/root');ow['special_paths']['react_independent_review'].update(state='FROZEN_NO_BLOCKING_FINDINGS_ADOPTED',evidence_ref=ref(V/'FINAL-SEAL.json'));ow['special_paths']['react_frontend_source'].update(state='FROZEN_SOURCE_ACCEPTED_FOR_MAIN_INTEGRATION')
ow['special_paths']['react_Main_integration']={'owner':'codex:/root','state':'REGISTERED','scope_ref':ref(O/'React-Main-integration-scope.json'),'write_scope':scope['source_allowlist']+[integration['build_output_root']],'original_data_or_process_authority':False}
for p,n in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:(O/n).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+chr(10)).encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+chr(10)).encode());swap(hp,raw[hp],('# Current verified continuation CP536'+chr(10)*2+'Read '+rr['path']+' first. React14 independentlyaccepted; exactMain FF registered but notyetexecuted. Preserve originaldist and dirty20. C57 source active on085b. Formal0/42/all22open, mixedrecords2117.'+chr(10)*2).encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':536,'ownership':322,'mixed_records':2117,'integration_scope':ref(O/'React-Main-integration-scope.json'),'resume':rr},ensure_ascii=False))
