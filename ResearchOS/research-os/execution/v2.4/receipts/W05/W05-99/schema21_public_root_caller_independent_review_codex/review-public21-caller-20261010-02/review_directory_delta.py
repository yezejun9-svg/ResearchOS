from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,types

R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
N=B/'schema21_public_root_caller_source_codex/s21public-caller-20261010-02'
O=B/'schema21_public_root_caller_source_codex/s21public-caller-20261010-01'
D=B/'schema21_public_root_caller_independent_review_codex/review-public21-caller-20261010-02'
V=B/'schema21_public_root_caller_independent_review_codex/review-public21-caller-20261010-01'
P=R/'execution/v2.4/receipts/W09/W09-99/full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
EXPECTED={'HDF.json':('f75d4c1c19349967e4ffe1ed1ed5b71e2c64208febc8a032f72cdda25221099a',12799),
 'MF.json':('29552bbf6ffaeb3c51c51f23945a3c9bff5f8d1cbc3cc3cf8e08714eeae6ed7a',10562),
 'public21_root.source.py':('36b971f853b257d58499dab05eee51f87c9f1ffabb5f3c4cfd6724f201a53021',55369),
 'root-calling-contract.source.json':('2fe0cc10bcca08501f9b98ae3b79d55b8a98336f6bf98767b0b432877b55b4d5',25434)}
def pin(p):
 p=Path(p);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def load(p):return json.loads(Path(p).read_bytes())
def write(name,value):
 with (D/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
 return pin(D/name)
support=types.ModuleType('public21_directory_review_support');support.__file__=str(P)
exec(compile(P.read_bytes(),str(P),'exec'),support.__dict__);support.D=D
origin=support.capture('b63c6a',1,1,1149)
write('original1149.failure-origin.json',{'schema':'researchos.public21-independent-review-original-failure.v1','ordinal':1149,
 'chunk_id':'b63c6a','actual_outer_exit':1,'actual_python_exit':1,'actual_Native_Go_SQL_model_TP_exits':None,
 'cause':'Reviewer AST query assumed a nonexistent top-level own_source function; StopIteration before guard acquisition.',
 'original_complete_IO':origin,'guard_acquisitions':0,'product_calls':0,'failure_count_reset':False,'retry_original_command':False})
h=load(N/'HDF.json');mf=load(N/'MF.json');allrefs={}
def add(ref):
 ref={k:ref[k] for k in ('path','sha256','bytes')};ref['path']=str(Path(ref['path']));prev=allrefs.get(ref['path']);assert prev is None or prev==ref;allrefs[ref['path']]=ref
def refs(v):
 if type(v) is dict:
  if {'path','sha256','bytes'}<=set(v):yield v
  else:
   for x in v.values():yield from refs(x)
 elif type(v) is list:
  for x in v:yield from refs(x)
for name,(sha,size) in EXPECTED.items():add({'path':str(N/name),'sha256':sha,'bytes':size})
for ref in mf['members']:add(ref)
for ref in refs(h):
 # Only full new publication, delta inputs, direct fixed Source links and immutable witnesses.
 # No recursive historical resource closure or Canon business expansion.
 if not Path(ref['path']).is_relative_to(B/'genuine_schema21_public_bootstrap_runner_source_codex'):
  add(ref)
for name in ['HDF.json','MF.json','source-decision.json']:add(pin(V/name))
for name in ['public21_root.source.py','source-inputs.json','root-calling-contract.source.json']:add(pin(O/name))
add(support.GREF)
author_audit_ref={'path':str(R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.public21-caller02-author.actual-audit.root.json'),'sha256':'b42abf6c52c882aed2a63eec7b67b26dc4b99b88c42a7590addc48de16165823','bytes':1119}
add(author_audit_ref);author_audit=load(author_audit_ref['path']);add(author_audit['original_capture_ref'])
guard=support.guard();checks=[]
report={'schema':'researchos.public21-caller02-independent-directory-delta.v1','review_author':'codex:/root/full_w09_source_review',
 'source_author':h['source_author'],'reviewed_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,
 'author13_old58_353_17_4154_rerun':False,'Source_review_only':True,'RootScope_issued':False,
 'runtime_qualification_issued':False,'actual_prepare_propose_check_activate_execute_calls':0,
 'actual_Leaf_Native_Go_SQLconnection_model_TP_calls':0,'live_Canon_held':False,'original1149_ref':pin(D/'original1149.failure-origin.json'),
 'execution_grant':False,'formal_acceptance':False}
def check(name,passed,details=None):
 checks.append({'name':name,'passed':bool(passed),'details':details})
 if not passed:raise AssertionError(name)
try:
 guard.acquire(list(allrefs.values()))
 def data(ref):return guard.get_buffer(ref['path'])
 source=data(h['caller_ref']);old=guard.get_buffer(str(O/'public21_root.source.py'));tree=ast.parse(source);oldtree=ast.parse(old)
 inv=json.loads(data(h['directory_inverse_ref']))
 before,after=inv['before_utf8'].encode('utf-8'),inv['after_utf8'].encode('utf-8')
 restored=source[:inv['new_start']]+before+source[inv['new_end']:]
 check('entire-Caller02-inverse-restores-original133-byte-delta',source[inv['new_start']:inv['new_end']]==after and old[inv['old_start']:inv['old_end']]==before and restored==old and len(source)-len(old)==133,{'inverse_ref':h['directory_inverse_ref']})
 oldnodes={n.name:n for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};newnodes={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 unchanged=[n for n in oldnodes if n!='safe_directory']
 check('all-other-functions-classes-and-top-level-metadata-unchanged',set(oldnodes)==set(newnodes) and all(ast.dump(oldnodes[n],include_attributes=False)==ast.dump(newnodes[n],include_attributes=False) for n in unchanged)
       and ast.dump(ast.Module(body=[n for n in oldtree.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))],type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=[n for n in tree.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))],type_ignores=[]),include_attributes=False),{'unchanged_functions_classes':len(unchanged),'names':unchanged})
 func=newnodes['safe_directory'];text=ast.unparse(func)
 check('strict-file-canonical-remains-first-with-separate-directory-comparison',ast.dump(func.body[0],include_attributes=False)==ast.dump(oldnodes['safe_directory'].body[0],include_attributes=False)
       and "canonical(str(path))" in text and "ntpath.normcase(str(ancestor.resolve(strict=True))) == ntpath.normcase(str(ancestor.absolute()))" in text
       and "getattr(ancestor.lstat(), 'st_file_attributes', 0) & 1024" in text)
 m=types.ModuleType('caller02_independent_directory');m.__file__=str(N/'public21_root.source.py');exec(compile(source,m.__file__,'exec'),m.__dict__)
 # Inert OC3/Guard are the exact Source already held, never their product branches.
 m.base();assert pin(Path(m.OC3_REF['path']))==m.OC3_REF
 observed=m.safe_directory(D,new=False)
 check('real-review-directory-all-ancestors-including-drive-root-complete',observed==D,{'path':str(D),'drive_root':str(D.parents[-1]),'directory_created_by_gate':False})
 def refusal(call,code):
  try:call()
  except ValueError as exc:return str(exc)==code
  return False
 absent=D/'never-created-after-directory-review';missing_parent=absent/'second-level'
 check('new-existing-absent-and-missing-parent-boundaries-preserved',refusal(lambda:m.safe_directory(D,new=True),'DIRECTORY_EXISTENCE')
       and refusal(lambda:m.safe_directory(absent,new=False),'DIRECTORY_EXISTENCE')
       and refusal(lambda:m.safe_directory(missing_parent,new=True),'DIRECTORY_EXISTENCE')
       and not absent.exists() and not missing_parent.exists())
 check('existing-regular-file-cannot-be-treated-as-directory',refusal(lambda:m.safe_directory(D/'review_directory_delta.py',new=False),'DIRECTORY_EXISTENCE'))
 # A pure AST metadata counterexample places each alias condition in a parent,
 # not in the candidate leaf. No symlink/junction/reparse is created.
 body=next(n for n in ast.walk(func) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='need' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='DIRECTORY_ALIAS')
 expr=ast.fix_missing_locations(ast.Expression(body.args[0]))
 class ParentMetadata:
  def __init__(self,kind):self.kind=kind
  def is_symlink(self):return self.kind=='symlink'
  def is_junction(self):return self.kind=='junction'
  def lstat(self):return types.SimpleNamespace(st_file_attributes=0x400 if self.kind=='reparse' else 0)
  def resolve(self,strict=True):return 'D:\\wrong-target' if self.kind=='resolve_alias' else 'D:\\'
  def absolute(self):return 'D:\\'
 def ancestor_allowed(kind):return eval(compile(expr,'<pure-parent-directory-metadata>','eval'),{'ancestor':ParentMetadata(kind),'ntpath':m.ntpath,'getattr':getattr,'str':str})
 check('drive-root-parent-metadata-accepts-ordinary-and-rejects-each-alias',ancestor_allowed('ordinary') and all(not ancestor_allowed(k) for k in ['symlink','junction','reparse','resolve_alias']),{'synthetic_predicate_only':True,'real_files_created':False})
 # Existing author13 denylist results are evidence, not replayed controls.
 author=json.loads(data(h['source_controls_ref']));strict_prefix_codes={row['name']:row['evidence']['error'] for row in author['controls'] if row['name'] in ['reject_UNC','reject_extended_namespace','reject_device_namespace','reject_ADS','reject_traversal']}
 check('unchanged-strict-OC3-Guard-denylist-evidence-reused',len(strict_prefix_codes)==5 and all(row['passed'] for row in author['controls']) and m.OC3_REF==h['OC3_source_ref'],strict_prefix_codes)
 check('file-reference-drive-root-still-refused',refusal(lambda:m.canonical('D:\\'),'reference path must have regular file components'),{'file_ref_gate_not_relaxed':True})
 contract=json.loads(data(h['contract_ref']));oldcontract=json.loads(guard.get_buffer(str(O/'root-calling-contract.source.json')))
 changed={k for k in set(contract)|set(oldcontract) if contract.get(k)!=oldcontract.get(k)}
 check('contract-changes-only-current-caller-and-directory-revision',changed=={'caller_ref','directory_gate_revision'} and contract['caller_ref']==h['caller_ref'],{'changed_fields':sorted(changed)})
 kernel=m.kernel();own_ast=next(n for n in ast.parse(guard.get_buffer(m.OC3_REF['path'])).body if isinstance(n,ast.FunctionDef) and n.name=='own_review');owntext=ast.unparse(own_ast)
 # This Source interface chooses Source HDF.registrar_ref, never contract.registrar_ref.
 currentfields={'source_hdf_ref':pin(N/'HDF.json'),'source_mf_ref':pin(N/'MF.json'),'caller_ref':h['caller_ref'],'registrar_ref':h['registrar_ref'],'calling_contract_ref':h['contract_ref']}
 check('actual-own-review-current-HDF-caller-registrar-and-decision-fields',h['caller_ref']==h['registrar_ref']==pin(N/'public21_root.source.py')
       and "same_ref(source['caller_ref'], pin(__file__))" in owntext and "same_ref(source['registrar_ref'], pin(__file__))" in owntext
       and 'CALLER_DECISION_REF_BINDING' in owntext and contract['source_review_contract']['caller']['decision_verdict']=='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION',currentfields)
 report['contract_metadata_note']={'field':'root-calling-contract.source.json.registrar_ref','value':contract['registrar_ref'],
  'classification':'STALE_NONEXECUTABLE_METADATA','actual_consumer':'specialized OC3 own_review consumes Source HDF.registrar_ref and current __file__, not contract.registrar_ref',
  'current_registration_ref':h['registrar_ref'],'Root_must_bind_current_Source_HDF_and_current_Caller02':True,
  'recommendation':'Refresh this contract metadata in a future sealed revision; do not route execution to historical Caller01.'}
 inp=json.loads(data(h['source_inputs_ref']));oldinp=json.loads(guard.get_buffer(str(O/'source-inputs.json')))
 inpchanges={k for k in set(inp)|set(oldinp) if inp.get(k)!=oldinp.get(k)}
 check('prior-runtime-resource-and-Leaf-declarations-inherited-without-replay',inp['references']==oldinp['references'] and inpchanges=={'directory_revision'}, {'changed_input_fields':sorted(inpchanges),'353_resources_revalidated':False})
 witnesses=h['Root_original1146_and_Task102_witnesses'];witness_rows=[]
 for item in witnesses:
  audit=json.loads(data(item['witness_ref']));raw=data(item['original_capture_ref']);lines=raw.splitlines(keepends=True)
  assert len(lines)==3 and all(x.endswith(b'\n') for x in lines);assert audit['source_line_offsets']==item['source_offsets']
  with Path(audit['source_audit_path']).open('rb') as stream:
   for off,digest,line in zip(audit['source_line_offsets'],audit['original_line_sha256'],lines):
    assert type(off) is int and off+len(line)<=audit['source_prefix_size_observed'] and hashlib.sha256(line).hexdigest()==digest
    stream.seek(off);assert stream.read(len(line))==line
  witness_rows.append({'actor':item['actor'],'witness_ref':item['witness_ref'],'original_capture_ref':item['original_capture_ref'],'original_offset_bytes_confirmed':True})
 check('original1146-and-Task102-three-line-source-evidence-retained',len(witness_rows)==2,witness_rows)
 lines=data(author_audit['original_capture_ref']).splitlines(keepends=True);assert len(lines)==3 and all(x.endswith(b'\n') for x in lines)
 rows=[json.loads(line) for line in lines];header,meta,final=rows;body=final['payload'];actualtext=body['content'][0]['text']
 with Path(author_audit['source_audit_path']).open('rb') as stream:
  for off,digest,line in zip(author_audit['source_line_offsets'],author_audit['original_line_sha256'],lines):
   assert type(off) is int and off+len(line)<=author_audit['source_prefix_size_observed'] and hashlib.sha256(line).hexdigest()==digest
   stream.seek(off);assert stream.read(len(line))==line
 envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/backup_regression_resources\nPayload:\n'
 assert actualtext.startswith(envelope)
 def strictpairs(pairs):
  value={}
  for k,v in pairs:
   if k in value:raise ValueError('DUPLICATE_SOURCE_DELIVERY_KEY')
   value[k]=v
  return value
 def badnumber(value):raise ValueError(value)
 delivery=json.loads(actualtext[len(envelope):],object_pairs_hook=strictpairs,parse_constant=badnumber)
 delivered_refs=list(refs(delivery))
 check('actual-Caller02-author-anchored-Final-original-offsets-and-fullrefs',header['type']=='session_meta' and header['payload']['id']==m.ROOT_THREAD
       and meta['type']=='inter_agent_communication_metadata' and final['type']=='response_item' and final['ordinal']==meta['ordinal']+1
       and meta['timestamp']==final['timestamp'] and final['metadata']['client_authored'] is False
       and body['type']=='agent_message' and body['author']=='/root/backup_regression_resources' and body['recipient']=='/root'
       and author_audit['actor_id']==m.AUTHOR and author_audit['Root_thread_id']==m.ROOT_THREAD
       and author_audit['binding_sha256']==EXPECTED['HDF.json'][0]
       and delivery['source_author']==m.AUTHOR and all(ref in delivered_refs for ref in [currentfields['source_hdf_ref'],currentfields['source_mf_ref'],h['caller_ref'],h['contract_ref']]),
       {'audit_ref':author_audit_ref,'raw_ref':author_audit['original_capture_ref'],'source_offsets':author_audit['source_line_offsets'],'metadata_ordinal':meta['ordinal'],'Final_ordinal':final['ordinal'],'timestamp':final['timestamp']})
 report['status']='PASSED_SOURCE_ONLY';report['held_refs']=list(allrefs.values());report['new_independent_checks_passed']=len(checks);report['current_Source_bindings']=currentfields
 report['prior_Task99_review_refs']={name:pin(V/name) for name in ['HDF.json','MF.json','source-decision.json']}
except BaseException as exc:
 report['status']='FAILED';report['error']=repr(exc);raise
finally:
 closed=guard.close();guardref=write('source-guard.closed.json',closed);report['all_guards_closed']=closed['closed'];report['retained_handles_count']=closed['retained_handles_count']
 reviewref=write('finite-directory-delta-review.json',report)
 assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
 print(json.dumps({'status':report.get('status'),'passed':sum(x['passed'] for x in checks),'guard_closed':closed['closed'],'held_refs':len(allrefs),'review_ref':reviewref,'guard_ref':guardref,'original1149':origin},ensure_ascii=False))
