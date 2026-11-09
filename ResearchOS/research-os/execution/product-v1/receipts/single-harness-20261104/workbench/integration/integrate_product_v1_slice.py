"""One-shot Root integration. Requires an independently approved, hash-pinned plan."""
import argparse, hashlib, json, os, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def observed(p):return sha(p) if p.is_file() else 'ABSENT_BEFORE'
def read(p):return json.loads(p.read_bytes())
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists(),str(t)
 t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
def git(cwd,*args):
 return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','user.name=Codex','-c','user.email=codex@local.invalid','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf8')
p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--sha',required=True);a=p.parse_args()
pf=Path(a.plan);assert sha(pf)==a.sha;plan=read(pf)
assert plan['formal_increment']==0 and plan['product_journey_increment']==0
scopefile=ROOT/plan['scope_ref'];assert sha(scopefile)==plan['scope_sha256'];scope=read(scopefile)
wt=Path(scope['worktree']);out=ROOT/plan['receipt_ref']
assert out.resolve().is_relative_to((ROOT/'execution/product-v1/receipts').resolve()) and out.is_dir()
journal=out/'root-integration-journal.json';assert not journal.exists(),'Reconcile existing outcome before any retry'
reviewfile=ROOT/plan['review_ref'];assert sha(reviewfile)==plan['review_sha256'];review=read(reviewfile)
assert review['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and review['formal_increment']==0 and not review['pending_blockers']
files=plan['source_sha256'];assert files==review['source_sha256']
assert set(files)==set(scope['production_paths']+scope['test_paths'])
for ref,digest in plan['evidence_pins'].items():assert sha(ROOT/ref)==digest,ref
for ref,digest in scope['baseline_sha256'].items():assert observed(ROOT/ref)==digest,('Main baseline drift',ref)
for ref,digest in files.items():assert sha(wt/ref)==digest,('Author freeze drift',ref)
assert git(ROOT,'rev-parse','HEAD').strip()==plan['expected_main_head']
assert git(wt,'rev-parse','HEAD').strip()==scope['base_head']
assert not git(ROOT,'diff','--cached','--name-only').strip() and not git(wt,'diff','--cached','--name-only').strip()
changed=set(git(wt,'diff','--name-only').splitlines())|set(git(wt,'ls-files','--others','--exclude-standard').splitlines())
assert changed==set(files),sorted(changed)
for ref in ['go.mod','go.sum']:assert sha(ROOT/ref)==sha(wt/ref)
protected=plan['protected_sha256']
def check_protected():
 for ref,digest in protected.items():assert observed(ROOT/ref)==digest,('Original result changed',ref)
check_protected();status_before=git(ROOT,'status','--porcelain=v1','-uno')
cpfile=ROOT/'execution/v2.4/checkpoint.json';cpraw=cpfile.read_bytes();cp=read(cpfile)
assert cp['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and cp['revision']==plan['expected_checkpoint']
assert len(cp['failure_counters'])==plan['expected_failure_records']
statefile=ROOT/'execution/product-v1/state.json';stateraw=statefile.read_bytes();state=read(statefile)
now=datetime.now(timezone.utc).isoformat();rev=cp['revision']+1
(out/'checkpoint.before.json').write_bytes(cpraw);(out/'state.before.json').write_bytes(stateraw)
put(journal,dict(status='CHECKED_AWAITING_EXACT_COPY',base_main=plan['expected_main_head'],plan_sha256=a.sha))
for ref,digest in files.items():
 dest=ROOT/ref;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((wt/ref).read_bytes());assert sha(dest)==digest
git(ROOT,'add','--',*files);assert set(git(ROOT,'diff','--cached','--name-only').splitlines())==set(files)
git(ROOT,'diff','--cached','--check');put(journal,dict(status='STAGED_AWAITING_COMMIT',paths=list(files)))
commit=git(ROOT,'commit','-m',plan['commit_message']);head=git(ROOT,'rev-parse','HEAD').strip();tree=git(ROOT,'rev-parse','HEAD^{tree}').strip()
put(journal,dict(status='COMMITTED_AWAITING_CHECKPOINT',main_head=head,commit_output=commit))
for ref,digest in files.items():assert sha(ROOT/ref)==digest
check_protected();assert git(ROOT,'status','--porcelain=v1','-uno')==status_before
original=list(cp['failure_counters']);known={v.get('origin_key') for v in original}
for event in plan.get('diagnostic_events',[]):
 assert event['origin_key'] and event['classification']
 if event['origin_key'] not in known:
  cp['failure_counters'].append({'at':now,'attempts':1,'counter_reset':False,**event});known.add(event['origin_key'])
assert cp['failure_counters'][:len(original)]==original
result=dict(status='INDEPENDENTLY_REVIEWED_SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED',at=now,checkpoint_revision=rev,main_head=head,main_tree=tree,source_sha256=files,review_ref=plan['review_ref'],review_sha256=plan['review_sha256'],formal_increment=0,product_journey_increment=0,failure_records=len(cp['failure_counters']),old_changes_preserved=True,real_model_requests=0,real_electron_qualification='NOT_RUN',next=plan['next'])
put(out/'integration.json',result);put(out/'RESUME.json',result)
cp.update(revision=rev,expected_previous_revision=rev-1,updated_at=now,head=head,current_Main_HEAD=head,current_Main_tree=tree,next_command=plan['next']+' Read '+str((out/'RESUME.json').relative_to(ROOT)))
cp['current_effective_formal_status']['current_head']=head;cp['current_effective_formal_status']['needs_rederive_after_source_change']=True
cp['current_implementation']=dict(status=result['status'],at=now,resume_ref=str((out/'RESUME.json').relative_to(ROOT)),formal_increment=0)
state.update(revision=state['revision']+1,updated_at=now,status=result['status'],last_progress_ref=str((out/'RESUME.json').relative_to(ROOT)),next=plan['next'])
state.setdefault('integrated_source',[]).append(dict(scope_id=scope['scope_id'],main_head=head,source_sha256=files,review_ref=plan['review_ref']))
for s in state.get('active_scopes',[]):
 if s['scope_id']==scope['scope_id']:s['status']='SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED'
assert cpfile.read_bytes()==cpraw and statefile.read_bytes()==stateraw
put(statefile,state);put(cpfile,cp)
handoff=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=handoff.read_bytes();(out/'handoff.before.md').write_bytes(old)
t=handoff.with_name(handoff.name+'.cp'+str(rev)+'.new');assert not t.exists()
t.write_bytes(('# Current resume CP'+str(rev)+' — PRODUCT V1 REVIEWED SOURCE INTEGRATED\n\nRead '+str((out/'RESUME.json').relative_to(ROOT))+'. '+plan['next']+' V1 journeys0/13; source checks do not establish real Harness or Desktop qualification. All original changes, failure records, paused worktrees and UNKNOWN retained.\n\n').encode('utf8')+old);os.replace(t,handoff)
(out/'root-integration-plan.json').write_bytes(pf.read_bytes());(out/'integrate_product_v1_slice.py').write_bytes(Path(__file__).read_bytes())
put(journal,dict(status='SOURCE_COMMIT_CHECKPOINT_SAVED',checkpoint_revision=rev,main_head=head))
print(json.dumps(dict(checkpoint=rev,main_head=head,source_files=len(files),failure_records=len(cp['failure_counters']),journeys_accepted=0)))
