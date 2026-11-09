"""Resume only the known staged precommit failure; never replay the old integrator."""
import argparse,hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
ORIGINAL=HERE/'product-v1-workbench-refinement-integration-plan.json'
ORIGINAL_SHA='9f638519d01318687407dfb2de40cf9bfdc3993c470703a0652011ff4ddab549'
AMENDMENT=HERE/'product-v1-workbench-assistant-newline-amendment-20261105'
AMENDMENT_SHA='43f076b3b0c13131017380e86708f6433bfa863104de73ae7c5ded3722e100e3'
OLD_JSX='69d0ecbbbfed1e5b51a8c60186131eb2e39ea8909c15160cb7949d03120df095'
NEW_JSX='08ca4e3f3b67660de3f52dbf7b687ae2a7e2e5e504716895032fb21d1ee87bf0'
JSX='apps/web/src/workbench.jsx'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def observed(p):return sha(p) if p.is_file() else 'ABSENT_BEFORE'
def put(p,v):
 t=p.with_name(p.name+'.newline-resume.new');assert not t.exists();t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
def gitbytes(cwd,*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','user.name=Codex','-c','user.email=codex@local.invalid','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT)
def git(cwd,*args):return gitbytes(cwd,*args).decode('utf8')
ap=argparse.ArgumentParser();ap.add_argument('--review-ref',required=True);ap.add_argument('--review-sha',required=True);a=ap.parse_args()
assert sha(ORIGINAL)==ORIGINAL_SHA and sha(AMENDMENT/'manifest.json')==AMENDMENT_SHA
plan=read(ORIGINAL);scopefile=ROOT/plan['scope_ref'];assert sha(scopefile)==plan['scope_sha256'];scope=read(scopefile);wt=Path(scope['worktree']);out=ROOT/plan['receipt_ref'];resume=out/'newline-resume'
assert not resume.exists() and not (out/'integration.json').exists()
oldjournal=out/'root-integration-journal.json';oldjournalbytes=oldjournal.read_bytes();assert read(oldjournal)==dict(status='CHECKED_AWAITING_EXACT_COPY',base_main=plan['expected_main_head'],plan_sha256=ORIGINAL_SHA)
reviewfile=ROOT/a.review_ref;assert reviewfile.resolve().is_relative_to(ROOT.resolve()) and sha(reviewfile)==a.review_sha
review=read(reviewfile);assert review['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and review['formal_increment']==0 and not review['pending_blockers']
files=review['source_sha256'];oldfiles=plan['source_sha256'];assert set(files)==set(oldfiles)==set(scope['production_paths']+scope['test_paths']) and len(files)==6
assert oldfiles[JSX]==OLD_JSX and files[JSX]==NEW_JSX
for ref,digest in oldfiles.items():
 assert sha(wt/ref)==sha(ROOT/ref)==digest
 assert hashlib.sha256(gitbytes(ROOT,'show',':'+ref)).hexdigest()==digest
 assert sha(AMENDMENT/'candidate'/ref)==files[ref]
 if ref!=JSX:assert files[ref]==digest
old=(ROOT/JSX).read_bytes();new=(AMENDMENT/'candidate'/JSX).read_bytes();assert old.count(b'\r')==1 and old.count(b'\n')==783 and len(old)==75212
assert old.split(b'\n')[418]==b'  const [hostError, setHostError] = useState(null)\r' and new==old.replace(b'\r\n',b'\n') and len(new)==75211
assert git(ROOT,'rev-parse','HEAD').strip()==plan['expected_main_head'] and git(wt,'rev-parse','HEAD').strip()==scope['base_head']
assert set(git(ROOT,'diff','--cached','--name-only').splitlines())==set(files) and not git(wt,'diff','--cached','--name-only').strip()
for ref,digest in plan['evidence_pins'].items():assert sha(ROOT/ref)==digest
protected=plan['protected_sha256']
def check_protected():
 for ref,digest in protected.items():assert observed(ROOT/ref)==digest
check_protected();status_staged=git(ROOT,'status','--porcelain=v1','-uno');status_before=''.join(line for line in status_staged.splitlines(keepends=True) if line[3:].rstrip('\r\n') not in files)
cpfile=ROOT/'execution/v2.4/checkpoint.json';statefile=ROOT/'execution/product-v1/state.json';cpraw=cpfile.read_bytes();stateraw=statefile.read_bytes()
assert cpraw==(out/'checkpoint.before.json').read_bytes() and stateraw==(out/'state.before.json').read_bytes()
cp=read(cpfile);state=read(statefile);assert cp['revision']==691 and cp['current_Main_HEAD']==plan['expected_main_head'] and len(cp['failure_counters'])==plan['expected_failure_records']
now=datetime.now(timezone.utc).isoformat();rev=cp['revision']+1;resume.mkdir();(resume/'original-plan.json').write_bytes(ORIGINAL.read_bytes());(resume/'original-journal.json').write_bytes(oldjournalbytes)
journal=resume/'journal.json';put(journal,dict(status='VERIFIED_STAGED_OLD_SIX_AWAITING_ONE_BYTE_NORMALIZATION',old_source_sha256=oldfiles,new_source_sha256=files))
(wt/JSX).write_bytes(new);(ROOT/JSX).write_bytes(new);git(ROOT,'add','--',JSX)
for ref,digest in files.items():assert sha(ROOT/ref)==sha(wt/ref)==digest and hashlib.sha256(gitbytes(ROOT,'show',':'+ref)).hexdigest()==digest
assert set(git(ROOT,'diff','--cached','--name-only').splitlines())==set(files);git(ROOT,'diff','--cached','--check');check_protected();assert oldjournal.read_bytes()==oldjournalbytes
plan.update(source_sha256=files,review_ref=a.review_ref,review_sha256=a.review_sha)
plan['diagnostic_events'].append(dict(origin_key='workbench-assistant-refinement/freeze03/mixed-newline-precommit',classification='SOURCE_FORMAT_DEFECT_FIXED',detail='Initial exact6 integration stopped at git diff --cached --check before commit: JSX line419 contained the only CR byte. Original staged bytes, journal, plan and tests preserved. Independent amendment removes exactly this one 0d; same scope and other5 source bytes unchanged. Resume validates old index and protected files, stages only amended JSX, then commits exact6. Prior73Node/Vite retain oldSHA; fresh Desktop14 compiles amendedSHA.'))
plan['evidence_pins'][a.review_ref]=a.review_sha;plan['newline_amendment_manifest_sha256']=AMENDMENT_SHA
pf=resume/'amended-plan.json';put(pf,plan);put(journal,dict(status='STAGED_AMENDED_EXACT_SIX_AWAITING_COMMIT',plan_sha256=sha(pf)))
commit=git(ROOT,'commit','-m',plan['commit_message']);head=git(ROOT,'rev-parse','HEAD').strip();tree=git(ROOT,'rev-parse','HEAD^{tree}').strip();put(journal,dict(status='COMMITTED_AWAITING_CHECKPOINT',main_head=head,commit_output=commit))
for ref,digest in files.items():assert sha(ROOT/ref)==digest
check_protected();assert git(ROOT,'status','--porcelain=v1','-uno')==status_before
original=list(cp['failure_counters']);known={v.get('origin_key') for v in original}
for event in plan['diagnostic_events']:
 assert event.get('origin_key') and event.get('classification')
 if event['origin_key'] not in known:cp['failure_counters'].append({'at':now,'attempts':1,'counter_reset':False,**event});known.add(event['origin_key'])
assert cp['failure_counters'][:len(original)]==original
result=dict(status='INDEPENDENTLY_REVIEWED_SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED',at=now,checkpoint_revision=rev,main_head=head,main_tree=tree,source_sha256=files,review_ref=a.review_ref,review_sha256=a.review_sha,formal_increment=0,product_journey_increment=0,failure_records=len(cp['failure_counters']),old_changes_preserved=True,real_model_requests=plan['prior_real_model_requests'],real_model_requests_unit=plan['prior_model_requests_unit'],source_operation_real_model_requests=0,real_electron_qualification='NOT_RUN_BY_THIS_SOURCE_OPERATION',newline_amendment='EXACT_ONE_CR_DELETION; PREVIOUS73NODE_AND_VITE_ONLY_OLD_SHA; FRESH_BUILD14_PENDING',next=plan['next'])
put(out/'integration.json',result);put(out/'RESUME.json',result);cp.update(revision=rev,expected_previous_revision=rev-1,updated_at=now,head=head,current_Main_HEAD=head,current_Main_tree=tree,next_command=plan['next']+' Read '+str((out/'RESUME.json').relative_to(ROOT)))
cp['current_effective_formal_status']['current_head']=head;cp['current_effective_formal_status']['needs_rederive_after_source_change']=True;cp['current_implementation']=dict(status=result['status'],at=now,resume_ref=str((out/'RESUME.json').relative_to(ROOT)),formal_increment=0)
state.update(revision=state['revision']+1,updated_at=now,status=result['status'],last_progress_ref=str((out/'RESUME.json').relative_to(ROOT)),next=plan['next']);state.setdefault('integrated_source',[]).append(dict(scope_id=scope['scope_id'],main_head=head,source_sha256=files,review_ref=a.review_ref))
for entry in state['active_scopes']:
 if entry['scope_id']==scope['scope_id']:entry['status']='SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED'
assert cpfile.read_bytes()==cpraw and statefile.read_bytes()==stateraw;put(statefile,state);put(cpfile,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';oldhandoff=hf.read_bytes();(resume/'handoff.before.md').write_bytes(oldhandoff);t=hf.with_name(hf.name+'.cp'+str(rev)+'.new');assert not t.exists();t.write_bytes(('# Current resume CP'+str(rev)+' - REVIEWED WORKBENCH SOURCE INTEGRATED\n\nRead '+str((out/'RESUME.json').relative_to(ROOT))+'. Exact6 committed after independently reviewed one-byte newline normalization. Old73Node/Vite retained; freshbuild14 compiles newSHA. OriginalTasknotreplayed; journeys0/13 formal0/42, olddata/counters preserved.\n\n').encode('utf8')+oldhandoff);os.replace(t,hf)
(resume/Path(__file__).name).write_bytes(Path(__file__).read_bytes());assert oldjournal.read_bytes()==oldjournalbytes;put(journal,dict(status='SOURCE_COMMIT_CHECKPOINT_SAVED',checkpoint_revision=rev,main_head=head));print(json.dumps(dict(checkpoint=rev,main_head=head,source_files=6,failure_records=len(cp['failure_counters']),host_tasks=plan['prior_real_model_requests'])))
