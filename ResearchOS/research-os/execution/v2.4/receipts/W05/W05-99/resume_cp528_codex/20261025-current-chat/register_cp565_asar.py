"""Preserve native attempt01 and scope a physical-filesystem repair."""
import datetime,json,os,subprocess
from pathlib import Path
from preserve_main_baseline import R,N,git,read,ref
from preserve_desktop_main_ecc28 import verify

def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    cp_path=R/'execution/v2.4/checkpoint.json';ow_path=R/'execution/v2.4/path_ownership.json';h=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';state=R/'execution/v2.4/step_state.json'
    old={p:p.read_bytes() for p in [cp_path,ow_path,h,state]};cp,ow=read(cp_path),read(ow_path)
    assert cp['revision']==564 and ow['revision']==349 and len(cp['failure_counters'])==2275
    preserved=verify();W=R/'.local/worktrees/desktop-installed-delivery-20261025'
    commit='448af57c208a3f29199d10e0fa9d9c7311776fad';tree='c4c9a19b5dce33a390620cb460e5b1c88d28cfc2'
    assert git(W,'rev-parse','HEAD').decode().strip()==commit and git(W,'rev-parse','HEAD^{tree}').decode().strip()==tree
    assert not git(W,'status','--porcelain=v1','--untracked-files=all')
    B=R/'execution/v2.4/receipts/W05/W05-99';E=B/'installed_delivery_codex/20261025-current-chat/continuation-20261028';I=B/'product_host_independent_20261028';A=B/'product_host_native_20261028'
    review=I/'native-attempt01-review/REVIEW-FINAL.json'
    assert ref(review)['sha256']=='9275badee147b64bd352e5491d2609a630e5933bd28d3ff84ddcc14f4fce491e'
    assert read(review)['native_accepted'] is False and read(review)['outer_exit']==1
    diagnosis=E/'asar-diagnosis-01/REPORT.json'
    assert ref(diagnosis)['sha256']=='eac642ec37f75f1cf61b8ae5c21da90b65f7497bc9bb73af4d4a8a0cf3aed419'
    prior=read(N/'continuation-cp564/Product-host-owned-native-scope.json');bundle=Path(prior['bundle_root'])
    marker=read(bundle/'installed-product.json')
    output_refs=[]
    for row in marker['files']:
        actual=ref(bundle/row['path']);assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'];output_refs.append(actual)
    assert read(A/'attempt-01-process-observation.json')['matched_processes']==[]
    out=N/'continuation-cp565';out.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    new(out/'postflight-preservation.json',{'at':now,'preserved':preserved,'candidate_commit':commit,'candidate_tree':tree,'bundle_refs':output_refs,'marker_ref':ref(bundle/'installed-product.json'),'attempt01_refs':[ref(p) for p in sorted(A.glob('attempt-01*/**/*')) if p.is_file()],'process_observation_ref':ref(A/'attempt-01-process-observation.json')})
    python=read(R/'execution/toolchains/locked.json')['tools']['python']['path']
    argv=[python,'-B',str(R.parent/'ResearchOS_Implementation_Package_v2.4/tools/task_packet.py'),'next','--state',str(state)]
    selected=subprocess.run(argv,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    (out/'task-packet.stdout.raw').write_bytes(selected.stdout);(out/'task-packet.stderr.raw').write_bytes(selected.stderr)
    packet=json.loads(selected.stdout.decode('utf-8-sig'));assert selected.returncode==0 and packet['state_source']=='VALIDATED_FILE'
    new(out/'selector.json',{'argv':argv,'exit':selected.returncode,'state_source':packet['state_source'],'stdout':ref(out/'task-packet.stdout.raw'),'stderr':ref(out/'task-packet.stderr.raw')})
    scope={'schema':'researchos.product-physical-filesystem-repair.v1','at':now,'owner':'codex:/root/product_host_resume_20261028','reviewer':'codex:/root/product_host_independent_20261028','worktree':str(W),'base_commit':commit,'base_tree':tree,
        'allowed_source_paths':['apps/desktop/main/main.js','tests/ui/desktop/product-host.test.mjs'],
        'source_before':[ref(W/p) for p in ['apps/desktop/main/main.js','tests/ui/desktop/product-host.test.mjs']],
        'unchanged_loader_ref':ref(W/'apps/desktop/main/lib/product-layout.js'),'diagnosis_ref':ref(diagnosis),'native_failure_review_ref':ref(review),
        'required_change':"Pass Electron require('original-fs') at the main.js loadProductLayout call. Preserve the loader and all checks, inventory entries and schema. No process.noAsar global change.",
        'artifact_root':str(W/'.local/asar-repair-cp565-20261028'),'receipt_root':str(E/'asar-repair-cp565'),
        'probe':{'allowed_once':True,'input_bundle':str(bundle),'marker_ref':ref(bundle/'installed-product.json'),'electron_ref':ref(bundle/'runtime/electron/electron.exe'),
            'entry':'New diagnostic entry written only under artifact_root; never require product main.js','expected':'Record node:fs versus original-fs physical ASAR stats. Complete unchanged build04 loader with default fs captures PRODUCT_PATH_TYPE; injected original-fs succeeds at same installation ID and133-file inventory.',
            'environment':'Fresh isolated LOCALAPPDATA APPDATA USERPROFILE TEMP TMP under artifact root; allowlist Windows system variables only; no inherited Node/product overrides',
            'launch':'Direct subprocess.Popen or node spawn windowsHide/CREATE_NO_WINDOW, shell false; immediate PID/raw/exit capture; no Playwright launch; no BrowserWindow/Core/provider/data binding; app.exit only own probe after proof',
            'failure':'Observe bounded time then leave exact child running if unresolved, no kill/retry; do not edit source if diagnosis not established'},
        'allowed_execution':['After probe establishes mechanism: exact2 source repair and relevant pureNode test group plus fresh main-entry VM with original-fs mock proving injected collaborator','Exact source-bound local commit with auto maintenance disabled','Fresh complete product layout build05 from clean commit in new output/receipt paths'],
        'do_not_repeat':['Unchanged GoProduct Python-layout ModelStream7 and unaffected CLI/regression suites'],
        'preserve':['All previous failures/builds/scopes/reviews and markers immutable','No writes to Main/C57/original data/credentials','Old attempt01 state remains unchanged'],
        'not_authorized':['Full product Electron/Core native replay','Installer/registry/PATH/upgrade/uninstall','Source paths beyond exact2 or weakening tests','Automatic retries or forced process termination'],
        'formal_increment':0}
    new(out/'ASAR-exact2-repair-scope.json',scope)
    records=[
        {'origin_key':'20261028|product-host-native|attempt01','status':'ACTUAL_PRODUCT_NATIVE_FAILED','attempts':1,'exit':1,'refs':[ref(A/'attempt-01/UNRESOLVED.json'),ref(A/'attempt-01-outer/exit.json'),ref(review)],'detail':'PRODUCT_PATH_TYPE before READY followed by45s launch timeout. Original result preserved; native not accepted.'},
        {'origin_key':'20261028|product-host-native|attempt01-framework-kill-review-gap','status':'CONTROL_BOUNDARY_REVIEW_FINDING_NOT_ANOTHER_PRODUCT_RUN','attempts':1,'ref':ref(review),'detail':'Playwright launch catch invokes kill; actual taskkill effect not captured. forced_termination=false cannot assert whole-chain nontermination. Subsequent driver avoids launchProcess.'},
        {'origin_key':'20261028|root|context-read-backend-unavailable','status':'TOOL_DIAGNOSTIC_NOT_PRODUCT_FAILURE','attempts':3,'detail':'Two private checkpoint reads and one prior-turn read returned backend request failed; local bounded recovery used.'},
        {'origin_key':'20261028|root|product-layout-wrong-locator','status':'READONLY_LOCATOR_DIAGNOSTIC_NOT_PRODUCT_FAILURE','attempts':1,'detail':'Get-Content apps/desktop/product-layout.js path not found; actual main/lib path read afterward; combined command outer0 retained as such.'}]
    existing={r.get('origin_key') for r in cp['failure_counters']}
    for r in records:assert r['origin_key'] not in existing;r['counter_reset']=False
    cp['failure_counters'].extend(records)
    new(out/'new-records-ledger.json',{'historical_count':2275,'current_count':len(cp['failure_counters']),'records':records})
    resume=read(N/'continuation-cp564/RESUME.current.json')
    resume.update(schema='researchos.current-chat-resume.v143',at=now,checkpoint_revision=565,ownership_revision=350,failure_records_preserved=len(cp['failure_counters']),product_host_asar_scope_ref=ref(out/'ASAR-exact2-repair-scope.json'),product_host_native_failure_review_ref=ref(review),
        active_source_cards=[{'owner':scope['owner'],'scope_ref':ref(out/'ASAR-exact2-repair-scope.json')}],
        next_command='Establish ASAR mechanism with one isolated Electron filesystem probe, then exact2 main/test fix and build05; driver-v2 preparation uses direct spawn/CDP and native WM_CLOSE. Independently review both before a new native scope. Then installer P1. Full22parents42formal remain required.')
    resume['current_product_host_status'].update(native='ATTEMPT01_FAILED_PRODUCT_PATH_TYPE_FRAMEWORK_KILL_PATH_UNOBSERVED_OS_EFFECT',source_build='448af_BUILD04_HISTORICAL_LIMITED_ONLY_ASAR_REPAIR_ACTIVE',driver_v2='PREPARATION_ONLY_NOT_NATIVE_AUTHORIZATION')
    new(out/'RESUME.current.json',resume)
    cp.update(revision=565,expected_previous_revision=564,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
    cp['work_in_progress']['current_chat_continuation_cp565']=ref(out/'RESUME.current.json')
    cp['evidence_index'].append({'kind':'NATIVE_FAILURE_PRESERVED_PHYSICAL_FS_EXACT2_REPAIR','ref':ref(out/'ASAR-exact2-repair-scope.json'),'failure_review':ref(review),'postflight':ref(out/'postflight-preservation.json'),'formal_increment':0})
    ow.update(revision=350,expected_previous_revision=349,updated_at=now,updated_by='codex:/root')
    ow['special_paths']['Installed_delivery_development'].update(state='ASAR_EXACT2_REPAIR_AFTER_BOUNDED_PROBE',asar_scope_ref=ref(out/'ASAR-exact2-repair-scope.json'))
    ow['special_paths']['Product_host_owned_native_20261028'].update(state='ATTEMPT01_FAILED_NO_AUTORETRY',failure_review=ref(review),process_observation=ref(A/'attempt-01-process-observation.json'))
    ow['special_paths']['Product_host_native_driver_v2']={'owner':'codex:/root/product_native_driver_v2','state':'PREPARATION_ONLY','write_root':str(A/'driver-v2'),'product_launch_authorized':False}
    prefix='# Current verified continuation CP565\n\nRead '+str(out/'RESUME.current.json')+' first. Native01 failed PRODUCT_PATH_TYPE; PID absent, termination mechanism unknown, frameworkkill review gap retained. Exact2 ASAR repair after ownedprobe and driver-v2 preparation active. Main/C57/originals unchanged; formal0/42/all22open.\n\n'
    changes={cp_path:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),ow_path:(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode(),h:prefix.encode()+old[h]}
    for p in old:assert p.read_bytes()==old[p]
    for p,data in changes.items():
        (out/(p.name+'.before.raw')).write_bytes(old[p]);pending=p.with_name(p.name+'.cp565.pending')
        with pending.open('xb') as f:f.write(data)
        assert p.read_bytes()==old[p];os.replace(pending,p)
    assert state.read_bytes()==old[state]
    print(json.dumps({'checkpoint':565,'ownership':350,'records':len(cp['failure_counters']),'scope':ref(out/'ASAR-exact2-repair-scope.json'),'selector':packet['state_source']}))

if __name__=='__main__':main()
