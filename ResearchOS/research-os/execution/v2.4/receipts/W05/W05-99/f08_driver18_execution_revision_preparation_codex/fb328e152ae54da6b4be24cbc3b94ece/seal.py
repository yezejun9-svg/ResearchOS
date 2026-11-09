import ast,hashlib,json
from pathlib import Path
N=Path(__file__).parent
def pin(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
    with (N/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
ast.parse(Path(__file__).read_bytes())
inputs=json.loads((N/'inputs.after.json').read_bytes())
for r in inputs:
    if pin(Path(r['path']))!=r:raise RuntimeError('INPUT_DRIFT')
scope=json.loads((N/'scope.UNBOUND.v3.proposed.json').read_bytes())
save('tool-observations.json',{'reads':[{'chunk':'3f1cf1','outer_exit':0,'native_exit':None},{'chunk':'f89b45','outer_exit':0,'native_exit':None},{'chunk':'598436','outer_exit':0,'native_exit':None},{'chunk':'407dc4','outer_exit':0,'native_exit':None}],'pure_IO_AST_preparation':{'chunk':'b5dab2','outer_exit':0,'python_native_exit':0,'invocation_ref':pin(N/'prepare.invocation.json'),'stdout_ref':pin(N/'prepare.stdout.raw'),'stderr_ref':pin(N/'prepare.stderr.raw')},'candidate_executed':False,'new_failure_origins':[]})
save('handoff.json',{'schema':'researchos.driver18-controller-tail-revision-handoff.v1','actor':'codex:/root/command_queue_impl','status':'PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','writer_status':'STOPPED','controller_ref':scope['controller_ref'],'scope_ref':pin(N/'scope.UNBOUND.v3.proposed.json'),'launcher_ref':scope['launcher_ref'],'original_v2_controller_ref':next(r for r in inputs if Path(r['path']).name=='driver18_controller.v2.proposed.py'),'request_ref':next(r for r in inputs if Path(r['path']).name=='REVIEW.md'),'original_review_handoff_ref':next(r for r in inputs if '2e6aada' in r['path'] and Path(r['path']).name=='handoff.json'),'audit_ref':pin(N/'static-audit.json'),'inverse_ref':pin(N/'exact-transform.json'),'diff_ref':pin(N/'controller.diff'),'tool_observations_ref':pin(N/'tool-observations.json'),'changes':'Exactly one tail insertion after all result/manifest IO, immediately before prior success/failure return. Expired completion emits raw stderr FINAL_RETURN with original first_cause and native NULL, and returns1; existing sealed output is never rewritten.','unchanged':'Entry catch fix, all calls and caps32/600/750/3300/3600/5, I16/I18 body, I17 OPEN_NOT_AUTHORIZED, resource/authority NULL, original launcher.','proof':'One exact byte replacement inverse restores9d1dc8; removing only new tail AST restores whole prior AST.','future_tests':'ALL_NOT_RUN','target_calls':0,'new_failure_origins':[],'source_acceptance':False,'actual_grant':False,'old_sources_receipts_canonical_modified':False,'limitations':['This is source preparation, not actual bounded runtime evidence.','Readers must require actual controller exit and captured raw stderr; previously written qualified/result files cannot override tail failure.','Synchronous evidence IO is not interrupted by this guard; unchanged outer owned Job limit remains required.']})
files=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
save('manifest.json',{'schema':'researchos.immutable-preparation-manifest.v1','files':files,'count':len(files),'excluded_only_self':True})
print(json.dumps({'handoff':pin(N/'handoff.json'),'manifest':pin(N/'manifest.json'),'listed':len(files)},ensure_ascii=False))
