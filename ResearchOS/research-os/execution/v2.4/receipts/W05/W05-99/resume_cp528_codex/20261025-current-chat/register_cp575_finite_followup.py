"""Seal accepted finite C then A2/D experiment with current owned-state pins."""
import datetime,importlib.util,json,os
from pathlib import Path
from preserve_main_baseline import R,N,read,ref
from preserve_desktop_main_ecc28 import verify

def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    paths=[R/'execution/v2.4/checkpoint.json',R/'execution/v2.4/path_ownership.json',R/'execution/v2.4/HANDOFF_RESUME_PACK.md',R/'execution/v2.4/step_state.json']
    old={p:p.read_bytes() for p in paths};cp,ow=read(paths[0]),read(paths[1])
    assert cp['revision']==574 and ow['revision']==359 and len(cp['failure_counters'])==2305
    preserved=verify();B=R/'execution/v2.4/receipts/W05/W05-99';E=B/'product_host_native_20261028/native-init-diagnosis-02/environment-probe';P=E/'preparation03'
    review=B/'product_host_independent_20261028/environment-probe-source-review/preparation03-88b2dc8d/REVIEW.json'
    assert ref(review)['sha256']=='64a337d5858da908f8eaa06903b5dfb53e5c6345c92cf7691cfeaa628fb9ea17'
    assert read(review)['controller_source_accepted'] and ref(P/'PREPARATION.json')['sha256']=='14772591b1998e1ee6de7d7d6b71f1bdfd2b99de10455fc5f35c491e8c8a22db'
    for row in read(P/'PREPARATION.json')['files'].values():assert ref(Path(row['path']))==row
    assert ref(P/'RUN-SCOPE-TEMPLATE.json')['sha256']=='617bb31437e02f27e4cbd9812d75dfa715af1736f79dedb1cfcb3af11590783b'
    spec=importlib.util.spec_from_file_location('readonly_prep03',P/'controller.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    scope=read(P/'RUN-SCOPE-TEMPLATE.json');state=Path(scope['state_root'])
    a,c,hint=module.build_environments(state,os.environ['SystemRoot'],os.environ['WINDIR']);manifest=module.manifest_state(state)
    assert scope['a_env_sha256']==module.env_digest(a) and scope['c_env_sha256']==module.env_digest(c)
    assert scope['state_manifest_sha256']==manifest['sha256']
    out=N/'continuation-cp575';out.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    scope.update(at=now,owner='codex:/root',native_execution_authorized=True,receipts_root=str(E/'execution-cp575-C-branch01'),
        independent_review_ref=ref(review),source_scope_ref=ref(N/'continuation-cp573/Native-folder-followup-preparation03-scope.json'),
        explicit_limit='Exactly C then the selected A2 or D branch, at most2 helper calls. No other retries, real profile, product/native lifecycle, force kill or original data actions.',
        interpretation='Environment-group/startup diagnostic only; shared state/order and50ms sampling limits retained.')
    scope['invocation']=[read(R/'execution/toolchains/locked.json')['tools']['python']['path'],'-B',str(P/'controller.py'),str(out/'Native-folder-finite-followup-scope.json')]
    assert ref(Path(scope['invocation'][0]))['sha256']=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
    new(out/'Native-folder-finite-followup-scope.json',scope)
    module.validate_scope(out/'Native-folder-finite-followup-scope.json')
    new(out/'current-state-before.json',manifest);new(out/'preservation.json',preserved)
    resume=read(N/'continuation-cp574/RESUME.current.json');resume.update(schema='researchos.current-chat-resume.v153',at=now,checkpoint_revision=575,ownership_revision=360,
      native_followup_source_review_ref=ref(review),native_followup_run_scope_ref=ref(out/'Native-folder-finite-followup-scope.json'),
      next_command='Execute once prep03 controller under CP575 exact C then A2/D scope; not started. Record tool session/terminal immediately; preserve hold if unresolved, no kill. Installer P1b exact11 building independently; no actual installation. Full goal unfinished.')
    new(out/'RESUME.current.json',resume);cp.update(revision=575,expected_previous_revision=574,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
    cp['work_in_progress']['current_chat_continuation_cp575']=ref(out/'RESUME.current.json');cp['evidence_index'].append({'kind':'NATIVE_FINITE_FOLLOWUP_RUN_SCOPE','ref':ref(out/'Native-folder-finite-followup-scope.json'),'formal_increment':0})
    ow.update(revision=360,expected_previous_revision=359,updated_at=now,updated_by='codex:/root');ow['special_paths']['Native_folder_environment_probe'].update(owner='codex:/root',state='FINITE_C_BRANCH_EXECUTION_SCOPED_NOT_STARTED',native_authorized=True,scope_ref=ref(out/'Native-folder-finite-followup-scope.json'))
    prefix='# Current verified continuation CP575\n\nRead '+str(out/'RESUME.current.json')+' first. Accepted exact finite C then A2/D helper run scoped but NOT STARTED. Installer P1b source/media build active independently. Full product/formal goal unfinished.\n\n'
    changes={paths[0]:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),paths[1]:(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode(),paths[2]:prefix.encode()+old[paths[2]]}
    for p in paths:assert p.read_bytes()==old[p]
    for p,data in changes.items():
        (out/(p.name+'.before.raw')).write_bytes(old[p]);temp=p.with_name(p.name+'.cp575.pending')
        with temp.open('xb') as f:f.write(data)
        assert p.read_bytes()==old[p];os.replace(temp,p)
    assert paths[3].read_bytes()==old[paths[3]]
    print(json.dumps({'checkpoint':575,'ownership':360,'records':len(cp['failure_counters']),'scope':ref(out/'Native-folder-finite-followup-scope.json')}))

if __name__=='__main__':main()
