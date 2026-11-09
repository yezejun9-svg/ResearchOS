"""Independent read-only actual-build validation; no product or authority calls."""
from pathlib import Path
import ast,hashlib,json,ntpath,types,traceback,datetime
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
D=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
FB=B/'fresh_main23_programme_builder_source_codex/main23b-20261009-01'
CASE='3ef8ee61a94e4adca86a00f55a8b7a13';C=B/('integration_codex/fresh-main23-caller-'+CASE)
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def save(n,x):
 p=N/n
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def loadmodule(r,n):
 m=types.ModuleType(n);exec(compile(q.exact(r),r['path'],'exec'),m.__dict__);return m
q=types.ModuleType('review_checks');exec(compile((N/'review_checks.py').read_bytes(),str(N/'review_checks.py'),'exec'),q.__dict__)
checked=[]
def need(ok,label):
 q.need(ok,label);checked.append(label)
def refs_in(x):
 if isinstance(x,dict):
  if set(x)==q.REF_KEYS:return [x]
  return [r for v in x.values() for r in refs_in(v)]
 if isinstance(x,list):return [r for v in x for r in refs_in(v)]
 return []
contract=q.doc(pin(FB/'contract.json'));state=q.doc(pin(C/'builder-returned-state.root.json'));caller=q.doc(pin(C/'caller-return.root.json'))
actual=q.doc(state['root_context']['root_request_ref']);request=q.doc(state['request_ref'])
sealref=pin(D/'main23.v4.actual.complete-hostpair-seal-v2.root.json');need(sealref['sha256']=='fb1762e099f5d8b3a195811614a95ab571321f32b680d22b30da32533f10b300','ROOT_SEAL_PIN')
seal=q.doc(sealref);vector=q.doc(seal['current_canonical_observation_ref']);scope=q.doc(actual['scope_ref']);facts=q.doc(actual['facts_ref']);runtime=q.doc(actual['runtime_qualification_ref'])
leaf=loadmodule(contract['builder_ref'],'independent_main23_leaf');base=loadmodule(contract['base_helper_ref'],'independent_base');gm=loadmodule(contract['source_guard_ref'],'independent_source_guard')
original=q.doc(state['source_before_ref'])['refs'];frozen=q.doc(state['frozen_before_ref'])['refs'];cache=q.doc(state['cache_after_build_ref'])['refs'];work=q.doc(state['retained_build_work_ref'])['refs'];manifest=q.doc(contract['input_manifest_ref'])
metadata=[pin(__file__),pin(N/'review_checks.py'),pin(FB/'contract.json'),sealref,pin(C/'builder-returned-state.root.json'),pin(C/'caller-return.root.json')]
metadata+=refs_in(state)+refs_in(seal)+refs_in(scope)+refs_in(facts)+[actual['runtime_qualification_ref'],runtime['caller_ref']]+vector['archive_refs']
# Historical canonical identities are verified through immutable archives, not recursively traversed.
canonical_paths={q.canonical(r['path']) for r in actual['current_canonical_refs']}
allrefs={}
for r in metadata+original+frozen+cache+work:
 if q.canonical(r['path']) in canonical_paths:continue
 key=q.canonical(r['path'])
 need(key not in allrefs or q.ref_key(allrefs[key])==q.ref_key(r),'CONSISTENT_REF_'+str(len(allrefs)))
 allrefs[key]=r
guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=1024*1024*1024)
error=None;result=None
try:
 guard.acquire(list(allrefs.values()))
 need(caller['builder_returned_state']==state and caller['caller_error'] is None and caller['Root_failure_assignment_required'] is False,'EXACT_DURABLE_RETURN')
 closed=q.doc(state['closed_receipt']['ref'])
 need({k for k in set(closed)|set(state) if closed.get(k)!=state.get(k)}=={'closed_receipt','candidate_for_independent_review'},'ONLY_SOURCE_DEFINED_CLOSED_PUBLICATION_DELTAS')
 need(closed['closed_receipt']=={'ref':None,'status':'PUBLICATION_ATTEMPTED_ROOT_MUST_CONFIRM_REF'},'CLOSED_RECEIPT_PREPUBLICATION')
 result=q.check_factual_build(contract,request,state,leaf,base)
 need(leaf.main_inventory(contract,base)==sorted(base.regular_absolute(i['ref']['path']) for i in manifest['items'] if i['kind']=='main'),'CURRENT_COMPLETE_MAIN_572_INVENTORY')
 leaf.verify_frozen_inventory(leaf.compile_request(contract,request,base)['paths'],frozen,base)
 frozenmap={q.canonical(r['path']):r for r in frozen}
 paths=leaf.compile_request(contract,request,base)['paths']
 for i in manifest['items']:
  if i['kind'] not in ('main','module'):continue
  dst=ntpath.join(paths['frozen_main'] if i['kind']=='main' else paths['module_cache'],*i['relative_path'].split('/'))
  r=frozenmap[q.canonical(dst)]
  need((r['sha256'],r['bytes'])==(i['ref']['sha256'],i['ref']['bytes']),'FROZEN_EQUALS_ORIGINAL_'+i['relative_path'])
 for kind,expected in [('original_inputs',original),('frozen_inputs',frozen),('export_inputs',[x['ref'] for x in q.doc(state['export_closure_ref'])['exports']]),('program',[state['program_ref']])]:
  g=state['guard_cleanup'][kind];q.clean_guard(g)
  need(g['share_mode']=='FILE_SHARE_READ_ONLY' and g['failure'] is None,'ORIGINAL_GUARD_MODE_'+kind)
  entries=g['entries'];need({q.ref_key(x) for x in entries}=={q.ref_key(x) for x in expected},'COMPLETE_ORIGINAL_GUARD_COVERAGE_'+kind)
  need(all(x['verified'] is True and x['final_path_match'] is True and x['closed'] is True for x in entries),'EVERY_ORIGINAL_GUARD_ENTRY_'+kind)
 q.clean_guard(caller['source_guard_cleanup'])
 need(state['gocache_initial']['files']==[] and state['gocache_initial']['shared_cache_copied'] is False,'INITIAL_EMPTY_UNSHARED_CACHE')
 for c in state['calls']:
  o=c['observation'];need(o['timed_out'] is False and o['error'] is None and o['resumed'] is True,'NO_TIMEOUT_ERROR_'+c['phase'])
  need(o['job_cleanup']['termination_requested'] is False and o['job_cleanup']['termination_succeeded'] is None,'NO_TERMINATION_'+c['phase'])
 declared=q.doc(state['declared_closure_ref']);export=q.doc(state['export_closure_ref']);packages={x['ImportPath']:x for x in declared['packages']}
 for p in packages.values():
  need(all(p['ImportMap'].get(x,x) in packages for x in p['Imports'] if x!='C'),'COMPLETE_IMPORT_GRAPH_'+p['ImportPath'])
 sums={tuple(line.split()[:2]):line.split()[2] for line in (Path(paths['frozen_main'])/'go.sum').read_text().splitlines()}
 modules={}
 for p in packages.values():
  m=p['module']
  if not m['Path'] or m['Main']:continue
  need(sums[(m['Path'],m['Version'])]==m['Sum'] and sums[(m['Path'],m['Version']+'/go.mod')]==m['GoModSum'],'MODULE_SUMS_'+m['Path'])
  modules[m['Path']]=(m['Version'],m['Sum'])
 buildinfo=q.exact(state['calls'][4]['stdout_ref']).decode().splitlines();deps={}
 for l in buildinfo[1:]:
  f=l.strip().split('\t')
  if f[0]=='dep':deps[f[1]]=(f[2],f[3])
 need(deps==modules,'EXACT_BINARY_MODULE_GRAPH_AND_SUMS')
 need(buildinfo[0]==state['program_ref']['path']+': go1.27.1','BINARY_METADATA_EXACT_TARGET')
 toolchain={q.canonical(i['ref']['path']) for i in manifest['items'] if i['kind']=='toolchain'}
 for name in ['compile.exe','link.exe','asm.exe']:
  need(q.canonical(ntpath.join(contract['goroot'],'pkg/tool/windows_amd64',name)) in toolchain,'OFFICIAL_TOOL_'+name)
 need(q.canonical(contract['go_ref']['path']) in toolchain,'OFFICIAL_GO_EXE')
 trace=q.exact(state['calls'][3]['stderr_ref']).decode();workroot=trace.splitlines()[0].removeprefix('WORK=')
 cfg=next(r for r in work if r['path'].endswith('importcfg.link'));exe=next(r for r in work if r['path'].endswith('a.out.exe'))
 need(leaf.below(cfg['path'],workroot) and leaf.below(exe['path'],workroot),'RETAINED_WORK_FROM_ACTUAL_TRACE')
 need((exe['sha256'],exe['bytes'])==(state['program_ref']['sha256'],state['program_ref']['bytes']),'RETAINED_LINK_OUTPUT_EXACT_BINARY')
 exports={x['ImportPath']:q.canonical(x['path']) for x in export['exports']};cfgmap={}
 for line in q.exact(cfg).decode().splitlines():
  if line.startswith('packagefile '):
   name,path=line[len('packagefile '):].split('=',1);cfgmap[name]=q.canonical(path)
 need(cfgmap==exports,'LINK_IMPORTCFG_EXACT_EXPORT_GRAPH')
 need(ntpath.join(contract['goroot'],'pkg/tool/windows_amd64/link.exe').replace('\\','/') in trace.replace('\\','/'),'TRACE_USES_OFFICIAL_LINKER')
 # Re-read the original immutable tool-call/result bytes from the issuing audit offsets.
 audits=[]
 for pair in seal['actual_toolpairs']:
  binding=q.doc(pair['binding_ref']);raw=q.exact(pair['raw_ref']);parts=[]
  with Path(binding['source_audit_path']).open('rb') as f:
   for offset,size,digest in zip(binding['source_line_offsets'],binding['source_line_bytes'],binding['original_line_sha256']):
    f.seek(offset);v=f.read(size);need(hashlib.sha256(v).hexdigest()==digest,'AUDIT_SOURCE_LINE_'+pair['actual_chunk_id']);parts.append(v)
  need(b''.join(parts)==raw,'ORIGINAL_AUDIT_EXACT_'+pair['actual_chunk_id'])
  rows=[json.loads(x) for x in parts];need(rows[0]['payload']['id']==seal['root_thread_id'],'ROOT_AUDIT_IDENTITY_'+pair['actual_chunk_id'])
  need(rows[1]['payload']['call_id']==rows[2]['payload']['call_id']==binding['original_call_id'],'ORIGINAL_TOOL_PAIR_'+pair['actual_chunk_id'])
  need(pair['actual_chunk_id'] in str(rows[2]['payload']['output']),'ACTUAL_TOOL_CHUNK_'+pair['actual_chunk_id'])
  audits.append(dict(chunk=pair['actual_chunk_id'],call=rows[1],result=rows[2],binding_ref=pair['binding_ref']))
 final=next(x for x in audits if x['chunk']=='5bd8be');need('8164529' in str(final['result']) and 'truncat' in str(final['result']).lower(),'ORIGINAL_API_TRUNCATION_PRESERVED')
 start=next(x for x in audits if x['chunk']=='2712c4');need('39534' in str(start['result']),'ACTUAL_SESSION_BOUND')
 for chunk in ('4011e4','5bd8be'):need('39534' in str(next(x for x in audits if x['chunk']==chunk)['call']),'ORIGINAL_POLL_SESSION_'+chunk)
 need(scope['issued_by']==actual['issued_by']==facts['issued_by']=='codex:/root' and scope['builder_ref']==contract['builder_ref'] and scope['case_request_ref']==state['request_ref'],'ROOT_SCOPE_CASE_SOURCE_BOUND')
 starttime=datetime.datetime.fromisoformat(start['call']['timestamp'].replace('Z','+00:00'));endtime=datetime.datetime.fromisoformat(final['result']['timestamp'].replace('Z','+00:00'));lease=datetime.datetime.fromisoformat(scope['lease_expires_at'])
 need(starttime<endtime<lease,'ACTUAL_CALL_WITHIN_ROOT_LEASE')
 for live,archive in zip(actual['current_canonical_refs'],vector['archive_refs']):need((live['sha256'],live['bytes'])==(archive['sha256'],archive['bytes']),'ACTIVATED_CANON_ARCHIVE_EXACT')
 for live,archive in zip(facts['before_canonical_refs'],facts['before_archive_refs']):need((live['sha256'],live['bytes'])==(archive['sha256'],archive['bytes']),'BEFORE_CANON_ARCHIVE_EXACT')
 need(runtime['status']=='QUALIFIED_FOR_MAIN23_BUILD' and runtime['formal_programme_qualification'] is False,'ROOT_RUNTIME_ALREADY_QUALIFIED')
 result.update(program_ref=state['program_ref'],source_refs=contract['current_main_source_refs'],root_actual_request_ref=state['root_context']['root_request_ref'],root_complete_hostpair_seal_ref=sealref,closure_counts=dict(original=len(original),frozen=len(frozen),cache=len(cache),work=len(work),packages=len(packages),modules=len(modules),exports=len(exports)),original_process_stdout_complete=False,original_API_truncation_preserved=True,original_API_reconstructed=False)
except BaseException as e:error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
finally:closure=guard.close()
gr=save('actual-review-Source-guard.closed.json',closure)
q.clean_guard(closure)
out=save('actual-review-checks.json',dict(status='FACTUAL_REVIEW_PASSED' if error is None else 'REVIEW_DIAGNOSTIC_FAILURE',checks=checked,check_count=len(checked),error=error,result=result,guard_ref=gr,held_ref_count=len(allrefs),held_bytes=sum(x['bytes'] for x in allrefs.values()),formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(report_ref=out,guard_ref=gr,check_count=len(checked),error=error,held_ref_count=len(allrefs)),ensure_ascii=False),flush=True)
if error:raise SystemExit(1)
