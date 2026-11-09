"""Preserve the completed diagnostic and scope two independent concrete next steps."""
import datetime,json,os
from pathlib import Path
from preserve_main_baseline import R,N,git,read,ref
from preserve_desktop_main_ecc28 import verify

def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    paths=[R/'execution/v2.4/checkpoint.json',R/'execution/v2.4/path_ownership.json',R/'execution/v2.4/HANDOFF_RESUME_PACK.md',R/'execution/v2.4/step_state.json']
    old={p:p.read_bytes() for p in paths};cp,ow=read(paths[0]),read(paths[1])
    assert cp['revision']==569 and ow['revision']==354 and len(cp['failure_counters'])==2289
    preserved=verify();B=R/'execution/v2.4/receipts/W05/W05-99';A=B/'product_host_native_20261028';D=A/'native-init-diagnosis-02';I=B/'product_host_independent_20261028'
    nreview=I/'native-chooser-execution-cp569-review/FINAL-REVIEW.json';assert ref(nreview)['sha256']=='780098be2380fecae77b3eaf83e2861058e7e48c36a59e5f1585f463a7b05d0d'
    nr=read(nreview);assert nr['controller_exit']==1 and nr['controller_reconciled_release_accepted'] and nr['separate_root_normal_close_accepted'] and not nr['native_chooser_success']
    dreview=I/'driver-v3-review/revision02-efe3999d/REVIEW.json';assert ref(dreview)['sha256']=='6f4f0cc536609cbbcc5597b4db2af31e06be7289d5d61b6cb11a203d5cf288e0'
    ireview=B/'installer_p1a_independent_review_20261028/REVIEW.json';assert ref(ireview)['sha256']=='83555b309a7d49e0a238b1490f4b735100ccf5f8c6de9a937ad4cea025ae9e8d' and read(ireview)['status']=='NEEDS_REVISION'
    author=B/'installer_p1a_source_codex/20261028/FINAL-MANIFEST.json';assert ref(author)['sha256']=='9dbf53f83e2d5b6d3fba152450887541b256dcf523b35ca3ccca7d7b12b2bdf1'
    W=R/'.local/worktrees/installer-p1a-20261028';P=R/'.local/worktrees/desktop-installed-delivery-20261025'
    assert git(W,'rev-parse','HEAD').decode().strip()=='6cf0457072bdd1d730dae961474d4d885a2cdd1b' and not git(W,'status','--porcelain=v1','--untracked-files=all')
    assert git(P,'rev-parse','HEAD').decode().strip()=='5c4c94022bd92da68ef544f2779527bfe065c428' and not git(P,'status','--porcelain=v1','--untracked-files=all')
    out=N/'continuation-cp570';out.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    files=['ops/release/product_installer/build.py','ops/release/product_installer/finalize/main.go','ops/release/product_installer/finalize/main_test.go','tests/release/product_installer_build_test.py']
    installer={'schema':'researchos.installer-p1a-exact4-revision-scope.v1','at':now,'owner':'codex:/root/installer_p1a_builder','reviewer':'codex:/root/installer_p1a_independent_review','worktree':str(W),'base_commit':'6cf0457072bdd1d730dae961474d4d885a2cdd1b','base_tree':'7af2395a271731f1159c367fc0ab24d69bb26751','allowed_source_paths':files,'source_before':[ref(W/p) for p in files],'prior_scope_ref':ref(N/'continuation-cp568/Installer-P1a-source-scope.json'),'marker_selection_clarification_ref':ref(N/'continuation-cp569/Installer-P1a-marker-selection-clarification.json'),'independent_review_ref':ref(ireview),'prior_author_ref':ref(author),'artifact_root':str(W/'.local/installer-p1a/revision01'),'receipt_root':str(B/'installer_p1a_source_codex/20261028/revision01'),
      'required_changes':['R1: atomic same-filesystem no-replace marker publication; fail if target appears at commit, preserving its bytes. Keep marker last and all existing inventory checks. Guard all newly generated metadata against clobber. No claim that a broader installer transaction is now qualified.',
        'R2: reject noncanonical paths and prove resolved output/receipt containment beneath explicit authorized roots before any write. Reject Windows reparse/symlink ancestors and overlaps with source or each other. Bind exact new receipt root in builder invocation rather than infer arbitrary output authority.',
        'R3: track receipt directory acquisition; only an exclusively created, owned, validated receipt directory may receive failure evidence. Early refusal uses stderr and must not mutate preexisting receipt roots.',
        'Regression tests must demonstrate existing-target/no-clobber and controlled publication race, dotdot and junction parent rejection, preexisting receipts byte-for-byte unchanged; run relevant earlier tests once after revision.'],
      'allowed_execution':['Pinned offline Go/Python focused tests with private cache','New source-bound exact4 local commit; all Git mutations use -c gc.auto=0 -c maintenance.auto=false','One new complete static payload/finalizer build and fresh relocation fixture using unchanged frozen product marker; retain old candidates/results'],
      'not_authorized':['Other source paths or schema changes','Product/native/registry/install/upgrade/uninstall','Shared Git maintenance or fixing historical corrupt objects','Overwrite old artifacts/failure records or arbitrary directory cleanup'],
      'formal_increment':0}
    new(out/'Installer-P1a-exact4-revision-scope.json',installer)
    prep=B/'product_host_native_20261028/native-init-diagnosis-02/environment-probe/preparation01';artifact=P/'.local/native-folder-environment-cp570'
    envscope={'schema':'researchos.native-folder-environment-probe-preparation.v1','at':now,'owner':'codex:/root/product_host_resume_20261028','reviewer':'codex:/root/product_host_independent_20261028','worktree':str(P),'candidate_commit':'5c4c94022bd92da68ef544f2779527bfe065c428','source_ref':ref(P/'internal/host/native_folder_windows.go'),'management_ref':ref(P/'apps/desktop/main/lib/desktop-management.js'),'analysis_ref':ref(D/'static-cause-analysis01/REPORT.md'),'failed_native_review_ref':ref(nreview),'write_root':str(prep),'artifact_root':str(artifact),'native_execution_authorized':False,'formal_increment':0,
      'goal':'Prepare the smallest disposable helper and controller that distinguish exact production Core environment from the same environment plus SystemDrive, using identical unchanged chooser code, same Unicode hint path and same hidden startup.',
      'source_fidelity':'Copy only the frozen native_folder_windows.go bytes with package host changed to package main; record original/transformed hashes and exact single-line delta. New main.go defines matching ErrFrameShape and calls unchanged chooser once; no product source edits. Compile offline using existing pinned module inputs and toolchain, output only in artifact_root.',
      'controller_requirements':['No inherited provider/credential environment; derive the exact Core Windows allowlist from frozen management source and use explicitly isolated User/AppData/Temp paths. Case B differs only by current verified SystemDrive; log key names plus this nonsecret Windows drive value.',
        'Do not inject COM initialization or alter callback/flags/chooser internals. Record startup flags, timing, exact returned error, owned window PID/HWND/class/visibility/rectangle and whether controller cancelled it.',
        'One helper call per case; hold handle immediately on Popen. No test timeout, kill, automatic retry, full product startup, or global keyboard/mouse. Cancel only exact owned dialog after identity and HWND recheck using normal IDCANCEL. Early Shell-null exit is evidence, not successful choice.',
        'Prepare finite A(actual stripped)/B(+SystemDrive) comparison, optional A2 only if A/B differ and later Root explicitly scopes it. Source preparation/build only now; Root seals actual hashes/run limits before any native GUI.',
        'Unexpected live helper or IO failure must keep parent/handle alive and record unresolved. Reuse reviewed hold/release patterns as appropriate; do not invoke old test harness that kills helper on failure.'],
      'not_authorized':['Any native GUI execution before Root separately scopes accepted helper/controller','Modify actual product sources or build05/old diagnostic evidence','Model/provider/network traffic or original user data','Automatically replay failed product lifecycle']}
    new(out/'Native-folder-environment-preparation-scope.json',envscope);new(out/'preservation.json',preserved)
    failures=[{'origin_key':'20261028|native-chooser|cp569-single-diagnostic','status':'RAW_DIAGNOSTIC_CAPTURED_NATIVE_CHOICE_FAILED','attempts':1,'exit':1,'ref':ref(nreview),'detail':'Shell returned null; client post-reply PID query and visibility-only chooser helper failed; root reconciliation separately accepted.'},
      {'origin_key':'20261028|native-chooser|cp569-normal-close-visible-filter','status':'DIAGNOSTIC_HELPER_FAILED_NO_MESSAGE_THEN_EXACT_HIDDEN_WINDOW_RECONCILED','attempts':1,'ref':ref(D/'reconcile-cp569/execution01/RESULT.json')},
      {'origin_key':'20261028|installer-p1a|source-build01-extra-cache','status':'AUTHOR_INITIAL_BUILD_REJECTED_SOURCE_EXTRAS_PRESERVED','attempts':1,'ref':ref(author)},
      {'origin_key':'20261028|installer-p1a|commit-automatic-gc-bad-tree','status':'GIT_MAINTENANCE_DIAGNOSTIC_COMMIT_EXISTS_NO_REPAIR_ATTEMPTED','attempts':1,'ref':ref(author)},
      {'origin_key':'20261028|installer-p1a|independent-review-r1-r3','status':'SOURCE_NEEDS_REVISION_THREE_FINDINGS','attempts':1,'ref':ref(ireview)},
      {'origin_key':'20261028|installer-p1a|review-scratch-cleanup-policy','status':'AUTO_APPROVAL_REJECTED_RECURSIVE_DELETE_NOT_EXECUTED','attempts':1,'ref':ref(ireview.parent/'scratch-cleanup.json'),'detail':'blocked by policy; no narrower reason supplied. Scratch retained for revision verification, no bypass.'}]
    existing={v.get('origin_key') for v in cp['failure_counters']}
    for row in failures:assert row['origin_key'] not in existing;row['counter_reset']=False;cp['failure_counters'].append(row)
    resume=read(N/'continuation-cp569/RESUME.current.json')
    resume.update(schema='researchos.current-chat-resume.v148',at=now,checkpoint_revision=570,ownership_revision=355,native_cp569_final_review_ref=ref(nreview),wrapper_v3_revision02_review_ref=ref(dreview),installer_revision_scope_ref=ref(out/'Installer-P1a-exact4-revision-scope.json'),environment_probe_preparation_scope_ref=ref(out/'Native-folder-environment-preparation-scope.json'),next_command='Fix installer exact4 R1-R3 and prepare disposable Core-environment native chooser A/B helper/controller in independent directories. No current product processes remain. Source/build review then Root finite experimental scope. C57 admin resource remains separate; full22parents42formal unchanged.')
    new(out/'RESUME.current.json',resume)
    cp.update(revision=570,expected_previous_revision=569,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress']['current_chat_continuation_cp570']=ref(out/'RESUME.current.json')
    cp['evidence_index'].extend([{'kind':'NATIVE_CHOOSER_FAILURE_AND_NORMAL_ROOT_RECONCILIATION_REVIEW','ref':ref(nreview),'formal_increment':0},{'kind':'INSTALLER_P1A_INDEPENDENT_FINDINGS_EXACT4_REPAIR_SCOPE','ref':ref(out/'Installer-P1a-exact4-revision-scope.json'),'formal_increment':0}])
    ow.update(revision=355,expected_previous_revision=354,updated_at=now,updated_by='codex:/root')
    ow['special_paths']['Product_host_chooser_diagnostic'].update(state='FAILED_DIAGNOSIS_NORMAL_ROOT_RECONCILIATION_ACCEPTED_NO_PROCESSES',native_authorized=False,final_review_ref=ref(nreview))
    ow['special_paths']['Product_host_native_driver_v3'].update(state='REVISION02_SOURCE_ACCEPTED_FROZEN',native_authorized=False,independent_review_ref=ref(dreview))
    ow['special_paths']['Installer_P1a_source'].update(state='EXACT4_R1_R3_REVISION_SCOPED',scope_ref=ref(out/'Installer-P1a-exact4-revision-scope.json'))
    ow['special_paths']['Native_folder_environment_probe']={'owner':envscope['owner'],'state':'PREPARATION_AND_BUILD_ONLY','native_authorized':False,'scope_ref':ref(out/'Native-folder-environment-preparation-scope.json')}
    prefix='# Current verified continuation CP570\n\nRead '+str(out/'RESUME.current.json')+' first. CP569 chooser failed; separate normal close and controller release independently accepted, no related processes remain. Installer exact4 repairs and environment-probe preparation are active. No new native run authorized. Main/C57/originals protected.\n\n'
    changes={paths[0]:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),paths[1]:(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode(),paths[2]:prefix.encode()+old[paths[2]]}
    for p in paths:assert p.read_bytes()==old[p]
    for p,data in changes.items():
        (out/(p.name+'.before.raw')).write_bytes(old[p]);tmp=p.with_name(p.name+'.cp570.pending')
        with tmp.open('xb') as f:f.write(data)
        assert p.read_bytes()==old[p];os.replace(tmp,p)
    assert paths[3].read_bytes()==old[paths[3]]
    print(json.dumps({'checkpoint':570,'ownership':355,'records':len(cp['failure_counters']),'installer':ref(out/'Installer-P1a-exact4-revision-scope.json'),'environment':ref(out/'Native-folder-environment-preparation-scope.json')}))

if __name__=='__main__':main()
