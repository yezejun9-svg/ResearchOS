import ast, hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
BASE = ROOT / 'execution/v2.4/receipts/W05/W05-99'
OUT = Path(__file__).resolve().parent
def pin(path):
    raw = Path(path).read_bytes()
    return {'path':str(Path(path)), 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}
def write(name, obj):
    with (OUT/name).open('xb') as f:
        f.write((json.dumps(obj, ensure_ascii=False, indent=2)+'\n').encode())
    return pin(OUT/name)
review_path = BASE/'mu_sdk_controller_v7_observer_v4_independent_review_codex/3b202e893cb948ee83e27c14821195a2/independent-source-review.json'
assert pin(review_path)['sha256'] == 'bbbd98631391ab8186c6b03855f165a4ef205c1a6fea13a8b2fa5e9b5793963b'
review = json.loads(review_path.read_bytes())
fixed = {key:review[key+'_source_ref'] for key in ('controller','observer','hooks','runner','phase_worker','cleanup_producer')}
fixed['python_binary'] = review['python_binary_ref']
fixed['controller_review'] = pin(review_path)
names = {'canonical_transactions.py':'canonical_transactions','job_deadline_watchdog.py':'job_watchdog','source_read_guard.py':'source_guard','windows_owned_process.py':'base_owned','held_job_cleanup_producer.py':'cleanup_producer'}
for ref in review['additional_dependencies']:
    fixed[names[Path(ref['path']).name]] = ref
sdk = BASE/'sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d'
fixed['cli_binary'] = pin(sdk/'actual-go-validation-v3-fixtures/researchos.exe')
assert fixed['cli_binary']['sha256'] == '8098a45bcb7a5e8f4ca84738f99c985f417fcf37dcea49b2ca7f658c7a832c7d'
fixed['control_binary'] = pin(sdk/'actual-go-validation-v3-fixtures/researchos-control.exe')
assert fixed['control_binary']['sha256'] == '260e04d14beaac2ac87d581fe92a242b8aca33538484dffa779782f246476d05'
hostreview = BASE/'mu_sdk_trusted_host_revision_independent_review_codex/d2c9c1d21580433e9755969fe1f283ca'
fixed['trusted_host_review'] = pin(hostreview/'REVIEW.md')
fixed['trusted_host_compile_review'] = pin(hostreview/'compile-evidence-review.json')
evidence = json.loads((hostreview/'compile-evidence-review.json').read_bytes())
fixed['trusted_host_binary'] = next({k:r[k] for k in ('path','sha256','bytes')} for r in evidence['files'] if r['path'].endswith('/trusted-qualification-host.exe'))
fixed['node_binary'] = pin(Path('C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe'))
assert fixed['node_binary']['sha256'] == '5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
fixed['cancel_receipt'] = pin(sdk/'actual-go-validation-v4-mu-cancel/cancel.validation.closed.json')
cancel = json.loads(Path(fixed['cancel_receipt']['path']).read_bytes())
fixed['mu_bundle'] = cancel['bundle_ref']
hs = BASE/'mu_sdk_trusted_qualification_host_source_revision_codex/797a5659dec64d55a16915d1aea6e46c'
for name in ('main.go','execute.go','hostapi.go','prepare.go'):
    fixed['trusted_host_'+name.replace('.','_')] = pin(hs/name)
checked=[]
for role, ref in fixed.items():
    current=pin(ref['path'])
    assert current == ref, role
    checked.append({'role':role,'ref':ref,'matches':True})
fixed_ref=write('fixed-pins.json', fixed)
source_ref=pin(OUT/'root_coordinator.py')
placeholder={'path':'ROOT_MUST_SUPPLY_ACTUAL_ABSOLUTE_PATH','sha256':'ROOT_MUST_SUPPLY_EXACT_SHA256','bytes':0}
base={'schema':'researchos.root-sdk-coordinator-input.v1','mode':'NO_PROVIDER','coordinator_source_ref':source_ref,'fixed_pins_ref':fixed_ref,'bootstrap_result_ref':placeholder,'bootstrap_lifecycle_ref':placeholder,'bootstrap_guard_cleanup_ref':placeholder,'output_dir':'ROOT_MUST_SUPPLY_FRESH_ABSOLUTE_RECEIPTS_SUBDIRECTORY','public_environment':{'SystemRoot':'C:/Windows','WINDIR':'C:/Windows','PATH':'C:/Windows/System32;C:/Windows'}}
write('input.no-provider.template.json',base)
model={**base,'mode':'MODEL_TRIAL','root_execution_authority_ref':placeholder,'host_seed_ref':placeholder,'intake_review_ref':placeholder,'public_route_manifest_ref':placeholder,'parent_checkpoint_ref':placeholder,'parent_ownership_ref':placeholder,'ordinary_prompt':'Read evidence.txt using the read tool, then quote its complete witness text in a short reply.'}
write('input.model-trial.template.json',model)
write('root-execution-authority.template.json',{'schema':'researchos.root-sdk-coordinator-execution-authority.v1','actor_id':'codex:/root','approved':False,'mode':'MODEL_TRIAL','coordinator_source_ref':source_ref,'input_basis_sha256':'SHA256_OF_CANONICAL_INPUT_WITHOUT_root_execution_authority_ref','maximum_provider_requests':3,'requested_output_tokens_total':8192,'total_wall_seconds':300})
write('independent-source-review.template.json',{'schema':'researchos.root-sdk-coordinator-source-review.v1','actor_id':'INDEPENDENT_NONAUTHOR_REQUIRED','decision':'PENDING_REVIEW','source_ref':source_ref,'fixed_pins_ref':fixed_ref,'formal_acceptance':False,'execution_authority':False})
write('input-intake.json',{'checked':checked,'input_drift':0,'source_ref':source_ref,'candidate_imports':0,'candidate_native':0,'provider_calls':0,'Main_or_canonical_writes':0})
print(json.dumps({'source_ref':source_ref,'fixed_pins_ref':fixed_ref,'fixed_roles':len(fixed),'input_drift':0,'candidate_executions':0}))
