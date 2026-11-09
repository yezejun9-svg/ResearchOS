import ast,hashlib,json,os
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent
N=P/'integration_codex/cli43-fresh-held2-r325-71b091d20d94443bbf4e732d201eeb29'
reads={};checks=[]
def ck(v,n):checks.append({'check':n,'pass':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);b=p.read_bytes();reads[str(p)]=b;return b
def ref(p):
 p=path(p);b=read(p);return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def vr(r):
 b=read(r['path']);ck(hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes'],'pin '+r['path']);return b
def doc(p):return json.loads(read(p))
def rd(r):return json.loads(vr(r))
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
caller=read(N/'root-launch-once.py').decode();tree=ast.parse(caller);s=doc(N/'scope_registration.json');G=Path(s['new_authorization_root']);gr=doc(G/'authorization.execute.json');completed=doc(G/'grant.completed.json');mf=doc(G/'manifest.json')
ck(completed['grant_ref']['sha256']=='4358b6b1c494e33104aff066e4e07f12cec0b3029a95ed56f1be940500df9f7a','actual fixed grant')
vr(completed['grant_ref']);ck(completed['launcher_executions']==0 and not completed['source_acceptance'] and completed['formal_increment']==0,'grant closure no execution/source acceptance')
for r in mf['entries']:vr(r)
ck(any(path(r['path'])==G/'grant.completed.json' for r in mf['entries']),'grant completed included in sealed manifest')
inv=doc(N/'metadata-grant.invocation.json');ck(inv['actual_native_exit']==0 and inv['wrapper_error'] is None,'actual metadata grant exited0');vr(inv['stdout_ref']);vr(inv['stderr_ref'])
ck(gr['status']=='ROOT_REGISTERED_EXECUTION_AUTHORIZED' and gr['actual_registration_completed'] is True,'grant actual registered state')
can=[rd(x['ref']) for x in gr['canonical_copies']];ck([can[0]['revision'],can[1]['revision'],len(can[0]['failure_counters'])]==[325,153,442],'grant actual copied tuple')
ck(rd(gr['registration_refs']['audit'])['actual_registration_exit']==0,'sealed registration audit reports actual0')
ck(gr['scope_ref']['sha256']==ref(N/'scope_registration.json')['sha256']=='c942ced8bc4e34668e74997a1950150816ee819298e54a448b588e0e3ea2eb20','actual scope binding')
for k in ['new_output_root','new_wrapper_root','new_export_root']:ck(not os.path.lexists(s[k]),'execution leaf absent '+k)
vr(s['launcher_ref']);vr(s['python_ref'])
calls=[x for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and isinstance(x.func.value,ast.Name) and x.func.value.id=='subprocess' and x.func.attr=='run']
ck(len(calls)==1,'single subprocess call')
ck(not any(isinstance(x,(ast.For,ast.While)) for x in ast.walk(tree)),'no loop/retry')
ck(any(k.arg=='timeout' and isinstance(k.value,ast.Constant) and k.value.value==3900 for k in calls[0].keywords),'caller3900 bound')
for needle in ["'-I', '-S', '-X', 'utf8'","scope_ref['sha256'] == SCOPE_SHA","grant_ref['sha256'] == GRANT_SHA","pin(launcher['path']) == launcher","pin(PYTHON)['sha256'] == scope['python_ref']['sha256']","caller_OS_lifecycle_qualification': False","result.returncode if result else None","'counter_reset': False",".open('xb')"]:ck(needle in caller,'caller preserved guard '+needle)
ck(s['launch_limits']=={'outer_timeout_seconds':3600,'inner_soft_deadline_seconds':3300,'termination_cleanup_seconds':5},'inner limits unchanged')
finally_nodes=[x for x in ast.walk(tree) if isinstance(x,ast.Try) and x.finalbody]
ck(len(finally_nodes)==1,'one finally block')
ft='\n'.join(ast.get_source_segment(caller,x) for x in finally_nodes[0].finalbody)
ck("pin(OUT / 'root-launch.stdout.raw')" in ft and "pin(OUT / 'root-launch.stderr.raw')" in ft and not any(isinstance(x,ast.IfExp) for x in ast.walk(finally_nodes[0].finalbody[0]) if 'root-launch.stderr.raw' in ast.unparse(x)),'finally directly hashes both output files')
finding={'id':'CLI43-CALLER-01','severity':'BLOCKER','actual_execution':False,'location':'root-launch-once.py try xb open and finally save(root-launch.invocation.json)','cause':'If either xb raw-file open fails, result is still None and the first exception is recorded in error. Finally unconditionally pins both files. A missing stdout/stderr then throws before save, so the invocation is absent and a secondary FileNotFoundError masks the original failure.','minimal_fix':'New immutable caller: capture first failure, use nullable raw refs with guarded hashing, retain separate secondary receipt errors, and cover prelaunch/xb/subprocess paths within the owned attempt evidence boundary. Keep all exact pins, argv, public env, one invocation and limits unchanged. Original first cause/nativeNULL must survive even if receipt output fails; stderr fallback may report inability to write.','static_acceptance':'Inspect failure-before-start, stdout-only-created, subprocess timeout, nonzero native and successful native branches. No target execution required for this narrow revision.','native_failure_or_case_count_increment':0}
for fp,b in list(reads.items()):ck(Path(fp).read_bytes()==b,'after stable '+fp)
save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['pass']],'input_refs':[{'path':fp,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for fp,b in reads.items()],'target_execution':False,'new_failure_origins':[]})
review={'schema':'researchos.cli43-root-caller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REQUEST_CHANGES','requested_changes':[finding],'caller_ref':ref(N/'root-launch-once.py'),'scope_ref':ref(N/'scope_registration.json'),'grant_ref':completed['grant_ref'],'grant_completed_ref':ref(G/'grant.completed.json'),'grant_manifest_ref':ref(G/'manifest.json'),'metadata_grant_invocation_ref':ref(N/'metadata-grant.invocation.json'),'audit_ref':ref(O/'audit.json'),'actual_caller_execution':False,'actual_product_execution':False,'actual_registration_executed':False,'new_failure_origins':[],'status':'STOPPED'}
save('review.json',review)
save('handoff.json',{'review_ref':ref(O/'review.json'),'decision':'REQUEST_CHANGES','caller_ref':review['caller_ref'],'finding':'CLI43-CALLER-01','new_failure_origins':[],'actual_target_execution':False,'status':'STOPPED'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json'];save('manifest.json',{'entries':entries,'count':len(entries),'excluded_only_self':True})
print(json.dumps({n:ref(O/n) for n in ['review.json','manifest.json','handoff.json']},ensure_ascii=False))
