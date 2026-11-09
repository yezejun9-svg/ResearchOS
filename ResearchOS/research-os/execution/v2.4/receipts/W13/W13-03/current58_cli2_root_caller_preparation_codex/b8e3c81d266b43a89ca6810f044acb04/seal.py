import ast,hashlib,json
from pathlib import Path
OUT=Path(__file__).parent
def ref(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
    with (OUT/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
inputs=json.loads((OUT/'inputs.before.json').read_bytes())
assert inputs==[ref(x['path']) for x in inputs]
save('inputs.sealed.after.json',[ref(x['path']) for x in inputs])
for p in OUT.glob('*.py'):ast.parse(p.read_bytes())
save('handoff.json',{'schema':'researchos.current58-cli2-root-caller-source-handoff.v1','author':'codex:/root/command_queue_impl',
 'state':'STOPPED','decision':'SOURCE_PREPARATION_REPORTED_PENDING_ROOT_REVIEW','candidate_executed':False,'source_acceptance':False,
 'caller_ref':ref(OUT/'root-launch-once.current58.proposed.py'),'contract_ref':ref(OUT/'contract.json'),
 'inverse_ref':ref(OUT/'edits.inverse.json'),'static_audit_ref':ref(OUT/'static-audit.json'),'tool_observations_ref':ref(OUT/'tool-observations.json'),
 'change':'Five finite hunks: fixed r334 scope input path/SHA; actual grant SHA and fresh Root output directory are mandatory argv; exact e2 source and original launch limits guard. Full original result/try/except/finally/exit tail and helper functions unchanged.',
 'execution_boundary':'Root expressly confirmed original subprocess.run3900 caller retained; caller_OS_lifecycle_qualification=False. Actual pinned launcher OwnedJob3600 + runner3300 + cleanup5 must close in real future execution.',
 'future_grant_SHA':None,'future_Root_output_directory':None,'future_current_binding_ref':None,
 'binding':'Grant location derives exclusively from exact scope. Separate binding override unnecessary; existing launcher/gate consume actual grant/fullscope/registration facts. This caller does not grant authority.',
 'known_finally_limitation':'Original stderr.write/final print can fail after primary receipt attempt; no new fallback or claim of outer lifecycle qualification added. Original first-cause/secondary semantics preserved byte-for-byte.',
 'inputs':len(inputs),'input_drift':0,'whole_byte_inverse':True,'original_tail_equal':True,
 'Go_SQL_Node_HTTP_SDK_Model_candidate_calls':0,'new_failure_origins':[],'formal_increment':0,'manifest_relative_path':'manifest.json'})
rows=[ref(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'schema':'researchos.source-preparation-manifest.v1','count':len(rows),'entries':rows,'self_excluded':True})
print(json.dumps({'handoff':ref(OUT/'handoff.json'),'manifest':ref(OUT/'manifest.json'),'caller':ref(OUT/'root-launch-once.current58.proposed.py'),'listed':len(rows),'new_origins':0},ensure_ascii=False))
