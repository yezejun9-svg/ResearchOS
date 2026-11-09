"""Seal new authored Bridge04 Source; no self-acceptance or product call."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,traceback,types

R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
sp=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('review_support');s.__file__=str(sp)
exec(compile(sp.read_bytes(),str(sp),'exec'),s.__dict__);s.D=D
AUTHOR='codex:/root/full_w09_source_review';BACKEND='/root/full_w09_source_review'
controls_ref={'path':str(D/'delta-controls.json'),'sha256':'8233a9dc6da2d70914578e4592af427066e01b6b69ceebd20dc39a0b539974d0','bytes':10811}
if s.pin(controls_ref['path'])!=controls_ref:raise ValueError('ACTUAL_DELTA_CONTROLS_DRIFT')
controls=json.loads(Path(controls_ref['path']).read_bytes());built=controls['built_refs']
closed_build=json.loads(Path(controls['guard_ref']['path']).read_bytes())
if controls['failure'] is not None or controls['failed'] or controls['passed']!=29:raise ValueError('DELTA_NOT_PASSED')
if s.pin(controls['guard_ref']['path'])!=controls['guard_ref'] or not closed_build['closed'] or closed_build['retained_handles_count'] or closed_build['errors']:raise ValueError('BUILD_GUARD_NOT_CLOSED')
source_inputs=json.loads(Path(built['source_inputs_ref']['path']).read_bytes())
refs=source_inputs['refs'];host=s.capture('03d0f9',0,0)
new_members=[s.pin(p) for p in sorted(D.iterdir(),key=lambda p:p.name) if p.is_file() and p.name not in ('HDF.json','MF.json')]
g=s.guard();failure=None;check_result=None
try:
    g.acquire(new_members+[refs['old_hdf'],refs['old_mf']])
    for key,ref in built.items():
        raw=g.get_buffer(ref['path'])
        if hashlib.sha256(raw).hexdigest()!=ref['sha256'] or len(raw)!=ref['bytes']:raise ValueError('NEW_SOURCE_WRITTEN_PIN_DRIFT:'+key)
    old_hdf=json.loads(g.get_buffer(refs['old_hdf']['path']))
    check_result={'name':'all_new_written_Source_members_exact_match_build_refs','passed':True,'prior_29_delta_or_old_44_22_controls_reexecuted':False}
except BaseException as exc:failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
finally:
    closed=g.close();seal_guard_ref=s.write('seal-source-guard.closed.json',closed)
    seal_controls_ref=s.write('seal-source-pins.json',{'schema':'researchos.w09-bridge04-seal-source-pins.v1','input_members':new_members,'source_guard_ref':seal_guard_ref,'check':check_result,'failure':failure,'persisted_delta_controls_ref':controls_ref,'actual_build_host':host,'old_successful_controls_rerun':False,'actual_product_calls':0,'execution_grant':False,'formal_acceptance':False})
if failure or not closed['closed'] or closed['retained_handles_count'] or closed['errors']:
    print(json.dumps({'status':'SOURCE_SEAL_FAILED','failure':failure,'seal_guard_ref':seal_guard_ref,'seal_controls_ref':seal_controls_ref},ensure_ascii=False));raise SystemExit(1)

mf=s.write('MF.json',{'schema':'researchos.source-manifest.v1','members':[s.pin(p) for p in sorted(D.iterdir(),key=lambda p:p.name) if p.is_file() and p.name not in ('HDF.json','MF.json')],
   'exclusions':['MF.json self','HDF.json handoff references this immutable manifest'],
   'execution_grant':False,'formal_acceptance':False})
h=copy.deepcopy(old_hdf)
h.pop('NF5_qualification',None)
h.update(source_author=AUTHOR,source_author_backend=BACKEND,actual_source_thread=s.THREAD,
  actual_parent_thread='01a11007-5233-7ca1-b71f-9e9e5ce84c98',created_utc=datetime.now(timezone.utc).isoformat(),
  status='SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW',generation='bridge-20261010-04',
  source_revision_uuid=controls['source_revision_uuid'],source_ref=built['source_ref'],
  consumer_launcher_ref=built['consumer_launcher_ref'],contract_ref=built['contract_ref'],
  root_calling_contract_ref=built['root_calling_contract_ref'],manifest_ref=mf,
  base_hdf_ref=refs['old_hdf'],base_mf_ref=refs['old_mf'],
  original_Attach_contribution={'source_author':old_hdf['source_author'],'source_author_backend':old_hdf['source_author_backend'],
    'source_thread_id':old_hdf['actual_source_thread'],'hdf_ref':refs['old_hdf'],'mf_ref':refs['old_mf'],
    'source_ref':refs['old_source'],'consumer_launcher_ref':refs['old_launcher'],'contract_ref':refs['old_contract']},
  readiness_hdf_ref=refs['readiness_hdf'],readiness_mf_ref=refs['readiness_mf'],readiness_decision_ref=refs['readiness_decision'],
  exact_inverse_ref=built['exact_inverse_ref'],patch_ref=built['patch_ref'],
  delta_controls_ref=controls_ref,source_inputs_ref=built['source_inputs_ref'],source_guard_ref=controls['guard_ref'],
  seal_source_guard_ref=seal_guard_ref,seal_source_pins_ref=seal_controls_ref,
  actual_source_build_host=host,actual_tool_io_ref=host['raw_ref'],
  prior_source_actual_tool_io_ref=old_hdf['actual_tool_io_ref'],prior_source_preseal_tool_io_ref=old_hdf['preseal_tool_io_ref'],
  changes=['VERIFIER actual backend changed from Full to Backup','new actual Full Source author canonical/backend, generation and package/selfrefs','all functions/ten stages and consumer launcher unchanged'],
  finite_delta_controls=29,finite_new_seal_checks=1,old_18_and_24_controls_rerun=False,old_BR3_22_controls_rerun=False,
  delta_control_limits={'AST_exact_inverse_only':True,'Source_role_and_peer_expression_only':True,'Source_fixture_is_not_actual_audit_or_grant':True},
  verifier_backend='/root/backup_regression_resources',
  future_Root_Scope_source_actor=BACKEND,future_Root_Scope_source_author_canonical=AUTHOR,
  independent_source_review_required=True,independent_source_review_ref=None,
  Source_author_self_acceptance=False,NF6_qualification='PENDING_ACTUAL_CURRENT_NF6_FACTS_AND_INDEPENDENT_REVIEW',
  future_Root_scope=None,future_Root_request=None,future_execution_grant=None,future_Mode_refs=None,
  actual_bridge_stages=0,actual_dispatcher_calls=0,actual_Main_module_calls=0,
  actual_Native_Go_SQL_model_TP_calls=0,Main_Canon_Scope_written=False,Native_roots_moved=False,C_drive_files_written=False,
  Root_Scope_execution_grant=False,all_source_guards_closed_zero=True,retained_handles_count=0,new_original_failures=[],
  actual_product_exits={'Native':None,'Go':None,'SQL':None,'dispatcher':None,'model':None,'TP':None},
  execution_grant=False,formal_acceptance=False,parent_acceptance=False,STOP=True)
hdf=s.write('HDF.json',h)
print(json.dumps({'status':'SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW','source_author':AUTHOR,'source_author_backend':BACKEND,'source_thread_id':s.THREAD,
 'generation':'bridge-20261010-04','source_revision_uuid':controls['source_revision_uuid'],
 'hdf_ref':hdf,'mf_ref':mf,'contract_ref':built['contract_ref'],'root_calling_contract_ref':built['root_calling_contract_ref'],
 'caller_ref':built['source_ref'],'consumer_launcher_ref':built['consumer_launcher_ref'],'delta_controls_ref':controls_ref,
 'source_guard_ref':controls['guard_ref'],'seal_source_guard_ref':seal_guard_ref,'actual_source_build_host':host,
 'delta_passed':29,'seal_passed':1,'new_original_failures':[],'all_guards_closed':True,'retained_handles_count':0,
 'Source_author_self_acceptance':False,'actual_product_exits':h['actual_product_exits'],'execution_grant':False,'formal_acceptance':False,'STOP':True},ensure_ascii=False))
