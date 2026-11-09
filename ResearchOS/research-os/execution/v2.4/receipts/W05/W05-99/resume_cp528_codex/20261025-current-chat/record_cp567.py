"""Keep attempt02 and its unresolved termination history; register preparation."""
import datetime,json,os
from pathlib import Path
from preserve_main_baseline import R,N,git,read,ref
from preserve_desktop_main_ecc28 import verify

def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    cp_path=R/'execution/v2.4/checkpoint.json';ow_path=R/'execution/v2.4/path_ownership.json';handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';state=R/'execution/v2.4/step_state.json'
    old={p:p.read_bytes() for p in [cp_path,ow_path,handoff,state]};cp,ow=read(cp_path),read(ow_path)
    assert cp['revision']==566 and ow['revision']==351 and len(cp['failure_counters'])==2281
    preserved=verify();W=R/'.local/worktrees/desktop-installed-delivery-20261025'
    assert git(W,'rev-parse','HEAD').decode().strip()=='5c4c94022bd92da68ef544f2779527bfe065c428'
    assert not git(W,'status','--porcelain=v1','--untracked-files=all')
    B=R/'execution/v2.4/receipts/W05/W05-99';A=B/'product_host_native_20261028'
    review=B/'product_host_independent_20261028/native-attempt02-review/REVIEW.json'
    assert ref(review)['sha256']=='9f5b6dca04ffc872f218ba8ad063658710549b278eb45e843bc9da1620534521'
    assert read(review)['native_accepted'] is False
    assert read(A/'attempt-02-outer/exit.json')['exit']==1
    assert read(A/'attempt-02-reconcile/close.exit.json')['exit']==1
    observation=read(A/'attempt-02-reconcile/post-close-observation.json')
    assert observation['rows']==[] and observation['WM_CLOSE_reached'] is False
    files=[review,A/'attempt-02/UNRESOLVED.json',A/'attempt-02-outer/exit.json',A/'attempt-02-reconcile/scope.json',A/'attempt-02-reconcile/close.exit.json',A/'attempt-02-reconcile/post-close-observation.json',A/'native-init-diagnosis-02/REPORT.json',A/'native-init-diagnosis-02/preparation/PREPARATION.json',A/'driver-v3/PREPARATION.json',B/'installer_inventory_20261028/P1-IMPLEMENTATION-DESIGN.md',B/'installer_inventory_20261028/P1-EXACT-PATHS.json',B/'installer_p1_design_review_20261028/DESIGN-REVIEW.md',B/'installer_p1_design_review_20261028/PATH-REVISION.json']
    out=N/'continuation-cp567';out.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    refs=[ref(p) for p in files]
    new(out/'adopted-facts.json',{'at':now,'preserved':preserved,'refs':refs,'native':'PARTIAL_READY_AND_SINGLE_HOST_PROVEN_INIT_REJECTED_LIFECYCLE_INCOMPLETE','termination':'NO_PROCESS_AT_RECONCILIATION_UNKNOWN_MECHANISM_NO_WM_CLOSE_SENT_READY_WITNESS_RETAINED','source':'5c4c940/build05 immutable','diagnostic_tools':'PREPARATION_REVISIONS_ACTIVE_NO_NATIVE_AUTHORITY','installer':'P1a static payload/finalizer feasible; upgrade requires consumer maintenance gate/journal and verifier replacement admission; no installer implemented','formal_increment':0})
    records=[
      {'origin_key':'20261028|product-host-native|attempt02','status':'ACTUAL_NATIVE_INIT_REJECTED_LIFECYCLE_FAILED','attempts':1,'exit':1,'ref':ref(review),'detail':'CLI init NATIVE_INVALID_REQUEST; folder helper subsequently finds no dialog. One native batch, both raw nonzero children preserved. READY/duplicate/status partial proof retained.'},
      {'origin_key':'20261028|product-host-native|attempt02-root-close-identity-refused','status':'ACTUAL_RECONCILIATION_HELPER_REFUSED_NO_MESSAGE','attempts':1,'exit':1,'refs':[ref(A/'attempt-02-reconcile/close.exit.json'),ref(A/'attempt-02-reconcile/post-close-observation.json')],'detail':'Guard rejected absent process before WM_CLOSE; no automatic retry. Termination mechanism unknown.'},
      {'origin_key':'20261028|root|native3-directory-locator','status':'READONLY_LOCATOR_DIAGNOSTIC','attempts':1,'exit':1,'tool_chunk':'5f1003','detail':'Guessed internal/native3 directory absent; correct native pipe sources subsequently located with rg --files.'},
      {'origin_key':'20261028|root|powershell-native-glob-locator','status':'READONLY_LOCATOR_DIAGNOSTIC','attempts':1,'exit':1,'tool_chunk':'a66ecc','detail':'Literal wildcard passed as path to rg; switched to directory with -g filter.'},
      {'origin_key':'20261028|root|host-schema-filename-locator','status':'READONLY_LOCATOR_DIAGNOSTIC','attempts':1,'exit':1,'tool_chunk':'1abde5','detail':'Guessed schema.go absent; no repeated locator after this; diagnostic request chosen instead of speculative fixes.'}]
    prior={r.get('origin_key') for r in cp['failure_counters']}
    for r in records:assert r['origin_key'] not in prior;r['counter_reset']=False
    cp['failure_counters'].extend(records)
    new(out/'new-records-ledger.json',{'historical_count':2281,'current_count':len(cp['failure_counters']),'records':records,'static_review_findings_not_counted_as_native_test_runs':True})
    resume=read(N/'continuation-cp566/RESUME.current.json')
    resume.update(schema='researchos.current-chat-resume.v145',at=now,checkpoint_revision=567,ownership_revision=352,failure_records_preserved=len(cp['failure_counters']),product_host_native_failure_review_ref=ref(review),product_host_attempt02_reconcile_ref=ref(A/'attempt-02-reconcile/post-close-observation.json'),installer_p1_review_ref=ref(B/'installer_p1_design_review_20261028/PATH-REVISION.json'),active_source_cards=[],
        next_command='Finish independent review of chooser raw-error diagnostic revision and wrapper-v3 revision; Root registers one fresh chooser diagnostic to locate init refusal. Do not replay old states or kill any process. In parallel prepare isolated P1a installer payload/finalizer implementation from reviewed static subset. Native lifecycle/installer/full22parents42formal remain open.')
    resume['current_product_host_status'].update(native='ATTEMPT02_PARTIAL_STARTUP_PROVEN_INIT_REJECTED_NO_LIFECYCLE_ACCEPTANCE',diagnosis='SINGLE_RAW_NATIVE_CHOOSER_TOOL_REVISION_PREPARATION',driver_v3='SOURCE_REVIEW_FIX_ACTIVE_NO_NATIVE',installer='STATIC_P1A_FEASIBLE_UPGRADE_DESIGN_NEEDS_MAINTENANCE_GATE')
    new(out/'RESUME.current.json',resume)
    cp.update(revision=567,expected_previous_revision=566,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
    cp['work_in_progress']['current_chat_continuation_cp567']=ref(out/'RESUME.current.json')
    cp['evidence_index'].append({'kind':'ATTEMPT02_FAILURE_AND_INSTALLER_DESIGN_REVIEW_PRESERVED','ref':ref(out/'adopted-facts.json'),'formal_increment':0})
    ow.update(revision=352,expected_previous_revision=351,updated_at=now,updated_by='codex:/root')
    ow['special_paths']['Product_host_owned_native_20261028'].update(state='ATTEMPT02_FAILED_PID_ABSENT_TERMINATION_UNKNOWN_NO_RETRY',failure_review=ref(review))
    ow['special_paths']['Product_host_native_driver_v3']={'owner':'codex:/root/product_native_driver_v2','state':'PREPARATION_REVISION_ONLY','write_root':str(A/'driver-v3'),'native_authorized':False}
    ow['special_paths']['Product_host_chooser_diagnostic']={'owner':'codex:/root/product_host_resume_20261028','state':'PREPARATION_REVISION_ONLY','write_root':str(A/'native-init-diagnosis-02'),'native_authorized':False,'location_note':'Root records actual new diagnostic artifact location under native receipts; product sources were not edited.'}
    prefix='# Current verified continuation CP567\n\nRead '+str(out/'RESUME.current.json')+' first. Native02 proved startup/singlehost but init rejected; later PIDs absent with stalewitness, termination unknown, WM_CLOSE never sent. Rawchooser+v3wrapper revisions are preparation only. Installer P1a static feasible, upgrade needs gate. Main/C57/originals preserved; formal0/42/all22open.\n\n'
    changes={cp_path:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),ow_path:(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode(),handoff:prefix.encode()+old[handoff]}
    for p in old:assert p.read_bytes()==old[p]
    for p,data in changes.items():
        (out/(p.name+'.before.raw')).write_bytes(old[p]);pending=p.with_name(p.name+'.cp567.pending')
        with pending.open('xb') as f:f.write(data)
        assert p.read_bytes()==old[p];os.replace(pending,p)
    assert state.read_bytes()==old[state]
    print(json.dumps({'checkpoint':567,'ownership':352,'mixed_records':len(cp['failure_counters']),'facts':ref(out/'adopted-facts.json')}))

if __name__=='__main__':main()
