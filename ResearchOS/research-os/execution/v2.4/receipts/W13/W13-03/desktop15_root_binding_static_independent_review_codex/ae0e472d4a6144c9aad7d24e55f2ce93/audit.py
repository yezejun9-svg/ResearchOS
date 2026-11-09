import ast, hashlib, json
from pathlib import Path
O=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W13/W13-03'
N=P/'desktop15_root_scope_binding_preparation_codex/5097ef19e4414a81b6457363a3b76060'
OLD=P/'desktop15_root_scope_binding_preparation_codex/f2adb6bf003a47498516d95970690096'
PR=P/'desktop15_root_binding_static_independent_review_codex/743aa36608ea40829475e0128ea8992e/review.json'
checks=[]; reads={}
def check(name,value):
 checks.append({'check':name,'passed':bool(value)})
 if not value: raise RuntimeError(name)
def read(p):
 p=Path(p); b=p.read_bytes(); k=str(p.resolve()); r={'path':k,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if k in reads: check('repeat stable '+k,reads[k]==r)
 reads[k]=r; return b
def ref(p):
 read(p); return reads[str(Path(p).resolve())]
def verify(r):
 b=read(r['path']); check('pin '+r['path'],hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes']); return b
def doc(p): return json.loads(read(p))
def save(name,x):
 with (O/name).open('xb') as f: f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
for name,sha in [('handoff.json','b0e527ce2566145ea58abf33fad75502e6bc7abd4eb96ccd20beb6e10a004ad8'),('manifest.json','5e0bd37f66f9decb776db6942ada8926475f570fe9655ac63a4dc4a63d324d7c')]:
 check('Root pin '+name,ref(N/name)['sha256']==sha)
m=doc(N/'manifest.json'); check('16 unique members',m['count']==len(m['entries'])==len({r['path'] for r in m['entries']})==16)
for r in m['entries']: verify(r)
before=doc(N/'inputs.before.json'); after=doc(N/'inputs.after.json'); check('17 inputs before/after',before==after and len(before)==17)
for r in before: verify(r)
check('prior nonauthor review pin',ref(PR)['sha256']=='146b4992373d6c528cf59ae57f36c44c5289d9c5aba5e2bbf4cf9bf112bc7e32')
newb=read(N/'build-metadata-templates.py'); oldb=read(OLD/'build-metadata-templates.py')
nb=b"    b = path(r['path']).read_bytes()\n    need(hashlib.sha256(b).hexdigest() == r['sha256'] and len(b) == r['bytes'], 'ref bytes changed')\n    return b"
ob=b"    a = ref(r['path'])\n    need(a['sha256'] == r['sha256'] and a['bytes'] == r['bytes'], 'ref bytes changed')\n    return path(r['path']).read_bytes()"
check('builder only verified buffer inverse',newb.count(nb)==1 and newb.replace(nb,ob)==oldb)
ne=read(N/'metadata-engine.template.py'); oe=read(OLD/'metadata-engine.template.py')
a=b"    b = raw(r['path'])\n    need(hashlib.sha256(b).hexdigest() == r['sha256'] and len(b) == r['bytes'], 'reference drift')\n    return b"
z=b"    actual = ref(r['path'])\n    need(actual['sha256'] == r['sha256'] and actual['bytes'] == r['bytes'], 'reference drift')\n    return raw(r['path'])"
g1=b"        need(all(raw(x) == b for x, b in zip(CANON, live)), 'four canonical completed prefix drift after source guard')\n"
g2=b"    need(all(raw(q) == b for q, b in zip(CANON, target)), 'four canonical target drift after final source guard')\n"
check('engine three exact substitutions inverse',ne.count(a)==ne.count(g1)==ne.count(g2)==1 and ne.replace(a,z).replace(g1,b'').replace(g2,b'')==oe)
check('immediate all4 before replace',g1+b"        os.replace(" in ne)
check('final guard then all4 then verified',b"    source_guard(p, lock, helper, 'register-after')\n"+g2+b"    save('canonical-write.verified.json'" in ne)
check('scope exact unchanged',read(N/'build-scope.py')==read(OLD/'build-scope.py'))
asts=[]
for name in ['build-scope.py','build-metadata-templates.py','metadata-engine.template.py']:
 ast.parse(read(N/name)); asts.append(name)
for row in doc(N/'static-revision-audit.json')['mode_variants']:
 b=ne.replace(b"MODE = 'register'",('MODE = '+repr(row['mode'])).encode())
 check('mode bytes '+row['mode'],hashlib.sha256(b).hexdigest()==row['sha256'] and len(b)==row['bytes']); ast.parse(b); asts.append('mode:'+row['mode'])
check('actual nonauthor metadata identity remains exact',b"review['reviewer'] == 'codex:/root/w05_merge_review'" in ne)
s=doc(N/'revision-spec.json'); check('future authority absent',s['authorized'] is False and s['future_root_grant'] is None and s['future_tuple'] is None and s['selected_pending_origins'] is None)
check('example Rootrequest unchanged',read(N/'root-request.example.json')==read(OLD/'root-request.example.json'))
# Final actual current-read check; no target imports or execution.
for r in list(reads.values()): verify(r)
summary={'checks':len(checks),'failed':sum(not x['passed'] for x in checks),'read_files':len(reads),'new_manifest_members':16,'old_input_refs':17,'ast_parses':len(asts),'target_execution':0,'source_canonical_index_writes':0}
save('audit.json',{'checks':checks,'inputs':list(reads.values()),'summary':summary,'AST_only':asts,'target_imports':0})
review={'schema':'researchos.desktop15-root-binding-preparation-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'PREPARATION_STATIC_REVIEWED_WITH_FUTURE_ROOT_BINDING_REQUIRED','requested_changes':[], 'actual_template_execution':False,'actual_registration_executed':False,'actual_integration_executed':False,'execution_authorized':False,'source_acceptance':False,'formal_increment':0,'prior_request_review_ref':ref(PR),'input_handoff_ref':ref(N/'handoff.json'),'input_manifest_ref':ref(N/'manifest.json'),'build_scope_ref':ref(N/'build-scope.py'),'metadata_builder_ref':ref(N/'build-metadata-templates.py'),'metadata_engine_ref':ref(N/'metadata-engine.template.py'),'audit_ref':ref(O/'audit.json'),'closed_findings':[{'id':'DESKTOP-BIND-01','evidence':'Engine lines278/285: all four actual bytes checked immediately after the retained source guards and immediately before replace/verified. Original checks and two-intent/STCM logic preserved; exact three-substitution inverse equals original engine.'},{'id':'DESKTOP-BIND-02','evidence':'Both verify functions read once, hash/length-check and return that same immutable byte buffer. Existing doc/helper consumers unchanged; exact whole-file inverse established.'}], 'reuse_statement':'Prior review146b499 complete static design is reused for unchanged functions and scope. This review independently hashes16 new manifest members and17 prior input refs, performs exact whole-file inverse and7 AST parses. No fresh6983 source vector or runtime/test qualification is claimed. Prior review and its tooling failure remain unchanged.', 'conditions':['Root must supply actual tuple/cut/old failure prefix/current43 canonical4/HEAD/UUID/public resource refs; example NULL fields are not authority.','Fresh bound scope/payload/controller/launcher/new template hashes require independent review; generated actual register/run/seal/prepared/audit/desired bytes require a separate registration review.','Future outer path must preserve failure/raw/nullable exits and observe successful actual CAS, seal and grant completion before source controller. Partial grant presence is not permission.','Filesystem multi-file replacement is not atomic; Root sole-writer lease and forward-only recovery remain necessary.','Current43 validation and Desktop HEAD changes remain serial. No native/module/helper/DLL/Go/SQL/HTTP/model execution is authorized by this review.','Exact15 source import and combined58/Node independent replay/GUI/NVDA/P02/SDK/formal qualification remain separate future gates.'],'checks_summary':summary,'new_failure_origins':[],'writer_status':'STOPPED'}
save('review.json',review)
print(json.dumps({'output':str(O),'review':ref(O/'review.json'),'summary':summary},ensure_ascii=False))