"""Independent OLD21 factual validation. No process launch or authority entry."""
from pathlib import Path
import hashlib,json,ntpath,types,traceback,re,struct
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
CASE='9c80f2c133f443bb8a2a629680cbba5d'
C=B/('integration_codex/old21-caller-'+CASE)
S=B/'schema21_programme_builder_source_codex/main21b-20261010-01'
G=B/'schema21_original_resource_discovery_source_codex/discovery-20261010-01'
Q=B/'fresh_main23_programme_actual_independent_review_codex/actual-main23-20261010-01/review_checks.py'
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def save(name,v):
 p=N/name
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
q=types.ModuleType('old21_fact_primitives');exec(compile(Q.read_bytes(),str(Q),'exec'),q.__dict__)
checks=[]
def need(v,label):q.need(v,label);checks.append(label)
def mod(ref,name):
 m=types.ModuleType(name);exec(compile(q.exact(ref),ref['path'],'exec'),m.__dict__);return m
def refs(x):
 if isinstance(x,dict):
  if set(x)==q.REF_KEYS:return [x]
  return [r for v in x.values() for r in refs(v)]
 if isinstance(x,list):return [r for v in x for r in refs(v)]
 return []
cr=pin(S/'contract.v2.json');sr=pin(C/'builder-returned-state.root.json');rr=pin(C/'caller-return.root.json')
need(cr['sha256']=='1472e40c8806dcb82de62352378c306077fef8e674925b57941f305527bf4402','CONTRACT_PIN')
need(sr['sha256']=='476db49e358ca6b96b7c57c01b4282ae30d62c06c458080bddb26f552a7d74ca','ROOT_STATE_PIN')
need(rr['sha256']=='ddda653303194eacf23aec90543808802679eccd8378d6d5699b2cb228ebf2eb','ROOT_CALLER_PIN')
contract=q.doc(cr);state=q.doc(sr);caller=q.doc(rr);request=q.doc(state['request_ref'])
leaf=mod(contract['builder_ref'],'old21_factual_leaf');base=mod(contract['base_helper_ref'],'old21_factual_base');common=mod(contract['common_builder_ref'],'old21_factual_common');gm=mod(contract['source_guard_ref'],'old21_factual_guard')
manifest=q.doc(contract['input_manifest_ref']);inventory=q.doc(contract['frozen_source_manifest_ref']);scope=q.doc(inventory['source_scope_ref'])
original=q.doc(state['source_before_ref'])['refs'];frozen=q.doc(state['frozen_before_ref'])['refs']
gitref=pin(G/'git-commands.actual.json');gitcommands=q.doc(gitref);gitselected=gitcommands[5:8]
metadata=[pin(__file__),pin(Q),cr,sr,rr,gitref]+refs(contract)+refs(state)+refs(inventory)+refs(gitselected)
cachework=[]
for tr in state['target_results'].values():
 for key in ['cache_before_build_ref','cache_after_build_ref','build_work_ref']:
  cachework+=q.doc(tr[key])['refs']
live={q.canonical(str(R/'execution/v2.4'/n)) for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']}
allrefs={}
for r in metadata+original+frozen+cachework:
 key=q.canonical(r['path'])
 if key in live:continue
 need(key not in allrefs or q.ref_key(allrefs[key])==q.ref_key(r),'CONSISTENT_PIN_'+str(len(allrefs)))
 allrefs[key]=r
guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=1536*1024*1024)
error=None;result={};stages=[]
try:
 guard.acquire(list(allrefs.values()))
 need(caller['builder_returned_state']==state and caller['caller_error'] is None and caller['Root_failure_assignment_required'] is False,'EXACT_DURABLE_CALLER_STATE')
 need(caller['persisted_builder_state_ref']==sr and caller['candidate_qualification_ref'] is None and caller['automatic_retry'] is False,'DURABLE_REF_NO_SELF_QUALIFICATION')
 closed=q.doc(state['closed_receipt']['ref'])
 need({k for k in set(closed)|set(state) if closed.get(k)!=state.get(k)}=={'closed_receipt','candidate_for_independent_review'},'ONLY_SOURCE_DEFINED_CLOSED_DELTAS')
 need(closed['closed_receipt']==dict(ref=None,status='PUBLICATION_ATTEMPTED_ROOT_MUST_CONFIRM_REF'),'PREPUBLICATION_RECEIPT')
 need(state['status']=='BUILT_OLD21_CANDIDATES_PENDING_NONAUTHOR_PROGRAMME_REVIEW' and state['first_failure'] is None,'SUCCESS_PENDING_NONAUTHOR')
 need(state['case_id']==request['case_id']==CASE and state['phase']=='backup-inspect','CASE_FINAL_PHASE')
 need(state['formal_acceptance'] is False and state['product_program_executions']==state['SQL_calls']==state['model_calls']==0,'BUILD_ONLY_BOUNDARY')
 need(state['automatic_retry'] is False and not state.get('cleanup_errors'),'NO_RETRY_CLEANUP_ERRORS')
 objects=leaf.validate_source_manifest(contract,manifest,inventory,base,common)
 leaf.validate_blob_bytes(objects,guard.get_buffer);leaf.source_membership(contract,objects,base)
 need(len(objects)==272 and scope['control_backup_and_runtime_union']==[{k:v for k,v in x.items() if k!='ref'} for x in inventory['objects']],'EXACT_ORIGINAL_SCOPE_272')
 candidates=q.doc(inventory['source_inventory_ref']);historical=next(x for x in candidates if x['commit']==contract['source_commit'])
 need(historical['tree']==contract['source_tree'],'ORIGINAL_INVENTORY_TREE')
 historicalmap={x['git_path']:x for x in historical['source_objects']}
 need(all(historicalmap[n]=={k:v for k,v in x.items() if k!='ref'} for n,x in objects.items()),'ALL_272_ORIGINAL_INVENTORY_OBJECTS')
 treecmd,batchcmd,revparse=gitselected
 need(treecmd['argv'][-4:]==['ls-tree','-r','-z',contract['source_commit']] and revparse['argv'][-2:]==['rev-parse',contract['source_commit']+'^{tree}'],'ORIGINAL_GIT_COMMIT_COMMANDS')
 need(all(x['exit']==0 and q.exact(x['stderr'])==b'' for x in gitselected),'ORIGINAL_GIT_EXITS_ZERO')
 need(q.exact(revparse['stdout']).decode().strip()==contract['source_tree'],'ORIGINAL_TREE_STDOUT')
 tree={};trie={}
 for row in q.exact(treecmd['stdout']).split(b'\0'):
  if not row:continue
  head,path=row.split(b'\t',1);mode,kind,oid=head.split();tree[path.decode()]=(mode.decode(),oid.decode())
  d=trie;parts=path.split(b'/')
  for part in parts[:-1]:d=d.setdefault(part,{})
  d[parts[-1]]=(mode,oid)
 def hash_tree(d):
  data=b''
  for name,value in sorted(d.items(),key=lambda kv:kv[0]+(b'/' if isinstance(kv[1],dict) else b'')):
   mode,oid=(b'40000',hash_tree(value).encode()) if isinstance(value,dict) else value
   data+=mode+b' '+name+b'\0'+bytes.fromhex(oid.decode())
  return hashlib.sha1(b'tree '+str(len(data)).encode()+b'\0'+data).hexdigest()
 need(hash_tree(trie)==contract['source_tree'],'RECOMPUTED_ORIGINAL_RECURSIVE_GIT_TREE')
 need(all(tree[n]==(o['mode'],o['git_blob']) for n,o in objects.items()),'ALL_272_BLOBS_IN_ORIGINAL_TREE')
 raw=q.exact(inventory['original_git_batch_ref']);need(batchcmd['stdout']==inventory['original_git_batch_ref'],'ORIGINAL_BATCH_PIN')
 blobs={};pos=0
 while pos<len(raw):
  end=raw.index(b'\n',pos);oid,kind,size=raw[pos:end].split();size=int(size);body=raw[end+1:end+1+size]
  need(kind==b'blob' and raw[end+1+size:end+2+size]==b'\n' and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+body).hexdigest()==oid.decode(),'ORIGINAL_BATCH_BLOB_'+str(len(blobs)))
  blobs[oid.decode()]=body;pos=end+2+size
 need(pos==len(raw) and all(blobs[o['git_blob']]==guard.get_buffer(o['ref']['path']) for o in objects.values()),'ALL_272_EXACT_ORIGINAL_BATCH_BYTES')
 plan=leaf.compile_request(contract,request,base);paths=plan['paths'];common.verify_frozen_inventory(paths,frozen,base)
 need([q.ref_key(x) for x in original]==[q.ref_key(x) for x in q.doc(state['source_after_ref'])['refs']],'ORIGINAL_VECTOR_UNCHANGED')
 need([q.ref_key(x) for x in frozen]==[q.ref_key(x) for x in q.doc(state['frozen_after_ref'])['refs']],'FROZEN_VECTOR_UNCHANGED')
 need(all(q.ref_key(i['ref']) in {q.ref_key(x) for x in original} for i in manifest['items']),'ALL_INPUTS_ORIGINALLY_HELD')
 frozenmap={q.canonical(x['path']):x for x in frozen}
 for item in manifest['items']:
  if item['kind']=='toolchain':continue
  path=ntpath.join(paths['frozen_main'] if item['kind']=='historical_source' else paths['module_cache'],*item['relative_path'].split('/'));r=frozenmap[q.canonical(path)]
  need((r['sha256'],r['bytes'])==(item['ref']['sha256'],item['ref']['bytes']),'FROZEN_COPY_'+item['relative_path'])
 stages.append(save('stage-source-passed.json',dict(status='PASSED',historical_objects=272,git_tree_recomputed=True,original_count=len(original),frozen_count=len(frozen),held_ref_count=len(allrefs))))
 print('SOURCE_STAGE_PASSED',flush=True)
 env=q.doc(state['environment_ref'])
 need(env==common.environment(contract,paths),'EXACT_OFFLINE_ENVIRONMENT')
 need(state['gocache_initial']['files']==[] and state['gocache_initial']['shared_cache_copied'] is False,'INITIAL_EMPTY_UNSHARED_CACHE')
 need([x['phase'] for x in state['calls']]==[x['id'] for x in plan['phases']] and len(state['calls'])==9,'EXACT_NINE_GO_PHASES')
 need(state['root_created'] is True and len(state['prepared_directories'])==7,'PREPARE_EVIDENCE')
 streams={};last_end=0
 for phase,call in zip(plan['phases'],state['calls']):
  name=phase['id'];o=call['observation'];q.typed_owned(o)
  need(call['argv']==phase['argv'] and q.canonical(call['cwd'])==q.canonical(paths['frozen_main']) and call['timeout_seconds']==phase['timeout'] and call['env']==env,'EXACT_INVOCATION_'+name)
  need(type(call['actual_exit']) is int and call['actual_exit']==0,'ACTUAL_GO_ZERO_'+name)
  need(o['timed_out'] is False and o['error'] is None and o['resumed'] is True and o['job_cleanup']['termination_requested'] is False,'OWNED_JOB_SUCCESS_'+name)
  need(call['individual_descendant_exit_codes'] is None,'NO_INVENTED_DESCENDANT_EXITS_'+name)
  need(type(call['started_at_unix_ns']) is int and type(call['ended_at_unix_ns']) is int and last_end<=call['started_at_unix_ns']<=call['ended_at_unix_ns'],'EXACT_SEQUENTIAL_TIME_'+name);last_end=call['ended_at_unix_ns']
  need(q.doc(call['result_ref'])=={k:v for k,v in call.items() if k!='result_ref'},'ORIGINAL_RESULT_'+name)
  before=q.doc(call['before_ref'])
  need(all(before[k]==call[k] for k in ['phase','argv','cwd','env','timeout_seconds','started_at_unix_ns']) and before['observation'] is None and before['actual_exit'] is None,'ORIGINAL_BEFORE_'+name)
  out,err=q.exact(call['stdout_ref']),q.exact(call['stderr_ref']);need(max(len(out),len(err))<=16*1024*1024,'COMPLETE_STREAMS_'+name);streams[name]=(out,err)
 need(streams['go-version'][0].decode().strip()=='go version go1.27.1 windows/amd64','ACTUAL_GO_VERSION')
 allowed=frozen+[x['ref'] for x in manifest['items'] if x['kind']=='toolchain'];targetfacts={}
 sums={tuple(l.split()[:2]):l.split()[2] for l in (Path(paths['frozen_main'])/'go.sum').read_text().splitlines()}
 expectedguards={'original_inputs':original,'frozen_inputs':frozen}
 for call in state['calls']:expectedguards['raw_'+call['phase']]=[call['stdout_ref'],call['stderr_ref']]
 for target,tr in state['target_results'].items():
  declared=leaf.declared_closure(common.parse_json_stream(streams[target+'-declared'][0]),allowed,paths,contract,base,common,target,False)
  export=leaf.declared_closure(common.parse_json_stream(streams[target+'-export'][0]),allowed,paths,contract,base,common,target,True)
  recorded=q.doc(tr['export_closure_ref'])
  need(declared==q.doc(tr['declared_closure_ref']),'RECOMPUTED_DECLARED_'+target)
  need(export['packages']==declared['packages']==recorded['packages'] and export['input_refs']==declared['input_refs']==recorded['input_refs'],'RECOMPUTED_EXPORT_GRAPH_'+target)
  need(export['exports']==[{k:v for k,v in x.items() if k!='ref'} for x in recorded['exports']],'RECOMPUTED_EXPORT_RECORDS_'+target)
  cb=q.doc(tr['cache_before_build_ref'])['refs'];ca=q.doc(tr['cache_after_build_ref'])['refs'];cas={q.ref_key(x) for x in ca};cbs={q.ref_key(x) for x in cb}
  need(all(q.ref_key(x) in cas for x in cb),'BUILD_CACHE_NO_DRIFT_'+target)
  need(all(q.ref_key(x['ref']) in cbs and q.canonical(x['ref']['path'])==q.canonical(x['path']) for x in recorded['exports']),'ALL_EXPORTS_PINNED_BEFORE_BUILD_'+target)
  packages={x['ImportPath']:x for x in declared['packages']};modules={}
  for p in packages.values():
   need(all(p['ImportMap'].get(x,x) in packages for x in p['Imports'] if x!='C'),'COMPLETE_IMPORTS_'+target+'_'+p['ImportPath'])
   m=p['module']
   if not m['Path'] or m['Main']:continue
   need(sums[(m['Path'],m['Version'])]==m['Sum'] and sums[(m['Path'],m['Version']+'/go.mod')]==m['GoModSum'],'EXACT_MODULE_SUM_'+target+'_'+m['Path']);modules[m['Path']]=(m['Version'],m['Sum'])
  rawmeta=streams[target+'-inspect'][0];leaf.verify_binary_metadata(rawmeta,contract,target);lines=rawmeta.decode().splitlines();deps={}
  for line in lines[1:]:
   f=line.strip().split('\t')
   if f[0]=='dep':deps[f[1]]=(f[2],f[3])
  need(deps==modules and lines[0]==tr['program_ref']['path']+': go1.27.1','EXACT_BINARY_MODULE_GRAPH_'+target)
  binary=guard.get_buffer(tr['program_ref']['path']);peoff=struct.unpack_from('<I',binary,0x3c)[0]
  need(binary[:2]==b'MZ' and binary[peoff:peoff+4]==b'PE\0\0' and struct.unpack_from('<H',binary,peoff+4)[0]==0x8664,'REAL_AMD64_PE_'+target)
  need(q.canonical(tr['program_ref']['path'])==q.canonical(paths[target+'_program']),'EXACT_BINARY_PATH_'+target)
  trace=streams[target+'-build'][1].decode();workroot=trace.splitlines()[0].removeprefix('WORK=');work=q.doc(tr['build_work_ref'])['refs']
  targetwork=[x for x in work if common.below(x['path'],workroot)]
  cfg=next(x for x in targetwork if x['path'].endswith('importcfg.link'));exe=next(x for x in targetwork if x['path'].endswith('a.out.exe'))
  need((exe['sha256'],exe['bytes'])==(tr['program_ref']['sha256'],tr['program_ref']['bytes']),'EXACT_RETAINED_LINK_OUTPUT_'+target)
  cfgmap={}
  for line in q.exact(cfg).decode().splitlines():
   if line.startswith('packagefile '):name,path=line[12:].split('=',1);cfgmap[name]=q.canonical(path)
  need(cfgmap=={x['ImportPath']:q.canonical(x['path']) for x in recorded['exports']},'EXACT_LINK_IMPORTCFG_'+target)
  quoted=[json.loads(x) for x in re.findall(r'"(?:[^"\\]|\\.)*"',trace)]
  need(q.canonical(ntpath.join(contract['goroot'],'pkg/tool/windows_amd64/link.exe')) in {q.canonical(x) for x in quoted},'OFFICIAL_LINKER_TRACE_'+target)
  expectedguards['exports_'+target]=[x['ref'] for x in recorded['exports']];expectedguards['program_'+target]=[tr['program_ref']]
  targetfacts[target]=dict(program_ref=tr['program_ref'],packages=len(packages),modules=len(modules),exports=len(recorded['exports']),cache_before=len(cb),cache_after=len(ca),retained_work=len(targetwork),binary_metadata_ref=tr['binary_metadata_ref'])
 need(set(expectedguards)==set(state['guard_cleanup']),'ALL_15_BUILD_GUARDS')
 for name,expected in expectedguards.items():
  g=state['guard_cleanup'][name];q.clean_guard(g)
  need(g['share_mode']=='FILE_SHARE_READ_ONLY' and g['failure'] is None,'ORIGINAL_GUARD_MODE_'+name)
  need({q.ref_key(x) for x in g['entries']}=={q.ref_key(x) for x in expected} and all(x['verified'] is True and x['final_path_match'] is True and x['closed'] is True for x in g['entries']),'ORIGINAL_GUARD_COMPLETE_'+name)
 q.clean_guard(caller['source_guard_cleanup'])
 candidate=state['candidate_for_independent_review']
 need(candidate['program_refs']=={t:tr['program_ref'] for t,tr in state['target_results'].items()} and candidate['qualification_ref'] is None and candidate['provenance_ref']==state['closed_receipt']['ref'],'CANDIDATES_UNQUALIFIED_EXACT')
 need(candidate['source_commit']==contract['source_commit'] and candidate['source_tree']==contract['source_tree'] and candidate['frozen_source_manifest_ref']==contract['frozen_source_manifest_ref'],'CANDIDATE_HISTORICAL_SOURCE_EXACT')
 result=dict(targets=targetfacts,source_commit=contract['source_commit'],source_tree=contract['source_tree'],runtime_source_refs=contract['runtime_source_refs'],public_bootstrap_source_refs=contract['public_bootstrap_source_refs'],original_input_count=len(original),frozen_input_count=len(frozen),nine_actual_Go_jobs_checked=True,git_blob_and_tree_recomputed=True,formal_acceptance=False,SQL_executions=0,product_executions=0)
 stages.append(save('stage-nine-jobs-passed.json',dict(status='PASSED',result=result)))
except BaseException as e:error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
finally:closed_guard=guard.close()
gr=save('facts-Source-guard.closed.json',closed_guard);q.clean_guard(closed_guard)
report=save('facts-review-checks.json',dict(status='FACTUAL_REVIEW_PASSED' if error is None else 'REVIEW_DIAGNOSTIC_FAILURE',checks=checks,check_count=len(checks),error=error,result=result,stage_refs=stages,guard_ref=gr,held_ref_count=len(allrefs),held_bytes=sum(x['bytes'] for x in allrefs.values()),formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(report_ref=report,guard_ref=gr,checks=len(checks),held_refs=len(allrefs),error=error),ensure_ascii=False),flush=True)
print('PYTHON_EXIT_CODE='+str(1 if error else 0),flush=True)
raise SystemExit(1 if error else 0)
