import json,hashlib,re
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';S=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009';K=R.parent/'ResearchOS_Implementation_Package_v2.4';O=Path(__file__).parent
pins=[];catalog={}
def pin(p):
 p=Path(p);b=p.read_bytes();r=dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b));pins.append(r);return r,b
def save(n,x):
 with (O/n).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def add(label,p):
 rr,b=pin(p);d=json.loads(b);catalog[label]={'ref':rr,'document':d};return d
paths={
'main23_qualification':S/'main23.programme.qualification.bound.actual.root.json',
'old21_qualification':S/'old21.programme.qualification.bound.actual.root.json',
'old21_binding_review':B/'schema21_programme_root_binding_independent_review_codex/bind-old21-20261010-01/HDF.json',
'public21_actual':B/'schema21_public_bootstrap_actual_independent_review_codex/review-public21-actual-20261010-01/actual-decision.json',
'history20_actual':B/'history20_r2_actual_independent_review_codex/h20r2a-20261009-review/HDF.json',
'history20_r2_source':B/'historical20_upgrade_test_revision_codex/h20r2-1a11ee4f162766098eda3028b0679f2/HDF.json',
'history20_source_review':B/'historical20_upgrade_source_independent_review_codex/h20r2-20261009-source-review/HDF.json',
'history20_resource':B/'historical20_resource_route_readonly_codex/current_target_actual_review_01/HDF.json',
'public22_actual':B/'public22_existing_observation_actual_independent_review_codex/actual-20261010-01/decision.json',
'public22_runner':B/'genuine_schema22_public_upgrade_runner_source_codex/s22public-20261009-01-v3/HDF.json',
'public22_contract':B/'genuine_schema22_public_upgrade_runner_source_codex/s22public-20261009-01-v3/contract.json',
'public22_source_review':B/'public22_leaf_v3_independent_source_review_codex/review-01a12145/decision.json',
'prepared24_source':B/'prepared_abandonment_schema_upgrade_source_codex/e841e7fcddaa45ecb115f84df9827af2/HDF.json',
'prepared24_revision':B/'prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6/HDF.json',
'prepared24_review':B/'prepared_abandonment_schema_upgrade_independent_review_codex/cca15e02b36a4545b4218f1e9b7f472c/HDF.json',
'schema24_fixture_source':B/'schema24_current_fixture_revision_codex/e43b3af533177e02749afc2b8112814e/HDF.json',
'schema24_fixture_actual':B/'schema24_fixture_actual_independent_review_codex/3e1e9204c6804e119c289c06a07d953d/HDF.json',
'typed_Q3_source':B/'typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49/HDF.json',
'typed_Q3_source_review':B/'typed_runtime_goal_fixture_q3_independent_review_codex/9c5969e8d1a94b1eab93205758bb53a9/HDF.json',
'typed_Q3_actual':B/'typed_q3_epoch_actual_independent_review_codex/7340313b128c426b97c9acb20731fa73/HDF.json',
'remaining_boundary':B/'remaining_boundary_independent_review_codex/boundary-20261009-01/review.json',
}
for k,p in paths.items():add(k,p)
# Pin compact sibling metadata discovered from the directory; do not verify old test matrices again.
for name,p in paths.items():
 for child in p.parent.iterdir():
  if child.name in ('MF.json','manifest.json','HDF.json','decision.json','actual-decision.json','source-decision.json') and child.is_file() and child!=p:
   rr,_=pin(child);catalog[name].setdefault('related_metadata_refs',[]).append(rr)
for name in ('checkpoint.json','step_state.json','commands.json','HANDOFF_RESUME_PACK.md'):
 p=R/'execution/v2.4'/name;rr,b=pin(p)
 (O/('observed-'+name)).write_bytes(b)
 catalog['current_'+name]={'ref':rr,'snapshot_path':str(O/('observed-'+name))}
cp=json.loads((O/'observed-checkpoint.json').read_bytes());ss=json.loads((O/'observed-step_state.json').read_bytes());cm=json.loads((O/'observed-commands.json').read_bytes())
tasks=add('frozen_tasks',K/'contracts/tasks.json');ac=add('frozen_acceptance',K/'contracts/acceptance.json');plan=add('frozen_plan',K/'contracts/execution.plan.json')
for p in (R/'AGENTS.md',K/'tasks/steps/W05-99.md',K/'tools/task_packet.py',R/'tests/runtime/check/legacy.go',R/'ops/ci/runtime.py'):pin(p)
def objects(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from objects(x)
 elif isinstance(v,list):
  for x in v:yield from objects(x)
task=next(x for x in objects(tasks) if x.get('task_id')=='W05' and 'task_gate_checks' in x)
case=next(x for x in objects(ac) if x.get('id')=='A04' and 'assertions' in x)
step=next(x for x in objects(plan) if x.get('id')=='W05-99' and 'verification_commands' in x)
runtime=cm['commands']['test.runtime']
canonical_steps=[x for x in ss['steps'] if x.get('id','').startswith('W05')]
source_comparison=[]
for r in catalog['main23_qualification']['document']['source_refs']:
 now,_=pin(r['path']);source_comparison.append({'expected':r,'current':now,'sha_bytes_match':now['sha256']==r['sha256'] and now['bytes']==r['bytes']})
for key in ('program_ref',):
 r=catalog['main23_qualification']['document'][key];now,_=pin(r['path']);source_comparison.append({'expected':r,'current':now,'sha_bytes_match':now['sha256']==r['sha256'] and now['bytes']==r['bytes']})
main_inventory=sorted(str(p.relative_to(R)).replace('\\','/') for root in (R/'internal/domain',R/'migrations/sqlite',R/'ops/backup') for p in root.rglob('*') if p.is_file() and (re.search('history20|restored21|prepared_abandonment|prepared_run_abandonment|002[0-9]_',p.name) or p==R/'ops/backup/main.go'))
save('current-contract-map.json',dict(task_gates=task['task_gate_checks'],A04=case,W05_99=step,canonical_W05_steps=canonical_steps,command_registry_revision=cm['revision'],test_runtime=runtime,main_inventory=main_inventory,main23_resource_source_comparison=source_comparison))
save('artifact-catalog.json',catalog)
save('input-pins.json',pins)
print(json.dumps(dict(artifacts=len(paths),pins=len(pins),Main23_all_pins_match=all(x['sha_bytes_match'] for x in source_comparison),Main_inventory=main_inventory,public22_source_review={k:v for k,v in catalog['public22_source_review']['document'].items() if isinstance(v,(str,bool,int))},public22_actual={k:v for k,v in catalog['public22_actual']['document'].items() if isinstance(v,(str,bool,int))}),ensure_ascii=False))

