"""Register the exact seven ModelStream regressions; preserve product acceptance."""
import datetime, hashlib, json, os, subprocess
from pathlib import Path
from preserve_desktop_main_ecc28 import verify
from preserve_main_baseline import R, N, read, ref

def new(p, d):
    with p.open('x', encoding='utf-8') as f: json.dump(d, f, ensure_ascii=False, indent=2); f.write('\n')

def main():
    paths = [R/'execution/v2.4'/f for f in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
    old = {p:p.read_bytes() for p in paths}
    cp, own = read(paths[0]), read(paths[1])
    assert cp['revision']==560 and own['revision']==345 and len(cp['failure_counters'])==2260
    preserved = verify()
    proposal = R/'execution/v2.4/receipts/W05/W05-99/product_host_independent_20261028/MODEL-STREAM-REGRESSION-EXACT-PROPOSAL.json'
    assert ref(proposal)['sha256']=='cbd62190fe8e04c184afeeaec5db0bee69bf92a4981a00f35a91f8ce98a771cc'
    scope=read(proposal)
    out=N/'continuation-cp561'; out.mkdir()
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    W=R/'.local/worktrees/desktop-installed-delivery-20261025'
    artifact=W/'.local/model-stream-cp561-20261028'
    receipts=R/'execution/v2.4/receipts/W05/W05-99/installed_delivery_codex/20261025-current-chat/continuation-20261028/model-stream-cp561'
    assert not artifact.exists() and not receipts.exists()
    checked=[]
    for d in scope['candidate_build01_dependency_refs']:
        actual=ref(Path(d['path'])); assert actual['sha256']==d['sha256'] and actual['bytes']==d['bytes']; checked.append(actual)
    scope.update(schema='researchos.model-stream-regression-scope.v1', status='ROOT_REGISTERED_CONDITIONAL_FROZEN_SOURCE_EXECUTION', at=now,
        owner='codex:/root/product_host_resume_20261028', reviewer='codex:/root/product_host_independent_20261028',
        worktree=str(W), artifact_root=str(artifact), receipt_root=str(receipts), proposal_ref=ref(proposal),
        actual_fixture_execution_authorized=True, product_native_launch_authorized=False,
        source_gate='Before execution capture exact clean commit/tree and exact14 source hashes plus test/dependency closure. No source writes during regression. Run only declared seven tests after final source freeze. Bind final Mu closure or prove build01 closure identical.',
        temp_policy='TEMP TMP GOTMPDIR GOCACHE and test-created DB/config/workspaces must resolve beneath artifact_root. Set isolated LOCALAPPDATA APPDATA USERPROFILE HOME beneath artifact_root. Do not use original user configuration or credentials.',
        child_policy='Record launcher PID, creation time, argv and executable; retain per-case TLS stdout/stderr/exit and known child lifecycle. Existing harness context cancellation/owned child cleanup is permitted. No process-name kills, no unrelated process actions. Preserve unresolved owned handles on failure.',
        failure_policy='One execution of exact test set; keep prior missing-env and current failures immutable. A failure requires diagnosis and a separately recorded changed-input rerun, never an identical retry to green.',
        cleanup_policy='Only newly created owned temporary outputs after receipts are sealed and absolute path containment verified. Preserve evidence, old build01 and all prior diagnostics.',
        shared_state_mutation=False, formal_increment=0)
    scope['clear_inherited_environment'] += ['RESEARCHOS_HOST_*','RESEARCHOS_DATA_*','RESEARCHOS_CORE_*','RESEARCHOS_RUNTIME_*']
    new(out/'ModelStream-exact7-fixture-scope.json', scope)
    cmd=['python',str(R.parent/'ResearchOS_Implementation_Package_v2.4/tools/task_packet.py'),'next','--state',str(paths[3])]
    result=subprocess.run(cmd,cwd=R,capture_output=True)
    (out/'selector.stdout.raw').write_bytes(result.stdout); (out/'selector.stderr.raw').write_bytes(result.stderr)
    packet=json.loads(result.stdout.decode('utf-8-sig'))
    assert result.returncode==0 and packet['state_source']=='VALIDATED_FILE' and packet['step']['id']=='W05-99'
    new(out/'registration-evidence.json',{'at':now,'preserved':preserved,'dependencies':checked,'scope_ref':ref(out/'ModelStream-exact7-fixture-scope.json'),'selector':{'argv':cmd,'exit':result.returncode,'stdout':ref(out/'selector.stdout.raw'),'stderr':ref(out/'selector.stderr.raw')},'formal_increment':0})
    diagnostic={'origin_key':'20261028|root-cp561|readonly-recovery-diagnostics','status':'READONLY_DIAGNOSTIC_PRESERVED','attempts':1,'product_failure':False,'counter_reset':False,'detail':'Private recovery backend unavailable (3 calls); broad reads truncated; one incorrect cli_model_stream_test.go path absent, corrected to integration_windows test; one nonexistent optional recipe read exit1; own broad rg traversal interrupted (session9314 exit1), no product process action.'}
    assert diagnostic['origin_key'] not in {x.get('origin_key') for x in cp['failure_counters']}
    cp['failure_counters'].append(diagnostic)
    new(out/'new-records-ledger.json',{'historical_count':2260,'current_count':2261,'records':[diagnostic],'counter_reset':False})
    resume=read(N/'continuation-cp560/RESUME.current.json')
    resume.update(schema='researchos.current-chat-resume.v139',at=now,checkpoint_revision=561,ownership_revision=346,failure_records_preserved=2261,
        model_stream_exact7_scope_ref=ref(out/'ModelStream-exact7-fixture-scope.json'),
        next_command='Builder freezes exact14, executes registered seven ModelStream regressions with owned Native3/CLI/Node/Mu loopback fixtures, finishes fresh build and independent source/build review. Then Root native lifecycle scope. Preserve original data, C57, all failures and full installer/22parent/42formal goal.')
    resume['current_product_host_status']['fixture7_scope']='ROOT_REGISTERED_CP561_FREEZE_REQUIRED_BEFORE_EXECUTION'
    new(out/'RESUME.current.json',resume)
    cp.update(revision=561,expected_previous_revision=560,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
    cp['work_in_progress']['current_chat_continuation_cp561']=ref(out/'RESUME.current.json')
    cp['evidence_index'].append({'kind':'EXACT7_MODELSTREAM_FIXTURE_SCOPE_REGISTERED','ref':ref(out/'registration-evidence.json'),'formal_increment':0})
    own.update(revision=346,expected_previous_revision=345,updated_at=now,updated_by='codex:/root')
    own['special_paths']['Installed_delivery_development']['model_stream_fixture_scope_ref']=ref(out/'ModelStream-exact7-fixture-scope.json')
    prefix='# Current verified continuation CP561\n\nRead '+str(out/'RESUME.current.json')+' first, with CP560 CONTINUATION.md. Exact7 ModelStream owned fixture scope registered conditional on source freeze. Product native still unissued; Main ecc28/C57/originals preserved. Mixed2261 plus pending author ledger; formal0/42/all22open.\n\n'
    changes={paths[0]:(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode(),paths[1]:(json.dumps(own,ensure_ascii=False,indent=2)+'\n').encode(),paths[2]:prefix.encode()+old[paths[2]]}
    for p in paths: assert p.read_bytes()==old[p]
    for p in changes: (out/(p.name+'.before.raw')).write_bytes(old[p])
    for p,data in changes.items():
        pending=p.with_name(p.name+'.cp561.pending')
        with pending.open('xb') as f:f.write(data)
        assert p.read_bytes()==old[p];os.replace(pending,p)
    assert paths[3].read_bytes()==old[paths[3]]
    print(json.dumps({'checkpoint':561,'ownership':346,'scope_ref':ref(out/'ModelStream-exact7-fixture-scope.json'),'formal_increment':0},ensure_ascii=False))

if __name__=='__main__':main()
