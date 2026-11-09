"""Independent old21 pure Source validation; never enter run_registered_build."""
import ast,copy,hashlib,json,ntpath,os,types
from pathlib import Path
D=Path(__file__).resolve().parent;W=D.parent.parent;S=W/'schema21_programme_builder_source_codex/main21b-20261010-01'
ACTOR='codex:/root/full_w09_source_review';ROOT='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=p.as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def key(r):return ntpath.normcase(ntpath.normpath(r['path'])),r['sha256'],r['bytes']
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
def module(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def need(v):
 if not v:raise ValueError('INDEPENDENT_SOURCE_CONDITION')
def unique(refs):
 rows={}
 for r in refs:
  k=key(r)[0]
  if k in rows:need(key(rows[k])==key(r))
  rows.setdefault(k,r)
 return list(rows.values())
def documents(v):
 out=[]
 def visit(v,depth=0):
  if depth>24:return
  if type(v) is dict:
   out.append(v)
   for c in v.values():visit(c,depth+1)
  elif type(v) is list:
   for c in v:visit(c,depth+1)
  elif type(v) is str:
   for t in dict.fromkeys([v,*v.splitlines()]):
    if not t.strip().startswith(('{','[')):continue
    try:a=json.loads(t)
    except (ValueError,TypeError):continue
    if type(a) in (dict,list):visit(a,depth+1)
 visit(v);return out
def main():
 h=read(S/'HDF.json');mf=read(S/'MF.json');c=read(S/'contract.v2.json');ins=read(S/'input-manifest.json');inv=read(S/'frozen-source-manifest.json');delivery=read(h['source_delivery_ref']['path']);offline=read(ins['offline_static_map_ref']['path']);prep=read(S/'source-preparation.json')
 reused=read(ins['reused_resource_review_ref']['path']);gitref=next(r for r in prep['metadata_refs'] if r['path'].endswith('/git-commands.actual.json'));git=read(gitref['path'])
 deps=[ins['reused_resource_manifest_ref'],ins['reused_resource_review_ref'],reused['source_guard_audit_ref'],inv['source_inventory_ref'],inv['source_scope_ref'],inv['original_git_batch_ref'],gitref]
 deps += [r for row in git[-3:] for r in [row['stdout'],row['stderr']]+([row['stdin']] if 'stdin' in row else [])]
 deps += [c[k] for k in ('common_builder_ref','base_helper_ref','source_guard_ref','owned_job_ref','toolchain_lock_ref','common_source_review_ref')]
 deps += [r for v in offline['modules'] for r in [v['expanded_go_mod_ref'],*v['cache_metadata_refs'].values()]]+[offline['locked_go_download_dir_source_ref']]
 refs=unique([pin(__file__),pin(S/'HDF.json'),h['manifest_ref'],*mf['members'],*deps])
 gm=module(c['source_guard_ref']['path'],'independent_old21_guard');guard=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024);checks=[];failed=[];detail={}
 def check(name,fn,reject=False):
  try:
   fn()
   if reject:raise AssertionError('EXPECTED_REJECTION_NOT_OBSERVED')
   checks.append(dict(name=name,passed=True,evidence_class='INDEPENDENT_PURE_SOURCE_ONLY'))
  except Exception as e:
   ok=reject and isinstance(e,(ValueError,RuntimeError,KeyError,TypeError))
   row=dict(name=name,passed=ok,error_type=type(e).__name__,error=str(e),evidence_class='INDEPENDENT_PURE_SOURCE_ONLY');checks.append(row)
   if not ok:failed.append(row)
 try:
  guard.acquire(refs)
  check('official_five_Root_pins',lambda:need([(pin(S/n)['sha256'],pin(S/n)['bytes']) for n in ('HDF.json','MF.json','old21_builder.py','contract.v2.json','input-manifest.json')]==[('355407c30d1d0081a5fac90d32e8c7c47f95ddb0d56681768d8688bf2684ef84',3255),('6e40bbe378edf370ac8cb870f581d76cd8b48b3c127534855068787c66188069',103057),('b590cc502c90408f3c5b91332982a31acfec09ac279a5e0ebcc417d0a91ae320',27200),('1472e40c8806dcb82de62352378c306077fef8e674925b57941f305527bf4402',22410),('bfa48741c773883c11a31f75dc58a6ee9c2d295dfc47dc7218e418e6f6cfc0b0',5281064)]))
  for r in refs:check('held_pin:'+r['path'],lambda r=r:need(key(pin(r['path']))==key(r)))
  b=module(h['builder_ref']['path'],'old21_independent_inert');base=module(c['base_helper_ref']['path'],'old21_base_pure');common=module(c['common_builder_ref']['path'],'old21_common_pure')
  check('independent_Source_author_and_no_actual_grant',lambda:need(h['source_author']==b.AUTHOR!=ACTOR and not c['runtime_grant'] and not c['formal_acceptance'] and c['future_Root_scope_ref'] is None and c['actual_build_hostpair_obligation']['actual_complete_pair_ref'] is None))
  oldins=read(ins['reused_resource_manifest_ref']['path']);newitems=[i for i in ins['items'] if i['kind']!='historical_source'];olditems=[i for i in oldins['items'] if i['kind'] in ('module','toolchain')]
  check('14098_module_toolchain_items_reused_exactly',lambda:need(newitems==olditems and len(newitems)==14098 and reused['verdict']=='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION' and reused['independent_non_author'] is True and key(reused['author_input_manifest_ref'])==key(ins['reused_resource_manifest_ref'])))
  priorguard=read(reused['source_guard_audit_ref']['path'])['audit'];priorpins={key(v) for v in priorguard['entries']}
  check('reused_resources_all_covered_by_closed_independent_guard',lambda:need(priorguard['closed'] and priorguard['retained_handles_count']==0 and priorguard['errors']==[] and all(key(i['ref']) in priorpins for i in newitems)))
  request=dict(case_id='a'*32,output_root=c['output_parent']+'/old21-build-'+'a'*32);plan=b.compile_request(c,request,base);paths=plan['paths']
  check('nine_Go_only_phases_control_then_backup',lambda:need(len(plan['phases'])==9 and [p['target'] for p in plan['phases']]==[None]+['control']*4+['backup']*4 and all(p['argv'][0]==c['go_ref']['path'] for p in plan['phases'])))
  check('two_distinct_outputs_and_declared_export_build_inspect',lambda:need([p['kind'] for p in plan['phases']]==['version']+['declared','export','build','inspect']*2 and paths['control_program']!=paths['backup_program'] and all('-work' in p['argv'] and '-x' in p['argv'] for p in plan['phases'] if p['kind']=='build')))
  for name,update in [('extra_grant',{'execution_grant':True}),('escape',{'output_root':'D:/outside'}),('uppercase',{'case_id':'A'*32}),('bool',{'case_id':True})]:check('reject_request_'+name,lambda u=update:b.compile_request(c,{**request,**u},base),True)
  for name,update in [('schema22',{'schema_version':22}),('bool_schema',{'schema_version':True}),('wrong_commit',{'source_commit':'0'*40}),('wrong_tree',{'source_tree':'0'*40})]:check('reject_contract_'+name,lambda u=update:b.compile_request({**c,**u},request,base),True)
  env=common.environment(c,paths);check('offline_unique_allowlisted_environment',lambda:need(all(env[k]==v for k,v in dict(GOPROXY='off',GOSUMDB='off',GOTOOLCHAIN='local',GOENV='off',GOWORK='off',CGO_ENABLED='0',GOOS='windows',GOARCH='amd64',GOAMD64='v1',GOCACHE=paths['gocache'],GOMODCACHE=paths['module_cache']).items()) and not any(k.startswith('RESEARCHOS_') for k in env) and 'GOCACHEPROG' not in env))
  objects=b.validate_source_manifest(c,ins,inv,base,common);check('272_Git_blobs_SHA256_bytes',lambda:b.validate_blob_bytes(objects,guard.get_buffer));check('exact_frozen_source_membership',lambda:b.source_membership(c,objects,base))
  treebytes=Path(git[-3]['stdout']['path']).read_bytes();treeobjects={}
  for row in treebytes.split(b'\0'):
   if not row:continue
   prefix,name=row.split(b'\t',1);mode,typ,sha=prefix.decode().split();treeobjects[name.decode()]=(mode,typ,sha)
  check('original_commit_tree_real_Git_metadata',lambda:need(git[-3]['argv'][-1]==b.COMMIT and git[-3]['exit']==0 and Path(git[-1]['stdout']['path']).read_text().strip()==b.TREE))
  raw=guard.get_buffer(inv['original_git_batch_ref']['path']);pos=0;blobs={}
  while pos<len(raw):
   end=raw.index(b'\n',pos);sha,typ,size=raw[pos:end].decode().split();size=int(size);pos=end+1;value=raw[pos:pos+size];pos+=size
   need(raw[pos:pos+1]==b'\n' and typ=='blob' and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+value).hexdigest()==sha);pos+=1;blobs[sha]=value
  for name,obj in objects.items():check('original_Git_path_blob:'+name,lambda n=name,o=obj:need(treeobjects[n]==(o['mode'],'blob',o['git_blob']) and blobs[o['git_blob']]==guard.get_buffer(o['ref']['path'])))
  def rename_sql(before,after):
   v=copy.deepcopy(inv);o=next(o for o in v['objects'] if o['git_path'].startswith('migrations/sqlite/'+before));o['git_path']=o['git_path'].replace(before,after);o['ref']['path']=o['ref']['path'].replace(before,after);return v
  for name,before,after in [('hole','0003_','0000_'),('SQL22','0021_','0022_'),('addon','next_v24_sessions.sql','other.sql')]:check('reject_source_'+name,lambda before=before,after=after:b.validate_source_manifest(c,ins,rename_sql(before,after),base,common),True)
  v=copy.deepcopy(c);v['runtime_source_refs']['migrations/sqlite/next_v24_sessions.sql']['sha256']='0'*64;check('reject_runtime_byte_pin_drift',lambda:b.validate_source_manifest(v,ins,inv,base,common),True)
  v=copy.deepcopy(inv);v['objects'][1]=copy.deepcopy(v['objects'][0]);check('reject_duplicate_object',lambda:b.validate_source_manifest(c,ins,v,base,common),True)
  check('nineteen_modules_no_actual_offline_claim',lambda:need(len(offline['modules'])==19 and offline['missing_zip_count']==8 and offline['result']=='STATIC_RESOURCE_MAPPING_ONLY' and ins['actual_compiler_closure']=='NOT_RUN_PENDING_ROOT'))
  sums={tuple(line.split()[:2]):line.split()[2] for line in guard.get_buffer(objects['go.sum']['ref']['path']).decode().splitlines()}
  for v in offline['modules']:
   check('offline_static_map:'+v['module'],lambda v=v:need(c['module_versions'][v['module']]==v['version'] and Path(v['cache_metadata_refs']['.ziphash']['path']).read_text().strip()==sums[(v['module'],v['version'])] and Path(v['cache_metadata_refs']['.mod']['path']).read_bytes()==Path(v['expanded_go_mod_ref']['path']).read_bytes() and not v['partial_present']))
  # Interface models below are explicitly Source-only, never Root-issued refs.
  fake=lambda p:dict(path='D:/SOURCE_ONLY_INTERFACE/'+p,sha256='0'*64,bytes=1)
  binding={k:fake(k+'.json') for k in ('source_review_ref','resource_qualification_ref','runtime_manifest_ref','outer_host_binding_ref')};binding.update(input_manifest_ref=c['input_manifest_ref'],source_author=b.AUTHOR,reviewer_actor=ACTOR)
  check('resource_binding_interface_only',lambda:b.validate_resource_binding(binding,c,base))
  for label,update in [('selfreview',{'reviewer_actor':b.AUTHOR}),('Rootreview',{'reviewer_actor':'codex:/root'}),('manifest_drift',{'input_manifest_ref':fake('wrong.json')}),('extra_approval',{'approved':True})]:check('reject_binding_'+label,lambda u=update:b.validate_resource_binding({**binding,**u},c,base),True)
  for scope in (None,{},object()):check('reject_unqualified_Scope_'+type(scope).__name__,lambda s=scope:b.require_live_scope(s),True)
  for target,package in b.TARGETS.items():
   file=ntpath.join(paths['frozen_main'],*package.split('/'),'main.go');mod=ntpath.join(paths['frozen_main'],'go.mod');allowed=[dict(fake('unused'),path=file),dict(fake('unused2'),path=mod)]
   p=dict(ImportPath=c['module_path']+'/'+package,Name='main',Dir=ntpath.dirname(file),GoFiles=['main.go'],Module=dict(Path=c['module_path'],Main=True,GoMod=mod),Export=ntpath.join(paths['gocache'],'aa','1'*64+'-d'),BuildID='SOURCE_ONLY_INTERFACE')
   check('target_declared_export_interface:'+target,lambda p=p,a=allowed,t=target:b.declared_closure([p],a,paths,c,base,common,t,True))
   for label,u in [('test_variant',{'ForTest':'test'}),('undeclared',{'GoFiles':['other.go']}),('outside',{'Dir':'D:/outside'}),('bad_export',{'Export':'D:/shared/file-d'}),('wrong_target',{'ImportPath':'wrong'}),('missing_BuildID',{'BuildID':''}),('package_error',{'Error':{'Err':'fail'}})]:check('reject_'+target+'_'+label,lambda u=u,p=p,a=allowed,t=target:b.declared_closure([{**p,**u}],a,paths,c,base,common,t,True),True)
   metadata=('SOURCE_ONLY.exe: go1.27.1\n\tpath\t'+c['module_path']+'/'+package+'\n'+''.join('\tbuild\t'+x+'\n' for x in ('CGO_ENABLED=0','GOOS=windows','GOARCH=amd64','GOAMD64=v1','-trimpath=true'))).encode()
   check('target_metadata_interface:'+target,lambda v=metadata,t=target:b.verify_binary_metadata(v,c,t))
   check('reject_'+target+'_embedded_vcs',lambda v=metadata,t=target:b.verify_binary_metadata(v+b'\tbuild\tvcs.revision=fake\n',c,t),True)
  tree=ast.parse(Path(h['builder_ref']['path']).read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_registered_build');loop=next(n for n in ast.walk(fn) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='phase')
  attrs=[n.func.attr for n in ast.walk(loop) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)];allattrs={n.func.attr for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
  check('every_phase_has_live_resource_source_and_owned_job_gates',lambda:need({'require_phase','require_resources','assert_pins','source_membership','verify_frozen_inventory','run_owned','validate_owned'}<=set(attrs) and {'require_registered','require_resources'}<=allattrs))
  check('no_top_level_runtime_or_subprocess_SQL',lambda:need(not any(isinstance(n,ast.Import) and any(v.name.split('.')[0] in ('subprocess','sqlite3') for v in n.names) for n in tree.body) and not any(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) for n in tree.body)))
  check('only_one_serial_close_inside_finally',lambda:need(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='close' for n in ast.walk(fn))==1 and any(isinstance(n,ast.Try) and any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='close' for stmt in n.finalbody for x in ast.walk(stmt)) for n in ast.walk(fn))))
  maintry=next(n for n in fn.body if isinstance(n,ast.Try));failurebody=ast.fix_missing_locations(ast.Module(body=copy.deepcopy(maintry.handlers[0].body),type_ignores=[]))
  for calls in ([],[{'actual_exit':None}],[{'actual_exit':1}],[{'actual_exit':0}]):
   state=dict(phase='SOURCE_ONLY_TEST_PHASE',calls=copy.deepcopy(calls));ns=dict(state=state,exc=ValueError('SOURCE_ONLY_FAILURE'));exec(compile(failurebody,'ACTUAL_SOURCE_FAILURE_HANDLER_ONLY','exec'),ns)
   check('pure_returned_failure_preserves_child_exit:'+str(calls),lambda s=state,v=calls:need(s['status']=='STOPPED_AT_FIRST_FAILURE' and s['first_failure']['original_ordinal'] is None and s['first_failure']['Root_assignment_required'] is True and s['first_failure']['last_child_exit']==(v[-1]['actual_exit'] if v else None)))
  check('causal_prior_observation_and_postreturn_actual_pair',lambda:need(c['outer_host_binding_contract']['must_predate_this_build_entry'] is True and c['outer_host_binding_contract']['current_build_not_yet_returned_complete_pair_prohibited'] is True and c['actual_build_hostpair_obligation']['timing']=='EXTERNAL_CAPTURE_AFTER_BUILD_RETURNS_OR_FAILS' and c['actual_build_hostpair_obligation']['current_build_complete_pair_required_at_entry'] is False))
  authorcontrols=read(delivery['source_controls_ref']['path']);check('83_author_controls_are_Source_only',lambda:need(authorcontrols['passed']==83 and authorcontrols['failed']==0 and authorcontrols['execution_branch_called'] is False))
  for r in delivery['guard_refs']:
   v=read(r['path']);check('author_guard_closed:'+Path(r['path']).name,lambda v=v:need(v['closed'] and v['retained_handles_count']==0 and v['errors']==[]))
  index=read(delivery['actual_source_tool_index_ref']['path']);actual=[]
  for pair in index['captures']:
   binding=read(pair['binding_ref']['path']);lines=Path(pair['raw_ref']['path']).read_bytes().splitlines(keepends=True);head,call,out=[json.loads(x) for x in lines]
   check('author_3row_pins:'+pair['chunk_id'],lambda:need([len(x) for x in lines]==binding['source_line_lengths'] and [hashlib.sha256(x).hexdigest() for x in lines]==binding['source_line_sha256']))
   with Path(binding['source_audit_path']).open('rb') as f:
    for off,line in zip(binding['source_line_offsets'],lines):
     f.seek(off);check('author_actual_offset:'+str(off),lambda off=off,line=line:need(off+len(line)<=binding['source_prefix_size_observed'] and f.read(len(line))==line))
   check('author_real_session_call_pair:'+pair['chunk_id'],lambda:need(head['payload']['id']=='01a11e22-ecb2-7720-80d2-af63727d414d' and head['payload']['agent_path']==b.AUTHOR.removeprefix('codex:') and call['payload']['call_id']==out['payload']['call_id']==binding['original_call_id']))
   hosts=[v for v in documents(out['payload']['output']) if type(v) is dict and v.get('chunk_id')==pair['chunk_id']];actual.append(dict(chunk_id=pair['chunk_id'],raw_ref=pair['raw_ref'],binding_ref=pair['binding_ref'],observed_host_exits=[v.get('exit_code') for v in hosts]))
  detail=dict(original_commit=b.COMMIT,original_tree=b.TREE,frozen_source_objects=272,numbered_migrations=list(range(1,22)),runtime_source_inputs=24,inherited_resource_items=14098,inherited_resources_not_rehashed=True,reuse_review_ref=ins['reused_resource_review_ref'],reuse_guard_ref=reused['source_guard_audit_ref'],actual_Source_hostpairs=actual,Source_condition_fixtures_only=True,runtime_branch_called=False,Go_Native_product_SQL_subprocess_calls=0,actual_offline_qualification='OPEN_ROOT_NEXT_STAGE',RootScope_and_runtime_grant_created=False,Canon_Main_existing_Source_writes=False)
 finally:closed=guard.close();cr=save('independent-Source-guard.closed.json',closed)
 check('review_guard_closed0',lambda:need(closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]))
 rr=save('finitechecks.json',dict(schema='researchos.old21-builder-independent-Source-checks.v1',review_author=ACTOR,reviewer_thread_id=os.environ['CODEX_THREAD_ID'],status='ACCEPTED_SOURCE_ONLY' if not failed else 'CHANGES_REQUIRED',checks=checks,failed=failed,details=detail,Source_guard_ref=cr,held_refs=len(refs),formal_acceptance=False,execution_grant=False))
 print(json.dumps(dict(result_ref=rr,guard_ref=cr,checks=len(checks),failed=failed,held_refs=len(refs),retained_handles_count=0,runtime_branch_called=False),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
