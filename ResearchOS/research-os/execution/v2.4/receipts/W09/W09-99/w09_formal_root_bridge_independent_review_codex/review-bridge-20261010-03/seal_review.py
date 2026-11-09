from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,types

R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99'
D=W/'w09_formal_root_bridge_independent_review_codex/review-bridge-20261010-03'
N=W/'w09_formal_root_bridge_source_codex/bridge-20261010-03'
P=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def load(p):return json.loads(Path(p).read_bytes())
def save(name,value):
 p=D/name
 with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
 return pin(p)
support=types.ModuleType('actual_bridge_review_host_capture');support.__file__=str(P)
exec(compile(P.read_bytes(),str(P),'exec'),support.__dict__);support.D=D
host=support.capture('d5c6f9',0,0)
guard=support.guard();ownrefs=[pin(D/n) for n in ['review_bridge_delta.py','finite-delta-review.json','source-guard.closed.json']]+[pin(P),pin(N/'HDF.json'),pin(N/'MF.json')]
try:
 guard.acquire(ownrefs)
 report=load(D/'finite-delta-review.json');closed=load(D/'source-guard.closed.json');h=load(N/'HDF.json');mf=load(N/'MF.json')
 assert report['status']=='PASSED_SOURCE_ONLY' and len(report['checks'])==18 and all(c['passed'] for c in report['checks'])
 assert closed['verification']=='PASSED' and closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
 assert report['held_refs'] if 'held_refs' in report else len(report['held_input_refs'])==44
 old=load(h['task98_review_hdf_ref']['path'])
 sourcebindings={'source_ref':h['source_ref'],'source_hdf_ref':pin(N/'HDF.json'),'source_mf_ref':pin(N/'MF.json'),'consumer_launcher_ref':h['consumer_launcher_ref']}
 assert (sourcebindings['source_hdf_ref']['sha256'],sourcebindings['source_hdf_ref']['bytes'])==('1f85ead2fffdd5400270c3d0f1078bb661df91fbd8ff94bfd1dd05992e45aa0f',7862)
 assert (sourcebindings['source_mf_ref']['sha256'],sourcebindings['source_mf_ref']['bytes'])==('225bb69692fde3fb0d54afa017a93248db968ef9e0a24cdd2c9a81b3ad0119d1',6046)
 assert sourcebindings['source_ref'] in mf['members'] and sourcebindings['consumer_launcher_ref'] in mf['members']
 now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
 prior=[old['original1144_ref'],h['original1145_ref']]
 inputref=save('input-source-pins.json',{'schema':'researchos.bridge03-independent-input-pins.v1','held_refs':report['held_input_refs'],'all_refs_previously_verified_under_full_Source_guard':True,'held_count':44,'live_CP_OW_held':False})
 decision={
  'schema':'researchos.w09-formal-root-bridge-independent-source-review.v1',
  'decision':'ACCEPTED_SOURCE_ONLY','status':'ACCEPTED_SOURCE_ONLY','verdict':'ACCEPTED_SOURCE_ONLY',
  'reviewer_id':'/root/full_w09_source_review','reviewer_actor':'codex:/root/full_w09_source_review',
  'source_author':h['source_author'],'source_author_backend':h['source_author_backend'],
  'Root_thread_id':'01a11007-5233-7ca1-b71f-9e9e5ce84c98','actual_reviewer_thread':support.THREAD,
  'created_utc':now,**sourcebindings,'contract_ref':h['contract_ref'],
  'independent_non_author':True,'findings':[],
  'resolved_prior_findings':['BRIDGE-ROLE-001','BRIDGE-TEMP-002'],
  'prior_review_hdf_ref':h['task98_review_hdf_ref'],'prior_review_mf_ref':h['task98_review_mf_ref'],
  'finite_controls_ref':pin(D/'finite-delta-review.json'),'input_pins_ref':inputref,
  'source_guard_ref':pin(D/'source-guard.closed.json'),'actual_reviewer_hostpair':host,
  'actual_Source_author_audit_ref':pin(W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.bridge03-author.actual-audit.root.json'),
  'new_independent_controls_passed':18,'full_Source_members':20,'verified_held_refs':44,
  'reused_controls':report['reused_controls'],'previous_failure_origin_refs_preserved':prior,
  'prior_failure_counters_reset':False,'new_review_failures':[],
  'known_remaining_conditions':[
   'Root alone must issue genuine finite request/grant and owner/worker Scope; Source review supplies no execution authority.',
   'Every real Bridge Python and consumer must receive the exact physical C TEMP/TMP before tempfile initialization; launcher rejects an incompatible process cache.',
   'NF5 qualification, all four current-Source Native producers and independent mode decisions must pass the existing Main gates; historical Source21 cannot substitute for current Source.',
   'Main retains exact metadata/peer timestamp equality; this Source author original Final satisfies it, and future reviewer/role Final must be checked against its actual records.',
   'Only the existing six CM40 routes are used; real consumer results, RoleRegistry proofs, assembler inputs and Main formal checks remain pending.'
  ],
  'Root_next_step':'Capture this genuine reviewer Final into the existing Main role-audit chain; bind the exact decision and Source package refs in a real Root request. Continue runtime/resource qualification and actual stages only under separately issued authority.',
  'actual_runtime_authority':None,'RootScope_qualification_created':False,
  'actual_Bridge_stage_calls':0,'actual_dispatcher_calls':0,'actual_Native_Go_SQL_model_TP_calls':0,
  'Main_Canon_old_Source_writes':0,'execution_grant':False,'formal_acceptance':False,
  'parent_acceptance':False,'STOP_after_seal':True}
 decision_ref=save('decision.json',decision)
finally:
 sealclosed=guard.close();sealguardref=save('seal-source-guard.closed.json',sealclosed)
 assert sealclosed['closed'] and sealclosed['retained_handles_count']==0 and not sealclosed['errors']

members=[pin(p) for p in sorted(D.iterdir()) if p.is_file() and p.name not in ['MF.json','HDF.json']]
mfref=save('MF.json',{'schema':'researchos.source-manifest.v1','members':members,'member_count':len(members),'exclusions':['MF.json self','HDF.json references completed manifest']})
handoff={
 'schema':'researchos.w09-bridge-independent-source-review-handoff.v1','status':'ACCEPTED_SOURCE_ONLY',
 'reviewer_id':'/root/full_w09_source_review','reviewer_actor':'codex:/root/full_w09_source_review',
 'actual_reviewer_thread':support.THREAD,'actual_parent_Root_thread':decision['Root_thread_id'],
 'subject_Source_author':h['source_author'],'independent_non_author':True,
 **sourcebindings,'subject_hdf_ref':sourcebindings['source_hdf_ref'],'subject_mf_ref':sourcebindings['source_mf_ref'],
 'subject_source_ref':sourcebindings['source_ref'],'consumer_launcher_ref':sourcebindings['consumer_launcher_ref'],
 'manifest_ref':mfref,'decision_ref':decision_ref,'controls_ref':pin(D/'finite-delta-review.json'),
 'source_guard_ref':pin(D/'source-guard.closed.json'),'seal_source_guard_ref':sealguardref,
 'source_pins_ref':inputref,'actual_reviewer_hostpair':host,
 'actual_Source_author_audit_ref':decision['actual_Source_author_audit_ref'],
 'resolved_prior_findings':decision['resolved_prior_findings'],'passed_finite_controls':18,
 'reused_controls':report['reused_controls'],'verified_held_refs':44,'full_Source_members':20,
 'previous_failure_origin_refs_preserved':prior,'new_review_failures':[],'prior_failure_counters_reset':False,
 'all_Source_guards_closed_zero':True,'actual_runtime_authority':None,
 'Root_Scope_or_runtime_qualification_ref':None,'execution_grant':False,'formal_acceptance':False,'parent_acceptance':False,'STOP':True}
href=save('HDF.json',handoff)
print(json.dumps({'schema':'researchos.w09-bridge-independent-source-review-delivery.v1','reviewer_id':'/root/full_w09_source_review','reviewer_actor':'codex:/root/full_w09_source_review','source_author':h['source_author'],'Root_thread_id':decision['Root_thread_id'],'operation':'SOURCE_REVIEW_WITNESS','decision':'ACCEPTED_SOURCE_ONLY','review_refs':[href,mfref,decision_ref],'new_checks':18,'held_refs':44,'all_guards_closed_zero':True,'new_review_failures':[],'execution_grant':False,'formal_acceptance':False,'STOP':True},ensure_ascii=False))
