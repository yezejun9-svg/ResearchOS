"""Seal final CP569 failure/reconciliation evidence; no process actions."""
import datetime,hashlib,json,os
from pathlib import Path
OUT=Path(__file__).resolve().parent
BASE=OUT.parent.parent
NATIVE=BASE/'product_host_native_20261028'/'native-init-diagnosis-02'
EXEC=NATIVE/'execution-cp569-01'
RECON=NATIVE/'reconcile-cp569'/'execution01'
SNAP=OUT/'final-input-snapshots'
SNAP.mkdir(exist_ok=False)
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(name,obj):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
refs=[]
for label,folder in [('diagnostic',EXEC),('reconciliation',RECON)]:
    target=SNAP/label;target.mkdir()
    for p in sorted(folder.iterdir()):
        if not p.is_file():continue
        raw=p.read_bytes();(target/p.name).write_bytes(raw)
        assert p.read_bytes()==raw,'Concurrent evidence change:'+str(p)
        refs.append(ref(p))
save('FINAL-INPUTS.json',refs)
waiting=load(EXEC/'WAITING_FOR_ROOT.json')
release=load(EXEC/'ROOT-RELEASE.json')
released=load(EXEC/'ROOT-RELEASED.json')
terminal=load(EXEC/'CONTROLLER-TERMINAL.json')
message=load(RECON/'normal-close-message.json')
closed=load(RECON/'RESULT.json')
preflight=load(RECON/'preflight.json')
scans=[json.loads(line) for line in (EXEC/'release-scans.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
for key in ('scope_sha256','controller_pid','release_nonce','known_identities'):
    assert release[key]==waiting[key]
assert release['actor']=='codex:/root' and release['root_confirmed_identity_absence'] is True
assert release['schema']=='researchos.native-chooser-root-release.v1'
assert datetime.datetime.fromisoformat(release['confirmed_absent_at'])>=datetime.datetime.fromisoformat(waiting['at'])
release_sha=ref(EXEC/'ROOT-RELEASE.json')['sha256']
assert released['release_sha256']==release_sha
assert released['known_identities']==waiting['known_identities']
assert released['status']=='ROOT_RELEASED_AFTER_TWO_ABSENCE_SCANS'
assert released['product_clean_close'] is False
images={os.path.normcase(p) for p in waiting['bundle_images']}
known_pids={p['pid'] for p in waiting['known_identities']}
recomputed=[]
for scan in scans:
    blockers=[]
    assert scan['status']=='OBSERVED' and scan['release_sha256']==release_sha
    for row in scan['rows']:
        if row['pid'] in known_pids:blockers.append('KNOWN_PID_PRESENT')
        if not row.get('image') or row.get('read_error'):blockers.append('UNKNOWN_IDENTITY')
        elif os.path.normcase(row['image']) in images:blockers.append('EXACT_BUNDLE_IMAGE_PRESENT')
    assert blockers==scan['blockers']==[]
    recomputed.append({'at':scan['at'],'row_count':len(scan['rows']),'blockers':blockers})
assert len(scans)>=2
spacing=(datetime.datetime.fromisoformat(scans[-1]['at'])-datetime.datetime.fromisoformat(scans[-2]['at'])).total_seconds()
assert spacing>=2
assert terminal['exit']==1 and terminal['controller_pid']==waiting['controller_pid']
assert terminal['native_request_count']==1 and terminal['automatic_retries']==0
assert message['sent'] is True and message['hwnd']==1183294 and message['pid']==60152
assert preflight['windows']==[{'hwnd':1183294,'title':'ResearchOS','class':'Chrome_WidgetWin_1','visible':False}]
assert closed['normal_close_confirmed'] is True and closed['witness_retired'] is True
assert all(row['signalled'] is True and row['exit']==0 for row in closed['exit_codes'].values())
assert set(closed['exit_codes'])=={'electron','core'}
assert closed['original_diagnostic_failed'] is True
final_process=load(OUT/'FINAL-PROCESS-OBSERVATION.json')
assert final_process['matching_processes']==[]
scope=load(OUT/'initial-input-snapshots'/'Owned-chooser-diagnostic-scope.json')
witness=Path(scope['state_root'])/'LocalAppData'/'ResearchOS'/'data'/'product-supervisor.json'
assert not witness.exists()
reply=load(EXEC/'native-reply.raw')
assert reply['error']['message']=='INVALID_REQUEST: folder selection cancelled'
save('FINAL-RECOMPUTATION.json',{'scope_binding':'PASS','release_binding':'PASS','known_identity_list':'EXACT',
    'scan_recomputation':recomputed,'last_two_scans_seconds_apart':spacing,'controller_failure_exit':terminal['exit'],
    'hidden_window_normal_close':closed,'current_witness_absent':True,'all_known_pids_and_bundle_absent':True})
report={'schema':'researchos.independent-owned-chooser-execution-final-review.v1',
    'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/product_host_independent_20261028',
    'status':'DIAGNOSTIC_FAILURE_CAPTURED_ROOT_NORMAL_RECONCILIATION_ACCEPTED',
    'raw_diagnostic_evidence_accepted':True,'native_chooser_success':False,
    'original_diagnostic_clean_close':False,'separate_root_normal_close_accepted':True,
    'controller_reconciled_release_accepted':True,'controller_exit':1,
    'formal_increment':0,'reviewer_product_process_actions':0,
    'conclusions':[
        'One raw request/reply captured: NATIVE_ERROR / INVALID_REQUEST / folder selection cancelled. Folder chooser succeeded=false; original client and folder helper exit1.',
        'Cancellation text means Shell selection API returned null, not evidence of a human cancel. Post-reply pipe PID error combines API failure and mismatch; server disconnects after one frame, so actual PID change is unproven.',
        'Root independently found the existing hidden ResearchOS Chrome_WidgetWin_1 HWND1183294 for PID60152. The original visibility-filtered helper failure did not mean the window was absent.',
        'One separately scoped exact-identity WM_CLOSE was delivered to that HWND. Retained Electron/Core handles both signalled with exit0 and witness retired; this Root reconciliation close is accepted.',
        'Exact Root release binding and known list validated. Two controller scans independently recomputed with no blockers, then controller returned failure exit1. Final reviewer CIM sees no known PID or bundle process and witness is absent.',
        'ROOT-RELEASED product_clean_close=false correctly preserves the original diagnostic result; it does not negate the separate Root normal-close proof.'
    ],
    'not_proven':['Native chooser usability or successful selection','Full CLI/GUI lifecycle acceptance','Reason the Shell folder dialog returned null','Cause of the earlier attempt02 process disappearance','SystemDrive omission as the cause of relative caches or chooser failure'],
    'evidence_refs':[ref(OUT/'INITIAL-REVIEW.json'),ref(OUT/'FINAL-INPUTS.json'),ref(OUT/'FINAL-RECOMPUTATION.json'),ref(OUT/'FINAL-PROCESS-OBSERVATION.json'),ref(OUT/'hidden-close-source-review'/'REVIEW.json')]
}
save('FINAL-REVIEW.json',report)
print(json.dumps(ref(OUT/'FINAL-REVIEW.json'),ensure_ascii=False))
