"""Bind independently reviewed ASAR repair and attach-only native controller."""
import datetime,json,os,sys
from pathlib import Path
from preserve_main_baseline import R,N,git,read,ref
from preserve_desktop_main_ecc28 import verify

def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def recheck(row):
    actual=ref(Path(row['path']));assert actual['sha256']==row['sha256'],row['path']
    if 'bytes' in row:assert actual['bytes']==row['bytes'],row['path']
    return actual

def main():
    source_review=Path(sys.argv[1]).resolve();driver_review=Path(sys.argv[2]).resolve()
    cp_path=R/'execution/v2.4/checkpoint.json';ow_path=R/'execution/v2.4/path_ownership.json';h=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';state=R/'execution/v2.4/step_state.json'
    old={p:p.read_bytes() for p in [cp_path,ow_path,h,state]};cp,ow=read(cp_path),read(ow_path)
    assert cp['revision']==565 and ow['revision']==350 and len(cp['failure_counters'])==2279
    preserved=verify();W=R/'.local/worktrees/desktop-installed-delivery-20261025'
    commit='5c4c94022bd92da68ef544f2779527bfe065c428';tree='133c6fdee17e1ad2f7758689c55c1486e778cec0'
    assert git(W,'rev-parse','HEAD').decode().strip()==commit and git(W,'rev-parse','HEAD^{tree}').decode().strip()==tree
    assert not git(W,'status','--porcelain=v1','--untracked-files=all')
    B=R/'execution/v2.4/receipts/W05/W05-99';E=B/'installed_delivery_codex/20261025-current-chat/continuation-20261028/asar-repair-cp565';I=B/'product_host_independent_20261028';A=B/'product_host_native_20261028';D=A/'driver-v2'
    reviewed=read(source_review);control=read(driver_review)
    assert reviewed['source_build_accepted'] is True and reviewed['formal_increment']==0
    assert reviewed['accepted_commit']==commit and reviewed['accepted_tree']==tree
    assert control['controller_source_accepted'] is True and control['actual_native_runs']==0 and control['formal_increment']==0
    reviewed_refs=[recheck(r) for r in reviewed['evidence_refs']]
    driver_refs=[recheck(r) for r in control['evidence_refs']+control['fixed_driver_files']]
    proof=read(N/'continuation-cp565/product-host-build05-root-verification.json')
    for row in proof['source_refs']+proof['output_refs']:recheck(row)
    bundle=Path(reviewed['accepted_build']);marker=read(bundle/'installed-product.json')
    assert ref(bundle/'installed-product.json')['sha256']==reviewed['accepted_marker_sha256']
    assert marker['installation_id']==reviewed['accepted_installation_id']
    preparation=read(D/'PREPARATION.json')
    for row in preparation['sources']+preparation['new_driver']:recheck(row)
    closure=read(N/'continuation-cp564/native-tool-closure.json')
    for row in [closure['node'],closure['powershell']]+closure['files']:recheck(row)
    node=bundle/'apps/desktop/resources/control/runtime/node.exe'
    assert ref(node)['sha256']==closure['node']['sha256']
    out=N/'continuation-cp566';out.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    fresh=W/'.local/product-host-native-cp566-20261028';tmp=W/'.local/product-host-native-toolenv-cp566-20261028';receipts=A/'attempt-02';outer=A/'attempt-02-outer'
    assert all(not p.exists() for p in [fresh,tmp,receipts,outer])
    bound=[ref(bundle/'installed-product.json'),ref(source_review),ref(driver_review),ref(D/'PREPARATION.json')]+preparation['new_driver']+[ref(node),closure['powershell']]+closure['files']
    scope=read(N/'continuation-cp564/Product-host-owned-native-scope.json')
    scope.update(schema='researchos.owned-product-host-native-scope.v2',at=now,candidate_commit=commit,candidate_tree=tree,bundle_root=str(bundle),installation_id=marker['installation_id'],state_root=str(fresh),receipts_root=str(receipts),outer_receipts_root=str(outer),outer_temporary_root=str(tmp),node_path=str(node),bound_files=bound,
        accepted_review_ref=ref(source_review),controller_review_ref=ref(driver_review),current_author_manifest_ref=ref(E/'FINAL-MANIFEST.json'),driver_version='DIRECT_SPAWN_ATTACH_ONLY_CDP_V2',
        prior_failed_attempt_ref=ref(A/'attempt-01/UNRESOLVED.json'),prior_process_observation_ref=ref(A/'attempt-01-process-observation.json'),
        changed_inputs='ASAR physical-fs injection at main5c4c940 and freshbuild05; replacement controller directly spawns and only attaches CDP; no automatic retry of448af/oldcontroller.',
        failure_policy='Capture spawn PID and raw output immediately. Observation timeout leaves process and data intact; detach CDP only and unref child. No kill, repeated shutdown, automatic restart or data-lock edits. Root reconciles exact handles.')
    new(out/'Product-host-owned-native-v2-scope.json',scope)
    new(out/'source-driver-adoption.json',{'at':now,'source_review_ref':ref(source_review),'controller_review_ref':ref(driver_review),'verified_source_review_refs':reviewed_refs,'verified_driver_review_refs':driver_refs,'preserved':preserved,'commit':commit,'tree':tree,'product_native_acceptance':False,'formal_increment':0})
    records=[{'origin_key':'20261028|root|overlapping-select-property-locator','status':'READONLY_TOOL_DIAGNOSTIC','attempts':1,'detail':'Select-Object overlappingwildcards emitted duplicate-property diagnostic; combined read exit0, no mutation'},
        {'origin_key':'20261028|root|asar-probe-result-wrong-filename','status':'READONLY_LOCATOR_DIAGNOSTIC','attempts':1,'exit':1,'detail':'Optional probe-result.json was not produced; raw evidence is probe-stdout.raw. Combined command exit1 retained, no product test failure.'}]
    existing={r.get('origin_key') for r in cp['failure_counters']}
    for row in records:assert row['origin_key'] not in existing;row['counter_reset']=False
    cp['failure_counters'].extend(records)
    new(out/'new-records-ledger.json',{'historical_count':2279,'current_count':len(cp['failure_counters']),'records':records})
    resume=read(N/'continuation-cp565/RESUME.current.json')
    resume.update(schema='researchos.current-chat-resume.v144',at=now,checkpoint_revision=566,ownership_revision=351,failure_records_preserved=len(cp['failure_counters']),active_source_cards=[],product_host_current_source=commit,product_host_current_tree=tree,product_host_native_scope_ref=ref(out/'Product-host-owned-native-v2-scope.json'),product_host_source_driver_adoption_ref=ref(out/'source-driver-adoption.json'),
        next_command='Run exactly once v2/run-owned.py with CP566 Product-host-owned-native-v2-scope.json; observe actual handles/results, independent native review. Installer P1 design independently reviewed in parallel; full22parents42formal not complete.')
    resume['current_product_host_status'].update(source_build='5c4c940_BUILD05_INDEPENDENTLY_ACCEPTED_LIMITED',native='ATTEMPT02_SCOPE_REGISTERED_NOT_YET_EXECUTED',driver_v2='INDEPENDENT_SOURCE_ACCEPTED_DIRECT_SPAWN_CDP')
    new(out/'RESUME.current.json',resume)
    cp.update(revision=566,expected_previous_revision=565,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
    cp['work_in_progress']['current_chat_continuation_cp566']=ref(out/'RESUME.current.json')
    cp['evidence_index'].append({'kind':'ASAR_REPAIR_AND_ATTACH_CONTROLLER_ADOPTED_NATIVE_V2_SCOPE_REGISTERED','ref':ref(out/'source-driver-adoption.json'),'scope_ref':ref(out/'Product-host-owned-native-v2-scope.json'),'formal_increment':0})
    ow.update(revision=351,expected_previous_revision=350,updated_at=now,updated_by='codex:/root')
    ow['special_paths']['Installed_delivery_development'].update(state='SOURCE_FROZEN_ACCEPTED_NO_FURTHER_SOURCE_WRITES',accepted_commit=commit,independent_review_ref=ref(source_review))
    ow['special_paths']['Product_host_owned_native_20261028'].update(state='ATTEMPT02_REGISTERED_NOT_YET_EXECUTED',scope_ref=ref(out/'Product-host-owned-native-v2-scope.json'))
    ow['special_paths']['Product_host_native_driver_v2'].update(state='FROZEN_SOURCE_ACCEPTED',independent_review_ref=ref(driver_review))
    prefix='# Current verified continuation CP566\n\nRead '+str(out/'RESUME.current.json')+' first. ASAR5c4c940/build05 and directspawn/CDP v2 accepted limited; attempt02 newly scoped, not run. Oldfailure/terminationuncertainty retained. Main/C57/originals unchanged; formal0/42/all22open.\n\n'
    changes={cp_path:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),ow_path:(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode(),h:prefix.encode()+old[h]}
    for p in old:assert p.read_bytes()==old[p]
    for p,data in changes.items():
        (out/(p.name+'.before.raw')).write_bytes(old[p]);pending=p.with_name(p.name+'.cp566.pending')
        with pending.open('xb') as f:f.write(data)
        assert p.read_bytes()==old[p];os.replace(pending,p)
    assert state.read_bytes()==old[state]
    print(json.dumps({'checkpoint':566,'ownership':351,'records':len(cp['failure_counters']),'scope':ref(out/'Product-host-owned-native-v2-scope.json'),'bound_files':len(bound)}))

if __name__=='__main__':main()
