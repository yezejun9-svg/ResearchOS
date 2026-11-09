import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;O=N/'continuation-cp546';E=N.parent.parent
P=E/'qualification_maintenance_c57_codex/20261025-current-chat';B=E/'qualification_recovery_boundary_boot6_codex/20261025-current-chat';V=E/'qualification_maintenance_c57_independent_review_codex/20261025-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix()if p.is_relative_to(R.resolve())else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def verify(x,base=R):
 p=Path(x.get('path',x.get('file','')));p=p if p.is_absolute()else base/p;a=ref(p);assert a['sha256']==x['sha256'],str(p)
 if 'bytes'in x:assert a['bytes']==x['bytes'],str(p)
 return a
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp546.pending')
 with q.open('xb')as f:f.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==545 and ow['revision']==331 and len(cp['failure_counters'])==2186
prior=read(N/'continuation-cp545/RESUME.current.json')
g=lambda *a:subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0']+list(a),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==prior['current_Main_HEAD'] and not g('diff','--cached','--name-only')
base=read(N/'React-Main-integration-baseline.json');assert g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==base['dirty_paths']
shared={'execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json','execution/v2.4/HANDOFF_RESUME_PACK.md'}
for x in base['dirty_files']:
 if x['relative_path']in shared:continue
 p=R/x['relative_path'];assert p.is_file()==x['exists']
 if x['exists']:assert ref(p)['sha256']==x['sha256']
for x in base['protected_source']+base['original_dist_refs']+read(N/'React-Main-integration-result.json')['staged_build_refs']:verify(x)
for name,sha in [('execution/project_identity.json','03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'),('.git/config','1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'),('execution/v2.4/step_state.json','168c55121a874be36522e7ac5c7286cd7f90af0b7c06d1b73e444c19aa57307e')]:verify({'path':name,'sha256':sha})
for name in ['060-c57-new-increments-r2','061-boot6-v11-verify']:assert read(N/(name+'.recipe.result.json'))['native_exit']==0
inc=read(N/'C57-new-increments-root-verification.json');boot=read(N/'C57-boot6-v11-root-verification.json')
for x in inc['verified_refs']+boot['verified_refs']:verify(x)
rs=V/'PHASE1-parent51-r3-r4-targeted-addendum-seal.json';verify({'path':str(rs),'sha256':'3f01567bbf5d954dd68460046d3d1ff0f1b1905a204d30de8eef04e19d74efe9'})
review=read(rs);items=review.get('files',review.get('references'));assert len(items)==60
reviewrefs=[verify(x,V)for x in items]
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O/'C57-r3-r4-independent-root-verification.json',{'seal':ref(rs),'verified_refs':reviewrefs,'status':'STATIC_FIX_CONFIRMED_PENDING_PHASE2','candidate_tests_run':False,'prepared_assertions':73,'formal_increment':0})
root_events=[
 {'id':'outer-agent-path-missing','native_exit':None,'tool_exit':0,'capture':'tool transcript a1b585','detail':'Read missing outer AGENTS path; repo AGENTS succeeded. Semantic PowerShell read error, no separate raw capture.'},
 {'id':'guessed-resume-script-path-missing','native_exit':1,'capture':'tool transcript 1e4dfe','detail':'Wrong verify_cp545_live_resume.py guess; actual 058-cp545-live-resume.py subsequently read. No product mutation.'},
 {'id':'059-freeze-schema-assumption','native_exit':1,'receipt':ref(N/'059-c57-new-increments.recipe.result.json'),'detail':'Verifier assumed inherited_pins_verified list in all historical manifests; R3/R4 have inherited_pin_count. Corrected060 verified current40 bytes.'},
 {'id':'v11-manifest-list-introspection','native_exit':1,'capture':'tool transcript 912bb1','detail':'Read-only display assumed object but source manifest is list. Subsequent061 exact6 verification passed.'}]
new(O/'root-diagnostics.json',{'events':root_events,'raw_capture_gaps_explicit':True})
records=[]
def add(key,status,detail,evidence):records.append({'origin_key':'20261025|'+key,'attempts':1,'status':status,'detail':detail,'evidence_ref':evidence,'counter_reset':False})
for c in inc['historical_boot_events']:
 if c['native_exit']!=0:add('boot6-'+c['id'],'NATIVE_FAILURE_PRESERVED',c,ref(N/'C57-new-increments-root-verification.json'))
for c in inc['parent_native_receipts']:
 if c['native_exit']!=0:add('c57-parent-'+c['id'],'NATIVE_FAILURE_PRESERVED',c,ref(N/'C57-new-increments-root-verification.json'))
add('C51-exact-row-classifier-P1','INDEPENDENT_FINDING_SOURCE_FIXED_PENDING_PHASE2',{'sites':['dispatch unchanged typed columns omitted','domain_objects immutable allowed non0/1'],'r2_component_fix':'independently static confirmed','r3_wiring_fix':'separately recorded'},ref(N/'C57-new-increments-root-verification.json'))
add('C51-r2-beforehash-journal-wiring-P1','INDEPENDENT_FINDING_SOURCE_FIXED_PENDING_PHASE2',{'r3':'dispatch_row in journal full-plan before hash; actual typed Host->journal fixture061','r4':'normalized fixture path correction; C+D lease tests0'},ref(O/'C57-r3-r4-independent-root-verification.json'))
add('reviewer-068-grep-no-match','EXPECTED_QUERY_NONZERO_PRESERVED',{'native_exit':1,'candidate_test':False,'reviewer_total_nonzero':3},ref(N/'C57-new-increments-root-verification.json'))
add('boot6-v10-crlf-diff','NATIVE_FAILURE_PRESERVED',{'native_exit':128,'cause':'PowerShell Out-File CRLF patch','v10b_corrected':0},ref(B/'final-v10-additive-seal.json'))
add('boot6-v8-full-02-numbered-gap','UNKNOWN_CAPTURE_NOT_ASSUMED_EXECUTED',inc['historical_boot_gaps'],ref(N/'C57-new-increments-root-verification.json'))
add('boot6-v11-dev-c-natural-01','EXIT0_NO_ASSERTION_SKIP_PRESERVED',boot['checks'][4],ref(N/'C57-boot6-v11-root-verification.json'))
add('boot6-v11-dev-c-natural-02','NATIVE_FAILURE_PRESERVED',boot['checks'][5],ref(N/'C57-boot6-v11-root-verification.json'))
for x in root_events:add('root-cp545-'+x['id'],'DIAGNOSTIC_PRESERVED',x,ref(O/'root-diagnostics.json'))
assert len(records)==23
assert not({x['origin_key']for x in records}&{x.get('origin_key')for x in cp['failure_counters']})
new(O/'new-records-ledger.json',{'distinct_mixed_records':len(records),'records':records,'product_failure_count':False,'semantic_boot_crosswalk':'v7/v8 five exit0 semantic discoveries are evidence for CP545 native preimage/ACEflags finding, not counted again. Two limited probes and two unavailable-SACL branches retain limits in original index.','author_capture_limits':'Historical per-command source hashes absent; v8-full-02 numbered gap does not prove execution. Old89 ledger rewrite incident remains.'})
new(O/'C57-frozen-components-progress.json',{'at':now,'parent':{'revision':'r4','freeze':ref(P/'C51-R4-SOURCEFREEZE.json'),'files':51,'pins':40,'root_verification':ref(N/'C57-new-increments-root-verification.json')},'boot6':{'revision':'v11','freeze':ref(B/'final-v11-six-source-manifest.json'),'root_verification':ref(N/'C57-boot6-v11-root-verification.json')},'independent':{'phase':'STATIC_ONLY','r3_r4_root_ref':ref(O/'C57-r3-r4-independent-root-verification.json'),'assertions':73,'final57_test_acceptance':False},'integration':'Root authorized original57 scoped local commit after v11 verification; in progress. No Main merge, push, original DB/Core/ACL/STOP/restart action.','linux':'069 full and075 expanded selective builds failed due Windows-only dependency baseline;076 selected store/journal/recoveryboundary/boot CLI build passes, no whole product Linux claim.','remaining_privileged_actual_gates':boot['remaining'],'cleanup_exception':read(N/'C57-boot6-v6-root-verification.json')['auto_review_cleanup'],'formal_increment':0})
old=list(cp['failure_counters']);cp['failure_counters'].extend(records);assert cp['failure_counters'][:2186]==old;total=len(cp['failure_counters']);assert total==2209
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v124',at=now,checkpoint_revision=546,ownership_revision=332,failure_records_preserved=total,C57_frozen_components_progress_ref=ref(O/'C57-frozen-components-progress.json'))
resume['next_command']='Obtain original57 scoped combined commit/tree/source manifest from parent after necessary final integration; R4 current51/40pins verified, Bootv11 six/currentC+D native suites verified, readonly independent r3/r4 STATIC_FIX_CONFIRMED. Root exact57 phase2 amendment required before independent candidate tests. Preserve historical23new mixed records/2209 total, source snapshots/capture gaps and deniedcleanup. MainReact7d/dirty20/protected9/old33/new3 unchanged; originaldata untouched; formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=546,expected_previous_revision=545,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp546=rr,C57_frozen_components_progress_ref=ref(O/'C57-frozen-components-progress.json'));cp['evidence_index'].append({'kind':'C57_R4_V11_FROZEN_AND_STATIC_FIXES_VERIFIED_PENDING_COMBINED57_PHASE2','ref':rr,'formal_increment':0})
ow.update(revision=332,expected_previous_revision=331,updated_at=now,updated_by='codex:/root');ow['special_paths']['C57_boot6_source'].update(state='V11_FROZEN_C_D_NATIVE_EVIDENCE_ROOT_VERIFIED_PENDING_COMBINED57',evidence_ref=ref(N/'C57-boot6-v11-root-verification.json'));ow['special_paths']['C57_independent_review'].update(state='PHASE1_R3_R4_STATIC_FIXES_CONFIRMED_WAIT_EXACT57_PHASE2')
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as f:f.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode())
swap(hp,raw[hp],('# Current verified continuation CP546\n\nRead '+rr['path']+' first. ParentR4/51 andBootv11/6 frozen; current57bytes/40pins checked. C+D native restore passed, static r3/r4 fix review confirmed; combined57 local commit in progress, final independent Phase2 awaits Root exact amendment. Preserve2209 mixed records and all raw/gaps/deniedcleanup. MainReact7d unchanged; formal0/42/all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':546,'ownership':332,'mixed_records':total,'new_mixed_records':len(records),'review_refs':60,'resume':rr},ensure_ascii=False))
