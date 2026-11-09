import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json,types
from pathlib import Path,PureWindowsPath
N=Path(__file__).resolve().parent;B=N.parents[1]
C=B/'checkpoint_r367_transaction_operation_v5_source_root/cp367-operation-v5-20261009'
Q=B/'checkpoint_r367_main_v2_binding_v4_independent_review_codex/cp367v4r-01a11fad'
pins={};checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
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
h=load(dict(path=str(C/'HDF.json'),sha256='49cdedad9104347f5bd66af35c63ce9b9e920b78d3181540ff9e2d62b64ddb2b',bytes=2667))
mf=load(h['manifest_ref'])
for r in mf['members']:read(r)
prior=load(dict(path=str(Q/'HDF.json'),sha256='95ab93dfd77646bebcba75b1f2f38ea1b8fb38022a80e2c63961b80f671c43b0',bytes=3495))
for r in load(prior['manifest_ref'])['members']:read(r)
for r in json.loads((Q/'input-pins.json').read_bytes()):read(r)
f=load(h['facts_ref']);sc=load(h['scope_ref']);proof=load(h['source_preview_ref']);inv=load(proof['complete_inverse_ref'])
oldwriter=read(inv['writer_before_ref']);writer=read(h['writer_ref'])
ck('one_writer_span_byte_inverse',writer.count(inv['writer_after_span'].encode())==1 and writer.replace(inv['writer_after_span'].encode(),inv['writer_before_span'].encode())==oldwriter)
oldraw=read(inv['facts_before_ref']);oldf=json.loads(oldraw)
changed={k for k in f if f[k]!=oldf[k]};allowed={'diagnostics','highest_observed_ordinal','next_failure_ordinal','registered_after','actual_refs','checkpoint_note'}
ck('facts_exact_changed_metadata_keys',changed==allowed and set(f)==set(oldf))
rollback=copy.deepcopy(f)
for k in changed:rollback[k]=copy.deepcopy(oldf[k])
ck('facts_complete_UTF8_byte_inverse',rollback==oldf and (json.dumps(rollback,ensure_ascii=False,indent=2)+'\n').encode()==oldraw)
ck('Scope_Source_reviews_WIP_unchanged',all(f[k]==oldf[k] for k in ('scope_ref','calling_contract_ref','reviews','work_in_progress','canonical_refs')))
ck('old14_unchanged_new951_once',f['diagnostics'][:-1]==oldf['diagnostics'] and [d['ordinal'] for d in f['diagnostics']]==list(range(937,952)))
d=f['diagnostics'][-1];origin=load(d['origin_ref'])
ck('951_original_outer_SourcePython1_exact',d['ordinal']==origin['ordinal']==951 and origin['original_result']['chunk_id']=='524e08' and origin['original_result']['exit_code']==d['actual_outer_exit']==1 and d['actual_python_exit']==origin['actual_source_python_exit']==1 and 'ROOT_SOURCE_PYTHON_EXIT=1' in origin['original_result']['output'])
ck('951_Native_model_NULL_not_replayed',d['actual_native_exit'] is None and origin['actual_product_native_exit'] is None and origin['model_exit'] is None and origin['replayed'] is False and origin['counter_reset'] is False)
ck('actual_refs_only_failed_guard_cleanup_appended',f['actual_refs'][:-1]==oldf['actual_refs'])
cl951=load(f['actual_refs'][-1]);ck('failed951_guard_closed0',cl951['closed'] is True and cl951['errors']==[] and cl951['retained_handles_count']==0)
raw=[read(r) for r in f['canonical_refs']];oldcp,oldow=[json.loads(b) for b in raw[:2]]
ck('before366_170_unchanged_after951',oldcp['revision']==366 and oldow['revision']==170)
live=load(next(r for r in mf['members'] if Path(r['path']).name=='live-context.preview-only.json'))
tp=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
tr=read(dict(path=str(tp),sha256='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9',bytes=6877))
# Execute the original helper AST prelude with zero filesystem or WinAPI access.
update=copy.deepcopy(next(v for v in ast.parse(tr).body if isinstance(v,ast.FunctionDef) and v.name=='update_pair'))
boundary_index=next(i for i,v in enumerate(update.body) if isinstance(v,ast.Assign) and isinstance(v.value,ast.Call) and isinstance(v.value.func,ast.Attribute) and v.value.func.attr=='WinDLL')
update.body=update.body[:boundary_index+1]
class StubPath(PureWindowsPath):
 def is_dir(self):return True
class BoundaryReached(Exception):pass
calls=[]
def dll(*args,**kwargs):calls.append(dict(args=list(args),kwargs=kwargs));raise BoundaryReached('STUBBED_WINDLL_BOUNDARY_NO_NATIVE_CALL')
tn=dict(Path=StubPath,PATHS=tuple(StubPath(r['path']) for r in f['canonical_refs'][:2]),os=types.SimpleNamespace(name='nt'),ctypes=types.SimpleNamespace(WinDLL=dll))
exec(compile(ast.Module(body=[update],type_ignores=[]),'<actual-helper-pure-prelude>','exec'),tn)
try:tn['update_pair'](f['canonical_refs'][:2],None,str(C),'register')
except RuntimeError as exc:old_error=str(exc)
else:old_error=None
ck('real_helper_old_register_rejected_before_DLL',old_error=='unknown canonical transaction' and calls==[])
try:tn['update_pair'](f['canonical_refs'][:2],None,str(C),'activate')
except BoundaryReached as exc:new_boundary=str(exc)
else:new_boundary=None
ck('real_helper_activate_reaches_stub_boundary',new_boundary=='STUBBED_WINDLL_BOUNDARY_NO_NATIVE_CALL' and calls==[dict(args=['kernel32'],kwargs={'use_last_error':True})])
ck('helper_partial_reconciliation_not_automatic_inverse',b'"automatic_inverse":False' in tr and b'"requires_root_reconciliation":True' in tr and b'failed.partial.json' in tr)
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=read(dict(path=str(gp),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404))
gm=types.ModuleType('cp367v5review_guard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(gr,str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(pins.values()))
try:
 ns=dict(Path=Path,copy=copy,hashlib=hashlib,json=json,TARGETS=sc['exact_targets'],KEY='c19_main_source_registry_adoption',SLICE='C19_MAIN_SOURCE_REGISTRY_ADOPTION')
 names={'require','pin','read','load','facts_scope','validate_live_context','transform'}
 exec(compile(ast.Module(body=[v for v in ast.parse(writer).body if isinstance(v,ast.FunctionDef) and v.name in names],type_ignores=[]),'<pure-v5-facts-transform>','exec'),ns)
 _,owner,worker=ns['facts_scope'](f)
 nc,no=ns['transform'](copy.deepcopy(oldcp),copy.deepcopy(oldow),f,h['facts_ref'],oldcp,oldow,owner,worker,'INDEPENDENT',live)
 ck('old934_exact_plus15_total949',nc['failure_counters'][:934]==oldcp['failure_counters'] and len(nc['failure_counters'])==949)
 ck('new15_once_exact_cut951_next952',len({v['origin_key'] for v in nc['failure_counters'][934:]})==15 and nc['work_in_progress']['r367_highest_observed_diagnostic_ordinal_at_cutoff']==951 and nc['work_in_progress']['r367_next_failure_ordinal_at_cutoff']==952)
 ck('new_row951_qualifies_original',nc['failure_counters'][-1]['original_payload']['immutable_origin_ref']==d['origin_ref'] and nc['failure_counters'][-1]['original_payload']['actual_outer_exit']==1 and nc['failure_counters'][-1]['original_payload']['actual_python_exit']==1 and nc['failure_counters'][-1]['original_payload']['actual_native_exit'] is None)
 ck('one_W09_worker_only',nc['workers']==oldcp['workers']+[worker] and worker['step_id']=='W09-99')
 ic,io=copy.deepcopy(nc),copy.deepcopy(no)
 for k in ('failure_counters','workers','work_in_progress','expected_previous_revision','revision','updated_at','updated_by','note'):ic[k]=copy.deepcopy(oldcp[k])
 del io['card_path_bindings']['W09-99']['subtasks'][ns['KEY']]
 for k in ('revision','updated_at','updated_by'):io[k]=oldow[k]
 ck('complete_Canon_semantic_inverse_no_W05_expansion',ic==oldcp and io==oldow)
 pcraw=read(proof['proposed_checkpoint_ref']);pc=json.loads(pcraw);po=load(proof['proposed_ownership_ref'])
 for v in (nc,no,pc,po):v.pop('updated_at',None)
 ck('independent_transform_equals_preview',nc==pc and no==po)
 def arr(b):
  t=b.decode();s=t.index('[',t.index('"failure_counters":'));_,n=json.JSONDecoder().raw_decode(t[s:]);return t[s:s+n]
 ck('old934_raw_prefix_preserved',arr(pcraw).startswith(arr(raw[0]).rstrip()[:-1].rstrip()+','))
 ck('four_current_Canon_unchanged',[Path(r['path']).read_bytes() for r in f['canonical_refs']]==raw)
 save('helper-prelude-controls.json',dict(helper_ref=pin(tp),old_operation='register',old_error=old_error,new_operation='activate',new_boundary=new_boundary,stub_calls=calls,actual_helper_WinAPI_calls=0,actual_helper_filesystem_calls=0,automatic_inverse=False,partial_requires_explicit_Root_reconciliation=True))
finally:
 cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup);assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
ck('all_exact_inputs_unchanged',all(pin(r['path'])==r for r in pins.values()))
save('input-pins.json',list(pins.values()));save('checks.json',checks)
save('result.json',dict(status='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_LIVE_CONTEXT_VALIDATION',checks=len(checks),pins=len(pins),helper_operation_fix_pass=True,helper_automatic_inverse=False,registered_after_preview=949,source_cut951_next952=True,new_original_failures=[],actual_registration_qualified_now=False,condition='New post-review Root live context with cut951/next952 and current live/pending interval; exact validation before one invocation; any partial canonical write requires explicit Root reconciliation, never automatic replay',actual_Main_Canon_written=False,actual_helper_WinAPI_executed=False,Go_SQL_API_model_executed=False,formal_case_accepted_delta=0))
print(json.dumps(dict(status='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_LIVE_CONTEXT_VALIDATION',checks=len(checks),pins=len(pins),new_failures=0)))
