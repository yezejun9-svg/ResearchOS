"""Freeze the narrow integrity patch and actual new control evidence."""
from pathlib import Path
import ast, hashlib, json
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]; CARD=HERE.parent
CONTROL=CARD/'formal_validator_codex/registration-repair-controls/runs'
def load(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def check(r):
    p=(ROOT/r['path']).resolve(); assert p.is_relative_to(ROOT.resolve()) and sha(p)==r['sha256'],r
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as stream: json.dump(v,stream,ensure_ascii=False,indent=2); stream.write('\n')
passed=CONTROL/'controls-dd45f568eefa4a978e2467defcef3646/receipt.json'
failed=CONTROL/'controls-523201990f284c369f582182574b3050/receipt.json'
assert sha(passed)=='d34cc8d0f17bed0e842f23090373672ac4d5f4f84c1f195e895c35d99d731b85'
assert sha(failed)=='e64d2be066c078a51d275ec880f6a9f6e05b9169a2d93b0f7b1e92c16e483266'
for path in (passed,failed):
    receipt=load(path)
    assert receipt['product_commands_executed']==receipt['formal_case_count_delta']==0
    for r in [receipt['stdout'],receipt['stderr'],receipt['source_snapshot_ref']]: check(r)
    snap=load(ROOT/receipt['source_snapshot_ref']['path'])
    for item in snap['sources']: check(item['snapshot_ref'])
success=load(passed)
assert success['status']=='PASS' and type(success['exit_code']) is int and success['exit_code']==0 and success['control_count']==10
assert success['source_unchanged_during_run'] and success['control_roster_complete']
for name,digest in success['source_hashes'].items(): assert sha(ROOT/name)==digest,name
old_snap=load(ROOT/load(failed)['source_snapshot_ref']['path'])
failed_script=next(item['snapshot_ref'] for item in old_snap['sources'] if item['original_ref']['path'].endswith('/test_registration_repair.py'))
save(HERE/'additional_control_failure_registration_codex.json',{'schema':'researchos.root-synthetic-control-failure-registration.v1',
    'failures':[{'kind':'REPAIR_CONTROL_LOCAL_RETURN_SHAPE','receipt_ref':ref(failed),'failed_script_ref':failed_script,
        'input_hash':failed_script['sha256'],'resolution_ref':ref(passed),'classification':'SYNTHETIC_CONTROL_HARNESS_FAILURE_NOT_PRODUCT',
        'detail':'New control test initially requested public input_hashes on local checker result; corrected to observe local Reader.finish read_hashes while calling the real finish. All5 local errors shared this single test-interface cause; public5 passed. Failed source/raw retained; changed inputs10/10 pass.'}]})
def functions(p):
    tree=ast.parse(p.read_bytes()); return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
changes=[]
for before,after in [(HERE/'validator_before_registration_repair.py',CARD/'formal_validator_codex/validate.py'),
                     (HERE/'formal_index_before_registration_repair.py',ROOT/'execution/v2.4/formal_case_index.py')]:
    old,new=functions(before),functions(after)
    assert old.keys()==new.keys()
    changed=[name for name in old if old[name]!=new[name]]; assert changed==['registered_dispatch'],changed
    changes.append({'before':ref(before),'after':ref(after),'changed_functions':changed})
save(HERE/'registration_repair_source_codex.json',{'schema':'researchos.root-registration-integrity-repair.v1',
    'status':'CHANGED_INPUT_CONTROLS_PASS_PENDING_INDEPENDENT_ROUND2','actor':'codex:/root',
    'actual_original_rejection':ref(HERE/'registration_integrity_failure_codex.json'),
    'source_changes':changes,'actual_preflight':ref(HERE/'repair_reviewed_integrity_invocation_codex.json'),
    'new_controls':ref(passed),'failed_control_retained':ref(failed),'formal_case_count_delta':0,
    'original_product_vector_changed':False,'original_review_context_raw_changed':False,
    'repeated_go_or_dispatcher':0,
    'boundary':'Dispatcher is independently pinned by the actual later native construction invocation; fixed-path reader.ref records current hash for finish/CAS. Earlier product vector and child input pins are unchanged.'})
print(json.dumps({'status':'PASS_REPAIR_INPUTS_READY_FOR_SOURCE_FREEZE','new_controls':10,'pending_failure_origins':4,'formal_accepted':0}))
