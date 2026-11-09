"""Independent, finite Source-only review. No runtime qualification or Root grant."""
import ast,copy,hashlib,json,ntpath,os,types
from datetime import datetime,timedelta,timezone
from pathlib import Path
W=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
D=Path(__file__).resolve().parent
S=W/'fresh_main23_root_caller_registration_source_codex/main23root-20261010-04'
OLD=W/'fresh_main23_root_caller_registration_source_codex/main23root-20261009-03'
PR=W/'fresh_main23_root_caller_registration_independent_source_review_codex/review-20261010-03'
T=W/'main23_qualification_time_contract_independent_review_codex/review-20261010-01'
G=W/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
ACTOR='codex:/root/full_w09_source_review'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def key(r):return (ntpath.normcase(ntpath.normpath(r['path'])),r['sha256'],r['bytes'])
def unique(refs):
 values={}
 for r in refs:
  k=key(r)[0]
  if k in values:assert key(values[k])==key(r),'CONFLICTING_REF'
  values.setdefault(k,r)
 return list(values.values())
def save(name,v):
 with (D/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/name)
def inert(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def pure_parts(m,tree):
 funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
 rt=funcs['runtime_review_chain'];pj=next(n for n in rt.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='projected' for t in n.targets))
 needs={n.value.args[-1].value:n for n in rt.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='need' and isinstance(n.value.args[-1],ast.Constant)}
 peer=funcs['validate_peer_delivery'];i=next(i for i,n in enumerate(peer.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='text' for t in n.targets))
 j=next(i for i,n in enumerate(peer.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and n.value.args and isinstance(n.value.args[-1],ast.Constant) and n.value.args[-1].value=='PEER_REVIEW_REF_BINDING')
 def fn(name,args,body):return ast.FunctionDef(name=name,args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=a) for a in args],vararg=None,kwonlyargs=[],kw_defaults=[],kwarg=None,defaults=[]),body=copy.deepcopy(body),decorator_list=[])
 a=fn('SOURCE_ONLY_time',('qualification','payload','scope','review','received','root_binding'),[pj,needs['QUALIFICATION_PAYLOAD_EXACT_BINDING'],needs['RUNTIME_ORIGINAL_REVIEW_ISSUANCE_TIME_ORDER']])
 b=fn('SOURCE_ONLY_peer',('payload','expected_refs','peer_actor','operation'),[peer.body[0],*peer.body[i:j+1],ast.Return(value=ast.Name(id='delivered',ctx=ast.Load()))])
 tree=ast.fix_missing_locations(ast.Module(body=[a,b],type_ignores=[]));ns=dict(m.__dict__);exec(compile(tree,str(S/'main23_root.source.py')+'#SOURCE_INTERFACE_ONLY','exec'),ns)
 return ns['SOURCE_ONLY_time'],ns['SOURCE_ONLY_peer'],ast.unparse(tree)
def diffs(a,b,p=''):
 if type(a) is dict and type(b) is dict:
  return sum((diffs(a[k],b[k],p+'/'+k) if k in a and k in b else [p+'/'+k] for k in sorted(a.keys()|b.keys())),[])
 return [] if a==b else [p]
def main():
 h=read(S/'HDF.json');mf=read(S/'MF.json');inputs=read(S/'source-inputs.json');oldinputs=read(OLD/'source-inputs.json');pr=read(PR/'HDF.json');task58=read(T/'decision.json')
 oldkeys={key(r) for r in oldinputs['references']};added=[r for r in inputs['references'] if key(r) not in oldkeys]
 observations=next(f for f in task58['findings'] if f['id']=='M3-PEER-FINAL-02')['actual_peer_observations']
 refs=unique([pin(__file__),pin(G),pin(S/'HDF.json'),h['manifest_ref'],*mf['members'],*added,pin(OLD/'HDF.json'),pin(OLD/'main23_root.source.py'),pin(OLD/'root-calling-contract.source.json'),pin(OLD/'source-inputs.json'),pin(PR/'HDF.json'),pr['manifest_ref'],pr['source_decision_ref'],pr['finitechecks_ref'],pr['Source_guard_ref'],pin(T/'decision.json'),*[r for o in observations for r in (o['raw_ref'],o['binding_ref'])]])
 gm=inert(G,'independent_M4_Source_guard');guard=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 checks=[];failed=[];details={}
 def check(name,fn,reject=False):
  try:
   value=fn()
   if reject:raise AssertionError('EXPECTED_REJECTION_NOT_OBSERVED')
   if value is False:raise AssertionError('CONDITION_FALSE')
   checks.append(dict(name=name,passed=True,kind='FINITE_SOURCE_ONLY'))
  except (ValueError,TypeError,KeyError,AssertionError) as e:
   ok=reject and not isinstance(e,AssertionError)
   row=dict(name=name,passed=ok,kind='FINITE_SOURCE_ONLY',error_type=type(e).__name__,error=str(e));checks.append(row)
   if not ok:failed.append(row)
 def ensure(v):
  if not v:raise ValueError('INDEPENDENT_SOURCE_CONDITION')
 try:
  guard.acquire(refs)
  check('official_Root_four_pins',lambda:ensure([(pin(S/n)['sha256'],pin(S/n)['bytes']) for n in ('HDF.json','MF.json','main23_root.source.py','root-calling-contract.source.json')]==[('348034a2f2f23342f6a309ed14ffe64183a3bbb031ed79d6c8ed5facf34c0fd3',32853),('dd65dabdff33ccc10b229222992cf7db5702837c60cd7ed565769248c09e88c1',22750),('85ec3da49ab65741d1f1a8a94996c55f22d3b2394959e641bb3f0bd4b694f75e',56626),('5b76f0351baa53dd3fc1b66d306f389b0c084cffcaa393e698bd36ee6f026fd0',21411)]))
  check('66_MF_members_held_and_independent',lambda:ensure(len(mf['members'])==66 and len({key(r)[0] for r in mf['members']})==66 and ACTOR not in (h['source_author'],h['builder_source_author'],'codex:/root')))
  check('Source_status_no_authorization',lambda:ensure(h['status']=='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING' and h['authority']=='NONE' and h['formal_acceptance'] is False and h['future_Root_grant_ref'] is None))
  for r in refs:check('held_pin:'+r['path'],lambda r=r:ensure(key(pin(r['path']))==key(r)))
  original=(OLD/'main23_root.source.py').read_bytes();candidate=(S/'main23_root.source.py').read_bytes();inverse=read(S/'exact-inverse.json');restored=candidate
  for edit in sorted(inverse['edits'],key=lambda x:x['new_offset'],reverse=True):
   start=edit['new_offset'];after=bytes.fromhex(edit['after_hex']);before=bytes.fromhex(edit['before_hex'])
   check('inverse_fragment:'+edit['label'],lambda s=start,a=after:ensure(restored[s:s+len(a)]==a))
   restored=restored[:start]+before+restored[start+len(after):]
  check('independently_rebuilt_full_original_byte_inverse',lambda:ensure(restored==original and len(inverse['edits'])==3))
  oldtree=ast.parse(original);tree=ast.parse(candidate);oldfn={n.name:ast.dump(n,include_attributes=False) for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};newfn={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  changed=[n for n in oldfn if oldfn[n]!=newfn.get(n)]
  check('only_two_logic_functions_changed',lambda:ensure(set(changed)=={'validate_peer_delivery','runtime_review_chain'} and oldfn.keys()==newfn.keys()))
  for n in oldfn:
   if n not in changed:check('unchanged_gate:'+n,lambda n=n:ensure(oldfn[n]==newfn[n]))
  contract=read(S/'root-calling-contract.source.json');oc=read(OLD/'root-calling-contract.source.json');paths=diffs(oc,contract)
  allowed={'/caller_ref/path','/caller_ref/sha256','/caller_ref/bytes','/registrar_ref/path','/registrar_ref/sha256','/registrar_ref/bytes','/source_inputs_ref/path','/source_inputs_ref/sha256','/source_inputs_ref/bytes','/future_binding_policy','/runtime_qualification/fields','/runtime_qualification/payload_rule','/runtime_qualification/time_order','/runtime_qualification/creation_rule','/runtime_qualification/wrapper_created_utc_semantics','/runtime_qualification/payload_created_utc_semantics','/actual_peer_delivery/content_rule','/M4_minimum_revision'}
  check('contract_delta_confined_to_time_peer_and_current_refs',lambda:ensure(set(paths)<=allowed))
  check('old_input_refs_preserved_exactly',lambda:ensure(oldkeys<={key(r) for r in inputs['references']} and oldinputs['creation_baseline']==inputs['creation_baseline']))
  pc=read(pr['finitechecks_ref']['path']);pg=read(pr['Source_guard_ref']['path'])
  check('reuse_14782_accepted_checks_without_rerun',lambda:ensure(len(pc['checks'])==14782 and pc['failed']==[] and pg['closed'] and pg['retained_handles_count']==0 and pg['errors']==[]))
  details['reuse_basis']=dict(prior_hdf_ref=pin(PR/'HDF.json'),prior_finitechecks_ref=pr['finitechecks_ref'],prior_guard_ref=pr['Source_guard_ref'],prior_accepted_checks=14782,unchanged_14670_pins_reused=True,prior_product_checks_rerun=0,complete_caller_inverse=True,old_input_refs_preserved=True)
  for k in ('Source_guard_ref','finite_controls_guard_ref','construction_guard_ref'):
   v=read(h[k]['path']);check('author_guard_closed:'+k,lambda v=v:ensure(v.get('retained_handles_count',v.get('retained_handles',None))==0 and v.get('all_handles_closed',v.get('closed')) is True))
  m=inert(S/'main23_root.source.py','M4_independent_inert_no_product');tc,peerc,expr=pure_parts(m,tree);save('exact-Source-interface-expressions.json',dict(caller_ref=h['caller_ref'],status='SOURCE_ONLY_INTERFACE_CHECKS_NOT_QUALIFICATION',expression=expr))
  base=datetime.now(timezone.utc)-timedelta(minutes=10);stamps=[base+timedelta(seconds=30*i) for i in range(7)]
  def fixture(times=stamps):
   scope,review,received,payload,call,out,wrapper=times
   q=dict(schema='researchos.root-main23-qualified-runtime.v2',payload_created_utc=payload.isoformat(),created_utc=wrapper.isoformat(),payload_ref='SOURCE_ONLY_NO_ACTUAL_REF',root_issuance_binding_ref='SOURCE_ONLY_NO_ROOT_GRANT',resource_refs=['SOURCE_ONLY_INTERFACE'],issued_by='SOURCE_ONLY_NO_REAL_AUTHORITY')
   p={k:copy.deepcopy(v) for k,v in q.items() if k not in ('schema','created_utc','payload_ref','root_issuance_binding_ref')};p['schema']='researchos.root-main23-runtime-qualification-payload.v2'
   return [q,p,dict(created_utc=scope.isoformat()),dict(reviewed_utc=review.isoformat()),received,dict(tool_call_timestamp=call.isoformat(),tool_result_timestamp=out.isoformat())]
  check('distinct_causal_times_are_implementable_Source_condition_only',lambda:tc(*fixture()))
  for i,name in enumerate(('scope_review','review_receipt','receipt_payload','payload_call','call_output','output_wrapper')):
   times=list(stamps);times[i]=times[i+1]+timedelta(seconds=1);check('reject_reverse_'+name,lambda ts=times:tc(*fixture(ts)),True)
  times=list(stamps);times[-1]=datetime.now(timezone.utc)+timedelta(minutes=1);check('reject_future_wrapper',lambda:tc(*fixture(times)),True)
  times=list(stamps);times[3]=datetime.now(timezone.utc)+timedelta(minutes=1);check('reject_future_payload',lambda:tc(*fixture(times)),True)
  for name in ('payload_created_utc','created_utc','resource_refs','issued_by'):
   f=fixture();f[1][name]='SOURCE_ONLY_CHANGED';check('reject_payload_binding_'+name,lambda f=f:tc(*f),True)
  f=fixture();del f[0]['payload_created_utc'];del f[1]['payload_created_utc'];check('reject_missing_payload_time',lambda:tc(*f),True)
  f=fixture();f[0]['created_utc']=f[0]['created_utc'].split('+')[0];check('reject_naive_wrapper',lambda:tc(*f),True)
  examples=[]
  for ob in observations:
   binding=read(ob['binding_ref']['path']);raw=Path(ob['raw_ref']['path']).read_bytes();lines=raw.splitlines(keepends=True);header,meta,message=[m.strict(x) for x in lines];p=message['payload'];actor=binding['actual_peer_actor']
   check('actual_peer_'+str(ob['ordinal'])+'_3_line_pins',lambda:ensure(len(lines)==3 and [len(x) for x in lines]==binding['source_line_bytes'] and [hashlib.sha256(x).hexdigest() for x in lines]==binding['original_line_sha256']))
   with Path(binding['source_audit_path']).open('rb') as stream:
    for off,line in zip(binding['source_line_offsets'],lines):
     stream.seek(off);check('actual_peer_original_offset:'+str(off),lambda off=off,line=line:ensure(off+len(line)<=binding['source_prefix_size_observed'] and stream.read(len(line))==line))
   check('actual_peer_metadata_actor_id_'+str(ob['ordinal']),lambda:ensure(header['payload']['id']==ROOT_THREAD and meta['type']=='inter_agent_communication_metadata' and meta['ordinal']+1==message['ordinal']==ob['ordinal'] and meta['timestamp']==message['timestamp'] and p['author']==actor.removeprefix('codex:') and p['recipient']=='/root' and message['metadata']['client_authored'] is False and p['id']==binding['actual_message_id'] and message['timestamp']==binding['actual_received_at'] and binding['qualifying_root_binding'] is False))
   body=p['content'][0]['text'];expected=ob['observed_delivered_refs'];op=ob['operation'];prefix=ob['exact_envelope_prefix'];plain=body[len(prefix):]
   check('actual_FINAL_'+str(ob['ordinal'])+'_M4_exact_decoder',lambda:peerc(p,expected,actor,op))
   def withtext(value):
    v=copy.deepcopy(p);v['content'][0]['text']=value;return v
   check('actual_plain_JSON_'+str(ob['ordinal'])+'_compatibility',lambda:peerc(withtext(plain),expected,actor,op))
   check('M3_Root_decoder_is_still_unchanged_and_has_zero_typed_FINAL_'+str(ob['ordinal']),lambda:ensure(not [v for v in m.structured_documents(body) if type(v) is dict and v.get('schema')=='researchos.main23-peer-review-delivery.v2']))
   negatives={'sender':body.replace('Sender: '+p['author'],'Sender: /root/wrong_peer',1),'recipient':body.replace('Task name: /root\n','Task name: /root/wrong\n',1),'type':body.replace('Message Type: FINAL_ANSWER','Message Type: MESSAGE',1),'unanchored':'x\n'+body,'leading_newline':'\n'+body,'trailing_text':body+'\nEXTRA','trailing_JSON':body+'\n{}','duplicate':prefix+'{"schema":"researchos.main23-peer-review-delivery.v2",'+plain.lstrip()[1:],'nonfinite':prefix+plain.replace('"formal_acceptance": false','"formal_acceptance": NaN',1)}
   for name,text in negatives.items():check('actual_'+str(ob['ordinal'])+'_reject_'+name,lambda text=text:peerc(withtext(text),expected,actor,op),True)
   decoded=m.strict(plain)
   for name,value in [('review_author',m.CALLER_AUTHOR),('root_thread_id','WRONG'),('operation','WRONG'),('execution_grant',True),('formal_acceptance',True),('verdict','WRONG')]:
    changedbody=copy.deepcopy(decoded);changedbody[name]=value;check('actual_'+str(ob['ordinal'])+'_reject_typed_'+name,lambda d=changedbody:peerc(withtext(prefix+json.dumps(d)),expected,actor,op),True)
   for name,value in [('path','D:/wrong'),('sha256','0'*64),('bytes',expected[0]['bytes']+1)]:
    changedbody=copy.deepcopy(decoded);changedbody['review_refs'][0][name]=value;check('actual_'+str(ob['ordinal'])+'_reject_ref_'+name,lambda d=changedbody:peerc(withtext(prefix+json.dumps(d)),expected,actor,op),True)
   for forbidden in (m.ROOT,m.CALLER_AUTHOR,m.BUILDER_AUTHOR,'codex:/unregistered'):
    check('actual_'+str(ob['ordinal'])+'_reject_actor_'+forbidden,lambda a=forbidden:peerc(p,expected,a,op),True)
   examples.append(dict(ordinal=ob['ordinal'],raw_ref=ob['raw_ref'],binding_ref=ob['binding_ref'],decoder_passed=True,all_original_offsets_verified=True,qualification_or_Root_grant=False))
  index=read(h['actual_Source_tool_index_ref']['path']);actual=[]
  for pair in index['actual_pairs']:
   binding=read(pair['binding_ref']['path']);lines=Path(pair['raw_ref']['path']).read_bytes().splitlines(keepends=True);head,call,result=[m.strict(x) for x in lines]
   check('author_actual_pair_pins:'+binding['original_call_id'],lambda:ensure(len(lines)==3 and [len(x) for x in lines]==binding['source_line_bytes'] and [hashlib.sha256(x).hexdigest() for x in lines]==binding['original_line_sha256'] and key(pair['raw_ref'])==key(binding['original_capture_ref'])))
   with Path(binding['source_audit_path']).open('rb') as stream:
    for off,line in zip(binding['source_line_offsets'],lines):
     stream.seek(off);check('author_original_offset:'+str(off),lambda off=off,line=line:ensure(off+len(line)<=binding['source_prefix_size_observed'] and stream.read(len(line))==line))
   check('author_actual_identity:'+binding['original_call_id'],lambda:ensure(head['payload']['id']==h['source_thread_id'] and head['payload']['agent_path']==h['actual_agent_path'] and head['payload']['parent_thread_id']==ROOT_THREAD and call['payload']['call_id']==result['payload']['call_id']==binding['original_call_id'] and call['ordinal']<result['ordinal']))
   hosts=[v for v in m.structured_documents(result['payload']['output']) if type(v) is dict and type(v.get('chunk_id')) is str and type(v.get('output')) is str]
   actual.append(dict(call_id=binding['original_call_id'],raw_ref=pair['raw_ref'],binding_ref=pair['binding_ref'],actual_hosts=[dict(chunk_id=v['chunk_id'],outer_exit=v.get('exit_code'),Python_exit=(1 if 'Python_exit=1' in v['output'] or 'ROOT_PYTHON_EXIT=1' in v['output'] else 0 if 'Python_exit=0' in v['output'] or 'ROOT_PYTHON_EXIT=0' in v['output'] else None)) for v in hosts]))
  failure=read(h['original1064_ref']['path']);check('original1064_preserved_no_new_number',lambda:ensure('1064' in json.dumps(failure) and key(h['original1064_raw_hostpair_ref'])==key(index['original1064_pair']['raw_ref'])))
  details.update(dict(changed_logic_functions=changed,contract_changed_paths=paths,added_resource_refs=added,actual_peer_examples=examples,actual_Source_hostpairs=actual,original1064_ref=h['original1064_ref'],product_processes=0,actual_runtime_qualification=None,actual_Root_scope=None,actual_Root_witness=None,source_only_condition_fixtures=True))
 finally:
  closed=guard.close();closed_ref=save('delta-Source-guard.closed.json',closed)
 check('independent_all_guards_final_closed0',lambda:ensure(closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]))
 result_ref=save('finitechecks.json',dict(schema='researchos.main23-M4-independent-finite-Source-checks.v1',review_author=ACTOR,reviewer_thread_id=os.environ['CODEX_THREAD_ID'],status='ACCEPTED_SOURCE_ONLY' if not failed else 'CHANGES_REQUIRED',checks=checks,failed=failed,details=details,Source_guard_ref=closed_ref,held_refs=len(refs),execution_grant=False,formal_acceptance=False))
 print(json.dumps(dict(finitechecks_ref=result_ref,Source_guard_ref=closed_ref,checks=len(checks),failed=failed,status='ACCEPTED_SOURCE_ONLY' if not failed else 'CHANGES_REQUIRED',held_refs=len(refs),retained_handles=closed['retained_handles_count'],product_processes=0),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
