import ast,hashlib,json
from pathlib import Path
OUT=Path(__file__).parent
def ref(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
    with (OUT/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
inputs=json.loads((OUT/'inputs.before.json').read_bytes())
after=[ref(x['path']) for x in inputs]
assert inputs==after
save('inputs.sealed.after.json',after)
for p in sorted(OUT.iterdir()):
    if p.suffix=='.py':ast.parse(p.read_bytes())
scope=json.loads((OUT/'scope.v2.proposed.json').read_bytes())
contract=json.loads((OUT/'contract.v2.json').read_bytes())
assert scope['expected_runtime_observation_paths'] is None
save('tool-observations.json',{'read_ref':ref(OUT/'tool-read.original.json'),'source_construction':{'tool':'f0ff1c','actual_outer_exit':0,'explicit_PYTHON_NATIVE_EXIT':0,'candidate_calls':0},'new_failure_origins':[],'old_origins_recounted':0})
save('handoff.json',{'schema':'researchos.desktop58-authority-adapter-revision-source-handoff.v1','author':'codex:/root/command_queue_impl',
 'state':'STOPPED','decision':'SOURCE_PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','source_acceptance':False,'execution_authorized':False,
 'request_ref':contract['revision_request_ref'],'candidate_ref':ref(OUT/'authorization_adapter.v2.proposed.py'),
 'scope_proposal_ref':ref(OUT/'scope.v2.proposed.json'),'contract_ref':ref(OUT/'contract.v2.json'),
 'inverse_ref':ref(OUT/'edit.inverse.json'),'static_audit_ref':ref(OUT/'static-audit.json'),
 'change':'One hunk within validate_grant before original observation loop: explicit nonempty expected ordered paths and actual unique exact refs, cardinality/order/path/sha/size validation, plus exact prelaunch/grant ref-sequence binding. Empty/missing/NULL/duplicate/foreign observations cannot reach success return.',
 'producer_contract':'New scope.expected_runtime_observation_paths remains NULL. Root must freeze actual future paths before fullscope review/CAS, then produce real observation bytes and pin the identical selected sequence in prelaunch/grant. Path-only scope avoids a future observation-hash/fullscope cycle; no count2/3 or observation facts fabricated.',
 'preserved':'Six6ff pureIO definitions byte/AST equal;16 prior definitions unchanged; original per-observation read/hash/allowlist and success-tail bytes unchanged; controller/launcher0byte change; all budgets/cases/Root semantics unchanged.',
 'limits':'Point-in-time runtime observation only. Actual Root producer adoption, current58 CLI2 qualification, resource inputs, budget, fullscope nonauthor review, sealed CAS and grant remain OPEN.',
 'future_controls_ref':ref(OUT/'future-controls.NOT_RUN.json'),'future_controls_status':'NOT_RUN',
 'input_count':len(inputs),'input_drift':0,'inputs_before_ref':ref(OUT/'inputs.before.json'),'inputs_after_ref':ref(OUT/'inputs.sealed.after.json'),
 'new_failure_origins':[],'old_failure_origins_recounted':0,'canonical_writes':0,'product_writes':0,
 'candidate_import_Go_SQL_Node_DLL_Job_HTTP_SDK_model_calls':0,'manifest_relative_path':'manifest.json'})
files=[ref(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'schema':'researchos.source-preparation-manifest.v1','count':len(files),'entries':files,'self_excluded':True})
print(json.dumps({'handoff':ref(OUT/'handoff.json'),'manifest':ref(OUT/'manifest.json'),'candidate':ref(OUT/'authorization_adapter.v2.proposed.py'),'listed':len(files),'new_origins':0},ensure_ascii=False))
