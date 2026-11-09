"""Authorize a two-file correction needed by the real shared-session lifecycle."""
import datetime, json, os, subprocess
from pathlib import Path
from preserve_main_baseline import R,N,git,read,ref
from preserve_desktop_main_ecc28 import verify

def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    cp_path=R/'execution/v2.4/checkpoint.json';ow_path=R/'execution/v2.4/path_ownership.json';handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';state=R/'execution/v2.4/step_state.json'
    before={p:p.read_bytes() for p in [cp_path,ow_path,handoff,state]}
    cp,ow=read(cp_path),read(ow_path)
    assert cp['revision']==561 and ow['revision']==346 and len(cp['failure_counters'])==2261
    preserved=verify();W=R/'.local/worktrees/desktop-installed-delivery-20261025'
    base='5ee2c694ee275a72f40e8aa1d6c377d719fb8631';tree='43e71226bbcb5d413bfa0ca2b11a767d255b2aec'
    assert git(W,'rev-parse','HEAD').decode().strip()==base and git(W,'rev-parse','HEAD^{tree}').decode().strip()==tree
    assert not git(W,'status','--porcelain=v1','--untracked-files=all')
    E=R/'execution/v2.4/receipts/W05/W05-99/installed_delivery_codex/20261025-current-chat/continuation-20261028'
    manifest=E/'BASE-5ee2-MANIFEST.json'
    assert ref(manifest)['sha256']=='1e37c66ffef97ea4cc6f558c9e2722593dac3bdf353557cec98e1db8d9bb8d80'
    assert not (W/'apps/cli/cli_host_metadata_scope_test.go').exists()
    out=N/'continuation-cp562';out.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    source=W/'apps/cli/cli_v2.go';core=W/'internal/domain/client_protocol.go'
    scope={'schema':'researchos.product-host-metadata-scope.v1','at':now,'owner':'codex:/root/product_host_resume_20261028',
        'reviewer':'codex:/root/product_host_independent_20261028','worktree':str(W),'base_commit':base,'base_tree':tree,
        'modify':['apps/cli/cli_v2.go'],'add':['apps/cli/cli_host_metadata_scope_test.go'],
        'source_baseline':[ref(source),ref(core)],'preserved_exact14_manifest':ref(manifest),
        'reason':'Existing CLI status sends selected-session fields to host.status, while the real Core rejects session_id/revision/epoch for host.status and workspace.list. This blocks the intended real shared-session lifecycle, regardless of baseline origin.',
        'must_implement':['Scope host.status and workspace.list envelopes to metadata: preserve selected project and authenticated client, omit session/revision/writer fields. Do not mutate shared context.',
            'Keep session reads/writes, session.attach, host.configure and first-use behavior unchanged; do not suppress Core refusal or relax the native lifecycle checks.',
            'Add focused tests with populated context, including valid session/write/configure controls and context immutability; retain all old failures.'],
        'allowed_execution':['Focused pure envelope tests named TestCLIHostMetadata*',
            'Existing TestW18ContinuationStatusProcess against compiled dev CLI plus in-process Go domain, owned SQLite/workspace and loopback HTTP fixture',
            'Pinned compiler and complete product-layout build on new clean commit, with new build03 output and receipts',
            'Compiled CLI non-host version/help/commands only with isolated environment',
            'Local atomic exact2 commit with git -c gc.auto=0 -c maintenance.auto=false'],
        'test_command':['go','test','./apps/cli','-run','^(TestCLIHostMetadata.*|TestW18ContinuationStatusProcess)$','-count=1','-timeout=300s','-v'],
        'artifact_root':str(W/'.local/host-metadata-cp562-20261028'),
        'receipt_root':str(E/'host-metadata-cp562'),
        'test_environment':'TEMP TMP GOTMPDIR GOCACHE LOCALAPPDATA APPDATA USERPROFILE HOME all inside fresh artifact_root; existing pinned Go/module cache read-only; GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off; clear inherited RESEARCHOS_* ROS_DESKTOP_* NODE_* ELECTRON_* proxy overrides; no user credentials.',
        'execution_order':'Preserve terminal CP561 exact7 at5ee2; exact2 repair and focused checks; freeze exact2 successor commit; fresh full build03; separately record impact decision for previous7, then independent current source/build review. No blind full suite rerun.',
        'not_authorized':['Change any original exact14 file or Core/tests outside these exact2 paths','Main merge/shared registry/state edits','Product Core/Electron native launch','Original data/credential/ACL/restart','Installer/P1 source or actual install','Whole-package CLI/renderer suite or unchanged pagination rerun','Changing acceptance criteria or erasing failures'],
        'formal_increment':0,'source_acceptance':False,'product_native_launch_authorized':False}
    new(out/'CLI-host-metadata-exact2-scope.json',scope)
    cmd=['python',str(R.parent/'ResearchOS_Implementation_Package_v2.4/tools/task_packet.py'),'next','--state',str(state)]
    p=subprocess.run(cmd,cwd=R,capture_output=True);(out/'selector.stdout.raw').write_bytes(p.stdout);(out/'selector.stderr.raw').write_bytes(p.stderr)
    packet=json.loads(p.stdout.decode('utf-8-sig'));assert p.returncode==0 and packet['state_source']=='VALIDATED_FILE' and packet['step']['id']=='W05-99'
    new(out/'registration-evidence.json',{'at':now,'scope':ref(out/'CLI-host-metadata-exact2-scope.json'),'preserved':preserved,'selector':{'argv':cmd,'exit':p.returncode,'stdout':ref(out/'selector.stdout.raw'),'stderr':ref(out/'selector.stderr.raw')},'formal_increment':0})
    rows=[
        {'origin_key':'20261028|root-cp562|installer-report-mutated-restored','detail':'An already-bound report was edited. Changed bytes preserved as revision02; original7565 bytes restored to exact35958c hash; Root rehashed both and retained correction ledger.'},
        {'origin_key':'20261028|root-cp562|native-wrapper-python-assert-gate','detail':'Independent review found assert authorization gates removable by Python optimization. Replaced by explicit RuntimeError gates; -I -O unauthorized-scope expected rejection exit1; no native process launched.'},
        {'origin_key':'20261028|root-cp562|readonly-observation-diagnostics','detail':'Optional absent receipt reads returned exit1, wrong cli_v2_test.go path probe corrected to actual tests; two wait dispatches aborted on incoming agent messages. No product writes from these probes.'},
        {'origin_key':'20261028|root-cp562|baseline-status-real-native-blocker','detail':'Independent source trace proved existing host.status session-scope rejection affects real Core and planned native status --project --session. Source repair registered; baseline origin does not waive behavior requirement.'},
    ]
    existing={x.get('origin_key') for x in cp['failure_counters']}
    for row in rows:
        assert row['origin_key'] not in existing
        row.update(status='DIAGNOSTIC_PRESERVED',attempts=1,counter_reset=False,product_failure=False)
    cp['failure_counters'].extend(rows)
    new(out/'new-records-ledger.json',{'historical_count':2261,'current_count':len(cp['failure_counters']),'records':rows,'author_ledger_import':'PENDING_FINAL_CURRENT_MANIFEST','counter_reset':False})
    resume=read(N/'continuation-cp561/RESUME.current.json')
    resume.update(schema='researchos.current-chat-resume.v140',at=now,checkpoint_revision=562,ownership_revision=347,tree=preserved['Main_tree'],failure_records_preserved=len(cp['failure_counters']),
        product_host_metadata_scope_ref=ref(out/'CLI-host-metadata-exact2-scope.json'),product_host_base_manifest_ref=ref(manifest),
        current_product_host_status={'source':'5ee2_FROZEN_EXACT14_PLUS_REGISTERED_EXACT2_REPAIR_PENDING','build02':'BUILT133_ROOT_AND_INDEPENDENT_CLOSURE_CHECKED','model_stream7':'REPORTED_ALL7_PASS_ON5ee2_NO_EXTERNAL_PROVIDER','native':'NOT_RUN_REAL_STATUS_SCOPE_BLOCKER','author_failures':'PENDING_IMPORT'},
        next_command='Repair only CLI metadata envelope exact2, verify actual compiled status fixture, freeze successor/build03 and independent review. Preserve5ee2/build02/exact7 successes and historical failures. Then Root native lifecycle and approved installer P1; full22parents42formal remain.')
    new(out/'RESUME.current.json',resume)
    cp.update(revision=562,expected_previous_revision=561,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
    cp['work_in_progress']['current_chat_continuation_cp562']=ref(out/'RESUME.current.json')
    cp['evidence_index'].append({'kind':'REAL_STATUS_ENVELOPE_BLOCKER_EXACT2_REPAIR_REGISTERED','ref':ref(out/'registration-evidence.json'),'formal_increment':0})
    ow.update(revision=347,expected_previous_revision=346,updated_at=now,updated_by='codex:/root')
    ow['special_paths']['Installed_delivery_development'].update(state='EXACT14_FROZEN_EXACT2_METADATA_REPAIR_ACTIVE_NO_NATIVE',metadata_scope_ref=ref(out/'CLI-host-metadata-exact2-scope.json'))
    prefix='# Current verified continuation CP562\n\nRead '+str(out/'RESUME.current.json')+' first, with CP560 CONTINUATION.md. Exact14 frozen5ee2/build02 and7model fixtures passed; realstatus scope bug needs new exact2 CLI repair before native. Main ecc28/originals/C57 preserved. Mixed2265 plus pending author ledger; formal0/42/all22open.\n\n'
    changes={cp_path:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),ow_path:(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode(),handoff:prefix.encode()+before[handoff]}
    for p in before:assert p.read_bytes()==before[p]
    for p,data in changes.items():
        (out/(p.name+'.before.raw')).write_bytes(before[p]);pending=p.with_name(p.name+'.cp562.pending')
        with pending.open('xb') as f:f.write(data)
        assert p.read_bytes()==before[p];os.replace(pending,p)
    assert state.read_bytes()==before[state]
    print(json.dumps({'checkpoint':562,'ownership':347,'mixed_records':len(cp['failure_counters']),'scope_sha256':ref(out/'CLI-host-metadata-exact2-scope.json')['sha256']}))

if __name__=='__main__':main()
