"""Seal bounded read-only readiness evidence, not a Source acceptance or Mode."""
from pathlib import Path
from datetime import datetime, timezone
import json, types

R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
sp=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('review_support');s.__file__=str(sp)
exec(compile(sp.read_bytes(),str(sp),'exec'),s.__dict__);s.D=D
decision_ref=s.pin(D/'readiness-decision.json')
controls_ref=s.pin(D/'delta-controls.json')
decision=json.loads(Path(decision_ref['path']).read_bytes())
controls=json.loads(Path(controls_ref['path']).read_bytes())
guard_ref=controls['guard_ref'];guard=json.loads(Path(guard_ref['path']).read_bytes())
if s.pin(guard_ref['path'])!=guard_ref or controls['failure'] is not None or controls['passed']!=10 or controls['failed']:
    raise ValueError('PERSISTED_READINESS_NOT_PASSED')
if not guard['closed'] or guard['retained_handles_count'] or guard['errors']:
    raise ValueError('PERSISTED_READINESS_GUARD_NOT_CLOSED')
host=s.capture('783ee8',0,0)
mf=s.write('MF.json',{'schema':'researchos.w09-nf6-bridge-reviewer-readiness-manifest.v1',
   'members':[s.pin(p) for p in sorted(D.iterdir(),key=lambda p:p.name) if p.is_file() and p.name not in ('HDF.json','MF.json')],
   'execution_grant':False,'formal_acceptance':False})
hdf=s.write('HDF.json',{'schema':'researchos.w09-nf6-bridge-reviewer-readiness-handoff.v1',
   'actor_id':'codex:/root/full_w09_source_review','backend_actor_id':s.ACTOR,
   'source_thread_id':s.THREAD,'root_thread_id':'01a11007-5233-7ca1-b71f-9e9e5ce84c98',
   'created_utc':datetime.now(timezone.utc).isoformat(),
   'status':'READONLY_REVIEW_COMPLETE_BR3_REPIN_REQUIRED','decision':'BR3_VERIFIER_REPIN_REQUIRED',
   'manifest_ref':mf,'source_decision_ref':decision_ref,'finite_controls_ref':controls_ref,
   'source_guard_ref':guard_ref,'actual_readonly_host':host,'inputs':decision['inputs'],
   'finding_id':'NF6-BR3-VERIFIER-001','finding_severity':'P1',
   'finding_summary':'BR3 fixed verifier Full conflicts with actual new NF6 author Full and future independent verifier Backup. Main dynamic five-role gate supports a truthful new BR4 author Full and verifier Backup.',
   'new_checks_passed':10,'new_checks_failed':0,'old_44_or_3905_controls_rerun':False,
   'all_source_guards_closed':True,'retained_handles_count':0,'new_original_failures':[],
   'original_BR3_Attach_author_preserved':True,'Root_authority_or_actual_audits_fabricated':False,
   'Mode_signed':False,'source_package_acceptance_issued':False,
   'Main_Canon_Scope_or_BR3_written':False,'actual_Native_Go_SQL_model_dispatcher_TP_calls':0,
   'future_qualification_or_execution_refs':None,'execution_grant':False,'formal_acceptance':False,
   'STOP':True})
print(json.dumps({'status':'READONLY_REVIEW_COMPLETE_BR3_REPIN_REQUIRED',
 'hdf_ref':hdf,'mf_ref':mf,'decision_ref':decision_ref,'controls_ref':controls_ref,
 'guard_ref':guard_ref,'actual_readonly_host':host,'new_checks_passed':10,
 'all_guards_closed':True,'retained_handles_count':0,'new_original_failures':[],
 'Mode_signed':False,'execution_grant':False,'formal_acceptance':False,'STOP':True},ensure_ascii=False))
