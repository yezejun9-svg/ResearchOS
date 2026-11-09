import hashlib,json,traceback
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W05/W05-99'
N=P/'cli43_http_bytes_ownership_preparation_codex/310e0bf842a34df6813dad1126e2970a'
O=Path(__file__).resolve().parent
checks=[];refs={}
def pin(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();r={'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};refs[p.as_posix()]=r;return r
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def verify(r):
 p=Path(r['path']);p=p if p.is_absolute() else R/p;q=pin(p);ck('pin '+str(p),q['sha256']==r['sha256'] and q['bytes']==r['bytes']);return p
def read(p):pin(p);return json.loads(Path(p).read_bytes())
def save(n,v):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
try:
 h=read(N/'handoff.json');mf=read(N/'manifest.json')
 ck('handoff expected',pin(N/'handoff.json')['sha256']=='2f8804bade77ee6bdf5c838055709167551ce76eab5f14acfd858e19d53ed56b')
 ck('manifest expected',pin(N/'manifest.json')['sha256']=='1b6d9474904aeaafb01ce0720e890a6e368e45228330b4fbc5f9b6c7e77dbbb7')
 ck('7 distinct manifest files',len(mf['files'])==len({x['path'] for x in mf['files']})==7)
 for r in mf['files']:verify(r)
 ck('manifest complete except self',{Path(x['path']).resolve() for x in mf['files']}=={p.resolve() for p in N.iterdir() if p.is_file() and p.name!='manifest.json'})
 old=verify(h['old_helper_ref']).read_bytes();new=verify(h['helper_ref']).read_bytes()
 insertion=b'func cli43Bytes(b []byte) map[string]any{b=bytes.Clone(b);'
 original=b'func cli43Bytes(b []byte) map[string]any{'
 ck('exact one insertion',new.count(insertion)==1 and old.count(original)==1)
 ck('entire file inverse exact',new.replace(insertion,original,1)==old)
 ck('17 byte growth',len(new)-len(old)==17)
 ck('existing bytes import',b'"bytes"' in old)
 oldplan=read(verify(h['old_plan_ref']));plan=read(verify(h['instrumentation_plan_ref']))
 changed=[k for k in set(oldplan)|set(plan) if oldplan.get(k)!=plan.get(k)]
 ck('plan exact key set',set(oldplan)==set(plan))
 ck('plan only helper ref change',changed==['additional_file_ref'])
 ck('new plan helper pin',plan['additional_file_ref']==h['helper_ref'])
 test=verify(h['unchanged_instrumented_test_ref'])
 ck('instrumented assertions full bytes unchanged',pin(test)['sha256']=='37220e2a574343f7e291b41745e556d23775711d79f01cc8deb47ee1c0b19966')
 ck('plan preserves instrumented test hash',plan['instrumented_sha256']==pin(test)['sha256'])
 ck('saved inputs equal',(N/'inputs.before.json').read_bytes()==(N/'inputs.after.json').read_bytes())
 E=P/'cli43_fresh_compiler_executor_codex/bf943a8137c74df09e010347615b0eec'
 graph=read(E/'go-graph.actual.json')
 clones=[r for r in graph['all_referenced_files'] if Path(r['path']).as_posix().endswith('/src/bytes/bytes.go')]
 ck('one frozen Go bytes source',len(clones)==1)
 if len(clones)!=1:raise RuntimeError('Expected exactly one frozen bytes.go ref')
 gosource=verify(clones[0]);g=gosource.read_text(encoding='utf-8')
 clone='func Clone(b []byte) []byte {\n\tif b == nil {\n\t\treturn nil\n\t}\n\treturn append([]byte{}, b...)\n}'
 ck('actual Clone body strict',clone in g)
 lineno=g[:g.index('func Clone(')].count('\n')+1
 scope=read(P/'integration_codex/cli43-fresh-held2-r328-bf943a8137c74df09e010347615b0eec/scope_registration.json')
 runner=verify(scope['runner_ref']);rr=runner.read_text(encoding='utf-8')
 ck('strict raw digest guard retained',"need(len(b)==value['bytes'] and hashlib.sha256(b).hexdigest()==value['sha256'],'Actual body bytes/SHA')" in rr)
 # Preserve the complete prior failure closure and narrow review boundary.
 prior=P/'cli43_failed_execution_independent_review_codex/684f0c8b739541fe8da3b2f06ca78d09'
 for name in ['review.json','cause-and-minimal-correction.json','manifest.json']:pin(prior/name)
 lines=new.decode('utf-8').splitlines();calls=[{'line':i+1,'source':s} for i,s in enumerate(lines) if 'cli43Bytes(' in s]
 save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'changed_plan_keys':changed,'clone_source_ref':pin(gosource),'clone_function_lines':[lineno,lineno+5],'helper_call_sites':calls,'semantics':{'nil':'returns nil; JSON null representation preserved','nonnil_empty':'append to nonnil empty literal produces a nonnil empty slice; JSON empty base64 representation preserved','nonempty':'append to zero-capacity empty literal allocates independent backing storage and copies immediately before raw/length/SHA construction','boundary':'Write(p) is still delegated first; the snapshot is captured before this wrapper returns, under the existing io.Writer no-modification contract. No earlier socket observation is newly claimed.'},'actual_target_executions':0,'full_resource_tree_rehashed':False})
 print(json.dumps({'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'audit_ref':pin(O/'audit.json')},ensure_ascii=False))
except BaseException as e:
 save('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':checks,'input_refs':list(refs.values()),'actual_target_executions':0});raise
