"""Read-only v8 Source controls; this script never imports or runs the trial."""
import ast, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
OUT = Path(__file__).resolve().parent
SDK = ROOT / 'execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d'
V4 = SDK / 'actual-go-validation-v4-mu-cancel'
OLD = ROOT / 'execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v7_source_codex/73cdde53fe0e4da2ae29fb6898d4b7ef/mu_sdk_trial.v7.final.proposed.py'
NEW = OUT / 'mu_sdk_trial.v8.proposed.py'

def read(p): return p.read_bytes()
def doc(p): return json.loads(read(p))
def pin(p):
    raw = read(p)
    return {'path': p.as_posix(), 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}
def same_bytes(ref, p):
    actual = pin(p)
    assert actual['sha256'] == ref['sha256'] and actual['bytes'] == ref['bytes']

def main():
    old, new = ast.parse(read(OLD)), ast.parse(read(NEW))
    oldf = {x.name:x for x in old.body if isinstance(x, ast.FunctionDef)}
    newf = {x.name:x for x in new.body if isinstance(x, ast.FunctionDef)}
    changed = [k for k in oldf if ast.dump(oldf[k]) != ast.dump(newf[k])]
    assert len(oldf) == len(newf) == 40 and changed == ['validate_input']
    def value(tree, name):
        return ast.literal_eval(next(x.value for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id==name for y in x.targets)))
    limits = {k:value(new,k) for k in ('MAX_PROVIDER_REQUESTS','MAX_OUTPUT_TOKENS_TOTAL_REQUESTED','MAX_OUTPUT_TOKENS_PER_REQUEST','MAX_WALL_SECONDS')}
    assert limits == {'MAX_PROVIDER_REQUESTS':3,'MAX_OUTPUT_TOKENS_TOTAL_REQUESTED':8192,'MAX_OUTPUT_TOKENS_PER_REQUEST':2730,'MAX_WALL_SECONDS':300}
    assert all(value(old,k)==v for k,v in limits.items())
    assert value(old,'PHASE_BASIS_KEYS') == value(new,'PHASE_BASIS_KEYS')
    template, commit, prep, cancel = (doc(OUT/'input.v8.template.json'), doc(SDK/'owned-git-five-go-commit/commit.closed.json'), doc(SDK/'preparation.json'), doc(V4/'cancel.validation.closed.json'))
    assert value(new,'SOURCE_COMMIT') == template['source_commit'] == commit['new_head'] == 'adc460c2138528f163f7fdab5e8d81dde157b7fb'
    assert commit['old_head'] == 'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7' and commit['owned_git_operations'] == 17 and commit['canonical_unchanged']
    assert commit['files'] == [x['target'] for x in prep['mapping']]
    five = []
    for row in prep['mapping']:
        p = ROOT/row['target']; same_bytes(row['prepared_ref'],p); five.append(pin(p))
    same_bytes(template['cancel_fixture_receipt'],V4/'cancel.validation.closed.json')
    assert template['maximum_provider_requests']==3 and template['qualification_requests']==1 and template['ordinary_requests']==2 and template['requested_output_tokens_total']==8192 and template['total_wall_seconds']==300
    assert cancel['schema']=='researchos.mu-sdk-local-cancel-validation.v1' and cancel['case_id']=='TestRuntimeMuTypedCancelStopsTransport'
    assert cancel['native_exit']==0 and cancel['actual_external_provider_requests']==0 and cancel['local_fixture_requests']==1 and cancel['canonical_unchanged'] and cancel['formal_acceptance_delta']==0
    invocations = []
    for row in cancel['invocation_refs']:
        p=Path(row['path']);same_bytes(row,p);invocations.append(doc(p))
    assert len(invocations)==2
    assert all(x['actual_native_exit']==x['result']['actual_exit']==0 and x['result']['job_cleanup']['job_idle_confirmed'] and x['result']['job_cleanup']['handles_closed'] for x in invocations)
    same_bytes(cancel['bundle_ref'],Path(cancel['bundle_ref']['path']))
    meta=doc(Path(cancel['bundle_metadata_ref']['path']));intent=doc(V4/'mu-bundle-build.intent.json')
    assert meta['bundle_sha256']==cancel['bundle_ref']['sha256'] and meta['bundle_bytes']==cancel['bundle_ref']['bytes']
    assert meta['source_sha256']==intent['worker_source_ref']['sha256']
    same_bytes(intent['worker_source_ref'],ROOT/'adapters/runtime/mu/worker.mjs')
    same_bytes(intent['build_script_ref'],ROOT/'adapters/runtime/mu/build.mjs')
    assert invocations[1]['environment']['RESEARCHOS_MU_BUNDLE']==cancel['bundle_ref']['path']
    assert invocations[1]['argv'][-2:]==['-run','^TestRuntimeMuTypedCancelStopsTransport$']
    stdout=read(Path(invocations[1]['stdout_ref']['path']))
    assert b'--- PASS: TestRuntimeMuTypedCancelStopsTransport' in stdout and b'--- SKIP:' not in stdout and b'FAIL' not in stdout
    root_io=doc(SDK/'root-validation-v4.closed.original-tool-io.json')
    assert root_io['provider_calls']==0 and root_io['terminal']['result']['exit_code']==0
    required=set()
    for node in new.body:
        if not isinstance(node,ast.FunctionDef) or node.name not in ('phase_basis','authority_binding','validate_input'): continue
        for x in ast.walk(node):
            if isinstance(x,ast.Subscript) and isinstance(x.value,ast.Name) and x.value.id=='doc' and isinstance(x.slice,ast.Constant) and isinstance(x.slice.value,str): required.add(x.slice.value)
            if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and isinstance(x.func.value,ast.Name) and x.func.value.id=='doc' and x.func.attr=='get' and x.args and isinstance(x.args[0],ast.Constant) and isinstance(x.args[0].value,str): required.add(x.args[0].value)
    assert required-set(template)=={'_expected_config_state','_sealed_phase_basis'}
    unissued=('input_basis_ref','root_registration','root_review','root_grant','owner_lease','root_checkpoint','outer_job_contract','job_probe_receipt','controller_source','controller_review','cli_binary','bootstrap_receipt')
    assert all(template[x] is None for x in unissued)
    result={'schema':'researchos.mu-sdk-v8-source-controls.v1','actor':'codex:/root/live_resource_lookup','old_runner_ref':pin(OLD),'new_runner_ref':pin(NEW),'forward_diff_ref':pin(OUT/'forward.v7-to-v8.diff'),'inverse_diff_ref':pin(OUT/'inverse.v8-to-v7.diff'),'template_ref':pin(OUT/'input.v8.template.json'),'root_commit_ref':pin(SDK/'owned-git-five-go-commit/commit.closed.json'),'root_commit_original_io_ref':pin(SDK/'root-owned-git-commit.original-tool-io.json'),'five_go_current_main_refs':five,'cancel_v4_ref':pin(V4/'cancel.validation.closed.json'),'cancel_root_original_io_ref':pin(SDK/'root-validation-v4.closed.original-tool-io.json'),'cancel_build_intent_ref':pin(V4/'mu-bundle-build.intent.json'),'cancel_bundle_ref':cancel['bundle_ref'],'cancel_bundle_metadata_ref':cancel['bundle_metadata_ref'],'worker_source_ref':intent['worker_source_ref'],'source_ast_function_count':40,'changed_function_names':changed,'limits_unchanged':limits,'phase_basis_keys_unchanged':True,'template_all_nontransient_static_doc_fields_present':True,'runtime_initialized_only_fields':['_expected_config_state','_sealed_phase_basis'],'unissued_authority_fields_null':list(unissued),'v4_test_preceded_git_commit':True,'v4_test_same_five_go_bytes_as_commit':True,'actual_external_provider_requests':0,'local_fixture_requests':1,'actual_native_exit':0,'bundle_matches_main_worker_source':True,'trial_executed':False,'source_author_provider_requests':0,'main_writes':0,'canonical_writes':0}
    path=OUT/'source-controls.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'source_controls_ref':pin(path),'checks':'PASS'},ensure_ascii=False))

if __name__=='__main__': main()
