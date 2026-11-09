import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent;B=N.parents[1]
C=B/'checkpoint_r367_scope_namespace_v3_source_root/cp367-scope-v3-20261009'
V2=B/'checkpoint_r367_main_registration_v2_source_root/cp367-main-v2-20261009'
Q=B/'checkpoint_r367_main_registration_v2_independent_review_codex/cp367v2r-01a11fad'
pins={};checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(r):
 r=dict(path=str(Path(r['path']).resolve(strict=True)),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes']);assert pin(r['path'])==r
 assert r['path'] not in pins or pins[r['path']]==r
 pins[r['path']]=r;return Path(r['path']).read_bytes()
def load(r):return json.loads(read(r))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ck(n,v):
 assert v,n
 checks.append(n)
h=load(dict(path=str(C/'HDF.json'),sha256='896e0eaa99a9470eb9f01a099760b0538520bf99cb9f18506619f88b4d5d86a6',bytes=3059))
mf=load(h['manifest_ref'])
for r in mf['members']:read(r)
q=load(dict(path=str(Q/'HDF.json'),sha256='4bb022d282498db9225fbb1b544753b73f1ba11223281424155e79e5a462e4ba',bytes=3827))
for r in load(q['manifest_ref'])['members']:read(r)
for r in json.loads((Q/'input-pins.json').read_bytes()):read(r)
f=load(h['facts_ref']);scope=load(h['scope_ref']);proof=load(h['source_preview_ref']);inv=load(proof['complete_inverse_ref'])
before=read(inv['before_ref']);after=read(inv['after_ref'])
ck('single_pointer_complete_byte_inverse',after.count(inv['after_token'].encode())==1 and after.replace(inv['after_token'].encode(),inv['before_token'].encode())==before)
oldfacts=json.loads(before);rollback=copy.deepcopy(f);rollback['scope_ref']['path']=oldfacts['scope_ref']['path']
ck('single_pointer_complete_semantic_inverse',rollback==oldfacts)
ck('scope_bytes_identical',read(inv['scope_after_ref'])==read(inv['scope_before_ref']))
writer=read(h['writer_ref']);ck('writer_bytes_identical_to_reviewed_v2',writer==read(inv['writer_before_ref']))
caller=read(scope['caller_ref']);contract=load(f['calling_contract_ref']);change=load(scope['change_set_ref'])
live=load(dict(path=str(V2/'root-postseal-live-950-20261009/live-context.actual.root.json'),sha256='9c68988b96b091c920f3873e7c8c2ad9c41c2212a6928615aa7f27d2e63d9291',bytes=1488))
for row in live['pending']:read(row['origin_ref'])
raw=[read(r) for r in f['canonical_refs']];old_c,old_o=[json.loads(b) for b in raw[:2]]
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=read(dict(path=str(gp),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404))
gm=types.ModuleType('cp367v3reviewguard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(gr,str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(pins.values()))
try:
 tree=ast.parse(writer);names=('require','pin','read','load','facts_scope','validate_live_context','transform')
 ns=dict(Path=Path,copy=copy,hashlib=hashlib,json=json,TARGETS=scope['exact_targets'],KEY='c19_main_source_registry_adoption',SLICE='C19_MAIN_SOURCE_REGISTRY_ADOPTION')
 exec(compile(ast.Module(body=[v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name in names],type_ignores=[]),'<pure-register-v3>','exec'),ns)
 _,owner,worker=ns['facts_scope'](f)
 nc,no=ns['transform'](copy.deepcopy(old_c),copy.deepcopy(old_o),f,h['facts_ref'],old_c,old_o,owner,worker,'INDEPENDENT',live)
 ck('registered_owner_worker_new_scope_ref',owner['scope_ref']==worker['scope_ref']==h['scope_ref'])
 ck('old934_semantic_preserved',nc['failure_counters'][:934]==old_c['failure_counters'])
 ck('old934_plus11_945_exact',len(nc['failure_counters'])==945 and [v['original_payload']['observed_ordinal'] for v in nc['failure_counters'][934:]]==list(range(937,948)))
 ck('diagnostics_identical_to_v2',f['diagnostics']==oldfacts['diagnostics'])
 ck('source_cut947_next948',nc['work_in_progress']['r367_highest_observed_diagnostic_ordinal_at_cutoff']==947 and nc['work_in_progress']['r367_next_failure_ordinal_at_cutoff']==948)
 ic,io=copy.deepcopy(nc),copy.deepcopy(no)
 for k in ('failure_counters','workers','work_in_progress','expected_previous_revision','revision','updated_at','updated_by','note'):ic[k]=copy.deepcopy(old_c[k])
 del io['card_path_bindings']['W09-99']['subtasks'][ns['KEY']]
 for k in ('revision','updated_at','updated_by'):io[k]=old_o[k]
 ck('complete_canonical_inverse',ic==old_c and io==old_o)
 pc=load(proof['proposed_checkpoint_ref']);po=load(proof['proposed_ownership_ref'])
 for d in (nc,no,pc,po):d.pop('updated_at',None)
 ck('transform_matches_sealed_preview',nc==pc and no==po)
 def failure_array(data):
  text=data.decode('utf-8');start=text.index('[',text.index('"failure_counters":'));_,length=json.JSONDecoder().raw_decode(text[start:]);return text[start:start+length]
 ck('old934_raw_array_prefix_preserved_in_preview',failure_array(read(proof['proposed_checkpoint_ref'])).startswith(failure_array(raw[0]).rstrip()[:-1].rstrip()+','))
 # Execute the exact namespace predicates extracted from Main caller.main.
 ct=ast.parse(caller);main=next(v for v in ct.body if isinstance(v,ast.FunctionDef) and v.name=='main')
 namespace_calls=[v for v in main.body if isinstance(v,ast.Expr) and isinstance(v.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value in ('ROOT_REQUEST_NAMESPACE','ROOT_SCOPE_NAMESPACE') for a in v.value.args)]
 W=Path(scope['caller_ref']['path']).parents[2]
 env=dict(Path=Path,W=W,require=ns['require'],sref=h['scope_ref'],qref=dict(path=str(Path(h['scope_ref']['path']).parent/'future-request.namespace-probe-only.json')))
 exec(compile(ast.Module(body=namespace_calls,type_ignores=[]),'<pure-main-namespace-predicates>','exec'),env)
 ck('main_scope_and_future_request_namespace_predicates_pass',len(namespace_calls)==2)
 ck('old_scope_path_rejected_by_main_namespace',not Path(oldfacts['scope_ref']['path']).is_relative_to(W/'integration_codex'))
 ck('caller_change_contract_bindings_exact',scope['caller_ref']==contract['caller_ref'] and scope['change_set_ref']==contract['change_set_ref'] and scope['exact_targets']==contract['exact_targets'])
 # Real cross-caller Source boundary uses four initial requires, before vector reads.
 boundary=copy.deepcopy(next(v for v in ct.body if isinstance(v,ast.FunctionDef) and v.name=='validate_scope'));boundary.body=boundary.body[:4]
 cns=dict(Path=Path,ROOT_ACTOR='codex:/root',TARGETS=[Path(p) for p in scope['exact_targets']],OUT=Path(scope['journal_root']),require=ns['require'])
 exec(compile(ast.Module(body=[boundary],type_ignores=[]),'<pure-main-scope-boundary>','exec'),cns)
 def boundary_error(sc):
  try:cns['validate_scope'](sc,h['scope_ref'],change,scope['change_set_ref'],scope['caller_ref'],scope['source_handoff_ref'],scope['source_manifest_ref'],[],None)
  except ValueError as e:return str(e)
  return None
 error=boundary_error(scope)
 ck('P1_actual_integer_zero_scope_rejected_by_main',type(scope['new_Go_SQL_API_model_calls']) is int and scope['new_Go_SQL_API_model_calls']==0 and error=='ROOT_SOURCE_ONLY_BOUNDARY')
 boolean_scope=copy.deepcopy(scope);boolean_scope['new_Go_SQL_API_model_calls']=False
 ck('P1_boolean_false_accepted_by_main_boundary',boundary_error(boolean_scope) is None)
 actual_load=ns['load'];ns['load']=lambda r:boolean_scope if r==f['scope_ref'] else actual_load(r)
 try:ns['facts_scope'](f)
 except ValueError as e:opposite=str(e)
 else:opposite=None
 finally:ns['load']=actual_load
 ck('P1_boolean_false_rejected_by_registration',opposite=='SCOPE_ZERO_CALLS_FORMAL')
 ck('canonical_four_unchanged',[Path(r['path']).read_bytes() for r in f['canonical_refs']]==raw)
 save('counterexample.json',dict(source_scope_ref=h['scope_ref'],registration_writer_ref=h['writer_ref'],main_caller_ref=scope['caller_ref'],integer0_registration_accepted=True,integer0_main_boundary_error=error,booleanFalse_main_boundary_accepted=True,booleanFalse_registration_error=opposite,actual_calls=False,succeeded_as_counterexample=True,new_failure_ordinal=None))
finally:
 cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup);assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
ck('all_inputs_unchanged',all(pin(r['path'])==r for r in pins.values()))
save('input-pins.json',list(pins.values()));save('checks.json',checks)
save('result.json',dict(status='REQUEST_CHANGES_CROSS_CALLER_SCOPE_BOUNDARY',P1_findings=1,scope_namespace_fix_pass=True,source_single_pointer_inverse_pass=True,canonical_inverse_pass=True,checks=len(checks),pins=len(pins),new_original_failures=[],actual_registration_qualified=False,Main_Canon_written=False,Go_SQL_API_model_executed=False,formal_case_accepted_delta=0,current_root_live_reported=951))
print(json.dumps(dict(status='REQUEST_CHANGES_CROSS_CALLER_SCOPE_BOUNDARY',checks=len(checks),pins=len(pins),new_failures=0)))
