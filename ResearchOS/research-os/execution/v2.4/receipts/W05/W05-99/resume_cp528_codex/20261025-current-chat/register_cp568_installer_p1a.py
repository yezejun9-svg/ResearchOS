"""Register the independently supported static payload/finalizer subset."""
import datetime,json,os,subprocess
from pathlib import Path
from preserve_main_baseline import R,N,git,read,ref
from preserve_desktop_main_ecc28 import verify

def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    cp_path=R/'execution/v2.4/checkpoint.json';ow_path=R/'execution/v2.4/path_ownership.json';handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';state=R/'execution/v2.4/step_state.json'
    old={p:p.read_bytes() for p in [cp_path,ow_path,handoff,state]};cp,ow=read(cp_path),read(ow_path)
    assert cp['revision']==567 and ow['revision']==352 and len(cp['failure_counters'])==2286
    preserved=verify();base='5c4c94022bd92da68ef544f2779527bfe065c428'
    product=R/'.local/worktrees/desktop-installed-delivery-20261025';W=R/'.local/worktrees/installer-p1a-20261028'
    assert git(product,'rev-parse','HEAD').decode().strip()==base and not git(product,'status','--porcelain=v1','--untracked-files=all')
    assert not W.exists();B=R/'execution/v2.4/receipts/W05/W05-99'
    review=B/'installer_p1_design_review_20261028/DESIGN-REVIEW.md'
    assert ref(review)['sha256']=='b24ea8ee5ca2bcd59c5f11f89239cb52c7abbc36598b1018f4f9e0114241f241'
    bundle=product/'.local/product-layout-cp558-20261028-05';marker=bundle/'installed-product.json'
    assert ref(marker)['sha256']=='c785a1bb1b328cac9c37794e8fbd7cf607c4e4322f80963ea203436ba4e2f8e3'
    paths=['ops/release/product_installer/build.py','ops/release/product_installer/payload.schema.json','ops/release/product_installer/finalize/main.go','ops/release/product_installer/finalize/main_test.go','tests/release/product_installer_build_test.py']
    assert git(R,'ls-tree','-r','--name-only',base,'--',*paths)==b''
    out=N/'continuation-cp568';out.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt=B/'installer_p1a_source_codex/20261028';artifact=W/'.local/installer-p1a'
    scope={'schema':'researchos.installer-static-payload-finalizer-scope.v1','at':now,'owner':'codex:/root/installer_p1a_builder','reviewer':'codex:/root/installer_p1_design_review','worktree':str(W),'base_commit':base,'base_tree':'133c6fdee17e1ad2f7758689c55c1486e778cec0','branch':'codex/installer-p1a-20261028','allowed_source_paths':paths,'artifact_root':str(artifact),'receipt_root':str(receipt),
      'input_bundle':str(bundle),'input_marker_ref':ref(marker),'source_build_review_ref':ref(B/'product_host_independent_20261028/cp565-source-review/FINAL-REVIEW.json'),'independent_design_review_ref':ref(review),'path_design_ref':ref(B/'installer_p1_design_review_20261028/PATH-REVISION.json'),
      'required_behavior':['Consume only exact independently reviewed candidate manifest and complete frozen payload; verify every source file before packaging and again afterward.',
        'Produce deterministic location-independent payload manifest plus compiled Go finalizer; exclude only candidate installed-product.json and absolute runtime-verifier-installation.json from physical product payload. Preserve source/protocol/schema/version and all required runtime/contracts/licenses facts.',
        'Embed trusted payload manifest digest in finalizer at build; empty/unbound digest must refuse. Finalizer requires the supplied manifest exact bytes hash match before using its paths or metadata.',
        'Operate only on an explicitly supplied newly staged root: reject existing product marker, extra/missing/tampered files, noncanonical paths, case aliases, symlinks/reparse redirection; never edit any user data or installed original.',
        'At final absolute root generate verifier installation manifest with final executable path/hash first, then exact complete inventory and current Go/JS-compatible installation identity, then write installed-product.json create-new/atomic last. Verify all five binary roles and derive counts, never silently relax validation.',
        'Output separate payload digest versus per-location installation digest; same payload in two Unicode/space roots must share payload identity but have different correctly derived installation identity.',
        'No install registry/PATH/start menu, NSIS execution, live product launch, upgrade/rebind/rollback/uninstall in this static subset. Those require maintenance/journal and verifier-registration admission design first.'],
      'allowed_execution':['Root creates new sparse worktree from exactbase; no existing worktree modified','Pinned Go stdlib-only finalizer compilation and focused Go tests; pinned Python focused builder tests; isolated cache/TEMP and no network/module installs','Run finalizer only on newly created roots under artifact_root, including intended negative cases; retain raw results and input hashes','Create one deterministic payload candidate with manifest/finalizer in newartifactpaths and source-bound local exact5 commit'],
      'not_authorized':['Source paths beyond exact5 or shared/go.mod/lock changes','Any existing installation/user data/config/credentials/registry/PATH/shortcuts operations','Product CLI/Electron/Core native startup','C57 verifier replacement or cross-schema migration','Copy frozen product code then patch it without rebuilding validator/source closure','Delete unknown or prior evidence/candidates'],
      'testing':'Meaningful fresh-root finalization and adversarial manifest/path/inventory tests; deterministic payload emission. Existing product loader can be loaded read-only under pinned Node solely to validate finalized fixture manifest; no product main.js or host methods.',
      'gates':'This is source/build/static relocation preparation only; known init/renderer lifecycle gaps remain open. Independent review before integration and NSIS/actual installation. Full22parents42formal unchanged.',
      'formal_increment':0}
    new(out/'Installer-P1a-source-scope.json',scope)
    new(out/'preservation.json',preserved)
    resume=read(N/'continuation-cp567/RESUME.current.json')
    resume.update(schema='researchos.current-chat-resume.v146',at=now,checkpoint_revision=568,ownership_revision=353,installer_p1a_scope_ref=ref(out/'Installer-P1a-source-scope.json'),
      active_source_cards=[{'owner':scope['owner'],'scope_ref':ref(out/'Installer-P1a-source-scope.json')}],
      next_command='Continue independent chooser diagnostic/review and one fresh raw-error run after Root scope. In parallel implement exact5 static installer payload/finalizer in new sparse worktree; no actual installation/upgrade or original data actions. Full22parents42formal remain open.')
    new(out/'RESUME.current.json',resume)
    cp.update(revision=568,expected_previous_revision=567,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
    cp['work_in_progress']['current_chat_continuation_cp568']=ref(out/'RESUME.current.json')
    cp['evidence_index'].append({'kind':'INSTALLER_P1A_STATIC_EXACT5_SCOPE','ref':ref(out/'Installer-P1a-source-scope.json'),'formal_increment':0})
    ow.update(revision=353,expected_previous_revision=352,updated_at=now,updated_by='codex:/root')
    ow['special_paths']['Installer_P1a_source']={'owner':scope['owner'],'state':'EXACT5_SETUP_REGISTERED','scope_ref':ref(out/'Installer-P1a-source-scope.json'),'worktree':str(W)}
    prefix='# Current verified continuation CP568\n\nRead '+str(out/'RESUME.current.json')+' first. Static installer payload/finalizer exact5 scoped in newworktree; chooser/v3 source revisions pending independentreview. Native02 failure preserved, nooldstate replay. Main/C57/originals unchanged; formal0/42/all22open.\n\n'
    changes={cp_path:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),ow_path:(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode(),handoff:prefix.encode()+old[handoff]}
    for p in old:assert p.read_bytes()==old[p]
    for p,data in changes.items():
        (out/(p.name+'.before.raw')).write_bytes(old[p]);pending=p.with_name(p.name+'.cp568.pending')
        with pending.open('xb') as f:f.write(data)
        assert p.read_bytes()==old[p];os.replace(pending,p)
    assert state.read_bytes()==old[state]
    commands=[(R,['git','-c','gc.auto=0','-c','maintenance.auto=false','worktree','add','--no-checkout','-b',scope['branch'],str(W),base]),(W,['git','sparse-checkout','set','--cone','ops/release','tests/release','docs/installation','execution/toolchains'])]
    results=[]
    for ordinal,(cwd,argv) in enumerate(commands,1):
        completed=subprocess.run(argv,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
        stem='setup-'+str(ordinal);(out/(stem+'.stdout.raw')).write_bytes(completed.stdout);(out/(stem+'.stderr.raw')).write_bytes(completed.stderr)
        row={'argv':argv,'cwd':str(cwd),'exit':completed.returncode,'stdout':ref(out/(stem+'.stdout.raw')),'stderr':ref(out/(stem+'.stderr.raw'))};results.append(row);new(out/(stem+'.json'),row)
        assert completed.returncode==0
    assert git(W,'rev-parse','HEAD').decode().strip()==base and not git(W,'status','--porcelain=v1','--untracked-files=all')
    new(out/'setup-complete.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':base,'scope_ref':ref(out/'Installer-P1a-source-scope.json'),'commands':results,'preserved_after':verify()})
    print(json.dumps({'checkpoint':568,'ownership':353,'worktree':str(W),'scope':ref(out/'Installer-P1a-source-scope.json')}))

if __name__=='__main__':main()
