from pathlib import Path
import ast,copy,difflib,hashlib,json,types
O=Path(__file__).resolve().parent;P=O.parent/'continue-20261010-03';B=O.parents[1]
D=B/'public22_main23_scope_generation_diagnosis_codex/diagnose-20261010-01'
Q=B/'public22_to_main23_continuation_independent_review_codex/review-20261010-03-full'
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def enc(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def doc(p):return json.loads(Path(p).read_bytes())
def verify(r):
 a=pin(r['path']);assert a['sha256']==r['sha256'] and a['bytes']==r['bytes'];return r
def save(n,v,raw=False):
 with (O/n).open('xb') as f:f.write(v if raw else enc(v))
 return pin(O/n)
fixed=[(P/'HDF.json','6b35f9035b3b8e59971d7afbd32e672e981337b7b4608b8daeed2bd4e3c8bb48',8487),
 (P/'MF.json','30840d853defc51994e6365a943f6e3f3d58c0e312dbfa0809d38ffe5f7e664d',7493),
 (P/'public22_to23_root.source.py','6763484bdaf4f41b13f4e5b54d89969f67c766064d86bdc3ecdc9b386d83a847',52377),
 (D/'HDF.json','6d46de8918313d2ed2d25638036bfa2f630ee88e7918469a8f8e5d9d396cd507',8673),
 (D/'MF.json','84a8bb497c0d288225815b7eddabaa3ca76778fefc629ad322310122c0a3b7d8',5294),
 (D/'decision.json','4f7c8901b6b7301ae6d80e3d533341d0d528d7caf9d363cdd8421aa110aa4848',13735),
 (Q/'decision.json','efc77d674a089aa676e523b335f57139fcd5516e898cd80104932d817b9e591c',16337)]
protected=[verify(dict(path=str(p),sha256=h,bytes=n)) for p,h,n in fixed]
for directory in (P,D,Q):
 h=doc(directory/'HDF.json');m=doc(directory/'MF.json');verify(h['manifest_ref'])
 protected.extend([pin(directory/'HDF.json'),pin(directory/'MF.json')])
 protected.extend(verify(r) for r in m['members'])
diagnosis=doc(D/'decision.json');review=doc(Q/'decision.json')
assert review['decision']=='ACCEPTED_SOURCE_ONLY' and review['source_author']=='codex:/root/attach_restore_independent_review'
lineage=diagnosis['predecessor_lineage']
line_refs=[v for v in lineage.values() if type(v) is dict and set(v)=={'path','sha256','bytes'}]+lineage['after_archive_refs']
protected.extend(verify(r) for r in line_refs)
guardpath=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=verify(dict(path=str(guardpath),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404))
protected.append(gr);protected=list({str(Path(r['path'])).lower():r for r in protected}.values())
gm=types.ModuleType('source04_guard');gm.__file__=str(guardpath);exec(compile(guardpath.read_bytes(),str(guardpath),'exec'),gm.__dict__)
guard=gm.SourceReadGuard();closed=None
try:
 guard.acquire(protected)
 cp0,ow0=[doc(r['path']) for r in lineage['after_archive_refs']]
 oldkey='public22_to_main23_continuation';oldslice='PUBLIC22_TO_MAIN23_CONTINUATION'
 oldworkers=[w for w in cp0['workers'] if w.get('slice_id')==oldslice];assert len(oldworkers)==1
 oldworker=oldworkers[0];oldtask=ow0['card_path_bindings']['W05-99']['subtasks'][oldkey]
 assert all(x['state']=='CLOSED_ACTUAL_PREPARE_FAILED_NO_NATIVE' and x['lease_status']=='CONSUMED' and x['one_shot_consumed'] is True and x['future_execution_permitted'] is False for x in (oldtask,oldworker))
 pred=dict(key=oldkey,slice_id=oldslice,scope_ref=lineage['scope_ref'],owner_ref=lineage['owner_ref'],worker_ref=lineage['worker_ref'],
  lease_id=oldtask['lease_id'],actual_failed_case_ref=lineage['actual_failed_case_ref'],closure_committed_ref=lineage['closure_committed_ref'],
  owner_canonical_sha256=hashlib.sha256(enc(oldtask)).hexdigest(),worker_canonical_sha256=hashlib.sha256(enc(oldworker)).hexdigest())
 predecessor=save('predecessor-lineage.json',dict(schema='researchos.public22-generation-predecessor.v1',fixed_predecessor=pred,
  frozen_lineage=lineage,source03_hdf_ref=pin(P/'HDF.json'),source03_mf_ref=pin(P/'MF.json'),source03_full_review_ref=pin(Q/'decision.json'),
  diagnosis_ref=pin(D/'decision.json'),original1201='FAILED_RETAINED',original1025='FAILED_RETAINED',
  archive_revisions_only=dict(checkpoint=386,path_ownership=190),future_before_counters='preserve complete actual before; do not reset to archival values',
  formal_acceptance=False,execution_grant=False))
 helper='''def predecessor_generation(cp,ow,scope_ref,owner,worker):
    """Pure fixed-generation gate; archival hashes never supply current counters."""
    p=PREDECESSOR
    tasks=ow['card_path_bindings']['W05-99']['subtasks']
    old=tasks.get(p['key'])
    prior=[w for w in cp['workers'] if w.get('slice_id')==p['slice_id']]
    need(type(old) is dict and len(prior)==1,'PREDECESSOR_EXACTLY_ONE')
    need(sum(w.get('scope_ref')==p['scope_ref'] for w in cp['workers'])==1
        and sum(t.get('slice_id')==p['slice_id'] or t.get('scope_ref')==p['scope_ref'] for t in tasks.values())==1,'PREDECESSOR_UNIQUE_CHAIN')
    previous=prior[0]
    for row in (old,previous):
        need(row.get('state')=='CLOSED_ACTUAL_PREPARE_FAILED_NO_NATIVE' and row.get('lease_status')=='CONSUMED'
            and row.get('one_shot_consumed') is True and row.get('future_execution_permitted') is False,'PREDECESSOR_CLOSED_CONSUMED')
        need(row.get('step_id')=='W05-99' and row.get('slice_id')==p['slice_id'] and row.get('owner')==ROOT
            and row.get('scope_ref')==p['scope_ref'] and row.get('worker_document_ref')==p['worker_ref']
            and row.get('lease_id')==p['lease_id'],'PREDECESSOR_EXACT_LINKS')
        actual=row.get('actual_closed',{})
        need(actual.get('case_closed_ref')==p['actual_failed_case_ref'] and actual.get('first_failure_original_ordinal')==1201
            and actual.get('Native_children_attempted')==0 and actual.get('actual_native_exit') is None,'PREDECESSOR_ORIGINAL1201')
    need(old.get('owner_document_ref')==previous.get('selected_owner_ref')==p['owner_ref']
        and old.get('owner_id')==old.get('selected_worker_id')==previous.get('worker_id')==ROOT,'PREDECESSOR_OWNER_WORKER')
    need(hashlib.sha256(encoded(old)).hexdigest()==p['owner_canonical_sha256']
        and hashlib.sha256(encoded(previous)).hexdigest()==p['worker_canonical_sha256'],'PREDECESSOR_CLOSED_BYTES')
    need(scope_ref!=p['scope_ref'] and owner.get('lease_id')!=p['lease_id'] and worker.get('lease_id')!=p['lease_id'],'NEW_GENERATION_FRESH_SCOPE_LEASE')


'''
 source=(P/'public22_to23_root.source.py').read_bytes().decode('utf-8')
 oldconstants="KEY='public22_to_main23_continuation';SLICE='PUBLIC22_TO_MAIN23_CONTINUATION'\n"
 newconstants="KEY='public22_to_main23_continuation_gen02';SLICE='PUBLIC22_TO_MAIN23_CONTINUATION_GEN02'\nPREDECESSOR="+repr(pred)+'\n'
 anchor='def projection(cp0,ow0,scope_ref,owner_ref,worker_ref,facts_ref,owner,worker,created):\n'
 call='    predecessor_generation(cp0,ow0,scope_ref,owner,worker)\n'
 oldbody='    cp=copy.deepcopy(cp0);ow=copy.deepcopy(ow0)\n'
 assert source.count(oldconstants)==source.count(anchor)==source.count(oldbody)==1
 candidate=source.replace(oldconstants,newconstants,1).replace(anchor,helper+anchor,1).replace(oldbody,call+oldbody,1)
 assert candidate.replace(newconstants,oldconstants,1).replace(helper,'',1).replace(call,'',1)==source
 caller=save('public22_to23_root.source.py',candidate.encode(),True)
 before_ast={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 after_ast={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(candidate).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 assert set(after_ast)-set(before_ast)=={'predecessor_generation'}
 assert [n for n in before_ast if before_ast[n]!=after_ast[n]]==['projection']
 save('revision.patch',''.join(difflib.unified_diff(source.splitlines(True),candidate.splitlines(True),fromfile='Source03/public22_to23_root.source.py',tofile='Source04/public22_to23_root.source.py')).encode(),True)
 save('revision-inverse.json',dict(prior_caller_ref=pin(P/'public22_to23_root.source.py'),caller_ref=caller,byte_inverse_exact=True,
  changed_functions=['projection'],added_functions=['predecessor_generation'],other_function_AST_unchanged=True,MODE_schema_business_gates_unchanged=True))
 i=doc(P/'source-inputs.json');oldinputs=copy.deepcopy(i)
 inherited=[pin(P/'HDF.json'),pin(P/'MF.json'),pin(Q/'HDF.json'),pin(Q/'MF.json'),pin(Q/'decision.json'),pin(D/'HDF.json'),pin(D/'MF.json'),pin(D/'decision.json'),predecessor,*line_refs]
 i['generation_predecessor_ref']=predecessor;i['source_resource_refs']+=inherited
 save('source-inputs.json',i)
 restored=copy.deepcopy(i);del restored['generation_predecessor_ref'];del restored['source_resource_refs'][-len(inherited):]
 assert restored==oldinputs
 save('input-inverse.json',dict(prior_inputs_ref=pin(P/'source-inputs.json'),added_generation_ref=predecessor,
  append_only_source_resource_refs=inherited,complete_structural_inverse=True,all_prior_inputs_unchanged=True))
 # Extract only pure functions. Neither caller import nor any entrypoint runs.
 selected={'need','encoded','predecessor_generation','projection'}
 nodes=[n for n in ast.parse(candidate).body if isinstance(n,ast.FunctionDef) and n.name in selected]
 assert len(nodes)==4
 env=dict(copy=copy,json=json,hashlib=hashlib,PREDECESSOR=pred,KEY='public22_to_main23_continuation_gen02',SLICE='PUBLIC22_TO_MAIN23_CONTINUATION_GEN02',ROOT='codex:/root')
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'<Source04-pure-generation-only>','exec'),env)
 basecp=copy.deepcopy(cp0);baseow=copy.deepcopy(ow0)
 basecp['revision']=387;baseow['revision']=191
 basecp['failure_counters'].append({'ordinal':999999,'status':'SYNTHETIC_PURE_CONTROL'})
 basecp['work_in_progress']['root_next_failure_ordinal_live']=1218
 fake=lambda n:dict(path=str(O/('synthetic-'+n+'.json')),sha256='a'*64,bytes=1)
 sr,oref,wref,fref=[fake(n) for n in ('scope','owner','worker','facts')]
 owner=dict(scope_ref=sr,selected_worker_id='codex:/root',lease_id='0'*32,slice_id=env['SLICE'])
 worker=dict(scope_ref=sr,selected_owner_ref=oref,worker_id='codex:/root',lease_id='0'*32,slice_id=env['SLICE'])
 def run(cp,ow,scope=sr,own=owner,work=worker):return env['projection'](cp,ow,scope,oref,wref,fref,own,work,'SYNTHETIC_CREATED')
 checks=[]
 resultcp,resultow=run(basecp,baseow)
 assert resultcp['workers'][:-1]==basecp['workers'] and resultow['card_path_bindings']['W05-99']['subtasks'][oldkey]==oldtask
 assert resultcp['failure_counters']==basecp['failure_counters'] and resultcp['work_in_progress']['root_next_failure_ordinal_live']==1218
 assert resultcp['revision']==388 and resultow['revision']==192
 checks.append(dict(name='closed_exact_predecessor_fresh_generation_complete_inverse_future_counters',result='PASS'))
 def negative(name,mutate,expected):
  cp,ow=copy.deepcopy(basecp),copy.deepcopy(baseow);own,work=copy.deepcopy(owner),copy.deepcopy(worker);sc=copy.deepcopy(sr)
  mutate(cp,ow,own,work,sc)
  try:run(cp,ow,sc,own,work)
  except ValueError as e:assert str(e)==expected,(name,str(e),expected)
  else:raise AssertionError(name+' accepted')
  checks.append(dict(name=name,rejected_by=expected,result='PASS'))
 task=lambda ow:ow['card_path_bindings']['W05-99']['subtasks'][oldkey]
 prior=lambda cp:next(w for w in cp['workers'] if w.get('slice_id')==oldslice)
 negative('missing_predecessor_owner',lambda cp,ow,*_:ow['card_path_bindings']['W05-99']['subtasks'].pop(oldkey),'PREDECESSOR_EXACTLY_ONE')
 negative('missing_predecessor_worker',lambda cp,ow,*_:cp['workers'].remove(prior(cp)),'PREDECESSOR_EXACTLY_ONE')
 negative('duplicate_old_worker',lambda cp,ow,*_:cp['workers'].append(copy.deepcopy(prior(cp))),'PREDECESSOR_EXACTLY_ONE')
 negative('alias_old_scope_worker',lambda cp,ow,*_:cp['workers'].append(dict(prior(cp),slice_id='ALIAS')),'PREDECESSOR_UNIQUE_CHAIN')
 negative('alias_old_owner',lambda cp,ow,*_:ow['card_path_bindings']['W05-99']['subtasks'].update(alias=copy.deepcopy(task(ow))),'PREDECESSOR_UNIQUE_CHAIN')
 negative('old_still_active',lambda cp,ow,*_:task(ow).update(state='ROOT_REGISTERED_PUBLIC22_TO_MAIN23_CONTINUATION'),'PREDECESSOR_CLOSED_CONSUMED')
 negative('old_lease_active',lambda cp,ow,*_:prior(cp).update(lease_status='ACTIVE'),'PREDECESSOR_CLOSED_CONSUMED')
 negative('old_not_consumed',lambda cp,ow,*_:task(ow).update(one_shot_consumed=False),'PREDECESSOR_CLOSED_CONSUMED')
 negative('old_future_permitted',lambda cp,ow,*_:prior(cp).update(future_execution_permitted=True),'PREDECESSOR_CLOSED_CONSUMED')
 negative('wrong_old_scope',lambda cp,ow,*_:task(ow).update(scope_ref=fake('foreign')),'PREDECESSOR_EXACT_LINKS')
 negative('wrong_old_worker_ref',lambda cp,ow,*_:task(ow).update(worker_document_ref=fake('foreign')),'PREDECESSOR_EXACT_LINKS')
 negative('wrong_old_owner_ref',lambda cp,ow,*_:prior(cp).update(selected_owner_ref=fake('foreign')),'PREDECESSOR_OWNER_WORKER')
 negative('wrong_original_failure',lambda cp,ow,*_:task(ow)['actual_closed'].update(first_failure_original_ordinal=1200),'PREDECESSOR_ORIGINAL1201')
 negative('old_closed_extra_mutation',lambda cp,ow,*_:task(ow).update(closed_at='mutated'),'PREDECESSOR_CLOSED_BYTES')
 negative('gen02_key_collision',lambda cp,ow,*_:ow['card_path_bindings']['W05-99']['subtasks'].update({env['KEY']:{}}),'READONLY_SLICE_ALREADY_REGISTERED')
 negative('gen02_slice_collision',lambda cp,ow,*_:cp['workers'].append(dict(slice_id=env['SLICE'])),'READONLY_SLICE_ALREADY_REGISTERED')
 negative('reused_old_scope',lambda cp,ow,own,work,sc:sc.update(pred['scope_ref']),'NEW_GENERATION_FRESH_SCOPE_LEASE')
 negative('reused_old_lease',lambda cp,ow,own,work,sc:own.update(lease_id=pred['lease_id']),'NEW_GENERATION_FRESH_SCOPE_LEASE')
 controls=save('generation-delta-controls.json',dict(schema='researchos.source04-pure-generation-controls.v1',checks=checks,count=len(checks),
  basis='immutable CP386/OW190 archives with synthetic future counter append and revisions 387/191; no live Canon reads',
  pure_projection_calls=len(checks),old_12_26_144_149_replayed=False,build_activate_execute_Native_SQL_models_TP_calls=0))
 prefix=save('historical-review-prefix.json',dict(source03_review_ref=pin(Q/'decision.json'),source03_hdf_ref=pin(P/'HDF.json'),
  source03_controls_ref=pin(P/'delta-source-controls.json'),source03_prefix_ref=pin(P/'historical-review-prefix.json'),
  prior_controls_12_26_144_149_replayed=False,source03_acceptance_does_not_accept_source04=True))
 contract=doc(P/'root-calling-contract.source.json')
 contract.update(caller_ref=caller,source_inputs_ref=pin(O/'source-inputs.json'),source_only_controls=controls,
  source_revision='continue-20261010-04',revision_reason='FIXED_GENERATION_02_AFTER_CLOSED_PREDECESSOR',historical_review_prefix_ref=prefix,
  generation=dict(KEY=env['KEY'],SLICE=env['SLICE'],predecessor_ref=predecessor,prior_scope_is_consumed=True,
   gate='Pure exact unique closed/consumed/futurefalse predecessor owner-worker-scope chain; fresh scope/lease; old generation rows immutable.',
   counters='Complete actual fresh before counters and next ordinal preserved; CP386 closure is lineage only.'),
  runtime_resource_qualification='Preserve Source03 runtime149 qualification evidence; Source04 still requires true Full non-author source review. No runtime replay performed by author.')
 save('root-calling-contract.source.json',contract)
 save('source-decision.json',dict(status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION',revision='continue-20261010-04',
  caller_ref=caller,source_inputs_ref=pin(O/'source-inputs.json'),calling_contract_ref=pin(O/'root-calling-contract.source.json'),
  predecessor_ref=predecessor,delta_controls_ref=controls,historical_prefix_ref=prefix,
  MODE_schema_business_gates_unchanged=True,original1201='FAILED_RETAINED',original1025='FAILED_RETAINED',
  old_scope_not_removed_or_reactivated=True,new_generation_fixed=True,prior_success_controls_replayed=False,
  live_Canon_read=False,Main_Canon_Scope_writes=0,Native_SQL_models_Rootstage_TP_calls=0,
  formal_acceptance=False,parent_acceptance=False,execution_grant=False,self_acceptance=False))
 save('protected-inputs.json',protected)
 assert all(verify(r) for r in protected)
finally:
 closed=guard.close();save('SourceGuard.closed.json',closed)
assert closed['closed'] is True and closed['retained_handles_count']==0 and not closed['errors']
print(json.dumps(dict(status='SOURCE04_PREPARED_UNSEALED',caller_ref=pin(O/'public22_to23_root.source.py'),controls_ref=pin(O/'generation-delta-controls.json'),guard_closed=True),ensure_ascii=False))
