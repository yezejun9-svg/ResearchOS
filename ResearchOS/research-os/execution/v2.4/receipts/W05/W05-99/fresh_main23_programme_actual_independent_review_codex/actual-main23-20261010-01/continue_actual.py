"""Continue only uncompleted trace/authority checks after retained successful prefix."""
from pathlib import Path
import ast,copy,datetime,hashlib,json,ntpath,types,traceback,re
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
D=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def save(n,x):
 p=N/n
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
q=types.ModuleType('review_checks');exec(compile((N/'review_checks.py').read_bytes(),str(N/'review_checks.py'),'exec'),q.__dict__)
def refs_in(x):
 if isinstance(x,dict):return [x] if set(x)==q.REF_KEYS else [r for v in x.values() for r in refs_in(v)]
 if isinstance(x,list):return [r for v in x for r in refs_in(v)]
 return []
checked=[]
def need(ok,label):q.need(ok,label);checked.append(label)
pr=pin(N/'actual-review-checks.json');prefix=q.doc(pr);pg=q.doc(prefix['guard_ref']);q.clean_guard(pg)
need(pr['sha256']=='b2e73dfc5cf1503ae42a60e5109f740787ccf08e8c99ca19255c0b1372c79632' and prefix['error']['message']=='TRACE_USES_OFFICIAL_LINKER','EXACT_SUCCESSFUL_PREFIX_BOUND')
meta=q.doc(pin(N/'actual-metadata-observation.json'));state=q.doc(meta['builder_state_ref']);caller=q.doc(meta['caller_return_ref']);contract=q.doc(state['contract_ref']);actual=q.doc(meta['actual_request_ref']);request=q.doc(state['request_ref'])
sealref=pin(D/'main23.v4.actual.complete-hostpair-seal-v2.root.json');seal=q.doc(sealref);vector=q.doc(seal['current_canonical_observation_ref']);scope=q.doc(actual['scope_ref']);facts=q.doc(actual['facts_ref']);runtime=q.doc(actual['runtime_qualification_ref']);reg=q.doc(scope['registration_request_ref'])
owner=q.doc(facts['owner_ref']);worker=q.doc(facts['worker_ref']);pending=q.doc(reg['pending_ref']);activation=q.doc(actual['registration_result_ref'])
result=prefix['result'];metadata=[pr,prefix['guard_ref'],pin(__file__),pin(N/'review_actual.py'),meta['builder_state_ref'],meta['caller_return_ref'],meta['actual_request_ref'],state['contract_ref'],sealref,actual['runtime_qualification_ref'],state['calls'][3]['stderr_ref']]
metadata+=refs_in(seal)+refs_in(scope)+refs_in(facts)+vector['archive_refs']+runtime['resource_refs']+[runtime['caller_ref'],reg['pending_ref']]
canonical_paths={q.canonical(r['path']) for r in actual['current_canonical_refs']};allrefs={q.canonical(r['path']):r for r in metadata if q.canonical(r['path']) not in canonical_paths}
gm=types.ModuleType('guard');exec(compile(q.exact(contract['source_guard_ref']),contract['source_guard_ref']['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=256*1024*1024);error=None
try:
 guard.acquire(list(allrefs.values()))
 trace=q.exact(state['calls'][3]['stderr_ref']).decode();linkline=next(x for x in trace.splitlines() if x.startswith("GOROOT='' ") and 'link.exe' in x)
 quoted=re.match(r"GOROOT='' (\"(?:\\.|[^\"])*\")",linkline).group(1)
 linker=json.loads(quoted)
 need(q.canonical(linker)==q.canonical(ntpath.join(contract['goroot'],'pkg/tool/windows_amd64/link.exe')),'GO_TRACE_QUOTED_LINKER_EXACT_OFFICIAL_INPUT')
 need(q.canonical(linker) in {q.canonical(x['path']) for x in pg['entries']},'LINKER_COVERED_BY_SUCCESSFUL_FULL_INPUT_GUARD')
 # Execute only the still-uncompleted audit/lease tail of the retained review source.
 tree=ast.parse((N/'review_actual.py').read_bytes());block=next(x for x in tree.body if isinstance(x,ast.Try))
 start=next(i for i,x in enumerate(block.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='audits' for t in x.targets))
 tail=block.body[start:]
 # Last statement reports factual counts whose original inputs are retained in prefix.
 tail=tail[:-1]
 exec(compile(ast.fix_missing_locations(ast.Module(body=tail,type_ignores=[])),str(N/'review_actual.py')+'#uncompleted-tail','exec'),globals())
 old=[q.doc(r) for r in facts['before_archive_refs']];new=[q.doc(r) for r in vector['archive_refs']]
 subtasks_before=old[1]['card_path_bindings']['W05-99']['subtasks'];subtasks_after=new[1]['card_path_bindings']['W05-99']['subtasks'];added=set(subtasks_after)-set(subtasks_before)
 need(len(added)==1,'ONE_NEW_REGISTERED_BUILD_OWNER')
 key=next(iter(added));source=q.exact(runtime['caller_ref']).decode();ct=ast.parse(source)
 funcs=[n for n in ct.body if isinstance(n,ast.FunctionDef) and n.name in ('encoded','projection')]
 env=dict(copy=copy,json=json,hashlib=hashlib,need=need,KEY=key,SLICE=scope['slice_id'],ROOT='codex:/root')
 exec(compile(ast.fix_missing_locations(ast.Module(body=funcs,type_ignores=[])),runtime['caller_ref']['path']+'#pure-projection','exec'),env)
 cp,ow=env['projection'](old[0],old[1],actual['scope_ref'],facts['owner_ref'],facts['worker_ref'],actual['facts_ref'],owner,worker,pending,reg['created_utc'])
 need(cp==new[0] and ow==new[1] and old[2:]==new[2:],'EXACT_PURE_REGISTRATION_TRANSFORM_NO_OTHER_CANON_CHANGE')
 task=subtasks_after[key];workers=[x for x in new[0]['workers'] if x.get('slice_id')==scope['slice_id']]
 need(len(workers)==1,'ONE_CANON_WORKER')
 for row in [owner,worker,task,workers[0]]:
  need(row['owner']=='codex:/root' and row['state']=='ROOT_REGISTERED_PENDING_FRESH_MAIN23_BUILD' and row['lease_status']=='ACTIVE' and row['scope_ref']==actual['scope_ref'] and row['lease_expires_at']==scope['lease_expires_at'] and row['output_root']==scope['output_root'],'ACTUAL_OWNER_WORKER_SCOPE_EXACT')
 need(activation['mode']=='activate' and activation['complete_inverse'] is True and activation['SS_CM_unchanged'] is True and activation['formal_acceptance'] is False,'ROOT_ACTIVATION_TRANSACTION_BOUND')
 for x,y in zip(activation['proposed_after_refs'],actual['current_canonical_refs'][:2]):need(q.ref_key(x)==q.ref_key(y),'ACTIVATION_EXACT_AFTER_PIN')
 cg=caller['source_guard_cleanup'];q.clean_guard(cg);cgs={q.ref_key(x) for x in cg['entries']}
 need(cg['failure'] is None and all(x['verified'] is True and x['closed'] is True and x['final_path_match'] is True for x in cg['entries']),'EVERY_CALLER_RESOURCE_GUARD_ENTRY_VERIFIED_CLOSED')
 need(all(q.ref_key(x) in cgs for x in runtime['resource_refs']),'ALL_QUALIFIED_RUNTIME_RESOURCES_HELD_BY_ACTUAL_CALLER')
 need(q.ref_key(runtime['caller_ref']) in cgs and q.ref_key(contract['builder_ref']) in cgs and q.ref_key(actual['runtime_qualification_ref']) in cgs,'CALLER_BUILDER_RUNTIME_QUALIFICATION_ACTUALLY_HELD')
 sourcecall=start['call']['payload']['input'];actualref=meta['actual_request_ref']
 need(actualref['sha256'] in sourcecall and str(actualref['bytes']) in sourcecall and 'ROOT_ACTUAL_MAIN23_BUILD:'+request['case_id'] in sourcecall and "'execute'" in sourcecall,'ACTUAL_ROOT_CALL_EXACT_REQUEST_CASE_AND_OPERATION')
 need(runtime['python_ref']['path'].replace('\\','/') in sourcecall.replace('\\\\','/'),'ACTUAL_ROOT_CALL_QUALIFIED_PYTHON')
 need(runtime['caller_ref']['path'].replace('\\','/') in sourcecall.replace('\\\\','/'),'ACTUAL_ROOT_CALL_EXACT_REVIEWED_CALLER')
 result.update(program_ref=state['program_ref'],source_refs=contract['current_main_source_refs'],root_actual_request_ref=meta['actual_request_ref'],root_complete_hostpair_seal_ref=sealref,original_process_stdout_complete=False,original_API_truncation_preserved=True,original_API_reconstructed=False,Root_binding_required=True,programme_qualification='QUALIFIED_CURRENT_MAIN23_BUILD_PENDING_ROOT_BINDING',root_authority_archive_transform_verified=True,qualified_runtime_actually_held=True)
except BaseException as e:error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
finally:closed=guard.close()
gr=save('actual-review-tail-Source-guard.closed.json',closed);q.clean_guard(closed)
out=save('actual-review-tail-checks.json',dict(status='INDEPENDENT_ACTUAL_PROGRAMME_REVIEW_PASSED' if error is None else 'REVIEW_DIAGNOSTIC_FAILURE',prefix_ref=pr,prefix_guard_ref=prefix['guard_ref'],prefix_successful_check_count=prefix['check_count'],checks=checked,error=error,result=result,guard_ref=gr,held_ref_count=len(allrefs),formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(report_ref=out,guard_ref=gr,checks=len(checked),error=error,result=result),ensure_ascii=False),flush=True)
if error:raise SystemExit(1)
