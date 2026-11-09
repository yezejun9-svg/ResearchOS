"""Static Main/Native inventory under a finite real SourceReadGuard."""
import ast
import importlib.util
import json
from pathlib import Path
import sys

N=Path(__file__).resolve().parent
R=N.parents[5]
P=R.parent/'ResearchOS_Implementation_Package_v2.4'
W=N.parent
def main():
 s=importlib.util.spec_from_file_location('gap_reader',N/'read_batch.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
 gs=importlib.util.spec_from_file_location('gap_guard_inventory',a.G);g=importlib.util.module_from_spec(gs);sys.modules[gs.name]=g;gs.loader.exec_module(g)
 known=[R/'execution/v2.4'/name for name in ('checkpoint.json','path_ownership.json','step_state.json','commands.json','current_spec.json','formal_case_index.py','formal_profile_w09.py')]
 known += [R/'ops/ci'/name for name in ('retrieval.py','w09_formal_router.py','w09_evidence_closure.py')]
 known += [P/'contracts/execution.plan.json',P/'contracts/acceptance.json',P/'contracts/tasks.json',P/'tasks/steps/W09-99.md',R/'execution/toolchains/locked.json',R/'AGENTS.md',Path(__file__),N/'read_batch.py',a.G]
 # Known report directories are enumerated, only existing report files are opened.
 report_paths=sorted((R/'execution/receipts/W09/retrieval').glob('run-*/report.json'))
 known+=report_paths
 legacy=W/'finite_controller_preparation_revision_codex/b9b9b105f8e74cc4a7b39a0c059914b8'
 known += [legacy/name for name in ('spec.v2.final.json','authority-contract.json','handoff.complete.json','finite-roster.json','case_worker.v2.final.py')]
 c19=W/'w09_c19_main_root_producer_v2_source_codex/mainc19p2-1a11fe4'
 known += [c19/name for name in ('HDF.json','MF.json','root-calling-contract.json','source.choice.json','main_c19_runtime.source.py','main_c19_launcher.source.py','prepare_main_c19.actual_owned.py','run_main_c19.actual_owned.py')]
 known += [W/'c19_two_actual_consumers_independent_review_codex/consumers-01a120dd/actual-decision.final.json',W/'c19_two_actual_consumers_independent_review_codex/consumers-01a120dd/consumer-summary.json']
 pins=[a.pin(p) for p in known]
 guard=g.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
 try:
  guard.acquire(pins)
  def read(p):return json.loads(Path(p).read_bytes())
  def literals(p,names):
   values={}
   for node in ast.parse(Path(p).read_bytes()).body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in names:
     values[node.targets[0].id]=ast.literal_eval(node.value)
   return values
  prod=literals(R/'ops/ci/retrieval.py',{'TESTS','SOURCES'});router=literals(R/'ops/ci/w09_formal_router.py',{'NATIVE','SELECTED','FORMAL'})
  source21=[a.pin(R/name) for name in prod['SOURCES']]
  # Hold Source21 in a separate actual guard before comparing the report hashes.
  second=g.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
  try:
   second.acquire(source21)
   hashes={str(Path(ref['path']).relative_to(R)).replace('\\','/'):'sha256:'+ref['sha256'] for ref in source21}
   reports=[]
   for p in report_paths:
    d=read(p);claimed=d.get('version_manifest',{}).get('source_sha256',{})
    reports.append(dict(report_ref=a.pin(p),run_id=d.get('run_id'),status=d.get('status'),check_id=d.get('check_id'),case_id=d.get('case_id'),scope=d.get('scope'),exit_code=d.get('exit_code'),assertion_ids=d.get('assertion_ids'),selected_tests=d.get('selected_tests'),source21_current=claimed==hashes,source_names_count=len(claimed),source_mismatches=[k for k in set(hashes)|set(claimed) if hashes.get(k)!=claimed.get(k)],error=d.get('error')))
  finally:second_cleanup=second.close()
  cp=read(R/'execution/v2.4/checkpoint.json');ss=read(R/'execution/v2.4/step_state.json');cm=read(R/'execution/v2.4/commands.json');ow=read(R/'execution/v2.4/path_ownership.json')
  plan=read(P/'contracts/execution.plan.json');card=next(row for row in plan['steps'] if row['id']=='W09-99');statuses={x['id']:x['status'] for x in ss['steps']}
  oldspec=read(legacy/'spec.v2.final.json');oldhandoff=read(legacy/'handoff.complete.json');oldroster=read(legacy/'finite-roster.json')
  oldsummary=dict(spec_keys=list(oldspec),handoff_keys=list(oldhandoff),spec_scalar_fields={k:v for k,v in oldspec.items() if type(v) not in (list,dict)},roster={k:v for k,v in oldroster.items() if k!='rows'})
  routes=[]
  for row in card['verification_commands']:
   route=(row['key'],'W09',row.get('check_id',''),row.get('case_id',''));tests=router['SELECTED'][route]
   routes.append(dict(command_key=row['key'],check_id=route[2],case_id=route[3],frozen_argv=row['argv_template'],formal_ids=router['FORMAL'][route],native_ids=router['NATIVE'][route],selected_tests=tests,packages=sorted({prod['TESTS'][test][0] for test in tests}),mode='LIVE_WINDOWS' if route[2]=='W09-G02' else 'FIXTURE',registry_entry=cm['commands'][row['key']]))
  summary=dict(schema='researchos.w09-static-gap-inventory.v1',current_canonical_refs=[a.pin(R/'execution/v2.4'/name) for name in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')],checkpoint_revision=cp['revision'],ownership_revision=ow['revision'],commands_revision=cm['revision'],dependency_statuses={d:statuses.get(d) for d in card['dependencies']},W09_99_status=statuses.get('W09-99'),current_formal_count=cp['work_in_progress']['formal_cases_current'],root_capture_authority=cp['work_in_progress'].get('w09_root_delivery_capture_index_ref'),fixed_root_capture_index_exists=(R/'execution/v2.4/root_delivery_captures/W09/W09-99/index.json').is_file(),routes=routes,Main_source21=source21,existing_Main_native_reports=reports,legacy_finite_controller=oldsummary,Native_or_dispatcher_or_SQLite_or_model_executed=False)
  assert all(a.pin(p['path'])==p for p in pins)
 finally:cleanup=guard.close()
 assert cleanup['closed'] and cleanup['retained_handles_count']==0 and cleanup['errors']==[] and second_cleanup['closed'] and second_cleanup['retained_handles_count']==0 and second_cleanup['errors']==[]
 gr=a.save(N/'inventory.guard.closed.json',dict(primary=cleanup,Source21=second_cleanup))
 sr=a.save(N/'inventory.json',summary)
 print(json.dumps(dict(inventory_ref=sr,guard_ref=gr,summary=summary),ensure_ascii=False))
if __name__=='__main__':main()
