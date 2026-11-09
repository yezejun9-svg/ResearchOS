import sys
sys.dont_write_bytecode=True
import observe_actual as o
import json,pathlib
E=o.E
acl=json.loads((E/'02-preflight-acl.json').read_text(encoding='utf-8'))
for row in acl['rows']:
 assert row['owner_is_current']
 if pathlib.Path(row['path']).name in ['host','host_state.json','runtime-verifier-installation.json']:
  assert row['protected'] and len(row['rules'])==1
  r=row['rules'][0];assert r['sid']==acl['current_sid'] and r['type']=='Allow' and r['mask']==0x001f01ff and not r['inherited'] and r['propagation_flags']==0
  assert r['inheritance_flags']==(3 if pathlib.Path(row['path']).name=='host' else 0)
amend=o.R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp493/actual-verifier-replacement-scope-amendment01.json'
assert o.pin(amend)['sha256']=='36118c237961a1d5bea414c1ede5934316869d07deaa0f16a207312cad1a3edb'
o.save(E/'02-preflight-summary.json',{'at':o.now(),'status':'PLAN_BINDINGS_MATCH_SHM_CHANGE_SEPARATELY_OBSERVED','phase_observation':o.pin(E/'02-preflight.json'),'plan_review':o.pin(E/'02-preflight-plan-review.json'),'additional_checks':o.pin(E/'02-preflight-additional-checks.json'),'scope_amendment':o.pin(amend),'observation_report':o.pin(E/'02-preflight-OBSERVATION.md'),'root_authorized_commit_not_executed_by_observer':True,'observer_failed_attempts_preserved':2,'data_acl_checks_pass':True,'schema_migration_performed':False,'signed_acceptance':False,'formal_increment':0})
print(json.dumps(o.pin(E/'02-preflight-summary.json'),ensure_ascii=False))
