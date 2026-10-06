"""Retain the three actually reported independent read-only harness errors."""
from pathlib import Path
import hashlib, json
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]
AUDIT=HERE.parent/'independent-review-codex-final-20261006-61a0d2e7'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_bytes())
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def check(r):
    p=(ROOT/r['path']).resolve()
    assert p.is_relative_to(ROOT.resolve()) and sha(p)==r['sha256'],r
manifest=AUDIT/'manifest.json'; supplement=AUDIT/'static_review_and_scope.json'
assert sha(manifest)=='c00a1393891ae59f3d5ec4248b2dda74e6bd9c04d6948ebfbd9d51aa8cf55f07'
assert sha(supplement)=='ca182948a4babfacea3c2ea01fe3054121dd0d58d9e0b0ec7f9bfa909f955e87'
document=load(manifest)
assert document['status']=='PASS' and document['product_commands_executed']==0
for r in document['files']+[document['review_ref']]: check(r)
supp=load(supplement)
assert supp['status']=='PASS' and supp['reviewed_root_commit']=='a1abcc56a993823b15125f57c84e03ba9103dc4c'
result=AUDIT/'audit_result.json'; assert sha(result)=='b2ffa00c4f842ba2b1e9f45da5570f86b01970f95a719ebf552b03129baf6e27'
kinds=['C04_REPLAY_RESPONSE_SHAPE','DISPATCHER_SOURCE_PATH','GO_PARENT_LEAF_FAILURE_COUNT']
details=[
    'Original decision ID and HTTP header string true were omitted/mistyped in the reviewer expectation; corrected exact response shape. No product command was rerun.',
    'Reviewer guessed bootstrap/dispatch.py; corrected read path to actual execution/command_dispatcher/dispatch.py. No product command was rerun.',
    'Reviewer counted Go parent and leaf failure events together; corrected to5 original leaf failures with separate parent/package events. Original product failure history is unchanged.']
failures=[]
for i,(kind,detail) in enumerate(zip(kinds,details),1):
    receipt=AUDIT/f'attempt{i}_receipt.json'; source=AUDIT/f'attempt{i}_source.py'
    value=load(receipt)
    assert type(value['exit_code']) is int and value['exit_code']==1 and value['product_commands_executed']==0
    failures.append({'kind':kind,'receipt_ref':ref(receipt),'failed_script_ref':ref(source),
        'input_hash':sha(source),'resolution_ref':ref(result),'detail':detail})
with (HERE/'independent_failure_registration_codex.json').open('x',encoding='utf8',newline='\n') as stream:
    json.dump({'schema':'researchos.root-independent-harness-failure-registration.v1',
        'scope':'HISTORICAL_HARNESS_ERRORS_NOT_PRODUCT_FAILURES','failures':failures,
        'manifest_ref':ref(manifest),'independent_supplement_ref':ref(supplement),
        'timing_limit':'First2 receipts preserve real command observation windows; precise child process timestamps and separate stderr were not captured and are not invented.',
        'message_record_id_meaning':'Root-generated local retention ID; no upstream collaboration message ID was exposed.'},stream,ensure_ascii=False,indent=2)
    stream.write('\n')
print(json.dumps({'status':'PASS_ACTUAL_INDEPENDENT_DELIVERY_AND_FAILURE_REFS','harness_origins':3,'product_failures_added':0}))
