import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=ROOT).decode('utf8')
p=argparse.ArgumentParser();p.add_argument('--kind',choices=['workbench','backend','managed-environment','cli-s04','assistant-home','public-health','source-context','core-system-drive','native-path-entry','native-conversation-layout','mobile-conversation-layout','mobile-scroll-region','native-policy-binding','harness-progress-ui','native-rpc-runtime','native-rpc-wiring','native-qualification-producer','native-preparation-wiring','qualification-build-binding','native-prelaunch-intent','native-normal-home-binding','native-preparation-desktop-drain','workbench-assistant-refinement'],required=True);p.add_argument('--review',required=True);p.add_argument('--review-sha',required=True);p.add_argument('--author-archive',required=True);p.add_argument('--evidence-pin',action='append',default=[]);p.add_argument('--output',required=True);a=p.parse_args()
out=Path(a.output);assert out.is_relative_to(HERE) and not out.exists()
rf=ROOT/a.review;assert sha(rf)==a.review_sha;r=read(rf)
assert r['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and r['formal_increment']==0 and not r['pending_blockers']
base='execution/product-v1/receipts/single-harness-20261104/'+a.kind
sf=ROOT/base/('scope.effective-v1.json' if a.kind in ('native-policy-binding','native-rpc-wiring','native-preparation-desktop-drain') else 'scope.json');scope=read(sf);cp=read(ROOT/'execution/v2.4/checkpoint.json')
assert set(r['source_sha256'])==set(scope['production_paths']+scope['test_paths'])
protected={}
excluded={'execution/v2.4/checkpoint.json','execution/v2.4/HANDOFF_RESUME_PACK.md','execution/product-v1/state.json'}
for b in git('diff','--name-only','-z').split('\0'):
 if b and b not in excluded:protected[b]=sha(ROOT/b) if (ROOT/b).is_file() else 'ABSENT_BEFORE'
assert not set(protected).intersection(r['source_sha256'])
events=list(r.get('diagnostic_events',[]))
if a.kind=='native-conversation-layout':
 events.extend([dict(origin_key='native-layout-author:encoding-observation-unverified',classification='UNVERIFIED_ENCODING_DISPLAY_DIAGNOSTIC',detail='Author briefly invalidated candidate01 on a PowerShell encoding concern. No distinct bad raw source was retained, and recorded01 SHA equals final02 SHA060ce0dd. Independent inverse of only two ASCII wrappers reproduces original e0f4 baseline, so current exact source is byte-safe; historical content corruption is unverified and not asserted. Original01/02 artifacts remain archived.'),dict(origin_key='root-native-layout-review:archive-selection-root-missing',classification='ROOT_EVIDENCE_ARCHIVE_PREFLIGHT',detail='Reviewer archive-file-list was a mixed C/D evidence map with absolute paths and no root field. Initial archive helper stopped before target creation. Root verified target absent, preserved original map, and created explicit C-only report/map selection; author and D source/scope evidence already pinned separately. No review/source bytes changed or runtime action occurred.')])
if a.kind=='public-health':events.append(dict(origin_key='root-product-v1-archive-bare-list-preflight',classification='ROOT_EVIDENCE_ARCHIVE',detail='Independent review selection was a bare relative-path JSON list. Initial archive failed before target creation; Root normalized this already-supported file list form without changing frozen review files, then archived once. Original exit1 retained.'))
if a.kind=='source-context':
 controller=read(ROOT/'execution/product-v1/receipts/single-harness-20261104/real-flow-controller04/reviews/report.json')
 for event in controller.get('diagnostic_events',[]):
  if event['origin_key']=='controller-native-deadline-default-json-datetime-local-coercion':event['origin_key']='product-v1-real-picker-deadline-before-action'
  events.append(event)
if a.kind=='workbench':
 author=read(HERE/'product-v1-workbench-author/AUTHOR-DIAGNOSTICS.json')
 skip={'resolved_environment','baseline_verification','root_authorized_contract_revision','build_nonblocking_notice'}
 for e in author['diagnostics']:
  if e['classification'] not in skip:events.append(dict(origin_key='product-v1-ui-author-'+e['origin'],classification=e['classification'],detail=e['detail'],evidence_ref=a.author_archive+'/prior-evidence/author.freeze01.diagnostics.json'))
 events.append(dict(origin_key='product-v1-ui-author-r2-cleanup-visible-fixture',classification='AUTHOR_TEST_HARNESS',detail='Cleanup VM fixture lacked visible callback before assertion; original45pass1fail preserved, corrected46pass.',evidence_ref=a.author_archive+'/DIAGNOSTICS.json'))
if a.kind=='backend':
 author=read(HERE/'product-v1-backend-author/diagnostics-04.json')
 events.extend(author['diagnostic_events'])
if a.kind=='cli-s04':
 author=read(HERE/'product-v1-cli-s04-author/diagnostics-02.json')
 events.extend(author['diagnostic_events'])
for event in events:
 if a.kind=='cli-s04' and event.get('finding_id')=='CLI-QA-001':
  event['canonical_origin_alias']=event.get('unique_origin');event['origin_key']='CLI-QA-001'
 if 'origin_key' not in event:event['origin_key']=event.get('unique_origin') or event.get('origin')
 assert event.get('origin_key') and event.get('classification'),event
archive=ROOT/a.author_archive;assert (archive/'ROOT_ARCHIVE.json').is_file()
pins={a.review:a.review_sha,a.author_archive+'/ROOT_ARCHIVE.json':sha(archive/'ROOT_ARCHIVE.json'),'execution/product-v1/contracts/harness.v1.interface.rev2.json':sha(ROOT/'execution/product-v1/contracts/harness.v1.interface.rev2.json')}
for entry in a.evidence_pin:
 ref,digest=entry.rsplit('=',1);f=ROOT/ref;assert f.resolve().is_relative_to(ROOT.resolve()) and sha(f)==digest;pins[ref]=digest
if a.kind=='source-context':pins['execution/product-v1/receipts/single-harness-20261104/real-flow-controller04/reviews/report.json']='c842e8a415fab1829bc4b5df365369fb4b4e838d49cac89fbc3bc0a807837c1d'
commit={'workbench':'feat(desktop): add native Harness task workbench with durable pending submissions','backend':'feat(runtime): execute Codex tasks through the existing Host coordinator','managed-environment':'fix(desktop): preserve installed Harness discovery for managed Core','cli-s04':'feat(cli): add authenticated native Harness task commands','assistant-home':'feat(desktop): make the default workbench a dark assistant home','public-health':'fix(desktop): allow fixed public health check without legacy principal','source-context':'fix(runtime): bind Harness input to the registered readonly source workspace','core-system-drive':'fix(desktop): derive the Windows system drive for managed Core','native-path-entry':'feat(desktop): support validated paths in the native folder chooser','native-conversation-layout':'fix(desktop): align native conversation with the shared canvas layout','mobile-conversation-layout':'fix(desktop): keep narrow conversation composer in normal document flow','mobile-scroll-region':'fix(desktop): bound mobile workbench scrolling above navigation','native-policy-binding':'fix(runtime): bind native policy identity to fail-closed Harness readiness','harness-progress-ui':'feat(desktop): visualize actual Harness task progress and permission blockers','native-rpc-runtime':'feat(runtime): gate native RPC turns on live permission evidence','native-rpc-wiring':'feat(runtime): revalidate Host authority before native model turns','native-qualification-producer':'feat(runtime): add bounded native qualification for synthetic tasks','native-preparation-wiring':'fix(runtime): settle stopped native preparation without model evidence','qualification-build-binding':'build(desktop): bind fixed synthetic qualification helper and provenance','native-prelaunch-intent':'fix(runtime): persist qualification intent before native launch','native-normal-home-binding':'fix(runtime): compare normal home using canonical Windows spelling','native-preparation-desktop-drain':'fix(runtime): allow proved stopped preparation on desktop exit','workbench-assistant-refinement':'feat(desktop): focus the Codex workbench on conversation and current task receipts'}[a.kind]
plan=dict(formal_increment=0,product_journey_increment=0,scope_ref=sf.relative_to(ROOT).as_posix(),scope_sha256=sha(sf),receipt_ref=base+'/integration',review_ref=a.review,review_sha256=a.review_sha,source_sha256=r['source_sha256'],expected_main_head=git('rev-parse','HEAD').strip(),expected_checkpoint=cp['revision'],expected_failure_records=len(cp['failure_counters']),protected_sha256=protected,evidence_pins=pins,diagnostic_events=events,commit_message=commit,next='Finish remaining independent source reviews and exact-path integration; build a fresh clean source-bound Desktop and verify the real single-Harness flow. Do not replay old model/Native scopes or count fixture checks as journey acceptance.')
receipt=ROOT/plan['receipt_ref'];assert not receipt.exists();receipt.mkdir()
if a.kind=='source-context':plan['next']='Build05 from the complete latest reviewed source, then register a NEW flow02 with independently reviewed controller04 and fresh owned data. Prior flow01 is consumed with zero submits; never replay it or resubmit UNKNOWN. Verify actual Task/Run/events and owned shutdown before any product acceptance.'
if a.kind=='core-system-drive':plan['next']='Build06 from complete latest reviewed source; keep poisoned build05/cache evidence unchanged. Use independently reviewed drive+owned-Electron-cwd controllers and NEW scopes for zero-model Tree diagnostic04 and same-Host CLI caps. Core cwd remains REPO because relative resource dependencies remain. Never waive bundle integrity or replay consumed03.'
if a.kind=='native-path-entry':plan['next']='Build07 from complete latest source, then review/bind a new zero-model real native invalid/valid path entry flow. Require fixed warning keeps chooser open and actual Shell-confirmed PIDL/canonical workspace matches fixture; typed edit text alone never grants a root. No arbitrary path API, no old-state replay, no model until separate actual ChatGPT gate and one-task scope.'
if a.kind=='native-conversation-layout':
 progress=read(ROOT/cp['current_implementation']['resume_ref']);assert progress['real_model_requests']==1
 plan['prior_real_model_requests']=1;plan['prior_model_requests_unit']='ONE_HOST_TASK_AND_NATIVE_HARNESS_INVOCATION; MODEL_INFERENCE_NOT_CONFIRMED'
 plan['next']='Build08 from complete latest reviewed source, then pin new zero-model real Native/responsive layout verification to the new bundle and unchanged authority flow. Check actual canvas/transcript/composer geometry and keep capability loading/unsupported statuses truthful. Codex model Task from CP647 remains failed closed; preserve original IDs/budget/history. MXC is local no-model availability only until separately verified; no profile relaxation, OS/admin setup or model replay.'
if a.kind in ('mobile-conversation-layout','mobile-scroll-region','native-policy-binding','harness-progress-ui'):
 progress=read(ROOT/cp['current_implementation']['resume_ref']);assert progress['real_model_requests']==1
 plan['prior_real_model_requests']=1;plan['prior_model_requests_unit']='PRIOR_ONE_HOST_TASK_NATIVE_HARNESS_INVOCATION; INFERENCE_NOT_CONFIRMED'
 plan['next']='Build09 from complete reviewed source and use NEW zero-model responsive visual02 scope. Preserve visual01 real mobile failures and all original Task/Run/model budget. MXC echo04 consumed with command syntax error; actual capability/enforcement remain unverified. Never relax product permissions, change saved native config/setup or replay model task.'
if a.kind=='mobile-scroll-region':plan['next']='Build10 from complete reviewed mobile viewport source, then new main-scroll-aware real visual03 controller/scope. Preserve original visual01/02 failures; actual main/document/transcript initial0 and all original overlap/overflow/control hit checks required. MXC fixed local echo diagnosis finished2/2, startup only; split-read profile/model/cancel/resume remain unverified. No extra echo, model task replay or permission/config/OS changes.'
if a.kind in ('native-policy-binding','harness-progress-ui'):
 plan['evidence_pins'][scope['contract_ref']]=scope['contract_sha256']
 plan['next']='Continue SourceA exact native-mode/shared-readiness/sealed-profile and immutable workspace binding fixes, independently review/tests before integration. Build latest complete backend+real-progress UI then fresh zero-model actual window/caps validation. Native appserver nonce same-thread barrier remains separate conditional SliceB; no production READY/model call until implemented and verified. Preserve old Task,echo2/2,FAILED/UNKNOWN and historical counters.'
 if a.kind=='native-policy-binding':
  plan['evidence_pins'][scope['original_lease_ref']]=scope['original_lease_sha256']
  for ref,digest in scope['reviewed_unchanged_sha256'].items():
   assert sha(ROOT/ref)==sha(Path(scope['worktree'])/ref)==digest
   plan['evidence_pins'][ref]=digest
if a.kind in ('native-rpc-runtime','native-rpc-wiring','native-qualification-producer','native-preparation-wiring','qualification-build-binding','native-prelaunch-intent'):
 progress=read(ROOT/cp['current_implementation']['resume_ref']);assert progress['real_model_requests']==1
 plan['prior_real_model_requests']=1;plan['prior_model_requests_unit']='PRIOR_ONE_HOST_TASK_NATIVE_HARNESS_INVOCATION; INFERENCE_NOT_CONFIRMED'
 for ref,digest in scope.get('contract_pins',{}).items():plan['evidence_pins'][ref]=digest
 if a.kind=='native-rpc-runtime':
  for ref in [base+'/scope.amendment01.json',base+'/job-budget-review.json']:plan['evidence_pins'][ref]=sha(ROOT/ref)
 if a.kind=='native-rpc-wiring':
  for refkey,hashkey in [('original_lease_ref','original_lease_sha256'),('amendment_ref','amendment_sha256')]:plan['evidence_pins'][scope[refkey]]=scope[hashkey]
 plan['next']='Complete final approved B1/B2/B3 combined fixtures and source integration serially; wire Host/helper shipped build identity and pre-RPC failure settlement under exact source scope. Build fresh Desktop then register one conditional synthetic Native qualification and NEW Task only after all gates. Production nil/missing qualification remains closed; preserve original failed Task, echo2/2 and all UNKNOWN/failure history.'
if a.kind=='workbench-assistant-refinement':commit='feat(desktop): focus the Codex workbench on conversation and current task receipts'
if a.kind in ('native-normal-home-binding','native-preparation-desktop-drain','workbench-assistant-refinement'):
 progress=read(ROOT/cp['current_implementation']['resume_ref']);prior=progress['real_model_requests'];assert type(prior) is int and prior==2
 plan['prior_real_model_requests']=prior;plan['prior_model_requests_unit']='TWO_CONFIRMED_HOST_TASK_SUBMISSIONS_NOT_INFERENCE_COUNT; PRIOR_CP647_UNCONFIRMED_AND_FLOW01_FAILED_BEFORE_MODEL'
 for ref,digest in scope.get('contract_pins',{}).items():plan['evidence_pins'][ref]=digest
 if a.kind=='native-preparation-desktop-drain':
  for refkey,hashkey in [('original_lease_ref','original_lease_sha256'),('amendment_ref','amendment_sha256')]:
   ref=scope[refkey];digest=scope[hashkey];assert sha(ROOT/ref)==digest;plan['evidence_pins'][ref]=digest
 plan['next']='Complete both disjoint runtime-home and Desktop preparation-drain source repairs, Root serial Go-only fixtures and independent reviews. Preserve original consumed flow01/Task IDs, forced original-Job cleanup and HostTask total2. Build a new clean complete Desktop after integration; any future live task needs a separate reviewed new scope, never replay old Task/echo2of2 or use archived proof as READY. No full product/formal completion claim.'
 if a.kind=='workbench-assistant-refinement':
  plan['commit_message']=commit
  plan['diagnostic_events'].append(dict(origin_key='root-build14-preparation-archive-selection-hash-parameter',classification='ROOT_EVIDENCE_ARCHIVE_PREFLIGHT',detail='Root passed an incorrect literal SHA for the build14 C selection. Archive stopped at selection hash assertion before target creation; Root verified target absent and actual selection SHA da88328f19c7b5058a62faa0ca43dfcc95d1fdd57ec533d0d3f573d4b5dfce26, then archived once. No build, model, source write, or uncertain action was replayed. Original failed command retained.'))
  plan['next']='Build fresh complete source-bound Desktop14 including the reviewed workbench and both backend fixes. Use a new independently reviewed zero-model visual scope for initial composer visibility at1440x1000 and390x844, permission blockers, actual activity and normal owned shutdown. Preserve original Task/UNKNOWN/failure/counters and HostTask total2. A future real model task requires a separate fresh reviewed scope; no replay or full acceptance claim.'
out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes((json.dumps(plan,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
print(json.dumps(dict(plan=str(out),sha256=sha(out),source_files=len(r['source_sha256']),checkpoint=cp['revision'],events=len(events))))
