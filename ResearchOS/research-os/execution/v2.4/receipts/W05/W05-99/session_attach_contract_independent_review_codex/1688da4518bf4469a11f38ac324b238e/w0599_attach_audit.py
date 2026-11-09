from pathlib import Path
import json,hashlib,re,difflib
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';Q=B/'session_attach_contract_revision_codex/1a11ded594f5378b7512125d';O=B/'session_attach_contract_independent_review_codex/1688da4518bf4469a11f38ac324b238e';T=R/'.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def pin(p):
 p=Path(p).resolve();d=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(d).hexdigest(),bytes=len(d))
def save(n,x):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return pin(p)
def copy(p,name):
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write(p.read_bytes())
 return dict(original=pin(p),copy=pin(target))
def text(p):return Path(p).read_text(encoding='utf-8')
canon=[R/'execution/v2.4'/(n+'.json') for n in ('checkpoint','path_ownership','step_state','commands')]
main=[R/'internal/domain'/n for n in ('client_protocol.go','client_protocol_control_windows_test.go','client_session_fence.go','backup_recovery.go')]
before=[pin(p) for p in canon+main]
checks=[]
def check(n,v):checks.append(dict(name=n,passed=bool(v)))
h=read(Q/'HDF.json');mf=read(Q/'MF.json');all_refs=[]
for ref in list(mf['members'].values())+read(Q/'public-input-pins.json')['inputs']:
 actual=pin(ref['path']);all_refs.append(actual);check('exact input:'+actual['path'],actual['sha256']==ref['sha256'].removeprefix('sha256:') and actual['bytes']==ref['bytes'])
check('HDF pinned',pin(Q/'HDF.json')['sha256']=='ce190fcd2df7983906707414f74f4a53887f1c9802d1877019b3de99318bdca2')
check('MF pinned',pin(Q/'MF.json')['sha256']=='c067c90baddfeceaaec1172d64254c71996e6cc60f9db775671d3cd3895dbbd8')
base=T/'internal/domain/client_protocol.go';candidate=Q/'candidate-root/internal/domain/client_protocol.go';tests=Q/'candidate-root/internal/domain/client_protocol_attach_contract_windows_test.go'
rawbase=base.read_bytes();rawcandidate=candidate.read_bytes();b=rawbase.decode('utf-8');c=rawcandidate.decode('utf-8')
replacements=read(Q/'production-replacements.json');forward=b;steps=[]
for r in replacements:
 pos=r['position'];valid=forward[pos:pos+len(r['before'])]==r['before'];steps.append(valid)
 if valid:forward=forward[:pos]+r['after']+forward[pos+len(r['before']):]
check('sequential replacement positions and forward bytes',all(steps) and forward.encode('utf-8')==rawcandidate)
inverse=c;steps=[]
for r in reversed(replacements):
 pos=r['position'];valid=inverse[pos:pos+len(r['after'])]==r['after'];steps.append(valid)
 if valid:inverse=inverse[:pos]+r['before']+inverse[pos+len(r['after']):]
check('inverse recovers complete T6 bytes',all(steps) and inverse.encode('utf-8')==rawbase)
marker='func (s *ClientService) handleWrite';check('complete prefix Execute dispatch unchanged',b[:b.index(marker)]==c[:c.index(marker)])
marker='\tcase "session.control":';bi=b.index(marker,b.index('func (s *ClientService) handleWrite'));ci=c.index(marker,c.index('func (s *ClientService) handleWrite'));check('complete suffix session control journal unchanged',b[bi:]==c[ci:])
names=re.findall(r'^func (Test\w+)\(',text(tests),re.MULTILINE);check('five test functions',len(names)==5)
candidate_branch=c[c.index('\tcase "session.attach":',c.index('func (s *ClientService) handleWrite')):ci]
renew=candidate_branch[:candidate_branch.index('\t\tif sess.runID != ""')]
check('renewal precedes all run settlement checks','return complete(' in renew and 'runState(' not in renew)
check('renewal does not inspect restore authority',all(term not in renew for term in ('backup_restore_barriers','runtime_observations','restore_fenced','client_queue_fences','HandoffEpoch','journal(')))
check('renewal CAS matches project revision epoch writer lease and archival state',all(term in renew for term in ('project_id=?','revision=?','writer_epoch=?','writer_client_id=?','lease_expires_at=?','sealed_at IS NULL','archived_at IS NULL')))
check('transfer always requires run children and queue settlement','if !settled {' in candidate_branch and 'liveRunStatuses[status]' not in candidate_branch)
check('old ACK replay untouched','original != nil && !(deref(env.Method) == "session.control" && deref(original.Status) == "ACKNOWLEDGED")' in c)
evidence=[]
sources=[(Q/'HDF.json','source-evidence/HDF.json'),(Q/'MF.json','source-evidence/MF.json'),(candidate,'source-evidence/client_protocol.go'),(tests,'source-evidence/client_protocol_attach_contract_windows_test.go'),(Q/'CONTRACT-MAPPING.md','source-evidence/CONTRACT-MAPPING.md'),(Q/'client-protocol-attach.patch','source-evidence/client-protocol-attach.patch'),(Q/'production-replacements.json','source-evidence/production-replacements.json'),(R.parent/'ResearchOS_Implementation_Package_v2.4/22_CLIENT_INTERFACE_DETAILS.md','contract-evidence/22_CLIENT_INTERFACE_DETAILS.md')]
for name in ('client_protocol.go','client_session_fence.go','backup_recovery.go','backup_command_queue.go','session_service.go','v24_sessions.go','client_protocol_journal.go','client_protocol_sessions.go','client_protocol_configuration.go','client_command_identity.go','client_command_queue.go','client_protocol_control_windows_test.go','client_protocol_configuration_test.go','runtime_configuration_binding_windows_test.go'):
 sources.append((T/'internal/domain'/name,'baseline-evidence/'+name))
q4=B/'typed_runtime_goal_fixture_attach_revision_codex/7d0b8a53d3d24e629a085fccb30b7d1e'
for name in ('HDF.json','MF.json','report.md'):sources.append((q4/name,'q4-evidence/'+name))
sources.append((T/'internal/domain/contracts/client.protocol.schema.json','contract-evidence/client.protocol.schema.json'))
for p,name in sources:evidence.append(copy(p,name))
counterexample=dict(kind='STATIC_SOURCE_PATH_COUNTEREXAMPLE_NOT_EXECUTED',preconditions=['Authenticated original owner/client after local reauthentication, exact current Session revision and writer_epoch=null.', 'Session maps Run R and still has an unexpired client_sessions.lease_expires_at copied from the snapshot.', 'Restore runs backupFence: backup_restore_barriers(P,R) refreshed, Run status RECONCILING and Run lease expired; client Session lease/epoch remain unchanged.', 'No runtime observation for same project/run/current Run epoch newer than the restore barrier proves children_stopped=true AND queue_empty=true.'],candidate_trace=['Execute identity replay lookup finds a new command and dispatch preserves valid identity/revision.', 'Candidate lines1131-1161 enters same-owner unexpired branch, updates only client lease with CAS, builds snapshot, returns COMPLETED/write_owner_acquired=true at unchanged epoch.', 'The only existing client restore trigger fires on UPDATE OF writer_epoch and NEW>OLD; lease-only UPDATE cannot trigger it.', 'runState and HandoffEpoch are below the early return and never execute.'],base_trace=['T6 enters runState for a mapped unsettled RECONCILING Run and returns SESSION_BUSY.', 'Even with stale settled Run flags, its epoch-advancing path reaches the existing restore fresh-observation trigger.'],impact='An unresolved restored ownership claim is extended and reported acquired with the pre-restore generation. This violates the source contract; no claim is made that a later runtime tool actually launched or that other queue/dispatch fences were bypassed.',required_fix='Fence the lease-only branch using current restore/reconciliation authority, not wall-clock expiry alone. An unresolved restored claim must be refused or routed through reviewed recovery before granting a fresh generation; ordinary active same-owner renewal without a restore fence must remain allowed.',required_witness_predicate=['Same authoritative project and Run, and the applicable current Run lease epoch.', 'Observation strictly newer than the most recent barrier for that project/Run.', 'Both children_stopped and queue_empty are true.', 'A restored old writer generation must not be treated as valid merely because its persisted Session lease is in the future; recovery must establish its new valid generation.', 'Existing session queue/control restore fences and resume_requires_explicit_user must remain effective; renewal/transfer must not clear them.'],required_regressions=['Normal active Run, same owner, valid lease and no restore fence still renews with unchanged epoch/revision/events.', 'Restored same owner with a still-future Session lease and no fresh observation cannot extend the lease, publish a successful acquired result, or mutate ownership/journal.', 'Old observation, wrong project/Run/epoch, only children_stopped, and only queue_empty never satisfy recovery.', 'Fresh correctly bound settlement flows through the actual reviewed recovery/reacquisition generation path; exact command replay repeats neither renewal nor transfer.'])
counterref=save('restore-counterexample.json',counterexample)
after=[pin(p) for p in canon+main];check('Main canonical unchanged during audit',before==after);check('current CP358',read(canon[0])['revision']==358)
checksref=save('static-checks.json',dict(schema='researchos.independent-session-attach-source-checks.v1',checks=checks,all_integrity_and_static_path_checks_passed=all(x['passed'] for x in checks),source_component_accepted=False,review_verdict='REQUEST_CHANGES',tests_executed=False,Go_SQL_native_model_executed=False,input_refs=all_refs,source_and_contract_evidence_copies=evidence,canonical_and_Main_before=before,canonical_and_Main_after=after,test_names=names,restore_counterexample_ref=counterref,mechanical_failure_ordinals=[829]))
print(json.dumps(dict(static_checks_ref=checksref,integrity_and_path_checks_passed=all(x['passed'] for x in checks),failed_checks=[x for x in checks if not x['passed']],counterexample=counterref,evidence_copies=len(evidence),verdict='REQUEST_CHANGES'),ensure_ascii=False))
