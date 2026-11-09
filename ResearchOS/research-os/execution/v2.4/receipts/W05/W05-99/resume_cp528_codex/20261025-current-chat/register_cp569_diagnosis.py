"""Seal the independently reviewed one-shot chooser diagnostic, preserving history."""
import datetime,json,os,subprocess
from pathlib import Path
from preserve_main_baseline import R,N,git,read,ref
from preserve_desktop_main_ecc28 import verify

def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    paths=[R/'execution/v2.4/checkpoint.json',R/'execution/v2.4/path_ownership.json',R/'execution/v2.4/HANDOFF_RESUME_PACK.md',R/'execution/v2.4/step_state.json']
    old={p:p.read_bytes() for p in paths};cp,ow=read(paths[0]),read(paths[1])
    assert cp['revision']==568 and ow['revision']==353 and len(cp['failure_counters'])==2286
    preserved=verify();B=R/'execution/v2.4/receipts/W05/W05-99';A=B/'product_host_native_20261028';D=A/'native-init-diagnosis-02';P=D/'preparation/revision01'
    review=B/'product_host_independent_20261028/native-chooser-diagnostic-review/revision01-4bfabee8/REVIEW.json'
    assert ref(review)['sha256']=='88843f5f00114efc859e86e538aefa0bb7c45387ce95f77dadedda0b4946a9cd'
    accepted=read(review);assert accepted['diagnostic_source_accepted'] and accepted['actual_native_runs']==0
    for expected in accepted['fixed_files']:assert ref(Path(expected['path']))==expected
    W=R/'.local/worktrees/desktop-installed-delivery-20261025';bundle=W/'.local/product-layout-cp558-20261028-05'
    head='5c4c94022bd92da68ef544f2779527bfe065c428';tree='133c6fdee17e1ad2f7758689c55c1486e778cec0'
    assert git(W,'rev-parse','HEAD').decode().strip()==head and git(W,'rev-parse','HEAD^{tree}').decode().strip()==tree
    assert not git(W,'status','--porcelain=v1','--untracked-files=all')
    marker=bundle/'installed-product.json';assert ref(marker)['sha256']=='c785a1bb1b328cac9c37794e8fbd7cf607c4e4322f80963ea203436ba4e2f8e3'
    m=read(marker);inventory=[]
    for row in m['files']:
        actual=ref(bundle/row['path']);assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'];inventory.append(actual)
    known={str((bundle/row['path']).resolve()).casefold() for row in m['files']}|{str(marker.resolve()).casefold()}
    extras=[ref(p) for p in sorted(bundle.rglob('*')) if p.is_file() and str(p.resolve()).casefold() not in known]
    locked=read(R/'execution/toolchains/locked.json')['tools'];python=Path(locked['python']['path'])
    assert ref(python)['sha256']==locked['python']['sha256']
    pwsh=Path('C:/Users/yqyyds/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe');assert pwsh.is_file()
    state=W/'.local/native-chooser-cp569-20261028-01';receipts=D/'execution-cp569-01'
    assert not state.exists() and not receipts.exists()
    out=N/'continuation-cp569';out.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    bounds=[ref(P/'diagnose_once.py'),ref(P/'choose-once.ps1'),ref(A/'driver-v2/choose-owned-folder.ps1'),ref(A/'driver-v2/close-owned-window.ps1'),ref(marker),ref(python),ref(pwsh)]
    scope={'schema':'researchos.owned-native-chooser-diagnostic-scope.v1','at':now,'owner':'codex:/root','native_chooser_diagnosis_authorized':True,'mode':'ONE_OWNED_NATIVE_CHOOSER_DIAGNOSIS_NO_PROVIDER','formal_increment':0,'worktree':str(W),'bundle_root':str(bundle),'candidate_commit':head,'candidate_tree':tree,'installation_id':m['installation_id'],'powershell_path':str(pwsh),'state_root':str(state),'receipts_root':str(receipts),'bound_files':bounds,'source_review_ref':ref(review),'inventory_preflight':inventory,'unlisted_source_files_before':extras,
      'run_command':[str(python),'-B',str(P/'diagnose_once.py'),str(out/'Owned-chooser-diagnostic-scope.json')],
      'environment':'No PYTHONOPTIMIZE or -O. Controller retains handles; exact reviewed child environment. Existing relative SystemDrive caches recorded, not removed or packaged. Their probable environment cause is an inference, not a process-level finding.',
      'allowed':['One fresh isolated Electron/Core pair and one native choose request','One exact identity-checked normal WM_CLOSE while controller remains live','Append-only raw reply, helper exit and process evidence','On unresolved closure keep controller alive; Root reconciliation with current identity evidence and unique scoped release only'],
      'not_authorized':['Full lifecycle replay or automatic retry','Provider or credentials use','Original data, registry, installed configuration or Main source writes','Any forced process termination','Reusing attempt01/02 state or weakening failure history'],
      'interpretation':'Controller exit0 proves owned clean close only; inspect reply and helper exits separately. Source acceptance is not native acceptance.'}
    new(out/'Owned-chooser-diagnostic-scope.json',scope);new(out/'preservation.json',preserved)
    new(out/'Installer-P1a-marker-selection-clarification.json',{'at':now,'prior_scope_ref':ref(N/'continuation-cp568/Installer-P1a-source-scope.json'),'selection':'Exact frozen marker whitelist with source file verification before and after; only two original metadata exclusions. List/hash source extras, do not copy or remove them. Destination finalizer must reject extras. Retain build01 rejection.','source_extras':extras,'formal_increment':0})
    failures=[{'origin_key':'20261028|root|cp568-empty-sparse-index-setup','status':'SETUP_ASSERTION_FAILED_THEN_SCOPED_READ_TREE_REPAIR','attempts':1,'exit':1,'tool_chunk':'9f42f5','refs':[ref(N/'continuation-cp568/sparse-unpopulated-status.raw'),ref(N/'continuation-cp568/setup-complete.json')]},
      {'origin_key':'20261028|root|cp569-recovery-backend-unavailable','status':'TOOL_DIAGNOSTIC_NOT_PRODUCT_FAILURE','attempts':3,'detail':'Two private note listings and one recent-user lookup unavailable; local continuation recovered.'},
      {'origin_key':'20261028|root|cp567-script-name-locator','status':'READONLY_LOCATOR_DIAGNOSTIC','attempts':1,'tool_chunk':'83d8ee','detail':'Wrong historical script name; no source changes or execution.'}]
    existing={v.get('origin_key') for v in cp['failure_counters']}
    for row in failures:
        assert row['origin_key'] not in existing;row['counter_reset']=False;cp['failure_counters'].append(row)
    resume=read(N/'continuation-cp568/RESUME.current.json')
    resume.update(schema='researchos.current-chat-resume.v147',at=now,checkpoint_revision=569,ownership_revision=354,native_chooser_scope_ref=ref(out/'Owned-chooser-diagnostic-scope.json'),next_command='Execute the accepted one-shot chooser diagnostic directly and inspect raw error; keep unresolved parent alive. Installer static exact5 continues independently. Wrapper revision02 author transferred to product_host_resume_20261028; independent review required before any replay.')
    new(out/'RESUME.current.json',resume)
    cp.update(revision=569,expected_previous_revision=568,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
    cp['work_in_progress']['current_chat_continuation_cp569']=ref(out/'RESUME.current.json')
    cp['evidence_index'].append({'kind':'ONE_OWNED_NATIVE_CHOOSER_DIAGNOSIS_SCOPED','ref':ref(out/'Owned-chooser-diagnostic-scope.json'),'formal_increment':0})
    ow.update(revision=354,expected_previous_revision=353,updated_at=now,updated_by='codex:/root')
    ow['special_paths']['Product_host_chooser_diagnostic']={'owner':'codex:/root','state':'ONE_FRESH_DIAGNOSTIC_SCOPED','scope_ref':ref(out/'Owned-chooser-diagnostic-scope.json'),'native_authorized':True,'source_write_authorized':False}
    ow['special_paths']['Product_host_native_driver_v3'].update(owner='codex:/root/product_host_resume_20261028',state='REVISION02_PREPARATION_ONLY',native_authorized=False)
    prefix='# Current verified continuation CP569\n\nRead '+str(out/'RESUME.current.json')+' first. One fresh chooser raw-error diagnostic scoped after independent source review. Installer static exact5 proceeds; no full native lifecycle acceptance. Main/C57/original data protected; formal0/42 and all22parents open.\n\n'
    changes={paths[0]:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),paths[1]:(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode(),paths[2]:prefix.encode()+old[paths[2]]}
    for p in paths:assert p.read_bytes()==old[p]
    for p,data in changes.items():
        (out/(p.name+'.before.raw')).write_bytes(old[p]);tmp=p.with_name(p.name+'.cp569.pending')
        with tmp.open('xb') as f:f.write(data)
        assert p.read_bytes()==old[p];os.replace(tmp,p)
    assert paths[3].read_bytes()==old[paths[3]]
    print(json.dumps({'checkpoint':569,'ownership':354,'records':len(cp['failure_counters']),'scope_ref':ref(out/'Owned-chooser-diagnostic-scope.json'),'source_extra_files':len(extras)}))

if __name__=='__main__':main()
