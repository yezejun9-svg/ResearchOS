import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;O=N/'continuation-cp548';V=N.parent.parent/'qualification_maintenance_c57_independent_review_codex/20261025-current-chat';T=V/'token-privilege-static'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix()if p.is_relative_to(R.resolve())else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp548.pending')
 with q.open('xb')as f:f.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
paths=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']];cp_p,ow_p,hp,sp=paths;raw={p:p.read_bytes()for p in paths};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==547 and ow['revision']==333 and len(cp['failure_counters'])==2209
prior=read(N/'continuation-cp547/RESUME.current.json');s=read(T/'seal-final.json');assert ref(T/'seal-final.json')['sha256']=='e84525c7a4e258984faa3484d40b5afd0783d7f72261c48e4b8d7b8c80fa407c'
assert s['commit']==prior['C57_frozen_commit'];refs=[ref(T/'seal-final.json')]
for x in s['files']:
 a=ref(T/x['name']);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];refs.append(a)
assert len(s['files'])==11 and ref(T/'source-reachability-addendum.md')['sha256']=='4a48d5640c3eedbc6556205f74e29d573cdc3aad9931177fe735c382f863b8a4'
assert int((T/'native-exit.txt').read_text(encoding='utf-8-sig'))==1 and int((T/'native-exit-utf8bom.txt').read_text(encoding='utf-8-sig'))==0
q=V/'089-phase2-core-c';d=read(q/'result.json');assert d['native_exit']==1 and d['test_event_counts']=={} and len(d['package_results'])==7
assert ref(q/'stdout.raw')['sha256']==d['stdout_sha256']and ref(q/'stderr.raw')['sha256']==d['stderr_sha256']
for name in ['recipe.json','result.json','stdout.raw','stderr.raw','test-events.json']:refs.append(ref(q/name))
g=lambda *a:subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0']+list(a),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==prior['current_Main_HEAD']and not g('diff','--cached','--name-only')
base=read(N/'React-Main-integration-baseline.json');assert g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==base['dirty_paths']
for x in base['protected_source']+base['original_dist_refs']+read(N/'React-Main-integration-result.json')['staged_build_refs']:
 p=Path(x['path']);a=ref(p if p.is_absolute()else R/p);assert a['sha256']==x['sha256']and a['bytes']==x['bytes']
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O/'C57-token-P1-root-adoption.json',{'status':'P1_SOURCE_GAP_ACCEPTED_REPAIR_WITHIN_ORIGINAL6','frozen_old_commit':prior['C57_frozen_commit'],'finding':'Assigned but disabled business SeRestore/SeTakeOwnership/SeBackup privileges are digested yet not rejected; native official-process producer and matching Explorer shape can reach arm. Existing F01/F05 and script FILE_READ_DATA promises require admission rejection.','reachability_report':ref(T/'source-reachability-addendum.md'),'verified_refs':refs,'actual_token_or_native_bypass_observed':False,'author_reopen':'Root reopened original6 scope for v12 minimal live business-token admission guard, producer and current/post consumers; assigned privilege rejection, not enabled-only. Do not affect legitimate management SeRestore restoration.','old_candidate_tests':'Independent08d63 snapshot continues unaffected assertions; no oldcommit acceptance. Newdelta/commit requires Rootfreeze and targeted supplementary independent review.','primary_reference_check':[{'url':'https://learn.microsoft.com/en-us/windows/win32/secbp/changing-privileges-in-a-token','paraphrase':'Existing disabled token privileges may be enabled; removed privileges differ.'},{'url':'https://learn.microsoft.com/en-us/windows/win32/secauthz/privilege-constants','paraphrase':'Restore includes WRITE_DAC/WRITE_OWNER, Backup supports read outside ordinary ACL checks, TakeOwnership grants ownership capability.'}],'formal_increment':0})
records=[
 {'origin_key':'20261025|C57-business-assigned-privileges-P1','attempts':1,'status':'SOURCE_P1_CONFIRMED_V12_FIX_ACTIVE','detail':'Reachable supported token class; no actual business bypass claim','evidence_ref':ref(O/'C57-token-P1-root-adoption.json'),'counter_reset':False},
 {'origin_key':'20261025|token-static-initial-PS51-encoding','attempts':1,'status':'DIAGNOSTIC_NATIVE_FAILURE_PRESERVED','detail':'UTF8 no-BOM script under Windows PowerShell5.1 corrupted Chinese path; original native1 retained, BOM recipe0','evidence_ref':ref(T/'seal-final.json'),'counter_reset':False},
 {'origin_key':'20261025|independent-089-module-cache-empty','attempts':1,'status':'ENVIRONMENT_SETUP_FAILURE_NO_TEST_ASSERTIONS','detail':{'native_exit':1,'actual_tests':0,'failed_setup_packages':7,'next':'Own expanded dependency cache then new-number rerun; no product-test PASS/FAIL inferred'},'evidence_ref':ref(q/'result.json'),'counter_reset':False}]
assert not({x['origin_key']for x in records}&{x.get('origin_key')for x in cp['failure_counters']});old=list(cp['failure_counters']);cp['failure_counters'].extend(records);assert cp['failure_counters'][:2209]==old and len(cp['failure_counters'])==2212
new(O/'new-records-ledger.json',{'records':records,'distinct_mixed_records':3,'product_failure_count':False})
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v126',at=now,checkpoint_revision=548,ownership_revision=334,failure_records_preserved=2212,C57_token_P1_ref=ref(O/'C57-token-P1-root-adoption.json'))
resume['next_command']='Continue independent73 assertions on immutable08d63 snapshot while Boot6v12 fixes SourceP1 livebusiness assigned SeRestore/TakeOwnership/Backup rejection in original6 only. Old08d63 not accepted; newdelta/commit+Rootfreeze needed for affected independent retest. Independent089 own module cache setupfail1/test0 retained, copy pinned expanded deps to owncache and rerun newnumber. MainReact7d preserved; mixed2212; no original data/Core/ACL/STOP/restart actions; formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json');cp.update(revision=548,expected_previous_revision=547,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp548=rr,C57_token_P1_ref=ref(O/'C57-token-P1-root-adoption.json'));cp['evidence_index'].append({'kind':'C57_INDEPENDENT_SOURCE_P1_PRIVILEGE_ADMISSION_FIX_ACTIVE_UNAFFECTED_REVIEW_CONTINUES','ref':rr,'formal_increment':0});ow.update(revision=334,expected_previous_revision=333,updated_at=now,updated_by='codex:/root');ow['special_paths']['C57_boot6_source'].update(state='V12_ORIGINAL6_REOPENED_BUSINESS_PRIVILEGE_P1',evidence_ref=ref(O/'C57-token-P1-root-adoption.json'));ow['special_paths']['C57_independent_review'].update(state='PHASE2_OLD08D63_UNAFFECTED_ASSERTIONS_CONTINUE_WAIT_V12_DELTA')
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as out:out.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());swap(hp,raw[hp],('# Current verified continuation CP548\n\nRead '+rr['path']+' first. Independent SourceP1 confirms dangerous assigned business privileges lack admission rejection; Bootv12 original6 fix active, old08d63 not accepted. Immutable snapshot unaffected73 review continues;089 dependencies setup failed/test0 preserved. MainReact7d unchanged; mixed2212; formal0/42/all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':548,'ownership':334,'mixed_records':2212,'token_refs':len(s['files']),'independent089_test_events':0,'resume':rr},ensure_ascii=False))
