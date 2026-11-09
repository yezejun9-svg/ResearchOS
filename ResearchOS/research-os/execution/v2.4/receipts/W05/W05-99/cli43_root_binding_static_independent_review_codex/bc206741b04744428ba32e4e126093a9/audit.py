import ast,hashlib,json
from pathlib import Path
O=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os'); P=R/'execution/v2.4/receipts/W05/W05-99'
N=P/'cli43_root_binding_preparation_revision_codex/c16c5b73941e4e8a89b189594e53b4c5'
V4=P/'cli43_root_binding_preparation_revision_codex/1496044d76eb4a919217533814612807'
PR=P/'cli43_root_binding_static_independent_review_codex/f3fcbb1b93a14bf5b289082612b26a9c/review.json'
checks=[]; reads={}
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 if not v: raise RuntimeError(n)
def rd(p):
 p=Path(p); b=p.read_bytes(); k=str(p.resolve()); rr={'path':k,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if k in reads: ck('stable '+k,reads[k]==rr)
 reads[k]=rr; return b
def ref(p):rd(p); return reads[str(Path(p).resolve())]
def vr(r):
 b=rd(r['path']);ck('pin '+r['path'],len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']);return b
def doc(p):return json.loads(rd(p))
def save(n,x):
 with (O/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def refs(x):
 if isinstance(x,dict):
  if {'path','sha256','bytes'}<=set(x):vr(x)
  else:
   for v in x.values():refs(v)
 elif isinstance(x,list):
  for v in x:refs(v)
for n,h in [('handoff.json','a0bbb49f7250d8d4d9abaea9d2073ce8bd4fe8f84388a5b701b53299cd388eb6'),('manifest.json','40b166a9eed13a35f9934ec49389936902cdf4beb436d332bb061c95f4ae8799')]:ck('Rootpin '+n,ref(N/n)['sha256']==h)
h=doc(N/'handoff.json');m=doc(N/'manifest.json');ck('new MF unique25',m['count']==len(m['entries'])==len({r['path'] for r in m['entries']})==25)
refs(m);refs(h)
oldcounts=[]
for row in h['old_manifest_prefixes']:
 old=json.loads(vr(row['manifest_ref']));ck('old MF count',old['count']==len(old['entries'])==row['members']);refs(old['entries']);oldcounts.append(row['members'])
ck('old25+20+24',oldcounts==[25,20,24])
inverses=[]
for ns in [V4,N]:
 inv=doc(ns/'exact-differences-and-inverse.json')
 for change in inv['changes']:
  old=vr(change['original_ref']); new=vr(change['new_ref']); forward=old
  for e in change['edits']:
   a=e['old'].encode();z=e['new'].encode();ck('old edit exists '+change['new_ref']['path'],a in forward);forward=forward.replace(a,z)
  ck('forward exact '+change['new_ref']['path'],forward==new)
  back=new
  for e in reversed(change['edits']):
   a=e['old'].encode();z=e['new'].encode();ck('new edit exists '+change['new_ref']['path'],z in back);back=back.replace(z,a)
  ck('inverse exact '+change['original_ref']['path'],back==old);inverses.append(change['new_ref'])
meta=vr(h['metadata_pipeline_ref']).decode(); gate=vr(h['gate_ref']).decode(); builder=vr(h['binding_builder_ref']).decode();runner=vr(h['unchanged_runner_ref']).decode()
asts=[]
for r in [h['gate_ref'],h['metadata_pipeline_ref'],h['binding_builder_ref'],*h['wrapper_refs']]:ast.parse(vr(r));asts.append(r)
ck('9 target AST only',len(asts)==9)
ck('runner single raw',"raw = p.read_bytes()\n    need(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'Immutable input mismatch')\n    return raw" in runner)
ck('builder2 cached JSON',"s=strict(verified_bytes(a.scope_template_ref))" in builder and "code=strict(verified_bytes(a.metadata_code_refs_ref))['entries']" in builder)
ck('metadata native raw verified',"outputs.append(verify(item['stdout_ref']))" in meta)
for guard,nextline in [("'all-four immediately before replace CAS')","os.replace(temp,target)"),("'post-source-guard final four CAS')","save(output/'canonical-write.verified.json'"),("'post-source-guard seal four CAS')","save(output/'registration-audit.json'")]:
 lines=meta.splitlines();idx=next(i for i,s in enumerate(lines) if guard in s);ck('immediate '+guard,nextline in lines[idx+1])
ck('W05 exact identity engine+gate',"d['reviewer']=='codex:/root/w05_merge_review'" in meta and "reg_review['reviewer'] == 'codex:/root/w05_merge_review'" in gate)
grant=meta[meta.index('def grant('):meta.index('def main(')]
ordered=["pf.mkdir()","gate.validate_authority(reader,scope,scope_ref,preliminary,rr)","facts('admission')","'post-admission live four CAS'","root.mkdir()","copies=[", "gate.validate_authority(reader,scope,scope_ref,copies,rr)","facts('grant-final')","for p in sorted(pf.iterdir())", "'immediate pre-grant live four CAS'","gr=save(root/'authorization.execute.json'","gate.validate_grant(","save(root/'grant.completed.json'"]
positions=[grant.index(x) for x in ordered];ck('grant exact ordered causal stages',positions==sorted(positions))
ck('exclusive dirs before ownership',"root.mkdir()\n    OWNED_GRANT_ROOT=root" in grant and "pf.mkdir()\n    OWNED_GRANT_PREFLIGHT_ROOT=pf" in grant)
ck('copies exact raw/link',"copied_ref=write(dest,raw)" in grant and "copied[source.name]={'original_ref':original,'copy_ref':copied_ref}" in grant)
ck('five disjoint bounded roots',"len(set(roots))==5" in grant and "new_grant_preflight_root" in builder)
ck('grant immediate canon final',"'immediate pre-grant live four CAS')\n    gr=save" in grant)
ck('native NULL timing not manufactured',"'actual_stage_native_exit':None,'point_in_time_only':True" in grant)
ck('failure original newleaf only',"if OWNED_GRANT_PREFLIGHT_ROOT is not None:" in meta and "'grant_usable':False" in meta)
scope=json.loads(vr(h['scope_ref'])); oldscope=doc(V4/'scope.v4.proposed.json'); reduced=dict(scope);reduced.pop('new_grant_preflight_root');reduced['authorization_gate_ref']=oldscope['authorization_gate_ref'];ck('scope onlygate+newNULLroot',reduced==oldscope and scope['new_grant_preflight_root'] is None)
ck('no scope review SHA cycle', 'controller_review_ref' not in scope and scope['controller_review_path'] is None and "wip['cli43_fresh_compiler_controller_review_ref']" in gate and "('scope_sha256', scope_ref['sha256'])" in gate)
ck('two cases and original bounds',scope['ordered_cases']==['real-existing-open-readonly','real-existing-self-send'] and scope['limits']['cases']==2 and scope['launch_limits']['inner_soft_deadline_seconds']==3300 and scope['source_acceptance'] is False and scope['formal_increment']==0)
ck('no future grant',scope['execution_authorized'] is False and all(scope[k] is None for k in ['expected_registration','expected_before_registration','runtime_resources_ref','compiler_resources_ref','current43_authority_ref']))
ck('old430 +STCM guards preserved', 'failure_prefix430_ref' in meta and "zip(CANON[2:]," in meta if 'zip(CANON[2:],' in meta else 'failure_prefix430_ref' in meta and "CANON[2:]" in meta)
ck('prior review pin',ref(PR)['sha256']=='3ec092da679105198c872c001560d3d5576b47f430aea143a453565f51c1eaa4')
for r in list(reads.values()):vr(r)
summary={'checks':len(checks),'failed':sum(not x['passed'] for x in checks),'read_files':len(reads),'new_manifest_members':25,'old_manifest_members':69,'whole_file_inverse_pairs':len(inverses),'AST_modules':9,'target_imports_or_execution':0,'source_canonical_index_mutations':0}
save('audit.json',{'checks':checks,'input_refs':list(reads.values()),'inverse_pairs':inverses,'summary':summary})
save('review.json',{'schema':'researchos.cli43-root-binding-preparation-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'PREPARATION_STATIC_REVIEWED_WITH_FUTURE_ROOT_BINDING_REQUIRED','requested_changes':[],'actual_template_execution':False,'actual_registration_executed':False,'execution_authorized':False,'source_acceptance':False,'formal_increment':0,'input_handoff_ref':ref(N/'handoff.json'),'input_manifest_ref':ref(N/'manifest.json'),'prior_request_review_ref':ref(PR),'gate_ref':h['gate_ref'],'scope_ref':h['scope_ref'],'metadata_pipeline_ref':h['metadata_pipeline_ref'],'binding_builder_ref':h['binding_builder_ref'],'runner_ref':h['unchanged_runner_ref'],'launcher_ref':h['unchanged_launcher_ref'],'audit_ref':ref(O/'audit.json'),'closed_findings':[{'id':'CLI43-BIND-01','facts':'Runner consumes one validated raw buffer; builder parses both JSON inputs from its checked immutable cache; metadata consumes verified stdout refs. Full v4 inverse verifies only those changes.'},{'id':'CLI43-BIND-02','facts':'Engine300/307/344 checks all four bytes immediately before replacement/verified/seal-audit, after retained long guards. Existing per-replace check remains intact.'},{'id':'CLI43-BIND-03','facts':'Engine362 owned preflight ->376 sealed authority/live4 ->401 actual admission Git ->402 live4 ->409 exclusive auth create ->429 exact original-byte copies ->431 copied authority ->432 new final Git ->440 raw fact copies with original references ->447 immediate live4 ->448 grant. Original timestamps/raw references and native nullable facts retained; grant.completed and actual successful outer completion still required.'},{'id':'CLI43-BIND-04','facts':'Gate212 and metadata274 require exact codex:/root/w05_merge_review registration reviewer, with existing schema/decision/tuple/script/copies guards retained.'}],'reuse_statement':'Unchanged prior REQUEST3 fixes, acyclic full-scope review chain and producer behavior are reused from sealed reviews. Current review independently verifies v4/v5 whole-byte inverse and all69 old manifest members plus25 new members. No target execution, fresh compiler graph, resource34311/runtime1213 rehash or product qualification claimed.','limitations':['Preparation templates are not an execution grant. Actual Root tuple/cut/origins/resources/source authority and all5 fresh roots remain required.','New actual bound scope/controller/launcher/gate must receive independent static review; then emitted registration scripts/prepared/audit/desired4 need independent CAS review before execution.','Outer producer success, completed proof and immutable manifests are prerequisites for separate once-only launcher. A directory, copied facts or partial authorization.execute.json is insufficient.','Python/module observations are point-in-time. Root sole-writer lease is still needed for residual filesystem races; multi-file CAS is not atomic.','Original430 prefix/11 deletions/empty index/STCM and2-case limits preserved by unchanged guards. No actual canonical/source/HEAD observation was refreshed this turn.','HTTP observed128 is a qualification bound; unobserved client outbound hardcap remains NULL. Combined43 product acceptance/wholeCLI/held results/formal remain open.'],'checks_summary':summary,'new_failure_origins':[],'writer_status':'STOPPED'})
print(json.dumps({'output':str(O),'review':ref(O/'review.json'),'summary':summary},ensure_ascii=False))