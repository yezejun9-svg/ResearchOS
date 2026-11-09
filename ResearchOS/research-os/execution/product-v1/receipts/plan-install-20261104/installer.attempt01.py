import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'product-v1-plan-20261104'
OUT = ROOT / 'execution/product-v1/receipts/plan-install-20261104'
PINS = {
 'PLAN.md':'11005cec84b9cc3ec225c11606d16b81e0a0d65d5948196c7281cb86328dcee3',
 'acceptance.json':'261f8f3be1bb02746eba4a83bf61e01a1bc126c6850e0993e001ca0ec6aefce7',
 'legacy_mapping.json':'e53fc198b3b1c9277fdb0c0038ff6e1f79ad6ccab458c2e48545ed430ed142a4',
 'evidence.json':'ec905350d5af509d86ae60b35ef54013331bbeb39decfa15186ea37b4e20428c',
 'plan.json':'51309fa8584e006e7dd6a58382d4bcf6059b07b01bc007fa869114fc8810bb7d'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def git(*args):
 return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','user.name=Codex','-c','user.email=codex@local.invalid','--no-optional-locks',*args],cwd=ROOT,stderr=subprocess.STDOUT).decode('utf-8')
def put(p,v):
 t=p.with_name(p.name+'.new'); assert not t.exists()
 t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(t,p)

for name,digest in PINS.items(): assert sha(SOURCE/name)==digest,name
a=read(SOURCE/'acceptance.json'); m=read(SOURCE/'legacy_mapping.json'); p=read(SOURCE/'plan.json'); e=read(SOURCE/'evidence.json')
assert len(a['journeys'])==13 and len({x['id'] for x in a['journeys']})==13
assert all(x['status']=='NOT_RUN' and not x['evidence'] for x in a['journeys'])
assert {x['legacy_id'] for x in m['parent_tasks']}=={'W'+str(i).zfill(2) for i in range(22)}
assert len(m['formal_cases'])==42 and len({x['legacy_id'] for x in m['formal_cases']})==42
assert all(x['completion_transfer']=='NONE' for x in m['parent_tasks']+m['formal_cases'])
assert not m['coverage']['missing_parent_ids'] and not m['coverage']['missing_case_ids']
assert all(x['status']=='NOT_STARTED' for x in p['slices']) and not p['autonomous_self_iteration']
for item in e['sources']:
 assert sha(Path(item['path']))==item['sha256'],item['path']
cpfile=ROOT/'execution/v2.4/checkpoint.json'; cpraw=cpfile.read_bytes();cp=json.loads(cpraw)
assert cp['revision']==602 and len(cp['failure_counters'])==2448
assert cp['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
oldhead=git('rev-parse','HEAD').strip(); assert oldhead=='b8e9efeee3c95dcb8577e5f3fee56ed0b812afc1'
status=git('status','--porcelain=v1','-uno'); assert len(status.splitlines())==20
assert not git('diff','--cached','--name-only').strip()
protected=read(ROOT/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json')['protected_preserved']
for rel,d in protected.items(): assert (sha(ROOT/rel) if (ROOT/rel).is_file() else 'ABSENT_BEFORE')==d,rel
destinations={n:('docs/product-v1/PLAN.md' if n=='PLAN.md' else 'execution/product-v1/'+n) for n in PINS}
assert not OUT.exists(), 'Inspect prior journal/uncertain effects before retry'
for rel in list(destinations.values())+['execution/product-v1/state.json']: assert not (ROOT/rel).exists(),rel
OUT.mkdir(parents=True)
(OUT/'checkpoint.cp602.before.json').write_bytes(cpraw)
put(OUT/'journal.json',dict(status='VERIFIED_BEFORE_COPY',source_sha256=PINS))
for name,rel in destinations.items():
 target=ROOT/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((SOURCE/name).read_bytes());assert sha(target)==PINS[name]
now=datetime.now(timezone.utc).isoformat()
state=dict(schema='researchos.product-v1-state/1',revision=1,updated_at=now,status='PLANNING_BASELINE_INSTALLED_READY_FOR_IMPLEMENTATION',
 plan_ref='execution/product-v1/plan.json',acceptance_ref='execution/product-v1/acceptance.json',legacy_mapping_ref='execution/product-v1/legacy_mapping.json',
 implementation_authorized=True,old_cards_paused=True,legacy_failure_counters_reset=False,
 slices={x['id']:dict(status='NOT_STARTED',verification='NOT_RUN',evidence=[]) for x in p['slices']},
 journeys={x['id']:dict(status='NOT_RUN',evidence=[]) for x in a['journeys']},active_scopes=[],
 legacy_checkpoint=602,legacy_diagnostic_records_preserved=2448,
 resource_state=dict(codex=dict(version='0.166.0',auth='OBSERVED_LOGGED_IN_CHATGPT',model='UNVERIFIED',permissions='UNVERIFIED',cancel='UNVERIFIED',resume='UNVERIFIED'),pi=dict(version='0.99.2',auth='UNVERIFIED',model='UNVERIFIED')),
 next='Register exact source scopes for same-Coordinator Codex readonly driver and default React/Desktop client integration; preserve old worktrees and do not replay old qualifications.')
put(ROOT/'execution/product-v1/state.json',state)
files=list(destinations.values())+['execution/product-v1/state.json']
git('add','-f','--',*files)
assert set(git('diff','--cached','--name-only').splitlines())==set(files)
git('diff','--cached','--check')
put(OUT/'journal.json',dict(status='PLAN_EXACT6_STAGED_AWAITING_COMMIT',files=files))
commit_output=git('commit','-m','docs: define finite harness workbench v1 and preserve legacy acceptance mapping')
head=git('rev-parse','HEAD').strip();tree=git('rev-parse','HEAD^{tree}').strip()
put(OUT/'journal.json',dict(status='PLAN_COMMITTED_AWAITING_CHECKPOINT',head=head,commit_output=commit_output))
assert git('status','--porcelain=v1','-uno')==status
for rel,d in protected.items(): assert (sha(ROOT/rel) if (ROOT/rel).is_file() else 'ABSENT_BEFORE')==d,rel
probe=HERE/'product-v1-codex-local-probe-01';(OUT/'codex-metadata').mkdir()
for f in ('result.json','version.txt','exec_help.txt'):(OUT/'codex-metadata'/f).write_bytes((probe/f).read_bytes())
resume=dict(checkpoint_revision=603,main_head=head,main_tree=tree,status=state['status'],planning_source_sha256=PINS,product_v1_journeys_accepted=0,product_v1_journeys_required=13,
 legacy_formal_accepted=0,legacy_formal_required=42,historical_diagnostic_records=2448,counter_reset=False,old_worktrees_preserved=True,
 implementation_authorized=True,active_construction_owners=[],
 prior_readonly_recovery='Old cell46 was terminated during disconnect. Fresh read e17050 completed exit0; no old write or CLI execution was replayed.',
 next=state['next'])
put(OUT/'RESUME.json',resume)
cp['revision']=603;cp['expected_previous_revision']=602;cp['updated_at']=now
cp['head']=cp['current_Main_HEAD']=head;cp['current_Main_tree']=tree
cp['current_effective_formal_status']['current_head']=head;cp['current_effective_formal_status']['needs_rederive_after_source_change']=True
cp['next_command']=state['next']+' Read execution/product-v1/state.json and '+str((OUT/'RESUME.json').relative_to(ROOT))
cp['current_implementation']=dict(status=state['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),active_construction_owners=[],formal_increment=0)
cp['product_direction']=dict(status='V1_IMPLEMENTATION_AUTHORIZED',plan_ref='docs/product-v1/PLAN.md',state_ref='execution/product-v1/state.json',legacy_metrics_preserved=True)
assert cpfile.read_bytes()==cpraw and len(cp['failure_counters'])==2448;put(cpfile,cp)
handoff=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(OUT/'handoff.cp602.before.md').write_bytes(before)
t=handoff.with_name(handoff.name+'.cp603.new');assert not t.exists()
t.write_bytes(('# Current resume CP603 — PRODUCT V1 IMPLEMENTATION AUTHORIZED\n\nRead docs/product-v1/PLAN.md and execution/product-v1/state.json. Five planning records+initial state committed;13 journeys NOT_RUN, old22/42 mapped without transferring PASS or resetting failures. Start same-Coordinator Codex readonly integration and real default React/Desktop entry, then serial Pi review/Windows delivery. Original worktrees retained; no old model/Native qualification replay.\n\n').encode('utf-8')+before);os.replace(t,handoff)
(OUT/'install_product_v1_plan.py').write_bytes(Path(__file__).read_bytes())
put(OUT/'journal.json',dict(status='PLAN_COMMIT_CHECKPOINT_HANDOFF_SAVED',checkpoint=603,head=head))
print(json.dumps(dict(checkpoint=603,head=head,plan_files=6,journeys=13,legacy_parents=22,legacy_cases=42,old_statuses=20,protected=len(protected),historical_records=2448)))
