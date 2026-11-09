"""Authorize isolated installer media/pure-model construction; no actual installation."""
import datetime,json,os
from pathlib import Path
from preserve_main_baseline import R,N,git,read,ref
from preserve_desktop_main_ecc28 import verify

def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    paths=[R/'execution/v2.4/checkpoint.json',R/'execution/v2.4/path_ownership.json',R/'execution/v2.4/HANDOFF_RESUME_PACK.md',R/'execution/v2.4/step_state.json']
    old={p:p.read_bytes() for p in paths};cp,ow=read(paths[0]),read(paths[1])
    assert cp['revision']==573 and ow['revision']==358 and len(cp['failure_counters'])==2304
    preserved=verify();B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'.local/worktrees/installer-p1b-20261028'
    base='69f91b72e919c01a2297da31109e59bf7a54ccbf';tree='f7cbb41dfc4cf5a5ef730161bc58afc1ec44c599'
    assert git(W,'rev-parse','HEAD').decode().strip()==base and git(W,'rev-parse','HEAD^{tree}').decode().strip()==tree
    assert not git(W,'status','--porcelain=v1','--untracked-files=all')
    reco=B/'installer_p1a_independent_review_20261028/next-stage-assessment/RECOMMENDATION.json'
    assert ref(reco)['sha256']=='d5ae89cd3fa5abdbeba6edef1b1e54f45507e06fc6aa33091f657fbde2fb81d7'
    recommendation=read(reco);source_paths=recommendation['immediate_implementation_scope']['source_paths']
    assert len(source_paths)==11 and all(not(W/p).exists() for p in source_paths)
    tool=N/'Installer-P1b-NSIS-inputs.json';assert ref(tool)['sha256']=='859b087937adb1ff294152e0f65244b4cc9b99cd985b0a5875fdfee5da58327a'
    tool_inputs=read(tool)
    for row in tool_inputs['files']:
        actual=ref(Path(tool_inputs['root'])/row['path']);assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes']
    a=read(B/'installer_p1a_source_codex/20261028/revision02/FINAL-MANIFEST.json');artifact=Path(a['artifact'])
    assert ref(artifact/'payload-manifest.json')['sha256']==a['payload_manifest_sha256']
    assert ref(artifact/'finalizer.exe')['sha256']==a['finalizer_sha256']
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();out=N/'continuation-cp574';out.mkdir()
    scope={'schema':'researchos.installer-p1b-source-build-scope.v1','at':now,'owner':'codex:/root/installer_p1b_builder','reviewer':'codex:/root/installer_p1a_independent_review',
      'worktree':str(W),'branch':'codex/installer-p1b-media-20261028','baseline_commit':base,'baseline_tree':tree,'source_paths':source_paths,
      'receipts_root':str(B/'installer_p1b_source_codex/20261028'),'artifact_root':str(W/'.local/installer-p1b'),
      'assessment_ref':ref(reco),'accepted_p1a_adoption_ref':ref(N/'continuation-cp572/Installer-P1a-static-adoption.json'),
      'payload_artifact_root':str(artifact),'payload_manifest_ref':ref(artifact/'payload-manifest.json'),'finalizer_ref':ref(artifact/'finalizer.exe'),
      'nsis_tool_inputs_ref':ref(tool),'toolchain_lock_ref':ref(R/'execution/toolchains/locked.json'),
      'fixed_install_layout':{'program':'%LOCALAPPDATA%/Programs/ResearchOS','business':'%LOCALAPPDATA%/ResearchOS','management':'%LOCALAPPDATA%/ResearchOS-Install'},
      'source_build_authorized':True,'native_product_or_installer_execution_authorized':False,'formal_increment':0,
      'requirements':[
        'Implement exact11 new files in isolated worktree. Existing frozen P1a/source/product/lock files byte-unchanged; no Main merge. Local scoped commits permitted with gc.auto=0 and maintenance.auto=false.',
        'Compile two actual NSIS media (Desktop and CLI) containing identical complete approved payload and finalizer. Hash/verify inputs before compile and outputs after; record exact argv/cwd/env/tool/include/plugin/stub/license closure, stdout/stderr and native exit. NSIS full installation input manifest is Root-pinned; shared locked.json remains untouched.',
        'These are unqualified build artifacts in artifact_root, not a ready installer release. No actual installation success claim. Until transaction/maintenance executor exists, emitted media must reject mutation before any program/data/registry/PATH integration. In particular existing/different payload or retained-data path returns UPGRADE_REQUIRES_MAINTENANCE, not success. First-install capability remains pending M3/M4.',
        'Media may package payload archive plus trusted finalizer for future transaction consumption. Verify embedded bytes by non-executing archive inspection/byte inventory. Do not launch installer even in silent mode, and do not run product/finalizer against real locations.',
        'Use ResearchOS branding, never upstream Mu branding/updater. Produce deterministic complete payload equivalence and honest unsigned status. Default program/data/management roots fixed above; user-visible docs distinguish direct CLI path, new-shell PATH behavior, and actual capabilities.',
        'Pure plan.go routes fresh/exact reinstall/changed payload even at same display version/unsupported schema or verifier history. No filesystem, registry, process or data mutation; explicit fact inputs are future adapter responsibility.',
        'Pure append-only journal models intent and completed steps, rollback/NEEDS_RECOVERY, refuses rollback after COMMITTED, preserves all prior records and requires observed ownership/facts for recovery decisions. Ownership compare-and-remove/restore preserves unknown or modified files, existing PATH entries and concurrent edits.',
        'Maintenance sequence contract: persist intent while serialized, block new use admission, drain existing shared holders by normal Safe Exit, verify captured identities, then exclusive maintenance. Never exclusive-before-drain deadlock. Actual OS gate and transaction adapter remain future separately scoped work.',
        'Focused Python media build tests and Go internal/installation pure unit/state tests only. No full Go suite/native GUI/provider/C57/registry. Reuse accepted P1a test evidence for identical bytes; compile offline from pinned available tools/deps. Stop and report exact missing resource instead of downloading/running unrelated binaries.',
        'Package model may be a library contract for later M4; do not claim it is live wired into installer when no transaction executor exists. Full J1-J5 and W20/A15/U08 obligations remain open.'
      ],'not_authorized':['Run media/installer/uninstaller/finalizer or product', 'Registry/PATH/shortcuts or original data operations','Source outside exact11','Edit frozen P1a/build05/C57/old receipts','Global toolchain lock edits, Main merge or external publish'],
      'setup':{'tool_start_chunk':'059e9b','exec_session':84225,'terminal_chunk':'fdeca4','terminal_exit':0}}
    new(out/'Installer-P1b-exact11-source-scope.json',scope);new(out/'preservation.json',preserved)
    pending=read(N/'continuation-cp573/pending-root-diagnostics.json');cp['failure_counters'].append(pending)
    resume=read(N/'continuation-cp573/RESUME.current.json');resume.update(schema='researchos.current-chat-resume.v152',at=now,checkpoint_revision=574,ownership_revision=359,
       installer_p1b_source_scope_ref=ref(out/'Installer-P1b-exact11-source-scope.json'),native_followup_preparation_ref=ref(B/'product_host_native_20261028/native-init-diagnosis-02/environment-probe/preparation03/PREPARATION.json'),
       next_command='Independent review prep03 then Root seals exact finite helper run. Parallel implement installer exact11 media/pure models in new69-base worktree; no actual install or Main integration. Goal unfinished.')
    new(out/'RESUME.current.json',resume);cp.update(revision=574,expected_previous_revision=573,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
    cp['work_in_progress']['current_chat_continuation_cp574']=ref(out/'RESUME.current.json');cp['evidence_index'].append({'kind':'INSTALLER_P1B_EXACT11_SOURCE_BUILD_SCOPE','ref':ref(out/'Installer-P1b-exact11-source-scope.json'),'formal_increment':0})
    ow.update(revision=359,expected_previous_revision=358,updated_at=now,updated_by='codex:/root');ow['special_paths']['Installer_P1b_media']={'owner':scope['owner'],'state':'EXACT11_SOURCE_BUILD_AUTHORIZED','worktree':str(W),'scope_ref':ref(out/'Installer-P1b-exact11-source-scope.json')}
    prefix='# Current verified continuation CP574\n\nRead '+str(out/'RESUME.current.json')+' first. Prep03 finite follow-up under independent review, no native run yet. Installer P1b exact11 isolated source/media build authorized; actual installation withheld. All prior evidence and full goal retained.\n\n'
    changes={paths[0]:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),paths[1]:(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode(),paths[2]:prefix.encode()+old[paths[2]]}
    for p in paths:assert p.read_bytes()==old[p]
    for p,data in changes.items():
        (out/(p.name+'.before.raw')).write_bytes(old[p]);temp=p.with_name(p.name+'.cp574.pending')
        with temp.open('xb') as f:f.write(data)
        assert p.read_bytes()==old[p];os.replace(temp,p)
    assert paths[3].read_bytes()==old[paths[3]]
    print(json.dumps({'checkpoint':574,'ownership':359,'records':len(cp['failure_counters']),'scope':ref(out/'Installer-P1b-exact11-source-scope.json')}))

if __name__=='__main__':main()
