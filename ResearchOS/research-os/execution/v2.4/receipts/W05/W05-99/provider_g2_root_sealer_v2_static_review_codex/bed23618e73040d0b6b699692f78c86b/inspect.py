from pathlib import Path
import ast,hashlib,json,datetime
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).resolve().parent
N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/root-g2-execute29-launch-r313'
P=R/'execution/v2.4/receipts/W05/W05-99/provider_g2_root_sealer_static_review_codex/0bce1b2d533441888f05c258d4c44319'
reads=[]
def ref(p,b=None):
 p=Path(p);b=p.read_bytes() if b is None else b
 return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):
 b=p.read_bytes();reads.append(ref(p,b));return b
def save(name,x):
 b=x if isinstance(x,bytes) else (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 with (O/name).open('xb') as f:f.write(b)
 return ref(O/name,b)
raw=read(N/'seal.v2.py'); old=read(N/'seal.py');producer=read(N/'prepare_sealer_v2.py')
assert hashlib.sha256(raw).hexdigest()=='e9438b115f1e95868e21d21e552ce775fbe024a59e0efee72e2976d4ccba88db'
assert hashlib.sha256(old).hexdigest()=='a0197b9db5637f930ccf67048d7bf92e27571a24dc5ed9225cc6b4a3f2ed238c'
for name,b in [('seal.v2.original.py',raw),('seal.v1.original.py',old),('prepare_sealer_v2.original.py',producer)]:ast.parse(b);save(name,b)
prior=read(P/'review.json'); prior_audit=read(P/'actual-read-audit.json')
save('prior-review.json',prior)
actual=json.loads(prior_audit)
grant=read(N/'authorization.execute.json');save('actual-authorization.original.json',grant)
launch=read(N/'launch.py');save('actual-launch.original.py',launch)
sample=[]
for i in range(6):
 p=P/('case-%02d-result.json'%i);b=read(p);d=json.loads(b)
 sample.append({'case':i,'saved_result_ref':ref(p,b),'shape':list(d),'native_invocation_shape':list(json.loads(read(P/('case-%02d-invocation.json'%i))))})
findings=[{'id':'V2-01','severity':'REQUIRED','lines':[66,67,75,76,87,88,97],'title':'Failure raw capture still depends on unchecked decoded JSON shape','evidence':'safe_capture returns any valid JSON value. outer/value/spec may be non-dict; a roster list member without selector causes line88 to throw outside collection try, before line97 persists failure_origin. The affected file may itself be the corrupted input responsible for stop.','minimal_change':'Persist a minimal raw failure envelope first, containing actual supplied outer exit, safe-captured outer/failure refs and no derived lookups. Normalize only interpretation (not rawbytes): dict/list/member guards; wrap all derived partition/model collection and record exceptions as diagnostics. Preserve raw JSON and unknown/null semantics. Never require valid spec/grant/current inputs to retain the original failure.'},{'id':'V2-02','severity':'REQUIRED','lines':[143,147,148,153,155,158,161],'title':'Bind current sealing grant to actual launcher invocation','evidence':'launch.py stores invocation.grant with actual authorization bytes hash. Success sealer verifies outer stdout/stderr and runner but never verifies outer.grant against current authorization.execute.json. It also omits grant candidate/work_root/output_root equality to pinned spec and fixed REPLAY.','minimal_change':'Verify outer.grant actual hash/bytes/path, require its resolved path exactly N/authorization.execute.json; require candidate/spec.candidate/prepared.source_commit equality, work/output equality to pinned spec and actual replay constants. Keep current roster and runner checks.'},{'id':'V2-03','severity':'REQUIRED','lines':[143,253],'title':'Preserve post-execution qualification failure separately from a successful controller exit','evidence':'Success-path validation is top-level with no diagnostic catch. A post-run current ref/vector mismatch produces only a new sealer traceback; it must not be reported as original controller/test failure or overwrite successful raw.','minimal_change':'Catch qualification/collection exceptions after reading actual outer outcome into a distinct immutable sealer-validation failure record and WITHHELD audit; preserve original outer/controller/native values and rawrefs. Do not create a false original G2 case failure when original outer=0. Maintain nonzero sealer exit and no retry.'}]
audit=save('audit.json',{'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_sealer_execution':False,'AST_only':True,'input_refs':reads,'previous_actual_read_audit_ref':ref(P/'actual-read-audit.json',prior_audit),'actual_structure_samples':sample,'resolved_prior_findings':['tool_exit1 dispatches to failure preservation before success qualification assertions.','Failure output reports actual MODEL total null, observed receipts lower bound, raw runner-unqualified list and observed-resumed attempts separately.','Success binds spec SHA to prepared/grant, actualexe/selector/cwd bijection, exactPASS/noSKIP, full aggregates29/4/13 and three vectors.'],'known_limits':['G2 execution remains in progress; no29 completion claimed.','Only saved/public JSON and Python text inspected.','No41958 underlying resource rehash orSQL/product/helper import.'],'new_failure_origins':[]})
review=save('review.json',{'schema':'researchos.g2-root-sealer-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REQUEST_CHANGES','reviewed_sealer_ref':ref(N/'seal.v2.py',raw),'actual_sealer_executed':False,'actual_product_executed':False,'independent_audit_ref':audit,'findings':findings,'requested_changes':[x['id'] for x in findings],'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'new_failure_origins':[]})
manifest=save('manifest.json',{'entries':[ref(p) for p in sorted(O.iterdir()) if p.is_file()],'self_excluded':True})
handoff=save('handoff.json',{'decision':'REQUEST_CHANGES','review_ref':review,'manifest_ref':manifest,'actual_execution':False,'new_failure_origins':[],'formal_increment':0})
print(json.dumps({'review':review,'manifest':manifest,'handoff':handoff},ensure_ascii=True))
