import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
N=Path(__file__).resolve().parent;B=N.parent.parent
def pin(p):
 raw=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,x):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
checks=json.loads((N/'checks.json').read_bytes())
assert checks['failed']==0 and len(checks['checks'])==25965 and checks['input_count']==5049
for v in json.loads((N/'input-pins.json').read_bytes()):assert pin(Path(v['path']))==v,v['path']
origin=B/'integration_codex/history20-r2-five-parent-caller-root-1791521480000/postseal-h20r2-actual-original-root-tool-io.json'
with (N/'root-actual.original-tool-io.json').open('xb') as f:f.write(origin.read_bytes())
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal.json','seal.original-tool-io.json','postseal.original-tool-io.json')]
save('MF.json',{'schema':'researchos.independent-review-manifest.v1','members':members,'member_count':len(members)})
save('HDF.json',{'schema':'researchos.history20-r2-actual-independent-review.v1','status':'COMPONENT_VALIDATION_ACCEPTED_A20_TO_PLAIN21_ONLY','report_ref':pin(N/'report.md'),'manifest_ref':pin(N/'MF.json'),'checks_ref':pin(N/'checks.json'),'inputs_ref':pin(N/'input-pins.json'),'guard_ref':pin(N/'sourceguard.final.json'),'terminal_audit_ref':pin(N/'terminal-audit.json'),'actual_guard_audit_ref':pin(N/'actual-guard-audit.json'),'owned_job_audit_ref':pin(N/'owned-job-audit.json'),'scope_ref':pin(N/'scope.json'),'actual_closed_ref':pin(B/'integration_codex/history20-r2-five-parent-target-root-1791521480000/validation.closed.json'),'actual_isolation_ref':pin(B/'integration_codex/history20-r2-five-parent-isolation-root-1791521480000/isolation.ready.json'),'checks':25965,'input_count':5049,'pass':9,'fail':0,'skip':0,'parents':5,'drift_leaves':4,'root_outer_exit':0,'root_python_exit':0,'official_test2json_primary_exit':0,'separate_test_binary_descendant_exit':None,'all10_jobs_closed':True,'all7_actual_guards_closed':True,'independent_guard_closed':True,'Main_adopted':False,'Main_evidence':'8 explicit guarded files and four canonical pins; no full-repository byte-baseline claim','canonical_revision':364,'CLI_built_or_executed':False,'other54_parents_executed':False,'old914':'FAILED_IMMUTABLE','formal_acceptance':False,'W05_parent_approved':False,'originaltrial_realOwner_nineNative_formal42_full20to24':'OPEN','new_mechanical_failures':[],'actual_reviewer_Git_Go_SQL_product_native_API_private_model':False,'STOP_FINAL':True})
print(json.dumps({'HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json')}))

