"""Only writes the independent review receipt; never source or Git."""
from pathlib import Path
import datetime, hashlib, json

MAIN=Path('D:/作品集/ResearchOS/research-os')
RECEIPT=MAIN/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/deliverygate-integration'
REVIEW=RECEIPT/'reviews/integration-readiness.json'
CHILD=Path(__file__).resolve().parent/'deliverygate-integration-review/D-lift-readback.json'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
child=json.loads(CHILD.read_bytes())
assert sha(CHILD)=='7b3891cbb8def51397c031d0666e989e74b3af5e350ed8f38a1b5ff4ae4a85be'
assert child['decision']=='ALLOW_EXACT_TWO_FILE_SOURCE_INTEGRATION_ONLY'
assert child['protection']['prefix_unchanged'] and child['protection']['old_protected_items_preserved']==18
assert child['protection']['candidate_untracked_only_exact_two_files'] and not child['actions']['tests_rerun']
files=['scope.json','import-adaptation.json','checks-03/result.json']
evidence={name:sha(RECEIPT/name) for name in files}
child_evidence={Path(item['path']).resolve():item['sha256'] for item in child['evidence']}
assert all(evidence[name]==child_evidence[(RECEIPT/name).resolve()] for name in files)
source_paths={'implementation':'internal/deliverygate/validate.go','test':'internal/deliverygate/validate_test.go'}
candidate=MAIN/'.local/worktrees/deliverygate-primitive-20261104'
actual_source={name:sha(candidate/path) for name,path in source_paths.items()}
assert actual_source=={name:child['source_hashes'][path] for name,path in source_paths.items()}
report={
 'schema':'researchos.independent-deliverygate-integration-readiness.v1',
 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'/root/implementation_review',
 'source_readback_reviewer':'/root/implementation_review/prompt_integration_readback',
 'decision':'ALLOW_EXACT_TWO_FILE_SOURCE_INTEGRATION_ONLY',
 'base_head':'556cdc353f47167e5609f23291bf2746e3c8896f',
 'candidate':str(candidate),'receipt':str(RECEIPT),
 'source_scope':source_paths,'candidate_source_sha256':actual_source,
 'evidence_sha256':evidence,'child_readback_sha256':sha(CHILD),
 'readback':child,
 'independent_C_primitive_review':{
   'path':'C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp586-continuation/pure-scalar/reviews/source-review.json',
   'sha256':'598acb7bc0c8cc0c4f6bdb9a079d64fa5b0bbd1682abeabfa9e9f3467da38a5e',
   'new_test_run':False
 },
 'qualification':[
  'Structural pure-scalar validation primitive only: fixed Clamp signature/grammar, finite budget, actual owned source bytes, digest and defensive copy.',
  'Implementation is byte-identical to previously independently reviewed C freeze. Test differs only by module import adaptation to real internal/deliverygate.',
  'D checks03 is actual offline package evidence (10 top-level +92 subtests); this review readbacks original output and does not rerun source tests.',
  'Old checks01 missing parent and checks02 import/setup failures remain preserved. No failed attempt or global counter was reset.',
  'This does not implement trusted business suite/inventory, service binding, current Owner/root/TaskRun/lease/lineage, canonical Host facts, ArtifactUse, split Task/Goal contracts, production migration or Goal LIVE exception.',
  'No model/provider/Core/Desktop/native process is started. Ordinary Goal503 and existing API/authority remain unchanged. No formal acceptance increment.'
 ],
 'diagnostics':child.get('reviewer_diagnostics',[]),
 'operations':{'source_mutations':0,'old_db_connections':0,'native_model_runs':0,'test_reruns':0,'formal_increment':0,'counter_reset':False}
}
REVIEW.parent.mkdir(parents=True,exist_ok=True)
with REVIEW.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2,ensure_ascii=False);stream.write('\n')
print(json.dumps({'path':str(REVIEW),'sha256':sha(REVIEW),'decision':report['decision']},ensure_ascii=False))
