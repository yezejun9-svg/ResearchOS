from pathlib import Path
import ast, json, hashlib, datetime, difflib
R=Path('D:/作品集/ResearchOS/research-os'); O=Path(__file__).resolve().parent
N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/root-g2-execute29-launch-r313'
P=R/'execution/v2.4/receipts/W05/W05-99/provider_g2_root_sealer_static_review_codex/0bce1b2d533441888f05c258d4c44319'
V2=R/'execution/v2.4/receipts/W05/W05-99/provider_g2_root_sealer_v2_static_review_codex/bed23618e73040d0b6b699692f78c86b'
reads={}; checks=[]
def ref(p,b=None):
 p=Path(p);b=p.read_bytes() if b is None else b
 return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):
 b=p.read_bytes();reads[p]=b;return b
def save(n,v):
 b=v if isinstance(v,bytes) else (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
 with (O/n).open('xb') as f:f.write(b)
 return ref(O/n,b)
def check(n,v):checks.append({'check':n,'ok':bool(v)})
raw=read(N/'seal.v3.py');v2=read(N/'seal.v2.py');v1=read(N/'seal.py')
check('v3 pinned bytes',ref(N/'seal.v3.py',raw)['sha256']=='3fbb01ec89ded4e0c0d9ba3032f99b597d80a50c3400cb10a9c4216ee94fcfe7' and len(raw)==20801)
check('v2 unchanged',ref(N/'seal.v2.py',v2)['sha256']=='e9438b115f1e95868e21d21e552ce775fbe024a59e0efee72e2976d4ccba88db')
check('v1 unchanged',ref(N/'seal.py',v1)['sha256']=='a0197b9db5637f930ccf67048d7bf92e27571a24dc5ed9225cc6b4a3f2ed238c')
for name,b in [('seal.v3.original.py',raw),('seal.v2.original.py',v2),('prepare_sealer_v3.original.py',read(N/'prepare_sealer_v3.py'))]:
 ast.parse(b);save(name,b)
save('v2-to-v3.diff.txt',''.join(difflib.unified_diff(v2.decode().splitlines(True),raw.decode().splitlines(True),fromfile='seal.v2.py',tofile='seal.v3.py')).encode())
prior=read(V2/'review.json');save('prior-review.json',prior)
check('v2 review pinned',ref(V2/'review.json',prior)['sha256']=='34afd1acfbeab09561e53cc7506ea24db446d699847d9fd947e5d41a78f62a0c')
tree=ast.parse(raw); funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
fn=funcs['seal_failed_execution']; first=fn.body[0]
check('failure minimal save is first statement',isinstance(first,ast.Assign) and isinstance(first.value,ast.Call) and isinstance(first.value.func,ast.Name) and first.value.func.id=='save' and first.value.args[0].value=='failure_origin.minimal.json')
fn2=funcs['seal_validation_failure']; first2=fn2.body[0]
check('validation failure minimal save first',isinstance(first2,ast.Assign) and first2.value.func.id=='save' and first2.value.args[0].value=='sealer-validation-failure.minimal.json')
text=raw.decode(); success=ast.get_source_segment(text,funcs['qualify_success'])
for n,s in [('actual grant verified',"verify(outer['grant'])"),('grant path bound',"actual_grant_path.resolve() == (OUT / 'authorization.execute.json').resolve()"),('candidate bound',"grant['candidate'] == spec['candidate'] == prepared['source_commit']"),('work bound',"Path(grant['work_root']).resolve() == Path(spec['work_root']).resolve()"),('output bound',"Path(grant['output_root']).resolve() == Path(spec['output_root']).resolve() == REPLAY.resolve()"),('counts exact',"len(qualified) == len(processes) == len(used_processes) == 29 and model == 4 and snapshots == 13")]:check(n,s in success)
runner=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/complete-public-graph-and-g2-r310/g2_replay.v4.py'
rb=read(runner);check('runner pinned',ref(runner,rb)['sha256']=='e687bd35560d4c34b4e939609b617a5d4770b4a45d51c3b132fca60a4bfa39f5');save('runner.original.py',rb)
for name in ['launch.py','authorization.execute.json']:save('actual-'+name,read(N/name))
specp=R/'execution/v2.4/receipts/W05/W05-99/provider_g2_finite_replay_preparation_codex/3ed3a3da52c3471d9ddc524897100842/execution_spec.json'
specraw=read(specp);spec=json.loads(specraw);grant=json.loads(read(N/'authorization.execute.json'));save('spec.original.json',specraw)
check('actual grant spec pin',ref(specp,specraw)['sha256']==grant['spec_sha256'])
check('roster29 model4',len(spec['roster'])==29 and sum(x['MODEL_calls'] for x in spec['roster'])==4)
check('actual grant roster matches',[x['selector'] for x in spec['roster']]==grant['roster'])
samples=[]
for i in range(6):
 resultp=P/('case-%02d-result.json'%i);invp=P/('case-%02d-invocation.json'%i)
 result=json.loads(read(resultp));inv=json.loads(read(invp));row=spec['roster'][i]
 check('saved sample %02d actual shape'%i,result['index']==i and result['selector']==row['selector'] and inv['actual_exit']==0 and isinstance(inv['result'],dict))
 samples.append({'case':i,'result_ref':ref(resultp,reads[resultp]),'invocation_ref':ref(invp,reads[invp]),'result_keys':list(result),'invocation_keys':list(inv)})
old_audit=read(P/'actual-read-audit.json')
check('all readonly inputs unchanged',all(p.read_bytes()==b for p,b in reads.items()))
failed=[c for c in checks if not c['ok']]
decision='READY_FOR_ACTUAL_POST_EXECUTION_SEAL' if not failed else 'REQUEST_CHANGES'
resolved=[{'id':'V2-01','resolution':'The immutable minimal original-failure envelope is saved before any execution JSON read/parse. safe_capture retains byte refs while recording unrepresentable JSON; dict/list/member guards and derived collection catch prevent unchecked interpretation blocking the minimal record. Observational resumed partition is explicitly not a complete process census; total MODEL stays null on failure.'},{'id':'V2-02','resolution':'Success verifies actual outer.grant hash/bytes/path against current authorization, candidate against pinned spec/prepared, work/output against fixed roots, as well as existing prepared/spec/runner/exe and unique actual process argv/cwd/selector bindings.'},{'id':'V2-03','resolution':'Success qualification/collection errors enter a distinct minimal sealer-validation failure before secondary capture. Original outer0 remains0; actual sealer exit remains null until observed externally, required nonzero1; WITHHELD takes explicit precedence over any partial positive audit. No original case failure is inferred.'}]
audit=save('audit.json',{'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'actual_sealer_executed':False,'actual_product_executed':False,'AST_only':True,'input_refs':[ref(p,b) for p,b in reads.items()],'saved_actual_structure_samples':samples,'previous_actual_read_audit_ref':ref(P/'actual-read-audit.json',old_audit),'resolved_findings':resolved,'static_success_guards':['All29 exact roster/process bijection and leaf PASS with no FAIL/SKIP; result aggregates equal original records.','Prepared41958 exact subset of before-first; before/nativeafter/fixtureafter each equal frozen observed vector; critical vectors subset.','Actual owned Job resumed/idle/primary/handles/errors and native0 required.','MODEL4 snapshot13 exact; snapshots described as VACUUM images, no original DB physical/rowid claim.','Full result/input closure remains checked only by actual later sealer; static review does not certify execution completion.'],'new_failure_origins':[]})
review=save('review.json',{'schema':'researchos.g2-root-sealer-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':decision,'reviewed_sealer_ref':ref(N/'seal.v3.py',raw),'independent_audit_ref':audit,'requested_changes':failed,'resolved_findings':resolved,'actual_sealer_executed':False,'actual_product_executed':False,'conditions':['Root waits for original G2 process/controller completion and supplies actual tool exit and original completion chunk.','Run exact reviewed source once with pinned Python isolated mode, optimization disabled, Main root cwd.','Preserve actual outer/native/sealer outcomes separately; collect outer raw if filesystem failure prevents even minimal record.','Original seal.py/v2 and all raw remain untouched; exclusive output collisions refuse rerun.','No source/Main/formal acceptance follows finite result sealing.'],'limitations':['Read-only static/AST review; no sealer import/execution, SQL, Go, Node, model or41958 underlying resource rehash.','Saved completed00..05 structures reused; running G2 output not read or modified.','Failure raw captures can contain source diagnostic strings; these are preserved observations, not independently qualified numeric outcomes.','External paid0 remains an authorized fixture-scope claim, not a new network measurement.'],'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'new_failure_origins':[]})
manifest=save('manifest.json',{'entries':[ref(p) for p in sorted(O.iterdir()) if p.is_file()],'self_excluded':True})
handoff=save('handoff.json',{'decision':decision,'review_ref':review,'manifest_ref':manifest,'actual_execution':False,'new_failure_origins':[],'formal_increment':0})
print(json.dumps({'review':review,'manifest':manifest,'handoff':handoff,'failed_checks':failed},ensure_ascii=True))
