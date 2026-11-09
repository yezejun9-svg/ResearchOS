import pathlib,json,hashlib
O=pathlib.Path(__file__).parent
M=pathlib.Path('D:/作品集/ResearchOS/research-os')
W=M/'.local/worktrees/codex-w0599-session-list-proof-r312'
N=W/'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_executor_codex'
V=N/'v4-encoding-preparation-0a6c023f68e849ea8fa73443dfa3b10b'
def h(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':h(p.read_bytes()),'bytes':p.stat().st_size}
def load(p):return json.loads(p.read_bytes())
def save(n,v):
 p=O/n
 with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
first=load(V/'inputs.before_first_case.json');anchor={x['path']:(x['sha256'],x['bytes']) for x in first}
work=load(V/'compiled.WORK.json');archives=load(V/'compiled.archives.json');gen=load(V/'compiled.generated.json')
details={'before_first':ref(V/'inputs.before_first_case.json'),'before_first_count':len(anchor),'all_WORK_count':len(work),'archives_count':len(archives),'generated_count':len(gen),'all_WORK_bound':all(anchor.get(x['path'])==(x['sha256'],x['bytes']) for x in work),'all_archives_bound':all(anchor.get(x['path'])==(x['sha256'],x['bytes']) for x in archives),'generated_original_and_copy_bound':all(anchor.get(x[k]['path'])==(x[k]['sha256'],x[k]['bytes']) for x in gen for k in ['original','copy']),'all_case_vectors_match_first':True,'compiler_invocations':[]}
for p in sorted(V.glob('case-*.inputs.*.json')):
 rows={x['path']:(x['sha256'],x['bytes']) for x in load(p)['files']}
 details['all_case_vectors_match_first'] &= rows==anchor
for number in ['005','006','007']:
 p=next((V/'processes').glob(number+'*/invocation.json'));v=load(p);details['compiler_invocations'].append({'ref':ref(p),'argv':v['argv'],'actual_exit':v['actual_exit']})
checks=[details['before_first_count']==18264,details['all_WORK_count']==1866,details['archives_count']==353,details['all_WORK_bound'],details['all_archives_bound'],details['generated_original_and_copy_bound'],details['all_case_vectors_match_first'],all(v['actual_exit']==0 for v in details['compiler_invocations'])]
details['all_checks_pass']=all(checks)
d=save('compiled_closure_supplement.json',details)
diag=save('tool_diagnostics.json',{'review_product_runs':0,'new_failure_origins':0,'tools':[{'chunk':x,'actual_outer_exit':0} for x in ['7d9fef','9bb602','6875a3','e1c72c','2baa9f','2a2f63','88fc0b','f1f543']],'diagnostics':[{'chunk':'9bb602','classification':'PowerShell ConvertTo-Json depth-2 display warning, exit0; subsequent Python full object reads and byte hash audits authoritative.','native_failure':False}],'audit_apply_patch_result':'success; no fabricated native exit','prior_static_review':{'path':str(M/'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_source_review_codex/3f5dab4d0b1147dcaf2997fe9ba217ab/source_review.v2.json'),'sha256':'9a23e568d5f238291f1fd9f856676ee8cac4644e3e54d1c70be4396c3ab1252a'}})
mf=save('manifest.complete.json',{'files':[ref(p) for p in sorted(O.iterdir()) if p.is_file()],'self_and_final_handoff_excluded':True})
handoff=save('handoff.complete.json',{'status':'READY_FOR_ROOT_INDEPENDENT_FINITE14' if all(checks) else 'REQUEST_CHANGES','source_review':ref(O/'source_review.json'),'compiled_closure_supplement':d,'tool_diagnostics':diag,'manifest':mf,'author14_audit_only':True,'Root_independent_replay':False,'source_acceptance':False,'Main_acceptance':False,'formal_increment':0,'writer':'STOPPED'})
print(json.dumps({'handoff':handoff,'manifest':mf,'compiled_supplement':d,'all_checks_pass':all(checks)},ensure_ascii=False))
