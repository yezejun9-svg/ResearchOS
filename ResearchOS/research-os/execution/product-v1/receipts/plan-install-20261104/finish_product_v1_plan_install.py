"""Reconcile the verified staged plan; finish only the unexecuted commit phase."""
import hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os'); HERE=Path(__file__).resolve().parent
OUT=ROOT/'execution/product-v1/receipts/plan-install-20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists();t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));os.replace(t,p)
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','user.name=Codex','-c','user.email=codex@local.invalid','--no-optional-locks',*args],cwd=ROOT,stderr=subprocess.STDOUT).decode('utf-8')
j=read(OUT/'journal.json');assert j['status']=='VERIFIED_BEFORE_COPY'
PINS=j['source_sha256'];destinations={n:('docs/product-v1/PLAN.md' if n=='PLAN.md' else 'execution/product-v1/'+n) for n in PINS}
for n,rel in destinations.items():assert sha(ROOT/rel)==PINS[n],n
files=list(destinations.values())+['execution/product-v1/state.json']
assert set(git('diff','--cached','--name-only').splitlines())==set(files)
assert git('rev-parse','HEAD').strip()=='b8e9efeee3c95dcb8577e5f3fee56ed0b812afc1'
cpfile=ROOT/'execution/v2.4/checkpoint.json';cpraw=cpfile.read_bytes();cp= json.loads(cpraw)
assert cpraw==(OUT/'checkpoint.cp602.before.json').read_bytes() and cp['revision']==602 and len(cp['failure_counters'])==2448
raw=(ROOT/'execution/product-v1/state.json').read_bytes();state= json.loads(raw)
assert b'\r\n' in raw and state['status']=='PLANNING_BASELINE_INSTALLED_READY_FOR_IMPLEMENTATION'
(OUT/'installer.attempt01.py').write_bytes((HERE/'install_product_v1_plan.py').read_bytes())
(OUT/'state.before-lf-fix.json').write_bytes(raw)
(ROOT/'execution/product-v1/state.json').write_bytes(raw.replace(b'\r\n',b'\n'))
assert read(ROOT/'execution/product-v1/state.json')==state
git('add','-f','--','execution/product-v1/state.json');git('diff','--cached','--check')
put(OUT/'journal.json',dict(status='EXACT6_LF_VERIFIED_AWAITING_COMMIT',source_sha256=PINS,repair='Only new Root-generated state CRLF to LF; five frozen planning files unchanged.'))
commit_output=git('commit','-m','docs: define finite harness workbench v1 and preserve legacy acceptance mapping')
head=git('rev-parse','HEAD').strip();tree=git('rev-parse','HEAD^{tree}').strip()
put(OUT/'journal.json',dict(status='PLAN_COMMITTED_AWAITING_CHECKPOINT',head=head,commit_output=commit_output))
status=git('status','--porcelain=v1','-uno');assert len(status.splitlines())==20
protected=read(ROOT/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json')['protected_preserved']
for rel,d in protected.items():assert (sha(ROOT/rel) if (ROOT/rel).is_file() else 'ABSENT_BEFORE')==d,rel
(OUT/'codex-metadata').mkdir()
for f in ('result.json','version.txt','exec_help.txt'):(OUT/'codex-metadata'/f).write_bytes((HERE/'product-v1-codex-local-probe-01'/f).read_bytes())
now=datetime.now(timezone.utc).isoformat()
event=dict(at=now,attempts=1,origin_key='20261104|v1-plan-install|ffafe7',classification='ROOT_STATE_CRLF_DIFF_CHECK_DIAGNOSTIC_NOT_PRODUCT_FAILURE',counter_reset=False,
 detail=dict(first_terminal='ffafe7 exit1',actual_git_check_exit=2,resolution='Readback6d65f2 identified only137 CRLF state lines. Original installer/state retained; five source planning hashes unchanged; LF-only fix passed before commit. No installation replay.'))
assert event['origin_key'] not in {x.get('origin_key') for x in cp['failure_counters']};cp['failure_counters'].append(event)
resume=dict(checkpoint_revision=603,main_head=head,main_tree=tree,status=state['status'],planning_source_sha256=PINS,product_v1_journeys_accepted=0,product_v1_journeys_required=13,
 legacy_formal_accepted=0,legacy_formal_required=42,historical_diagnostic_records=len(cp['failure_counters']),counter_reset=False,old_worktrees_preserved=True,implementation_authorized=True,active_construction_owners=[],
 prior_readonly_recovery='Old cell46 terminated on disconnect; fresh e17050 read exited0; no old write replay.',
 next=state['next'])
put(OUT/'RESUME.json',resume)
cp['revision']=603;cp['expected_previous_revision']=602;cp['updated_at']=now
cp['head']=cp['current_Main_HEAD']=head;cp['current_Main_tree']=tree
cp['current_effective_formal_status']['current_head']=head;cp['current_effective_formal_status']['needs_rederive_after_source_change']=True
cp['next_command']=state['next']+' Read execution/product-v1/state.json and '+str((OUT/'RESUME.json').relative_to(ROOT))
cp['current_implementation']=dict(status=state['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),active_construction_owners=[],formal_increment=0)
cp['product_direction']=dict(status='V1_IMPLEMENTATION_AUTHORIZED',plan_ref='docs/product-v1/PLAN.md',state_ref='execution/product-v1/state.json',legacy_metrics_preserved=True)
assert cpfile.read_bytes()==cpraw;put(cpfile,cp)
handoff=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(OUT/'handoff.cp602.before.md').write_bytes(before)
t=handoff.with_name(handoff.name+'.cp603.new');assert not t.exists()
t.write_bytes(('# Current resume CP603 — PRODUCT V1 IMPLEMENTATION AUTHORIZED\n\nRead docs/product-v1/PLAN.md and execution/product-v1/state.json. Five planning records+initial state committed;13 journeys NOT_RUN. Old22/42 mapped without transferring PASS or resetting failures. Start same-Coordinator Codex readonly integration and actual React/Desktop entry; then serial Pi review/Windows delivery. Original worktrees retained; no old model/Native qualification replay.\n\n').encode('utf-8')+before);os.replace(t,handoff)
(OUT/'finish_product_v1_plan_install.py').write_bytes(Path(__file__).read_bytes())
put(OUT/'journal.json',dict(status='PLAN_COMMIT_CHECKPOINT_HANDOFF_SAVED',checkpoint=603,head=head))
print(json.dumps(dict(checkpoint=603,head=head,plan_files=6,journeys=13,legacy_parents=22,legacy_cases=42,old_statuses=20,protected=len(protected),historical_records=len(cp['failure_counters']))))
