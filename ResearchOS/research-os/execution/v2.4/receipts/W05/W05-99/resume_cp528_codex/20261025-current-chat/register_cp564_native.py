"""Adopt independent source/build evidence and register one fresh native trial."""
import datetime,json,os
from pathlib import Path
from preserve_main_baseline import R,N,git,read,ref
from preserve_desktop_main_ecc28 import verify

def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    cp_path=R/'execution/v2.4/checkpoint.json';ow_path=R/'execution/v2.4/path_ownership.json';h=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';state=R/'execution/v2.4/step_state.json'
    old={p:p.read_bytes() for p in [cp_path,ow_path,h,state]};cp,ow=read(cp_path),read(ow_path)
    assert cp['revision']==563 and ow['revision']==348 and len(cp['failure_counters'])==2266
    preserved=verify();W=R/'.local/worktrees/desktop-installed-delivery-20261025'
    commit='448af57c208a3f29199d10e0fa9d9c7311776fad';tree='c4c9a19b5dce33a390620cb460e5b1c88d28cfc2'
    assert git(W,'rev-parse','HEAD').decode().strip()==commit and git(W,'rev-parse','HEAD^{tree}').decode().strip()==tree
    assert not git(W,'status','--porcelain=v1','--untracked-files=all')
    B=R/'execution/v2.4/receipts/W05/W05-99';E=B/'installed_delivery_codex/20261025-current-chat/continuation-20261028';I=B/'product_host_independent_20261028';A=B/'product_host_native_20261028'
    review=I/'final-448af-review/FINAL-REVIEW.json'
    assert ref(review)['sha256']=='be8584e90b2f49057d5253571701bf9ba502cffb6036505cf71a1ebd84a8fac2'
    reviewed=read(review)
    assert reviewed['status']=='LIMITED_SOURCE_BUILD_FIXTURE_ACCEPTED' and reviewed['source_build_accepted'] is True
    assert reviewed['accepted_commit']==commit and reviewed['accepted_tree']==tree and reviewed['formal_increment']==0
    verified=[]
    for row in reviewed['evidence_refs']:
        z=ref(Path(row['path']));assert z['sha256']==row['sha256'] and z['bytes']==row['bytes'];verified.append(z)
    proof=read(N/'continuation-cp563/product-host-final-build-root-verification.json')
    for row in proof['source_refs']+proof['output_refs']:
        z=ref(Path(row['path']));assert z['sha256']==row['sha256'] and z['bytes']==row['bytes']
    bundle=Path(reviewed['accepted_build']);marker_path=bundle/'installed-product.json';marker=read(marker_path)
    assert ref(marker_path)['sha256']==reviewed['accepted_marker_sha256'] and marker['installation_id']==reviewed['accepted_installation_id']
    preparation=read(A/'PREPARATION-v2.json')
    for row in preparation['sources']:
        z=ref(Path(row['path']));assert z['sha256']==row['sha256'] and z['bytes']==row['bytes']
    assert ref(A/'run-owned.py')['sha256']=='0c4d98665568d49ae1a348b593817766b5b4c3079c1dc4ebb1a60d21949f5edb'
    assert ref(I/'native-wrapper-preview-01/REVIEW.json')['sha256']=='6d9ecb97b00ef677a2665d7ab1f1ae3d569384c53016e05a8613417214f86bc6'
    out=N/'continuation-cp564';out.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    node=bundle/'apps/desktop/resources/control/runtime/node.exe'
    powershell=Path('C:/Users/yqyyds/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.EXE').resolve()
    playwright=Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package')
    assert read(playwright/'package.json')['version']=='1.58.0'
    tool_refs=[]
    for p in sorted(playwright.rglob('*')):
        assert not p.is_symlink() and not (getattr(p.stat(),'st_file_attributes',0)&0x400)
        if p.is_file():tool_refs.append(ref(p))
    tools=[ref(node),ref(powershell)]+tool_refs
    new(out/'native-tool-closure.json',{'node':ref(node),'powershell':ref(powershell),'playwright_root':str(playwright),'files':tool_refs})
    new_state=W/'.local/product-host-native-cp564-20261028';outer_tmp=W/'.local/product-host-native-toolenv-cp564-20261028'
    receipts=A/'attempt-01';outer=A/'attempt-01-outer'
    assert all(not p.exists() for p in [new_state,outer_tmp,receipts,outer])
    bound=[ref(marker_path),ref(review),ref(A/'PREPARATION-v2.json'),ref(A/'run-owned.py'),ref(I/'native-driver-preview-03/REVIEW.json'),ref(I/'native-wrapper-preview-01/REVIEW.json')]+preparation['sources']+tools
    scope={'schema':'researchos.owned-product-host-native-scope.v1','at':now,'owner':'codex:/root','reviewer':'codex:/root/product_host_independent_20261028',
        'mode':'OWNED_PRODUCT_HOST_LIFECYCLE_NO_PROVIDER','native_launch_authorized':True,'independent_source_build_accepted':True,
        'candidate_commit':commit,'candidate_tree':tree,'worktree':str(W),'bundle_root':str(bundle),'installation_id':marker['installation_id'],
        'state_root':str(new_state),'receipts_root':str(receipts),'outer_receipts_root':str(outer),'outer_temporary_root':str(outer_tmp),
        'node_path':str(node),'powershell_path':str(powershell),'playwright_path':str(playwright),'bound_files':bound,
        'accepted_review_ref':ref(review),'current_author_manifest_ref':ref(E/'marker-fixture-cp563/FINAL-MANIFEST.json'),
        'allowed_actions':['Run bound product CLI version/help/doctor without host startup on fresh isolated profile',
            'Start bound Electron/Core in new isolated LOCALAPPDATA APPDATA USERPROFILE TEMP; duplicate opens and simultaneous CLI status while same host alive',
            'CLI init only the exact newly created owned Unicode workspace; native folder confirmation only after expected PID/creation/image verification',
            'Save offline loopback model configuration with no credential; create/select/open one real project session using existing Desktop API',
            'CLI reads exact project/session/workspace/model identity; safe window close and observe exact parent/Core exits',
            'GUI then CLI cold reopen same nonempty data with new host identity; repeat exact session reads and final owned safe window close',
            'Capture screenshots, typed responses, stdout/stderr, PIDs, witness identity and all known exit/unresolved facts'],
        'network':'Only owned127.0.0.1 counting listener; model/provider/probe/session.send forbidden; expected provider_connections=0',
        'not_authorized':['Any original user DB/config/credential/data or previous app process action','Force kill/adopt/clear discovery/break data lock','Model calls, work execution, permissions or paid provider','Installer/registry/PATH/shortcut/upgrade/uninstall','Source edits or Main merge','C57 recovery or original ACL operations','Automatic retry or repeat shutdown after unknown result'],
        'failure_policy':'On failure preserve known handles and owned state, write unresolved facts, inspect same actual processes; no automatic restart or forced cleanup. Independent review follows actual outputs.',
        'evidence_scope':'Owned native lifecycle only; no busy/provider/clean-Windows/installer/formal acceptance implied','formal_increment':0}
    new(out/'Product-host-owned-native-scope.json',scope)
    new(out/'source-build-adoption.json',{'at':now,'status':'ROOT_ADOPTED_LIMITED_SOURCE_BUILD_FIXTURE','review_ref':ref(review),'verified_review_refs':verified,'preserved':preserved,'commit':commit,'tree':tree,'formal_increment':0})
    existing={x.get('origin_key') for x in cp['failure_counters']};rows=[]
    for row in read(E/'BASE-5ee2-MANIFEST.json')['diagnostics']:
        if row['origin_key'] not in existing:
            rows.append({**row,'status':'AUTHOR_DIAGNOSTIC_IMPORTED_ORIGINAL_PRESERVED','attempts':1,'counter_reset':False})
    extra=[{'origin_key':'CP558:GO_RISK_03:W18_CURRENT:2','status':'AUTHOR_FAILED_COMPARISON_PRESERVED','attempts':1,'refs':[ref(E/'test-go-risk-03'/n) for n in ['exit.json','stdout.raw','stderr.raw']]},
        {'origin_key':'20261028|independent|temporary-cleanup-policy-rejections','status':'POLICY_REJECTED_NO_DELETION','attempts':2,'ref':ref(I/'focused-9361-review/TEMP-CLEANUP-DETAIL.json'),'detail':'Blocked by policy. Narrowed second attempt also rejected before Root stop arrived; no further retry.'},
        {'origin_key':'20261028|independent|whole-record-timestamp-comparison-diagnostic','status':'REVIEWER_DIAGNOSTIC_NOT_PRODUCT_FAILURE','attempts':1,'ref':ref(I/'frozen-5ee2c694-review/REVIEWER-COMMAND-DIAGNOSTIC.json')}]
    for row in extra:
        if row['origin_key'] not in existing:row['counter_reset']=False;rows.append(row)
    assert len({x['origin_key'] for x in rows})==len(rows)
    cp['failure_counters'].extend(rows)
    new(out/'imported-records-ledger.json',{'historical_count':2266,'current_count':len(cp['failure_counters']),'records':rows,'counter_reset':False})
    resume=read(N/'continuation-cp563/RESUME.current.json')
    resume.update(schema='researchos.current-chat-resume.v142',at=now,checkpoint_revision=564,ownership_revision=349,failure_records_preserved=len(cp['failure_counters']),active_source_cards=[],
        product_host_current_source=commit,product_host_current_tree=tree,product_host_source_build_adoption_ref=ref(out/'source-build-adoption.json'),product_host_native_scope_ref=ref(out/'Product-host-owned-native-scope.json'),
        current_product_host_status={'source_build':'INDEPENDENTLY_ACCEPTED_LIMITED_448af_BUILD04','native':'ROOT_SCOPE_REGISTERED_NOT_YET_EXECUTED','fixture_history':'PRESERVED_WITH_EXPLICIT_VERSION_REUSE','installer':'P1_DESIGN_ADOPTED_NOT_IMPLEMENTED','pagination_HTTP403':'OPEN_UNRELATED_TO_METADATA_FIX'},
        next_command='Run the registered single owned native lifecycle through run-owned.py, preserve real results and handles, independent review. Continue approved installer P1 after source/build qualification; no original data/C57 actions and full22parents42formal remain open.')
    new(out/'RESUME.current.json',resume)
    cp.update(revision=564,expected_previous_revision=563,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
    cp['work_in_progress']['current_chat_continuation_cp564']=ref(out/'RESUME.current.json')
    cp['evidence_index'].append({'kind':'LIMITED_SOURCE_BUILD_ADOPTED_OWNED_NATIVE_SCOPE_REGISTERED','ref':ref(out/'source-build-adoption.json'),'native_scope_ref':ref(out/'Product-host-owned-native-scope.json'),'formal_increment':0})
    ow.update(revision=349,expected_previous_revision=348,updated_at=now,updated_by='codex:/root')
    ow['special_paths']['Installed_delivery_development'].update(state='SOURCE_FROZEN_ACCEPTED_NO_FURTHER_SOURCE_WRITES',accepted_commit=commit,independent_review_ref=ref(review))
    ow['special_paths']['Product_host_owned_native_20261028']={'owner':'codex:/root','state':'REGISTERED_NOT_YET_EXECUTED','scope_ref':ref(out/'Product-host-owned-native-scope.json')}
    prefix='# Current verified continuation CP564\n\nRead '+str(out/'RESUME.current.json')+' first. Source448af/build04 independently accepted limited; Root owned native scope registered, no run yet. Original Main/C57/data preserved. Mixed'+str(len(cp['failure_counters']))+'; formal0/42/all22open. Denied cleanup retained; no retry.\n\n'
    changes={cp_path:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),ow_path:(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode(),h:prefix.encode()+old[h]}
    for p in old:assert p.read_bytes()==old[p]
    for p,data in changes.items():
        (out/(p.name+'.before.raw')).write_bytes(old[p]);pending=p.with_name(p.name+'.cp564.pending')
        with pending.open('xb') as f:f.write(data)
        assert p.read_bytes()==old[p];os.replace(pending,p)
    assert state.read_bytes()==old[state]
    print(json.dumps({'checkpoint':564,'ownership':349,'mixed_records':len(cp['failure_counters']),'scope_sha256':ref(out/'Product-host-owned-native-scope.json')['sha256'],'bound_files':len(bound)}))

if __name__=='__main__':main()
