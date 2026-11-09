from pathlib import Path
import ast
from datetime import datetime, timezone
import hashlib
import json
import types

R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
N=W/'w09_formal_root_bridge_source_codex/bridge-20261010-03'
D=W/'w09_formal_root_bridge_independent_review_codex/review-bridge-20261010-03'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
G=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
EXPECTED={
 'HDF.json':('1f85ead2fffdd5400270c3d0f1078bb661df91fbd8ff94bfd1dd05992e45aa0f',7862),
 'MF.json':('225bb69692fde3fb0d54afa017a93248db968ef9e0a24cdd2c9a81b3ad0119d1',6046),
 'w09_root_bridge.source.py':('327b0e886b58008ad33dcbcfaaaa2c44bc10d4076d3d3c717b2ce6e96914cbfb',49240),
 'consumer_launch.source.py':('c64deb904e746fd2d5df6775e0b96375ce36741315109d47ab86408360de5011',1493),
 'ROOT_CALL_CONTRACT.md':('756b10ab0a4e7f798d9e4a0f7c994e23dc9e50fddddbaa560a8dcae9c0c21ea6',4147)}
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':sha(b),'bytes':len(b)}
def load(p):return json.loads(Path(p).read_bytes())
def save(name,value):
 with (D/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
def refs(value):
 if type(value) is dict:
  if {'path','sha256','bytes'}<=set(value):yield {k:value[k] for k in ('path','sha256','bytes')}
  else:
   for v in value.values():yield from refs(v)
 elif type(value) is list:
  for v in value:yield from refs(v)
def fn(tree,name):return next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
def dump(n):return ast.dump(n,include_attributes=False)
def named_calls(node):return [x.func.id for x in ast.walk(node) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name)]
def direct_calls(node):return [(i,x.value.func.id) for i,x in enumerate(node.body) if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Name)]

checks=[]
def check(name,condition,details=None):
 checks.append({'name':name,'passed':bool(condition),'details':details})
 if not condition:raise AssertionError(name)

h=load(N/'HDF.json');mf=load(N/'MF.json');inp=load(N/'source-inputs.json')
author_audit_ref=pin(S/'w09.bridge03-author.actual-audit.root.json')
assert (author_audit_ref['sha256'],author_audit_ref['bytes'])==('763a61b446724a4bb6c06d57afc303f686b1422980bd8da5d9dd30012315d3e9',1116)
author_audit=load(author_audit_ref['path'])
allrefs={}
def add(ref):
 ref=dict(ref);ref['path']=str(Path(ref['path']));old=allrefs.get(ref['path'])
 assert old is None or old==ref
 allrefs[ref['path']]=ref
for name,(digest,size) in EXPECTED.items():add({'path':str(N/name),'sha256':digest,'bytes':size})
for ref in refs(mf):add(ref)
for ref in refs(inp):add(ref)
for ref in refs(h):add(ref)
add(author_audit_ref);add(author_audit['original_capture_ref'])
source=(N/'w09_root_bridge.source.py').read_bytes();tree=ast.parse(source)
# Inert module construction has no Main imports or Bridge-stage invocation.
m=types.ModuleType('bridge03_independent_readonly');m.__file__=str(N/'w09_root_bridge.source.py')
exec(compile(source,m.__file__,'exec'),m.__dict__)
for rel,(digest,size) in m.TRUSTED.items():
 if rel!='execution/v2.4/commands.json':add({'path':str(R/rel),'sha256':digest,'bytes':size})
gb=G.read_bytes();assert (sha(gb),len(gb))==('e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
gm=types.ModuleType('bridge03_independent_guard');gm.__file__=str(G);exec(compile(gb,str(G),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
report={'schema':'researchos.bridge03-independent-delta-controls.v1','reviewer_id':'/root/full_w09_source_review',
 'created_utc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'checks':checks,
 'reused_controls':{'Bridge01_author':18,'Task98_independent':24,'Bridge03_author':22,'rerun':False},
 'Scope_fixtures':False,'actual_Bridge_stages':0,'actual_Main_calls':0,'actual_dispatcher_calls':0,
 'actual_Native_Go_SQL_model_TP_calls':0,'RootScope_issued':False,'execution_grant':False,'formal_acceptance':False}
try:
 guard.acquire(list(allrefs.values()))
 check('complete-new-Source-members-and-explicit-inputs-held',len(mf['members'])==mf['member_count']==20,
       {'held_refs':len(allrefs),'Source_members':20,'live_CP_OW_held':False})
 def data(ref):return guard.get_buffer(ref['path'])
 src=data(h['source_ref']);oldref=load(N/'exact-inverse.json')['base_ref'];old=data(oldref)
 inverse=json.loads(data(h['exact_inverse_ref']));restored=src.decode('utf-8')
 changes=[]
 for index,c in reversed(list(enumerate(inverse['changes']))):
  count=restored.count(c['after']);assert count==1,(index,count)
  restored=restored.replace(c['after'],c['before'],1);changes.append(index)
 check('independent-complete-13-change-byte-inverse',restored.encode('utf-8')==old,
       {'base_ref':oldref,'reverse_order':changes})
 oldtree=ast.parse(old)
 unchanged=['physical','pin','checked','ref2','document','references','module','save','engine','current4',
            'snapshot','native_inputs','consumer_plan','seed','registration','transact','registered',
            'publish_registration','assemble','capture','check','derive']
 check('old-security-CAS-mode-route-TP-functions-byte-semantics-retained',all(dump(fn(tree,n))==dump(fn(oldtree,n)) for n in unchanged),unchanged)
 oldm=types.ModuleType('bridge02_readonly');oldm.__file__=str(Path(oldref['path']));exec(compile(old,str(oldref['path']),'exec'),oldm.__dict__)
 check('exact-six-routes-trusted-pins-and-ten-stage-map-retained',m.ROUTES==oldm.ROUTES and m.NEW==oldm.NEW and m.TRUSTED==oldm.TRUSTED and list(m.STAGES)==list(oldm.STAGES),{'routes':m.ROUTES,'stages':list(m.STAGES)})
 def actual_rows(audit,ref,kind):
  lines=data(ref).splitlines(keepends=True);assert len(lines)==3 and all(x.endswith(b'\n') for x in lines)
  rows=[m.decode(x) for x in lines];offsets=audit['source_line_offsets'];digests=audit['original_line_sha256'];size=audit['source_prefix_size_observed']
  assert type(size) is int and type(offsets) is list and len(offsets)==3 and offsets==sorted(set(offsets)) and offsets[0]==0
  assert all(type(x) is int and x>=0 for x in offsets)
  with Path(audit['source_audit_path']).open('rb') as f:
   for off,digest,line in zip(offsets,digests,lines):
    assert off+len(line)<=size and sha(line)==digest;f.seek(off);assert f.read(len(line))==line
  header,first,last=rows;assert header['type']=='session_meta' and header['ordinal']==0 and header['payload']['id']==m.THREAD
  assert type(first['ordinal']) is int and type(last['ordinal']) is int and 0<first['ordinal']<last['ordinal']
  report[kind+'_actual_offsets']=[{'offset':x,'sha256':sha(line),'bytes':len(line)} for x,line in zip(offsets,lines)]
  return rows,lines
 rows,lines=actual_rows(author_audit,author_audit['original_capture_ref'],'Source_author')
 meta,final=rows[1:];payload=final['payload'];text=payload['content'][0]['text']
 env='Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+m.AUTHOR_BACKEND+'\nPayload:\n'
 assert text.startswith(env);delivery=m.decode(text[len(env):])
 check('genuine-new-Source-Final-backend-adjacency-time-full-HDF-binding',
       meta['type']=='inter_agent_communication_metadata' and final['type']=='response_item' and final['ordinal']==meta['ordinal']+1
       and meta['timestamp']==final['timestamp'] and final['metadata']['client_authored'] is False
       and payload['type']=='agent_message' and payload['author']==m.AUTHOR_BACKEND and payload['recipient']=='/root'
       and len(payload['content'])==1 and payload['content'][0]['type']=='input_text'
       and author_audit['actor_id']==m.AUTHOR and author_audit['Root_thread_id']==m.THREAD
       and author_audit['binding_sha256']==EXPECTED['HDF.json'][0]
       and EXPECTED['HDF.json'][0] in text and EXPECTED['MF.json'][0] in text
       and delivery['source_author']==m.AUTHOR and delivery['source_author_backend']==m.AUTHOR_BACKEND,
       {'metadata_ordinal':meta['ordinal'],'Final_ordinal':final['ordinal'],'timestamp':final['timestamp'],'actual_backend':payload['author']})
 profiletree=ast.parse(data({'path':str(R/'execution/v2.4/formal_profile_w09.py')}));role=fn(profiletree,'_role_audit')
 peer=next(n for n in ast.walk(role) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and ast.unparse(n.test).startswith("proof['actor_id']"))
 peer_call=peer.orelse[0].value;pred=ast.Expression(peer_call.args[0]);ast.fix_missing_locations(pred)
 def peer_ok(actor,records=rows):
  return eval(compile(pred,'<actual-Main-peer-predicate>','eval'),{'call':records[1],'result':records[2],'payload':records[2]['payload'],'proof':{'actor_id':actor}})
 mutations=[]
 for field,value in [('author',m.AUTHOR),('author','/root'),('recipient','/root/other'),('type','message')]:
  altered=json.loads(json.dumps(rows));altered[2]['payload'][field]=value;mutations.append(not peer_ok(m.AUTHOR_BACKEND,altered))
 check('unchanged-Main-peer-predicate-accepts-this-actual-backend-rejects-relabeling',peer_ok(m.AUTHOR_BACKEND) and not peer_ok(m.AUTHOR) and all(mutations),
       {'Main_function':'_role_audit','predicate_only':True,'Main_module_imported':False,'synthetic_negative_records_never_published':True})
 reviewfn=fn(tree,'source_review');selfcall=next(n for n in ast.walk(reviewfn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='need' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='SOURCE_REVIEW_BINDING')
 selfexpr=ast.Expression(selfcall.args[0]);ast.fix_missing_locations(selfexpr)
 def independent(actor):return eval(compile(selfexpr,'<independent-review-predicate>','eval'),dict(m.__dict__,review={'reviewer_id':actor,'source_ref':h['source_ref']},req={'bridge_source_ref':h['source_ref']}))
 check('four-fixed-author-Root-aliases-cannot-self-review',all(not independent(x) for x in [m.AUTHOR,m.AUTHOR_BACKEND,m.ROOT_ACTOR,'/root']) and independent('/root/full_w09_source_review'))
 reviewtext=ast.unparse(reviewfn)
 check('new-Source-HDF-MF-launcher-exact-reviewed-membership-gates',all(x in reviewtext for x in ['REVIEWED_CONSUMER_LAUNCHER','SOURCE_PACKAGE_REVIEW_BINDING','SOURCE_PACKAGE_MEMBERS','REVIEW_ACTUAL_AUTHOR','profile._role_audit']),
       {'required_decision_fields':['decision','formal_acceptance','reviewer_id','source_ref','source_hdf_ref','source_mf_ref','consumer_launcher_ref'],'synthetic_authority_created':False})
 propose=fn(tree,'propose');common=next(n.value for n in propose.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='common' for t in n.targets))
 kv={k.value:ast.unparse(v) for k,v in zip(common.keys,common.values)}
 check('future-Root-Scope-source-backend-canonical-generation-package-map',kv['source_actor']=='AUTHOR_BACKEND' and kv['source_author_canonical']=='AUTHOR' and kv['generation']=='BRIDGE_GENERATION' and kv['source_hdf_ref']=="req['source_hdf_ref']" and kv['source_mf_ref']=="req['source_mf_ref']",{'Scope_not_created':True,'fields':kv})
 roletext=ast.unparse(fn(tree,'roles'))
 check('role-registry-new-backend-plus-unchanged-full-Main-proof-validation',"AUTHOR_BACKEND in registry['roles']['source_authors']" in roletext and "AUTHOR not in registry['roles']['source_authors']" in roletext and 'profile._role_audit' in roletext)
 mainfn=fn(tree,'main');maintext=ast.unparse(mainfn);rootfn=fn(tree,'root_request');roottext=ast.unparse(rootfn)
 check('all-ten-stage-paths-validate-temp-before-Main-and-recheck-after-hold',maintext.index('require_process_temp()')<maintext.index('root_request(')
       and roottext.index('environment_request(req)')<roottext.index('engine()')
       and maintext.index('guard.acquire(')<maintext.rindex('environment_request(req)')<maintext.index('STAGES[args.stage](')
       and 'guard.close()' in maintext,{'stage_count':len(m.STAGES)})
 parent=m.PUBLIC_TEMP;ancestry=[]
 for p in (parent,*parent.parents):
  st=p.lstat();ancestry.append({'path':str(p),'is_directory':p.is_dir(),'symlink':p.is_symlink(),'junction':p.is_junction(),'reparse':bool(st.st_file_attributes&0x400)})
 check('actual-fixed-C-resource-directory-and-all-ancestors-physical',str(parent)==h['fixed_bridge_TEMP_TMP'] and parent.resolve(strict=True)==parent and all(x['is_directory'] and not any(x[k] for k in ['symlink','junction','reparse']) for x in ancestry),ancestry)
 envtext=ast.unparse(fn(tree,'environment_directory'));cachetext=ast.unparse(fn(tree,'require_process_temp'))
 check('directory-only-exact-C-policy-and-real-cache-without-reset',all(x in envtext for x in ['EXACT_SHARED_TEMP_PARENT','ENVIRONMENT_PATH_ALIAS','ENVIRONMENT_REPARSE','st_file_attributes']) and 'tempfile.gettempdir()' in cachetext and 'ACTUAL_PROCESS_TEMP_CACHE' in cachetext
       and not any(isinstance(x,(ast.Assign,ast.AugAssign)) and 'tempfile' in ast.unparse(x) for x in ast.walk(fn(tree,'require_process_temp'))))
 resource=json.loads(data(m.RESOURCE_PARENT_REF));audit=json.loads(data(m.RESOURCE_AUDIT_REF))
 resrows,reslines=actual_rows(audit,audit['original_capture_ref'],'resource_Root')
 f,l=resrows[1]['payload'],resrows[2]['payload']
 check('resource-only-existing-Root-hostpair-marker-not-a-grant',resource['actor_id']==m.ROOT_ACTOR and resource['resource_scope_only'] is True and resource['execution_grant'] is False
       and resource['RootScope_issued'] is False and resource['Native_calls']==0 and resource['resource_owner_marker_ref']==m.RESOURCE_OWNER_REF
       and resource['exact_parent_paths']==[str(parent.parent),str(parent)]
       and audit['actor_id']==m.ROOT_ACTOR and audit['Root_thread_id']==m.THREAD and audit['binding_sha256']==m.RESOURCE_PARENT_REF['sha256']
       and f['call_id']==l['call_id'] and f['type'] in ['custom_tool_call','function_call'] and l['type'] in ['custom_tool_call_output','function_call_output']
       and m.RESOURCE_PARENT_REF['sha256'] in reslines[1].decode()+reslines[2].decode())
 marker=json.loads(data(m.RESOURCE_OWNER_REF))
 check('exact-current-resource-marker-and-project-identity-held',marker=={'schema':'researchos.w09-native-private-resource-owner.v1','project_id':'aede0678-7308-43dc-b9f2-cfe3d90cfdfb','repository_root':str(R),'scratch_parent':str(parent)} and json.loads(data(resource['project_identity_ref']))['project_id']==marker['project_id'])
 launch=data(h['consumer_launcher_ref']);lt=ast.parse(launch);lf=fn(lt,'main');ltext=ast.unparse(lf)
 check('same-Python-launcher-preflight-pin-cache-resource-before-unchanged-dispatch',ltext.index('bridge.require_process_temp()')<ltext.index('bridge.resource_environment()')<ltext.index('runpy.run_path(')
       and 'BRIDGE_SOURCE_PIN' in ltext and 'EXACT_CONSUMER_ROUTE' in ltext and 'PINNED_MAIN_DISPATCHER' in ltext
       and 'bridge.TRUSTED' in ltext and not any(x in named_calls(lf) for x in ['Popen','system','run_owned','main']),{'launcher_AST_only':True,'dispatcher_invoked':False})
 argvnode=next(n.value for n in ast.walk(lf) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and ast.unparse(t)=='sys.argv' for t in n.targets))
 restoredroutes=[]
 for route in m.ROUTES:
  ex=ast.Expression(argvnode);ast.fix_missing_locations(ex);argv=eval(compile(ex,'<dispatcher-argv-expression>','eval'),{'str':str,'dispatcher':R/'execution/command_dispatcher/dispatch.py','route':route});restoredroutes.append(argv)
 check('all-six-dispatcher-argv-tuples-exactly-retain-original-product-contract',all(a==[str(R/'execution/command_dispatcher/dispatch.py'),r[0],'--task-id','W09','--check-id' if r[1] else '--case-id',r[1] or r[2],'--spec','v2.4'] for r,a in zip(m.ROUTES,restoredroutes)),restoredroutes)
 consume=ast.unparse(fn(tree,'consume'))
 check('consumer-parent-new-launcher-pin-plus-retained-OwnedJob-failure-order',"HERE / 'consumer_launch.source.py'" in consume and "req['bridge_source_ref']['sha256']" in consume
       and "req['bridge_source_ref']['bytes']" in consume and 'environment_directory' in consume and 'USERPROFILE' in consume
       and consume.index("record['observation'] = result")<consume.index("record['stdout_ref']")
       and 'FIRST_CHILD_FAILURE_STOP' in consume and 'helper.run_owned' in consume)
 report['status']='PASSED_SOURCE_ONLY';report['held_input_refs']=list(allrefs.values());report['independent_controls_passed']=len(checks);report['findings_resolved']=['BRIDGE-ROLE-001','BRIDGE-TEMP-002']
except BaseException as exc:
 report['status']='FAILED';report['error']=repr(exc)
 raise
finally:
 closed=guard.close();report['guard_closed']=closed['closed'];report['retained_handles_count']=closed['retained_handles_count']
 save('source-guard.closed.json',closed);save('finite-delta-review.json',report)
 assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
 print(json.dumps({'review_ref':pin(D/'finite-delta-review.json'),'guard_ref':pin(D/'source-guard.closed.json'),'status':report.get('status'),'passed':sum(x['passed'] for x in checks),'held_refs':len(allrefs),'guard_retained':closed['retained_handles_count']},ensure_ascii=False))
