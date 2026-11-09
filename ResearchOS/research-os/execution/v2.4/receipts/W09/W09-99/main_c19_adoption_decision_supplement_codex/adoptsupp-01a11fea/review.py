import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent;W=N.parents[1]
R=Path('D:/作品集/ResearchOS/research-os')
A=W/'cp367_main7_v2_actual_independent_review_codex/actualr-01a11fad'
M=W/'main_c19_source_registry_v2_source_codex/Mainv2-1a11fbc'
P=W/'w09_c19_main_root_producer_source_codex/mainc19p-1a11fbc'
ACTOR='codex:/root/attach_fixture_source_review'
pins={};checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def fixed(p,h,z):return dict(path=str(p.resolve()),sha256=h,bytes=z)
def read(r):
 assert pin(r['path'])==r, r['path']
 assert r['path'] not in pins or pins[r['path']]==r
 pins[r['path']]=r;return Path(r['path']).read_bytes()
def load(r):return json.loads(read(r))
def save(name,v):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ck(name,v):
 assert v,name
 checks.append(name)
ahr=fixed(A/'HDF.json','5713edc83e275fe25385ca29c7b7e0f7e6373abc55de472617bfc8513c711388',3962)
amr=fixed(A/'MF.json','5ba837d3e46be8ca5a94ea4156ba46bd6cd6feeb7d3f7378643be5c08a63f14d',3393)
apr=fixed(A/'postseal.json','be55c5d8b52620b476ba4fecd55656e2881482454cc3375049efe41dfc1d2914',991)
mhr=fixed(M/'HDF.json','bfcb5010778c27ed4065bc6cda5d963e8f568f2207a413e7b5029b541f0613e7',9816)
mmr=fixed(M/'MF.json','4d3bc4f86dbd64b103fa145400fb3ad9977b6d0ebaed3da63646ad8207110b25',7575)
orr=fixed(M/'actual-adoption/outcome.json','8ea1c5bfbc09f2c4458780169368753f20807acdb058f16d921514cd79c10ba7',98048)
cr=fixed(P/'root-calling-contract.json','5e00adb0b1de608247159afb8982cdd0dc58c6cec4abecb447df7a350da8b682',18632)
ah,am,ap,mh,mm,out,c=[load(r) for r in (ahr,amr,apr,mhr,mmr,orr,cr)]
for r in am['members']+mm['members']:read(r)
oldpins={r['path']:r for r in json.loads(read(next(r for r in am['members'] if Path(r['path']).name=='input-pins.json')))}
def oldlocal(p):return load(oldpins[str(p.resolve())])
intent=oldlocal(M/'actual-adoption/intent.json')
committed=oldlocal(M/'actual-adoption/committed.json')
owned=oldlocal(M/'actual-adoption/owned-handles.cleanup.actual.json')
inputguard=oldlocal(M/'actual-adoption/input-guard.cleanup.actual.json')
change=load(mh['change_set_ref'])
choice=load(c['bound_source_refs']['choice_ref'])
targets=out['final_target_refs'];source21=c['compiler_closure']['Source21']
for r in targets+source21:read(r)
gp=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=fixed(gp,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404);graw=read(gr)
gm=types.ModuleType('adoption_supplement_guard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(graw,str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(list(pins.values()))
 ck('every_finite_input_held_exact',all(hashlib.sha256(guard.get_buffer(r['path'])).hexdigest()==r['sha256'] and len(guard.get_buffer(r['path']))==r['bytes'] for r in pins.values()))
 ck('original_independent_pair_and_postseal',ah['manifest_ref']==amr and ap['handoff_ref']==ahr and ap['manifest_ref']==amr and ap['status']=='PASS_ACTUAL_REVIEW_INPUTS_STABLE')
 ck('original_actual_review_pass',ah['decision']=='ACTUAL_CP367_OW171_AND_MAIN7_SOURCE_ADOPTION_VERIFIED_PASS' and ah['independent_checks']==70 and ah['finite_exact_held_inputs']==312 and ah['actual_Main7_source_adoption_verified'] is True)
 ck('original_reviewer_independent',ah['actor_id']==ACTOR and ah['actor_role']=='INDEPENDENT_NON_AUTHOR' and ACTOR not in c['current_adoption_requirement']['actor_excludes'])
 ck('original_review_handles_closed',ah['all_review_guards_closed'] is True and ah['all_actual_guard_files_directories_closed'] is True and ah['retained_handles']==0)
 ck('source_pair_contract_exact',mh['manifest_ref']==mmr and c['current_adoption_requirement']['source_handoff_ref']==mhr and c['current_adoption_requirement']['source_manifest_ref']==mmr)
 ck('outcome_path_contract_exact',orr['path']==c['current_adoption_requirement']['outcome_path']==choice['future_adoption_outcome_path'])
 ck('actual_outcome_success',out['status']=='SOURCE_ADOPTED_PENDING_REAL_DISPATCH_AND_FORMAL_REVIEW' and out['error'] is None and out['final_matches_expected_commit_or_rollback'] is True)
 ck('committed_seven_exact',len(targets)==7 and targets==committed['after_refs']==[v['after_target_ref'] for v in change['targets']]==choice['main_seven_after_refs'])
 ck('seven_current_held',all(pin(v['path'])==v for v in targets))
 ck('source21_contract_choice_exact',len(source21)==21 and source21==choice['source21'])
 ck('source21_change_set_exact',all(dict(path=str((R/v['path']).resolve()),sha256=v.get('current_ref',v.get('desired_ref'))['sha256'],bytes=v.get('current_ref',v.get('desired_ref'))['bytes'])==s for v,s in zip(change['source21'],source21)))
 ck('source21_current_held',all(pin(v['path'])==v for v in source21))
 ck('transaction_success',out['transaction']['status']=='SEVEN_SOURCE_TARGETS_COMMITTED' and out['transaction']['written_indices']==list(range(7)) and out['transaction']['rollback_attempted'] is False and committed['all_seven_verified_while_held'] is True)
 ck('intent_exact_seven',intent['exact_targets']==[v['path'] for v in targets])
 for name,g in [('adoption_owned_files_and_directories',owned),('adoption_input',inputguard)]:
  ck(name+'_closed0',g['closed'] is True and g['errors']==[] and g['retained_handles_count']==0)
 ck('outcome_cleanup_receipts_exact',out['owned_cleanup']==owned and out['guard_cleanup']==inputguard)
 ck('input_entries_closed_verified',inputguard['verification']=='PASSED' and all(v['verified'] is True and v['closed'] is True and v['final_path_match'] is True for v in inputguard['entries']))
 ck('actual_adoption_no_formal_or_native',out['formal_dispatcher'] is False and type(out['formal_case_accepted_delta']) is int and out['formal_case_accepted_delta']==0 and out['new_Go_SQL_API_model_calls']==0)
 ck('original_pending952_remains_separate',ah['current_Root_reported_live']==953 and ah['Source_cut951_next952'] is True and ah['registered_failures']==949)
 ck('commands_revision_still39',json.loads(guard.get_buffer(targets[6]['path']))['revision']==39)
finally:
 cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup)
ck('supplement_guard_closed0',cleanup['closed'] is True and cleanup['errors']==[] and cleanup['retained_handles_count']==0 and cleanup['verification']=='PASSED')
ck('inputs_stable_after_guard_close',all(pin(v['path'])==v for v in pins.values()))
decision=dict(schema=c['current_adoption_requirement']['decision_schema'],decision=c['current_adoption_requirement']['decision'],actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',adoption_outcome_ref=orr,source_handoff_ref=mhr,source_manifest_ref=mmr,final_target_refs=targets,source21=source21,all_handles_closed=True,formal_acceptance=False,formal_case_accepted_delta=0)
ck('contract_exact_decision_fields',set(decision)==set(c['current_adoption_requirement']['decision_fields']))
save('actual-decision.json',decision)
save('input-pins.json',list(pins.values()))
save('checks.json',checks)
save('provenance.json',dict(original_actual_review_handoff_ref=ahr,original_actual_review_manifest_ref=amr,original_actual_review_postseal_ref=apr,calling_contract_ref=cr,adoption_outcome_ref=orr,source_handoff_ref=mhr,source_manifest_ref=mmr,reviewer_new_original_failures=[],Root_reported_next_failure=953,previous_pending_ordinals=[952],canonical_write=False,Main_write=False,product_Native_calls=0,formal_acceptance=False,formal_case_accepted_delta=0))
save('result.json',dict(status='PASS',decision=decision['decision'],checks=len(checks),finite_held_inputs=len(pins),all_handles_closed=True,new_reviewer_failures=0))
print(json.dumps(dict(status='PASS',checks=len(checks),pins=len(pins),decision_ref=pin(N/'actual-decision.json'))))

