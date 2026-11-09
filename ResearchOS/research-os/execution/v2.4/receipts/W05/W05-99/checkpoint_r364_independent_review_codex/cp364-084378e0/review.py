import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,importlib.util,re,traceback,ast
P=pathlib.Path
O=P(__file__).resolve().parent;R=P('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
N=B/'sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r364-component-actuals-source-ready'
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
T=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
checks=[];g=None;allrefs={};sources={}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def pin(p):
 p=P(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def norm(v):return dict(path=str(P(v['path'])),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes'])
def add(v,source):
 v=norm(v);k=v['path'].casefold()
 if k in allrefs:assert allrefs[k]==v,'conflicting current declaration: '+v['path']
 else:allrefs[k]=v
 sources.setdefault(k,[]).append(source)
def refs(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}.issubset(v) and isinstance(v['path'],str) and isinstance(v['sha256'],str) and type(v['bytes']) is int:yield v
  else:
   for x in v.values():yield from refs(x)
 elif isinstance(v,list):
  for x in v:yield from refs(x)
def members(v):
 m=v['members'];return list(m.values()) if isinstance(m,dict) else m
def ck(n,v,d=None):checks.append(dict(check=n,passed=bool(v),detail=d))
def good(v):return v.get('schema')=='researchos.source-read-guard-observation.v1' and v['closed'] is True and v['retained_handles_count']==0 and v['verification']=='PASSED' and v['failure'] is None and not v['errors'] and all(x['verified'] and x['final_path_match'] and x['closed'] for x in v['entries'])
def main():
 global g
 f0=json.loads((N/'checkpoint.execution.facts.json').read_bytes());pa=json.loads((N/'canonical_pair.actual.json').read_bytes());J=P(pa['transaction']['transaction_journal'])
 for p in list(N.iterdir())+list(J.iterdir()):
  if p.is_file():add(pin(p),'CP364-package-and-transaction')
 for v in refs(f0):add(v,'facts-reference')
 for name in ['handoff.json','manifest.json','writer-source-provenance.json']:
  for v in refs(json.loads((N/name).read_bytes())):add(v,name)
 manifests=[e['manifest_ref'] for e in f0['reviews']]+[v for v in f0['actual_refs'] if P(v['path']).name=='MF.json']
 for mr in manifests:
  for v in members(json.loads(P(mr['path']).read_bytes())):add(v,'declared-review-or-source-manifest')
 for d in f0['diagnostics']:
  for v in refs(json.loads(P(d['origin_ref']['path']).read_bytes())):add(v,'original-diagnostic-descendant')
 # Expand direct actual receipts only, not old checkpoint aliases or entire source inventories.
 for ar in f0['actual_refs']:
  if P(ar['path']).name=='validation.closed.json':
   for v in refs(json.loads(P(ar['path']).read_bytes())):add(v,'actual-closed-direct-descendant')
 for v in list(allrefs.values()):
  if P(v['path']).name.endswith('.invocation.json'):
   for rr in refs(json.loads(P(v['path']).read_bytes())):
    if P(rr['path']).name.endswith(('.raw','.log','.txt')):add(rr,'invocation-raw-stream')
 writer_guard=json.loads((N/'source_guard.cleanup.actual.json').read_bytes())
 for v in writer_guard['entries']:add(v,'writer-actually-held-runtime-or-input')
 for n,h,b in [('checkpoint','6ed349c5b8380ad6b099ae2237c33513f4e2717afc7789398968366a8cddf6dd',4237636),('path_ownership','48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452',192861),('step_state','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),('commands','b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129',68156)]:add(dict(path=str(R/'execution/v2.4'/(n+'.json')),sha256=h,bytes=b),'canonical')
 for p in [G,T,P(__file__),R/'execution/project_identity.json',P(sys.executable)]:add(pin(p),'review-support')
 assert pin(G)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
 spec=importlib.util.spec_from_file_location('cp364_readonly_guard',G);gm=importlib.util.module_from_spec(spec);spec.loader.exec_module(gm)
 g=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire(list(allrefs.values()))
 def raw(p):return g.get_buffer(str(P(p)))
 def obj(p):return json.loads(raw(p))
 def verify(v):
  b=raw(v['path']);return hashlib.sha256(b).hexdigest()==v['sha256'].removeprefix('sha256:') and len(b)==v['bytes']
 save('input-pins.json',list(allrefs.values()));save('reference-provenance.json',sources)
 for v in allrefs.values():ck('exact-input:'+v['path'],verify(v))
 f=obj(N/'checkpoint.execution.facts.json');cp=obj(R/'execution/v2.4/checkpoint.json');old=obj(J/'0.before.json');w=cp['work_in_progress'];ww=w['mu_sdk_r364']
 ck('HDF-MF-pins',hashlib.sha256(raw(N/'handoff.json')).hexdigest()=='32aa9698224c8438b2fc3638b306e1d9ca74687da62c26553907fc9d32498eac' and len(raw(N/'handoff.json'))==1062 and hashlib.sha256(raw(N/'manifest.json')).hexdigest()=='e0b38109fe7fa5872b3b2c8a39c523e4fae234e406eb79926631b35730c4e924' and len(raw(N/'manifest.json'))==3726)
 ck('oldCP363-pin',hashlib.sha256(raw(J/'0.before.json')).hexdigest()=='9e67531bd3b1f0fbd9bc5e239b3a240a39f668db2d367714a399ba4fd8bfeb25' and len(raw(J/'0.before.json'))==4223052)
 ck('project-head-revision',cp['project_id']==old['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and cp['head']==old['head']=='adc460c2138528f163f7fdab5e8d81dde157b7fb' and old['revision']==363 and cp['revision']==364 and cp['expected_previous_revision']==363)
 changed=[k for k in cp.keys()|old.keys() if cp.get(k)!=old.get(k)]
 ck('authorized-top-level-delta',set(changed).issubset({'revision','expected_previous_revision','updated_at','updated_by','failure_counters','work_in_progress','note'}),changed)
 overwrite={'later_diagnostics_observed_after_cutoff','root_next_failure_ordinal_live'}
 ck('old-WIP-preserved-except-current-cutoff-fields',all(k in w and w[k]==v for k,v in old['work_in_progress'].items() if k not in overwrite))
 ck('new-WIP-equals-facts',ww==f['work_in_progress']['mu_sdk_r364'] and verify(w['mu_sdk_r364_facts_ref']) and cp['note']==f['checkpoint_note'])
 ck('old893-whole-objects',len(old['failure_counters'])==893 and len(cp['failure_counters'])==900 and cp['failure_counters'][:893]==old['failure_counters'])
 def array(b):
  t=b.decode();i=t.index('[',t.index('"failure_counters":'));_,end=json.JSONDecoder().raw_decode(t[i:]);return t[i:i+end]
 prefix=array(raw(J/'0.before.json')).rstrip()[:-1].rstrip();ck('old893-raw-prefix',array(raw(R/'execution/v2.4/checkpoint.json')).startswith(prefix+','))
 new=cp['failure_counters'][893:];ds=f['diagnostics'];ck('exact-seven-ordinals',[d['ordinal'] for d in ds]==list(range(896,903)) and len(new)==7)
 qualifications=[]
 for d,c in zip(ds,new):
  n=d['ordinal'];o=obj(d['origin_ref']['path']);ex=(d['actual_outer_exit'],d['actual_python_exit'],d['actual_native_exit']);payload=c['original_payload'];key=hashlib.sha256((d['origin_ref']['sha256']+'#'+str(n)).encode()).hexdigest()
  ck(str(n)+':exact-once-origin',c['origin_key']==key and sum(x.get('origin_key')==key for x in cp['failure_counters'])==1 and norm(c['evidence_ref'])==norm(d['origin_ref'])==norm(payload['immutable_origin_ref']) and payload['observed_ordinal']==n and tuple(payload[k] for k in ['actual_outer_exit','actual_python_exit','actual_native_exit'])==ex and c['counted_once'] is True and c['counter_reset'] is False and c['automatic_retry'] is False)
  t=None;limit=None
  if n==896:
   t=o['original_tool_io']['result'];ck('896:KeyError-marker',"KeyError: 'closed'" in t['output'] and 'ROOT_PYTHON_EXIT=1' in t['output'] and ex==(1,1,None))
  elif n in (897,898):
   x=o['original_tool_io'];ck(str(n)+':schema-rejected-no-execution',x['tool']=='history.search_contents' and x['result']=='Unexpected argument. Use only fields defined in the tool schema.' and ex==(None,None,None) and o['attempt_count']==1)
  elif n==899:
   t=o['result'];ck('899:source-marker-not-native','SOURCE_PYTHON_EXIT=1 NATIVE_EXIT=NULL' in t['output'] and ex==(o['outer_exit'],o['source_python_exit'],o['native_exit'])==(1,1,None))
  elif n in (900,901):
   t=o['original_result'];ck(str(n)+':rg-inference-not-actual',o['rg_exit_actual'] is None and o['rg_exit_inferred']==d['inferred_rg_exit']==2 and ex==(o['outer_exit'],o['source_python_exit'],o['native_product_exit']) and ex[1:] == (None,None))
   limit='rg exit2 inferred from missing path; no separately captured numeric marker.'
  else:
   t=o['original_tool_io'];ck('902:summary-qualified-not-full-copy',ex==(o['actual_outer_exit_code'],o['actual_python_exit_code'],o['actual_native_exit_code'])==(1,None,None) and t['chunk_id']=='50c929' and 'retained in current chat' in o['qualification'] and 'RESUME.md' in t['output'])
   limit='Preserved file contains error summary and chunk50c929 locator; full original tool output is in originating chat, not copied into this file.'
  if t:ck(str(n)+':outer-exit',t['exit_code']==ex[0])
  qualifications.append(dict(ordinal=n,outer=ex[0],python=ex[1],native=ex[2],chunk_id=t.get('chunk_id') if t else None,qualification=limit))
 ck('counts-at-cutoff',w['r364_registered_failure_count']==900 and w['r364_highest_observed_diagnostic_ordinal_at_cutoff']==902 and w['r364_next_failure_ordinal_at_cutoff']==903 and w['later_diagnostics_observed_after_cutoff']==[] and w['root_next_failure_ordinal_live']==903)
 post=obj(N/'postwrite-original-root-tool-io.json')
 for key,ch in [('facts_prepare_original','b57e18'),('writer_original','0077ad')]:
  t=post[key];ck(key+':real-Python-exit0',t['chunk_id']==ch and t['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in t['output'])
  for v in refs(json.loads(t['output'].splitlines()[0])):ck(key+':output-ref',verify(v))
 ck('postwrite-later903-not-cutoff',post['later_pending']==[903] and post['live_next_failure_ordinal']==904 and post['ordinal904_never_used'] is True)
 intent=obj(J/'intent.json');commit=obj(J/'committed.json')
 for v in intent['before_refs']+intent['after_refs']+commit['after_refs']:ck('transaction-ref:'+v['path'],verify(v))
 ck('exclusive-committed',intent['mandatory_share_mode']==0 and intent['automatic_inverse'] is False and commit['written_indices']==[0,1] and commit['both_verified_while_exclusively_held'] is True)
 ck('proposed-exact-current',raw(J/'0.after.proposed.json')==raw(R/'execution/v2.4/checkpoint.json'))
 ck('OW168-unchanged',raw(J/'1.before.json')==raw(J/'1.after.proposed.json')==raw(R/'execution/v2.4/path_ownership.json') and obj(R/'execution/v2.4/path_ownership.json')['revision']==168)
 # Reproduce Source derivation and its complete inverse without importing/executing writer.
 prov=obj(N/'writer-source-provenance.json');base=raw(prov['base_ref']['path']).decode();candidate=raw(prov['new_ref']['path']).decode();derived=base
 for c in prov['changes']:
  positions=[m.start() for m in re.finditer(re.escape(c['before']),derived)]
  ck('writer-change:'+c['before'],positions==c['positions'] and len(positions)==c['count']);derived=derived.replace(c['before'],c['after'])
 ck('writer-whole-forward',derived==candidate)
 inverse=candidate
 for c in reversed(prov['changes']):
  a,b=c['before'],c['after']
  for i,p in reversed(list(enumerate(c['positions']))):
   q=p+i*(len(b)-len(a));ck('writer-inverse-span:'+str(q),inverse[q:q+len(b)]==b);inverse=inverse[:q]+a+inverse[q+len(b):]
 ck('writer-whole-inverse',inverse==base)
 ast.parse(candidate);ast.parse(raw(T));ast.parse(raw(N/'prepare_checkpoint_facts.actual.py'))
 ck('transaction-helper-pinned',hashlib.sha256(raw(T)).hexdigest()=='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9')
 ck('writer-guard-closed',good(writer_guard));held={v['path'].casefold() for v in writer_guard['entries']}
 ck('writer-helper-and-runtime-held',all(str(p).casefold() in held for p in [G,T,P(sys.executable),N/'checkpoint_component_actuals.atomic.py',N/'checkpoint.execution.facts.json']) and any(v['path'].endswith('.dll') for v in writer_guard['entries']))
 ck('writer-refs-held',all(v['path'].casefold() in held for v in refs(f) if v['path'].casefold() not in {str(R/'execution/v2.4/checkpoint.json').casefold(),str(R/'execution/v2.4/path_ownership.json').casefold()}))
 for e in f['reviews']:
  h=obj(e['handoff_ref']['path']);ck('review-component-authority:'+e['scope'],h.get('formal_acceptance') is False)
 a=ww['attach_T11'];n=ww['N12'];ck('T11-2parents3leaves-not-full',a['parent_count']==2 and a['leaf_count']==3 and a['pass_count']==5 and a['fail_count']==a['skip_count']==0 and a['main_adopted'] is False and a['formal_acceptance'] is False and a['other52_parents_not_run'] and a['other132_declared_not_scope'])
 ck('N12-3parents32leaves-not-live',n['parent_count']==3 and n['leaf_count']==32 and n['pass_count']==35 and n['fail_count']==n['skip_count']==0 and n['live_native_cases']==0 and n['live_four_minute_cleanup_qualified'] is False)
 ck('C12-Source-only-at-cutoff',ww['C12']['prepared_config_actual']=='NOT_RUN' and ww['C12']['final_prelaunch_review']=='PENDING' and ww['C12']['new_trial'] is False)
 nc=ww['native_cleanup_CTL4_NH1'];ck('CTL4-CL-NH1-Source-only',nc['source_accepted'] and nc['live_native_four_minute_retention']=='NOT_RUN' and nc['new_C12_outer_required_seconds']==1800 and nc['S10_observed_outer_seconds']==1440 and nc['cleanup_seconds']==240)
 hi=ww['history20'];ck('H20-sealed-not-reviewed-at-cutoff',hi['source']=='SEALED_PENDING_NONAUTHOR_REVIEW' and hi['Go_SQL_actual']=='NOT_RUN' and hi['Main_adopted'] is False and all(hi[k]=='OPEN' for k in ['full20_to24_chain','genuine_historical_owner_programs','historical_B_session_installation','owner_credential_product_flow']))
 t10=ww['native_T10'];ck('T10-failure-not-release',t10['status']=='FAILED_NATURAL_EXIT1_CLOSED_FIXTURE_LOST' and t10['grant_signed_once'] and not any(t10[k] for k in ['grant_published','wholeSQL_after','specific_fixture_release','TTL_refreshed']))
 ck('formal0of42-history6of22-unchanged',ww['historical_accepted_parents']==6 and ww['required_parents']==22 and ww['current_formal_accepted']==0 and ww['required_formal']==42 and cp['current_effective_formal_status']==old['current_effective_formal_status'])
 ck('paid-business-financial-provider-boundaries',ww['original_trial_business']=='OPEN' and ww['original_trial_provider_requests'] is None and ww['financial_closed'] is False and ww['counter_reset'] is False and cp['cost_unknown']==old['cost_unknown'])
 resume=obj(N/'RESUME.r364.original.json');ck('resume-no-completion-new-trial',resume['original_trial_once_consumed'] is True and resume['original_trial_clock_expired'] is True and resume['completion_asserted'] is False and resume['original_trial_provider_requests'] is None and resume['financial_closed'] is False and resume['native_T10_wholeSQL_after_observed'] is False and resume['native_T10_specific_release'] is False)
 # Python JSON integers preserve all 64bit FILETIME digits; export decimal strings only.
 filetimes=[]
 def collect(v,where):
  if isinstance(v,dict):
   for k,x in v.items():
    if k=='creation_time_100ns' and x is not None:
     ck('exact-FILETIME:'+where,type(x) is int);filetimes.append(dict(receipt=where,decimal_string=str(x)))
    elif isinstance(x,(dict,list)):collect(x,where)
  elif isinstance(v,list):
   for x in v:collect(x,where)
 for v in allrefs.values():
  if P(v['path']).name.endswith('.invocation.json'):collect(obj(v['path']),v['path'])
 save('filetime-exact-decimal.json',filetimes);save('failure-exit-qualifications.json',qualifications)
 save('semantic-delta.json',dict(changed_top_level=changed,old893_whole_and_raw_prefix_equal=True,new_ordinals=list(range(896,903)),registered=900,highest902=True,cutoff_next903=True,later903_H20_and904_reviewer_are_pending_not_registered=True,live_next_as_reported_by_Root=905,writer_source_forward_inverse_equal=derived==candidate and inverse==base))
 closure=g.close();save('guard.final.json',closure);ck('review-guard-closed',good(closure))
 result=dict(schema='researchos.independent-cp364-consistency-review.v1',decision='CP364_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY' if all(v['passed'] for v in checks) else 'CP364_CONSISTENCY_FINDINGS',checks=checks,remaining_findings=[v for v in checks if not v['passed']],guarded_input_count=len(allrefs),declared_input_bytes=sum(v['bytes'] for v in allrefs.values()),registered_failures=900,highest_registered_ordinal=902,next_at_cutoff=903,later_pending=[903,904],live_next_as_reported_by_Root=905,new_review_execution_failures=1,new_review_failure_ordinal=904,reviewer_is_not_checkpoint_author=True,canonical_writes=False,formal_acceptance=False,authority='CHECKPOINT_CONSISTENCY_ONLY',no_Git_Go_SQL_native_model_execution=True,no_private_key_or_original_trial_read=True,known_evidence_limitations=['900/901 rg exit2 is inferred only.','902 origin file contains error summary and original chat chunk locator, not a full copied tool output.','H20 followup REQUEST_CHANGES and C12 configuration preparation occur after CP364 cutoff.'],stop=True)
 save('review.json',result)
 print(json.dumps({k:result[k] for k in ['decision','remaining_findings','guarded_input_count','declared_input_bytes','new_review_execution_failures','stop']}|dict(checks_passed=sum(v['passed'] for v in checks),checks_total=len(checks),all_guards_closed=closure['closed']),ensure_ascii=True))
code=0
try:main()
except Exception:traceback.print_exc();code=1
finally:
 if g is not None:
  closure=g.close()
  if not (O/'guard.final.json').exists():save('guard.final.json',closure)
 print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)
