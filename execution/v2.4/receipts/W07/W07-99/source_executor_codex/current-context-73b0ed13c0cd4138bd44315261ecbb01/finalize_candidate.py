from pathlib import Path
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
ROOT=Path.cwd();OUT=Path(__file__).resolve().parent
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,x):(OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
context=read(OUT/'context.json');proof=read(ROOT/context['proof_ref']['path'])
receipt=read(OUT/'native-receipts/W07-G01.receipt.json')
stdout=read(ROOT/receipt['stdout']['path'])
g01_ref=stdout['product_proof_ref'];g01=read(ROOT/g01_ref['path'])
sources=read(ROOT/proof['source_before_ref']['path'])
assert len(sources)==2283
assert sources==read(ROOT/proof['source_after_ref']['path'])==read(ROOT/g01['source_before_ref']['path'])==read(ROOT/g01['source_after_ref']['path'])
assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h.removeprefix('sha256:') for n,h in sources.items())
write('native-G01-LIVE-source-equality.json',{'status':'IDENTICAL_CURRENT_2283','G01_proof_ref':g01_ref,'LIVE_proof_ref':context['proof_ref'],
 'G01_before_ref':g01['source_before_ref'],'G01_after_ref':g01['source_after_ref'],'LIVE_before_ref':proof['source_before_ref'],'LIVE_after_ref':proof['source_after_ref'],'count':len(sources)})
argv=[sys.executable,'-B','-X','utf8',str(OUT/'verify_candidate.py'),str(OUT/'context.json')]
start=datetime.now(timezone.utc).isoformat();p=subprocess.run(argv,cwd=ROOT,capture_output=True)
(OUT/'preflight.stdout').write_bytes(p.stdout);(OUT/'preflight.stderr').write_bytes(p.stderr)
write('preflight.invocation.json',{'actualargv':argv,'cwd':str(ROOT),'exit_code':p.returncode,'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),
 'stdout_ref':ref(OUT/'preflight.stdout'),'stderr_ref':ref(OUT/'preflight.stderr'),'purpose':'PRE_REGISTRATION_NO_ACCEPTANCE'})
assert p.returncode==0,p.stderr.decode()
assert read(OUT/'preflight.stdout')['status']=='PRE_REGISTRATION_NO_ACCEPTANCE'
assert all(x['status']=='PASS' for x in read(OUT/'preflight.json')['stages'])
assert read(OUT/'GLOBAL-run-receipt.json')['verifier_id']=='codex:/root/w05_merge_review'
for origin in read(OUT/'native-receipt-origins.json'):
 assert (ROOT/origin['original_ref']['path']).read_bytes()==(ROOT/origin['copied_ref']['path']).read_bytes()
handoff={'status':'PRE_REGISTRATION_NO_ACCEPTANCE','executor_id':'codex:/root/sources_parent_impl','intended_independent_verifier_id':'codex:/root/w05_merge_review',
 'context_ref':ref(OUT/'context.json'),'global_evidence_refs':context['global_evidence_refs'],'preflight_ref':ref(OUT/'preflight.json'),
 'preflight_invocation_ref':ref(OUT/'preflight.invocation.json'),'formal_vector_ref':ref(OUT/'formal-version-vector.json'),'tool_identity_ref':ref(OUT/'tool-identity.json'),
 'source_count':len(context['version_vector']['source_files']),'source_coverage_roots':len(context['source_coverage']['roots']),
 'compiled_input_count':len(sources),'compilation_missing':[],'native_LIVE_equality_ref':ref(OUT/'native-G01-LIVE-source-equality.json'),
 'proof_ref':context['proof_ref'],'native_origins_ref':ref(OUT/'native-receipt-origins.json'),'remaining':['Independent verifier review and actual GLOBAL validation','Root issuance and official registration'],
 'formal_acceptances':0,'review_issuance_created':False,'old_evidence_modified':False}
write('handoff.json',handoff)
print(json.dumps({'handoff_ref':ref(OUT/'handoff.json'),**handoff},ensure_ascii=False))
