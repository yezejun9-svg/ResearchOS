"""Adopt fixed static installer/source reviews; seal finite disposable native A/B."""
import datetime,json,os
from pathlib import Path
from preserve_main_baseline import R,N,git,read,ref
from preserve_desktop_main_ecc28 import verify
def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    paths=[R/'execution/v2.4/checkpoint.json',R/'execution/v2.4/path_ownership.json',R/'execution/v2.4/HANDOFF_RESUME_PACK.md',R/'execution/v2.4/step_state.json'];old={p:p.read_bytes() for p in paths};cp,ow=read(paths[0]),read(paths[1])
    assert cp['revision']==571 and ow['revision']==356 and len(cp['failure_counters'])==2299
    preserved=verify();B=R/'execution/v2.4/receipts/W05/W05-99';E=B/'product_host_native_20261028/native-init-diagnosis-02/environment-probe';P=E/'preparation02';I=B/'product_host_independent_20261028'
    er=I/'environment-probe-source-review/preparation02-5fcc8477/REVIEW.json';ir=B/'installer_p1a_independent_review_20261028/revision02/REVIEW.json'
    assert ref(er)['sha256']=='bdf7ed6b7c3a68c6fa2d69dad2ef4ae6c5e46b6815bbf7a8d2a565a882efa949'
    assert ref(ir)['sha256']=='5a2a494e6603e8f38597e9f9330cc99d1b930df31a3a1336b236dcea4d7c2604' and read(ir)['status']=='ACCEPTED_SOURCE_STATIC_P1A_ONLY'
    prep=read(P/'PREPARATION.json');assert ref(P/'PREPARATION.json')['sha256']=='a93ee48dc114d63f9b54fd99d4b6b167c31edad87343db6a33101d30ec0ff567'
    for expected in prep['files'].values():assert ref(Path(expected['path']))==expected
    W=R/'.local/worktrees/installer-p1a-20261028';author=B/'installer_p1a_source_codex/20261028/revision02/FINAL-MANIFEST.json';assert ref(author)['sha256']=='3d2a94993228095674484df4590054e30c0b16f6978aaf31ca0a5693ab841ff4';a=read(author)
    assert git(W,'rev-parse','HEAD').decode().strip()==a['commit'] and git(W,'rev-parse','HEAD^{tree}').decode().strip()==a['tree'] and not git(W,'status','--porcelain=v1','--untracked-files=all')
    source_refs=[]
    for row in a['changed_source']+a['unchanged_source']:
        actual=ref(W/row['path']);assert actual['sha256']==row['sha256'];source_refs.append(actual)
    artifact=Path(a['artifact']);assert ref(artifact/'payload-manifest.json')['sha256']==a['payload_manifest_sha256'];assert ref(artifact/'finalizer.exe')['sha256']==a['finalizer_sha256']
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();out=N/'continuation-cp572';out.mkdir()
    scope=read(P/'RUN-SCOPE-TEMPLATE.json');product=R/'.local/worktrees/desktop-installed-delivery-20261025'
    scope.update(at=now,owner='codex:/root',state_root=str(product/'.local/native-folder-environment-cp572-AB01'),receipts_root=str(E/'execution-cp572-AB01'),native_execution_authorized=True,source_review_ref=ref(er),preparation_scope_ref=ref(N/'continuation-cp571/Native-folder-environment-preparation02-scope.json'),not_authorized=['No product Electron/Core/CLI launch','No model/provider/user credentials','No automatic retry, extra case A2, process kill or old data reuse','No source/installer/registry/original user data writes'],interpretation='A/B fixed order and shared isolated profile provide diagnostic evidence only. Each case invokes unchanged chooser once. Own visible dialog is cancelled via exact identity normal IDCANCEL; returned null without an observed dialog is not a successful cancellation. On unresolved helper keep controller alive for Root reconciliation.')
    assert not Path(scope['state_root']).exists() and not Path(scope['receipts_root']).exists()
    python=Path(read(R/'execution/toolchains/locked.json')['tools']['python']['path']);assert ref(python)['sha256']=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
    scope['python_ref']=ref(python);scope['invocation']=[str(python),'-B',str(P/'controller.py'),str(out/'Native-folder-finite-AB-scope.json')];scope['python_environment']='Remove PYTHONOPTIMIZE, no -O; helper receives explicit reviewed environment only.'
    new(out/'Native-folder-finite-AB-scope.json',scope);new(out/'preservation.json',preserved)
    adoption={'at':now,'state':'ACCEPTED_SOURCE_STATIC_P1A_ONLY','commit':a['commit'],'tree':a['tree'],'source_refs':source_refs,'author_ref':ref(author),'independent_review_ref':ref(ir),'payload_ref':ref(artifact/'payload-manifest.json'),'finalizer_ref':ref(artifact/'finalizer.exe'),'formal_increment':0,'not_claimed':['Main integration','Actual install/upgrade/uninstall','Full native lifecycle','Parent or formal acceptance']};new(out/'Installer-P1a-static-adoption.json',adoption)
    resume=read(N/'continuation-cp571/RESUME.current.json');resume.update(schema='researchos.current-chat-resume.v150',at=now,checkpoint_revision=572,ownership_revision=357,installer_static_adoption_ref=ref(out/'Installer-P1a-static-adoption.json'),environment_probe_run_scope_ref=ref(out/'Native-folder-finite-AB-scope.json'),next_command='Execute exactly one accepted finite A/B helper controller under CP572 scope (not yet started). Record direct exec handle immediately and keep it alive on unresolved helper. Obtain independent actual-result review; identify minimal source repair from evidence. Static installer accepted/frozen, no actual installation or Main merge yet. Full goal remains unfinished.')
    new(out/'RESUME.current.json',resume);cp.update(revision=572,expected_previous_revision=571,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress']['current_chat_continuation_cp572']=ref(out/'RESUME.current.json');cp['evidence_index'].extend([{'kind':'INSTALLER_P1A_FIXED_STATIC_SOURCE_ADOPTION','ref':ref(out/'Installer-P1a-static-adoption.json'),'formal_increment':0},{'kind':'FINITE_NATIVE_FOLDER_ENVIRONMENT_AB_SCOPE','ref':ref(out/'Native-folder-finite-AB-scope.json'),'formal_increment':0}])
    ow.update(revision=357,expected_previous_revision=356,updated_at=now,updated_by='codex:/root');ow['special_paths']['Installer_P1a_source'].update(state='SOURCE_STATIC_ACCEPTED_FROZEN',adoption_ref=ref(out/'Installer-P1a-static-adoption.json'));ow['special_paths']['Native_folder_environment_probe'].update(owner='codex:/root',state='FINITE_AB_EXECUTION_SCOPED_NOT_STARTED',native_authorized=True,scope_ref=ref(out/'Native-folder-finite-AB-scope.json'))
    prefix='# Current verified continuation CP572\n\nRead '+str(out/'RESUME.current.json')+' first; compact details in prior CP571/CONTINUATION.md. Installer P1a source/static accepted frozen. Exact two-case disposable helper A/B scoped but NOT STARTED. Full product/installer/formal acceptance remains open.\n\n'
    changes={paths[0]:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),paths[1]:(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode(),paths[2]:prefix.encode()+old[paths[2]]}
    for p in paths:assert p.read_bytes()==old[p]
    for p,data in changes.items():
        (out/(p.name+'.before.raw')).write_bytes(old[p]);temp=p.with_name(p.name+'.cp572.pending')
        with temp.open('xb') as f:f.write(data)
        assert p.read_bytes()==old[p];os.replace(temp,p)
    assert paths[3].read_bytes()==old[paths[3]]
    print(json.dumps({'checkpoint':572,'ownership':357,'records':len(cp['failure_counters']),'scope':ref(out/'Native-folder-finite-AB-scope.json'),'installer_adoption':ref(out/'Installer-P1a-static-adoption.json')}))
if __name__=='__main__':main()
