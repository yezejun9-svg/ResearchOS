import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent
B=N.parents[1]
C=B/'checkpoint_r367_main_registration_v2_source_root/cp367-main-v2-20261009'
V1=B/'checkpoint_r367_main_registration_source_root/cp367-main-20261009'
V1R=B/'checkpoint_r367_main_registration_independent_review_codex/cp367r-01a11fad'
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
h=load(dict(path=str(C/'HDF.json'),sha256='469de4a7176e25ef0d844824fb97bc02bf0afb3b79b5026f4b7474c24c5a65cb',bytes=2748))
mf=load(h['manifest_ref'])
for r in mf['members']:read(r)
prior=load(dict(path=str(V1R/'HDF.json'),sha256='dd101d10a74545d660868048e6954bc2207d51fc00853bf5192e5ed959626458',bytes=3277))
prior_mf=load(prior['manifest_ref'])
for r in prior_mf['members']:read(r)
for r in json.loads((V1R/'input-pins.json').read_bytes()):read(r)
f=load(h['facts_ref']);proof=load(h['source_preview_ref']);scope=load(h['scope_ref'])
live=load(next(r for r in mf['members'] if Path(r['path']).name=='live-context.preview-only.json'))
for row in live['pending']:read(row['origin_ref'])
inverse=load(proof['complete_inverse_ref']);before=read(inverse['before_ref']);after=read(inverse['after_ref'])
restored=after.decode('utf-8')
for span in reversed(inverse['spans']):
 ck('unique_inverse_span_'+str(len(checks)),restored.count(span['after'])==1)
 restored=restored.replace(span['after'],span['before'])
ck('complete_source_utf8_inverse',restored.encode('utf-8')==before)
ck('facts_byte_copy_exact',read(h['facts_ref'])==(V1/'checkpoint.execution.facts.json').read_bytes())
raw=[read(r) for r in f['canonical_refs']];old_c,old_o=[json.loads(x) for x in raw[:2]]
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
graw=read(dict(path=str(gp),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404))
gm=types.ModuleType('cp367v2reviewguard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(graw,str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(pins.values()))
try:
 tree=ast.parse(after);old_tree=ast.parse(before)
 names=('require','pin','read','load','facts_scope','validate_live_context','transform')
 ns=dict(Path=Path,copy=copy,hashlib=hashlib,json=json,TARGETS=scope['exact_targets'],KEY='c19_main_source_registry_adoption',SLICE='C19_MAIN_SOURCE_REGISTRY_ADOPTION')
 exec(compile(ast.Module(body=[v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name in names],type_ignores=[]),'<pure-v2-functions>','exec'),ns)
 for name in ('facts_scope','read','pin'):
  ck('unchanged_'+name,ast.dump(next(v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name==name))==ast.dump(next(v for v in old_tree.body if isinstance(v,ast.FunctionDef) and v.name==name)))
 _,owner,worker=ns['facts_scope'](f)
 nc,no=ns['transform'](copy.deepcopy(old_c),copy.deepcopy(old_o),f,h['facts_ref'],old_c,old_o,owner,worker,'INDEPENDENT',live)
 ck('P1_fixed_live949_pending948',nc['work_in_progress']['root_next_failure_ordinal_live']==949 and nc['work_in_progress']['later_diagnostics_observed_after_cutoff']==live['pending'])
 ck('cut947_next948_preserved',nc['work_in_progress']['r367_highest_observed_diagnostic_ordinal_at_cutoff']==947 and nc['work_in_progress']['r367_next_failure_ordinal_at_cutoff']==948)
 ck('old934_plus11_preserved',nc['failure_counters'][:934]==old_c['failure_counters'] and len(nc['failure_counters'])==945)
 ck('worker_owner_exact',nc['workers']==old_c['workers']+[worker] and no['card_path_bindings']['W09-99']['subtasks'][ns['KEY']]==owner)
 ic,io=copy.deepcopy(nc),copy.deepcopy(no)
 for k in ('failure_counters','workers','work_in_progress','expected_previous_revision','revision','updated_at','updated_by','note'):ic[k]=copy.deepcopy(old_c[k])
 del io['card_path_bindings']['W09-99']['subtasks'][ns['KEY']]
 for k in ('revision','updated_at','updated_by'):io[k]=old_o[k]
 ck('full_canonical_semantic_inverse',ic==old_c and io==old_o)
 pc,po=load(proof['proposed_checkpoint_ref']),load(proof['proposed_ownership_ref'])
 for d in (nc,no,pc,po):d.pop('updated_at',None)
 ck('independent_transform_equals_source_preview',nc==pc and no==po)
 def reject(label,mutate):
  bad=copy.deepcopy(live);mutate(bad)
  try:ns['validate_live_context'](bad,f)
  except (ValueError,KeyError):checks.append(label)
  else:raise AssertionError(label)
 reject('bool_next',lambda d:d.update(next_original_failure_ordinal=True))
 reject('float_next',lambda d:d.update(next_original_failure_ordinal=949.0))
 reject('below_cut_next',lambda d:d.update(next_original_failure_ordinal=947))
 reject('missing_pending',lambda d:d.update(pending=[]))
 reject('duplicate_pending',lambda d:d['pending'].append(copy.deepcopy(d['pending'][0])))
 reject('wrong_cutoff',lambda d:d['source_cutoff'].update(highest_ordinal=946))
 reject('wrong_actor',lambda d:d.update(issued_by='codex:/other'))
 reject('extra_context_key',lambda d:d.update(extra=True))
 reject('bool_pending_ordinal',lambda d:d['pending'][0].update(ordinal=True))
 reject('float_pending_ordinal',lambda d:d['pending'][0].update(ordinal=948.0))
 reject('pending_wrong_sha',lambda d:d['pending'][0]['origin_ref'].update(sha256='0'*64))
 reject('pending_wrong_bytes',lambda d:d['pending'][0]['origin_ref'].update(bytes=1))
 reject('pending_bool_bytes',lambda d:d['pending'][0]['origin_ref'].update(bytes=True))
 reject('pending_extra_refkey',lambda d:d['pending'][0]['origin_ref'].update(extra=True))
 reject('pending_wrong_order',lambda d:d['pending'][0].update(ordinal=949))
 ck('preview_is_not_actual_live_authorization',proof['actual_live_context_issued'] is False and live['created_utc']=='SOURCE_PREVIEW_ONLY_ACTUAL_CONTEXT_ISSUED_BY_ROOT_LATER')
 main=ast.get_source_segment(after.decode('utf-8'),next(v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name=='main'))
 ck('main_typed_context_and_pending_are_guarded',"live_context=load(live_context_ref)" in main and "refs.append(live_context_ref)" in main and "refs.extend(item['origin_ref'] for item in live_context['pending'])" in main and main.index('validate_live_context(live_context,facts)')<main.index('tm.update_pair'))
 ck('proof_resume_persist_context_ref',main.count("'live_context_ref':live_context_ref")==2)
 ck('canonical_four_unchanged',[Path(r['path']).read_bytes() for r in f['canonical_refs']]==raw)
finally:
 cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup);assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
ck('all_input_pins_unchanged',all(pin(r['path'])==r for r in pins.values()))
save('checks.json',checks);save('input-pins.json',list(pins.values()))
save('result.json',dict(status='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_LIVE_CONTEXT_VALIDATION',checks=len(checks),pins=len(pins),P1_fixed=True,source_byte_inverse=True,canonical_semantic_inverse=True,actual_registration_qualified_now=False,condition='Root seals a fresh live context after this review; exact pending interval starting948 includes every assigned original through liveNext-1; reviewer validates typed ref, origin identities and freshness before actual registration',actual_Main_or_Canon_written=False,Go_SQL_API_model_executed=False,formal_case_accepted_delta=0))
print(json.dumps(dict(status='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_LIVE_CONTEXT_VALIDATION',checks=len(checks),pins=len(pins))))
