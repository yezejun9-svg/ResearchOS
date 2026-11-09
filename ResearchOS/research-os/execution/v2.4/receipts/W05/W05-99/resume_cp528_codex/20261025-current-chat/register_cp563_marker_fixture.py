"""Register only a proven file-removal precondition repair in a Node fixture."""
import datetime,json,os
from pathlib import Path
from preserve_main_baseline import R,N,git,read,ref
from preserve_desktop_main_ecc28 import verify

def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    cp_path=R/'execution/v2.4/checkpoint.json';ow_path=R/'execution/v2.4/path_ownership.json';h=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';state=R/'execution/v2.4/step_state.json'
    old={p:p.read_bytes() for p in [cp_path,ow_path,h,state]};cp,ow=read(cp_path),read(ow_path)
    assert cp['revision']==562 and ow['revision']==347 and len(cp['failure_counters'])==2265
    preserved=verify();W=R/'.local/worktrees/desktop-installed-delivery-20261025';base='9361c1b63fa658251f730771bc12633ff5f12c08'
    assert git(W,'rev-parse','HEAD').decode().strip()==base and not git(W,'status','--porcelain=v1','--untracked-files=all')
    E=R/'execution/v2.4/receipts/W05/W05-99/installed_delivery_codex/20261025-current-chat/continuation-20261028'
    manifest=E/'FINAL-MANIFEST.json';assert ref(manifest)['sha256']=='c0957ec54ab37b464e029c59325d3b1fe7e99c5ad6e61decd988fdb3563a8829'
    review=R/'execution/v2.4/receipts/W05/W05-99/product_host_independent_20261028/focused-9361-review'
    inputs=[ref(review/n) for n in ['node.stdout.raw','node.result.json','RESULT.json','delete-timing.json']]
    out=N/'continuation-cp563';out.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    scope={'schema':'researchos.product-marker-fixture-repair.v1','at':now,'owner':'codex:/root/product_host_resume_20261028','reviewer':'codex:/root/product_host_independent_20261028',
        'worktree':str(W),'base_commit':base,'base_tree':'8975ca6b0ac1cfb3c429e4be6a1ed697d9bdb020',
        'allowed_source_paths':['tests/ui/desktop/product-host.test.mjs'],
        'source_before':ref(W/'tests/ui/desktop/product-host.test.mjs'),'production_helper_unchanged_ref':ref(W/'apps/desktop/main/lib/product-layout.js'),
        'diagnostic_refs':inputs,'prior_current_manifest_ref':ref(manifest),
        'required_change':'In the removed-marker test use fs.unlinkSync for the regular marker file and assert fs.existsSync(markerPath)===false before asserting loader rejection. No production change or weakened assertion.',
        'allowed_execution':['One affected Node product-host.test.mjs group with frozen source/tool before-after binding in a fresh owned isolated environment','Exact one-file atomic local commit with gc.auto=0 maintenance.auto=false','Fresh complete build04 in a new output/receipt path from clean new commit'],
        'artifact_root':str(W/'.local/marker-fixture-cp563-20261028'),'receipt_root':str(E/'marker-fixture-cp563'),
        'test_env':'Pinned Node; isolate LOCALAPPDATA APPDATA USERPROFILE TEMP TMP under artifact root; clear inherited NODE_OPTIONS NODE_PATH NODE_EXTRA_CA_CERTS and product env overrides. No Core/Electron/provider.',
        'preserve':['All previously sealed manifests and reports remain at their paths with identical bytes','Independent7pass1fail and timing probes remain raw immutable evidence','Use a new FINAL manifest under marker-fixture-cp563; old top-level FINAL-MANIFEST.json continues to describe9361'],
        'do_not_repeat':['Unchanged GoProduct and Python layout fixtures','ModelStream7 with previous impact finding','VM4 and status fixture','Whole CLI or renderer suite'],
        'not_authorized':['Modify product helper or any other source','Main/shared state modifications','Actual native product launch','Installer or original data operations'],
        'formal_increment':0,'source_acceptance':False}
    new(out/'Marker-fixture-exact1-scope.json',scope)
    diagnostic={'origin_key':'20261028|independent-9361|node-marker-removal-precondition-failed','status':'INDEPENDENT_FIXTURE_FAILURE_PRESERVED','attempts':1,'counter_reset':False,'product_failure':False,
        'detail':'Bound current Node group7pass1fail: rmSync returned while marker still existed. Isolated probe confirmed unlinkSync removes it and absent-marker loader refuses. Repair fixture precondition only; original failure retained.', 'refs':inputs}
    assert diagnostic['origin_key'] not in {x.get('origin_key') for x in cp['failure_counters']};cp['failure_counters'].append(diagnostic)
    new(out/'new-records-ledger.json',{'historical_count':2265,'current_count':2266,'records':[diagnostic],'counter_reset':False})
    resume=read(N/'continuation-cp562/RESUME.current.json')
    resume.update(schema='researchos.current-chat-resume.v141',at=now,checkpoint_revision=563,ownership_revision=348,failure_records_preserved=2266,
        product_host_fixture_scope_ref=ref(out/'Marker-fixture-exact1-scope.json'),product_host_current_source=base,
        next_command='Fix only removed-marker test precondition, run affected boundNode8, commit exact1/build04/new manifest. Preserve9361/build03/statusPASS and all old failures. Independent final review then Root native lifecycle and installer P1. All22/42 remain open.')
    resume['current_product_host_status']={'source':'9361_METADATA_REPAIR_PASSED_ONLY_NODE_FIXTURE_PRECONDITION_REPAIR_PENDING','build03':'BUILT133_ROOT_VERIFIED','model_stream7':'5ee2_PASS_UNAFFECTED_BY_ONE_LINE_METADATA_CHANGE','independent_focused':'Python2 and effectiveGoProduct8passed; Node7pass1fixturepreconditionfail','native':'NOT_RUN','author_failure_import':'PENDING_FINAL_MANIFEST'}
    new(out/'RESUME.current.json',resume)
    cp.update(revision=563,expected_previous_revision=562,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
    cp['work_in_progress']['current_chat_continuation_cp563']=ref(out/'RESUME.current.json')
    cp['evidence_index'].append({'kind':'INDEPENDENT_NODE_FIXTURE_PRECONDITION_EXACT1_REPAIR_REGISTERED','ref':ref(out/'Marker-fixture-exact1-scope.json'),'formal_increment':0})
    ow.update(revision=348,expected_previous_revision=347,updated_at=now,updated_by='codex:/root')
    ow['special_paths']['Installed_delivery_development'].update(state='FROZEN9361_TEST_ONLY_MARKER_PRECONDITION_REPAIR_ACTIVE_NO_NATIVE',marker_fixture_scope_ref=ref(out/'Marker-fixture-exact1-scope.json'))
    prefix='# Current verified continuation CP563\n\nRead '+str(out/'RESUME.current.json')+' first, with CP560 CONTINUATION.md. Source9361 metadata fix/statusPASS andbuild03; independent Node fixture failed delete precondition, exact1 test-only repair registered. Loader unchanged. Main/C57/originals preserved. Mixed2266 plus pendingauthor ledger; formal0/42/all22open.\n\n'
    changes={cp_path:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),ow_path:(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode(),h:prefix.encode()+old[h]}
    for p in old:assert p.read_bytes()==old[p]
    for p,data in changes.items():
        (out/(p.name+'.before.raw')).write_bytes(old[p]);pending=p.with_name(p.name+'.cp563.pending')
        with pending.open('xb') as f:f.write(data)
        assert p.read_bytes()==old[p];os.replace(pending,p)
    assert state.read_bytes()==old[state]
    print(json.dumps({'checkpoint':563,'ownership':348,'scope_sha256':ref(out/'Marker-fixture-exact1-scope.json')['sha256'],'records':2266}))

if __name__=='__main__':main()
