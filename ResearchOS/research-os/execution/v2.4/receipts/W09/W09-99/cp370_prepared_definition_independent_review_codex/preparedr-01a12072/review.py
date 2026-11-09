"""Read-only PreparedDefinition audit. No build/check/activate entry point runs."""
import ast,copy,hashlib,json,sys,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
S=W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009'
N=Path(__file__).resolve().parent
def require(v,c):
 if not v:raise AssertionError(c)
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):
 require(pin(r['path'])==r,'PIN '+r['path']);return Path(r['path']).read_bytes()
def fixed(p,s,n):
 r=dict(path=str(p.resolve(strict=True)),sha256=s,bytes=n);read(r);return r
def save(name,value):
 with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
mr=fixed(S/'source-prepared-manifest.json','ff49d4a724cf3c51dac9971f781113f8db5797c9b04895a948e103075a3bb7bb',2124)
manifest=json.loads(read(mr));members=manifest['source_files_exact_refs'];byname={Path(r['path']).name:r for r in members}
for r in members:read(r)
sr=byname['register_cp370.source.py'];raw=read(sr);tree=ast.parse(raw)
module=types.ModuleType('cp370_prepared_independent');module.__file__=sr['path'];sys.modules[module.__name__]=module
# Only definitions/imports/constants, excluding the CLI guard. No registrar entry point.
exec(compile(ast.Module(body=[n for n in tree.body if not isinstance(n,ast.If)],type_ignores=[]),sr['path'],'exec'),module.__dict__)
prepared=json.loads(read(byname['source-prepared-verification.json']))
canon=prepared['current_before_canonical_refs'];cp,ow,ss,cm=[json.loads(read(r)) for r in canon]
origins=[row['origin_ref'] for row in cp['work_in_progress']['later_diagnostics_observed_after_cutoff']]
root_live_ref=fixed(W/'checkpoint_r369_native_source_root/cp369-c19-20261009/pending-diagnostics.live993.root.json','96f2fe4b7b076c6d49076482124d4ed0b639e59a96973732c0bb9af94b6db4cb',18907)
root_live=json.loads(read(root_live_ref))
prior_guard=json.loads(read(byname['source-guard.cleanup.prepared.json']))
refs=[mr,*members,*canon,*origins,root_live_ref,pin(__file__),pin(sys.executable)]
refs += [{k:e[k] for k in ('path','sha256','bytes')} for e in prior_guard['entries']]
unique={}
for r in refs:
 read(r);k=r['path'].casefold();require(k not in unique or unique[k]==r,'PIN_CONFLICT');unique[k]=r
gp=pin(module.GP);require((gp['sha256'],gp['bytes'])==module.EXACT[str(module.GP)],'TRUSTED_GUARD_PIN')
gm=types.ModuleType('cp370_review_finite_guard');gm.__file__=gp['path'];sys.modules[gm.__name__]=gm;exec(compile(read(gp),gp['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=512*1024*1024)
checks=[];examples=[]
def check(name,ok,detail=None):require(ok,name);checks.append(dict(name=name,passed=True,detail=detail))
def reject(fn):
 try:fn()
 except (ValueError,TypeError,KeyError):return True
 return False
guard.acquire(list(unique.values()))
try:
 check('exact_prepared_definition_and_five_members',len(members)==5 and sr['sha256']=='981ac827ca2c2eca27815580c3c2bbb5d958feba7e78d135b18049ea95f1d793')
 check('before_refs_CP369_OW173',module.before_refs()==canon and cp['revision']==369 and ow['revision']==173)
 check('no_generated_Source_scope_facts_owner_worker',all(not (S/name).exists() for name in ('scope-registration.root.json','registration-facts.root.json','owner-document.root.json','worker-document.root.json')))
 # Synthetic VFS validates genuine digest/size associations in memory only.
 memory={}
 def virtual_file(path,data):
  path=str(path);raw=data if isinstance(data,bytes) else module.encoded(data);memory[path]=raw
  return dict(path=path,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
 def vpin(path):
  path=str(path)
  if path not in memory:return module.pin(path)
  b=memory[path];return dict(path=path,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
 env=dict(module.__dict__);env['pin']=vpin
 # Retain exact original function implementations with virtualized file reads.
 functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
 exec(compile(ast.Module(body=functions,type_ignores=[]),sr['path'],'exec'),env)
 env['pin']=vpin
 def vload(ref):
  env['exact_ref'](ref)
  return module.decode(memory[ref['path']]) if ref['path'] in memory else module.load(ref)
 env['load']=vload
 rootcaller=module.CALLER_SOURCE_ROOT/'SYNTHETIC_NOT_CREATED'
 rc=virtual_file(rootcaller/'caller.py',b'SYNTHETIC_NONAUTHORITATIVE_CALLER')
 contract=virtual_file(rootcaller/'contract.md',b'SYNTHETIC_NONAUTHORITATIVE_CONTRACT')
 cmf=virtual_file(rootcaller/'MF.json',dict(caller_source_ref=rc,contract_ref=contract,members=[]))
 chdf=virtual_file(rootcaller/'HDF.json',dict(status='SOURCE_ONLY_PENDING_ROOT_REGISTRATION',manifest_ref=cmf,caller_source_ref=rc,root_contract_ref=contract))
 caller=env['ensure_caller_source'](chdf,cmf)
 check('counterexample_empty_caller_MF_members_accepted',caller==(chdf,cmf,rc,contract))
 reviewroot=module.CALLER_REVIEW_ROOT/'SYNTHETIC_NOT_CREATED'
 rm=virtual_file(reviewroot/'MF.json',dict(members=[]))
 d=dict(schema=module.SOURCE_REVIEW_SCHEMA,decision='ACCEPTED_SOURCE_ONLY',actor_role='INDEPENDENT_NON_AUTHOR',actor_id='codex:/root/designated_reviewer',source_author_id=module.AUTHOR,source_hdf_ref=chdf,source_mf_ref=cmf,caller_ref=rc,root_contract_ref=contract,SourceAcceptedonly=True,noactualorformal=True,actual_dispatcher_run=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0)
 def review_request(doc):
  dr=virtual_file(reviewroot/'decision.json',doc)
  rh=virtual_file(reviewroot/'HDF.json',dict(manifest_ref=rm,source_decision_ref=dr,actor_id=doc['actor_id'],actor_role='INDEPENDENT_NON_AUTHOR'))
  return dict(review_hdf_ref=rh,review_mf_ref=rm,review_decision_ref=dr)
 request=review_request(d)
 result=env['validate_review'](request,caller)
 check('counterexample_empty_review_MF_members_accepted',result[2]==request['review_decision_ref'])
 examples.append(dict(id='CP370-F1',input_kind='IN_MEMORY_ONLY_VALID_SHA_SIZE_REFS',caller_manifest=dict(caller_source_ref=rc,contract_ref=contract,members=[]),review_manifest=dict(members=[]),actual='ensure_caller_source and validate_review both return success without required files being manifest members',expected='Reject unsealed caller/contract/decision membership'))
 alias=copy.deepcopy(d);alias['actor_id']='/root'
 check('counterexample_Root_actor_alias_accepted',env['validate_review'](review_request(alias),caller)[3]['actor_id']=='/root')
 examples.append(dict(id='CP370-F1-ALIAS',actor_id='/root',source_author_id=module.AUTHOR,actual='validate_review accepts Root path alias as independent actor',expected='Reject canonical Root aliases and bind real designated independent reviewer'))
 author=copy.deepcopy(d);author['actor_id']=module.AUTHOR
 check('exact_Source_author_rejected',reject(lambda:env['validate_review'](review_request(author),caller)))
 root=copy.deepcopy(d);root['actor_id']=module.ROOT
 check('exact_Root_actor_rejected',reject(lambda:env['validate_review'](review_request(root),caller)))
 for field in ('source_hdf_ref','source_mf_ref','caller_ref'):
  bad=copy.deepcopy(d);bad[field]=contract
  check('wrong_exact4_binding_rejected_'+field,reject(lambda bad=bad:env['validate_review'](review_request(bad),caller)))
 bad=copy.deepcopy(d);bad['root_contract_ref']=rc
 check('wrong_contract_ref_rejected',reject(lambda:env['validate_review'](review_request(bad),caller)))
 live=dict(schema='researchos.root-postseal-live-diagnostic-context.v1',issued_by=module.ROOT,created_utc='SYNTHETIC_NONAUTHORITATIVE',source_cutoff={'highest_ordinal':965,'next_failure_ordinal':966},next_original_failure_ordinal=970,pending=[dict(row,actual_outer_exit=None,actual_python_exit=None,actual_native_exit=None) for row in cp['work_in_progress']['later_diagnostics_observed_after_cutoff']])
 for created in (None,False,'1900-01-01T00:00:00Z','not-a-time'):
  candidate=copy.deepcopy(live);candidate['created_utc']=created;env['validate_live'](candidate)
  check('counterexample_unverified_live_time_'+repr(created),True)
 register_ast=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='register')
 facts_gate=next(n for n in ast.walk(register_ast) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='FACTS_EXACT_SCOPE')
 source_live_ref=virtual_file(N/'source-live-not-on-disk.json',live)
 testfacts=dict(schema='researchos.root-cp370-c19-two-dispatcher-registration-facts.v1',issued_by=module.ROOT,live_ref=source_live_ref,source_cutoff=live['source_cutoff'],root_next_failure_ordinal_live=970,no_actual_consumer_run=True,formal_dispatcher=True,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0)
 facts_gate_code=compile(ast.Expression(facts_gate.args[0]),sr['path'],'eval')
 check('activation_facts_gate_accepts_same_early_context',eval(facts_gate_code,dict(facts=testfacts,live_ref=source_live_ref,live=live,ROOT=module.ROOT)))
 fresh=copy.deepcopy(live);fresh['created_utc']='2026-10-09T13:00:00Z'
 fresh_ref=virtual_file(N/'fresh-postseal-not-on-disk.json',fresh)
 check('activation_facts_gate_rejects_new_postseal_ref',not eval(facts_gate_code,dict(facts=testfacts,live_ref=fresh_ref,live=fresh,ROOT=module.ROOT)))
 examples.append(dict(id='CP370-F2',actual='register requires the exact early facts.live_ref and request.live_ref; a distinct fresh postseal ref is rejected, while early context time is never checked. validate_live also accepts null/false/1900/malformed created_utc.',known_Root_next_at_review=993,Root_current_ledger_ref=root_live_ref,qualification='Early Source cutoff is legitimate Source evidence, but cannot stand in for fresh activation context.',expected='Keep Source context immutable and require a separate authentic fresh postseal Root context at activation, bound to sealed review/facts and current original cutoff.'))
 fabricated=copy.deepcopy(live);fabricated['pending'][1]['actual_outer_exit']=0;fabricated['pending'][1]['actual_native_exit']=0
 env['validate_live'](fabricated)
 check('counterexample_known_failure_and_unknown_native_overridden_zero',True)
 examples.append(dict(id='CP370-F3',ordinal=967,origin_ref=fabricated['pending'][1]['origin_ref'],description=fabricated['pending'][1]['description'],supplied_outer_exit=0,supplied_native_exit=0,actual='Accepted despite origin description outer1 and no observed Native execution',expected='Bind observed numeric exits to original envelope; unknown Native exit remains null'))
 duplicate=copy.deepcopy(live);duplicate['next_original_failure_ordinal']=971;extra=copy.deepcopy(duplicate['pending'][0]);extra['ordinal']=970;duplicate['pending'].append(extra)
 env['validate_live'](duplicate)
 check('counterexample_same_origin_reused_under_new_ordinal',True)
 # Execute only the exact append loop, not register/build/activate or a Caller.
 transform_ast=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='transformed_pair')
 seen_node=next(n for n in transform_ast.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='seen')
 append_node=next(n for n in transform_ast.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='row')
 append_env=dict(env,cp=copy.deepcopy(cp),live=duplicate)
 exec(compile(ast.Module(body=[seen_node,append_node],type_ignores=[]),sr['path'],'exec'),append_env)
 appended=append_env['cp']['failure_counters'][963:]
 matches=[row for row in appended if row['evidence_ref']==extra['origin_ref']]
 check('counterexample_duplicate_origin_counted_twice',len(matches)==2 and {row['original_payload']['observed_ordinal'] for row in matches}=={966,970})
 row971=next(row for row in root_live['pending'] if row['ordinal']==971);row972=next(row for row in root_live['pending'] if row['ordinal']==972)
 check('actual_shared_file_distinct_selectors_are_legitimate',row971['origin_ref']==row972['origin_ref'] and row971['origin_selector']!=row972['origin_selector'])
 selected=copy.deepcopy(live);selected['pending'][0]['origin_selector']='2acc95'
 check('current_live_schema_rejects_required_original_selector',reject(lambda:env['validate_live'](selected)))
 examples.append(dict(id='CP370-F4',actual='The same single invocation966 is accepted and appended again as970; schema has no original selector and forbids adding one. Root actual971/972 legitimately share one file with distinct selectors, so file-ref uniqueness would be incorrect.',duplicated_single_invocation_origin_ref=extra['origin_ref'],appended_rows=matches,legitimate_shared_file_examples=[row971,row972],expected='Preserve and verify an original invocation selector and exit_qualification. Deduplicate original event identity (origin pin plus selector), permit distinct selectors in one file, and bind immutable original ordinals.'))
 for label,mutate in [('bool_exit',lambda x:x['pending'][0].__setitem__('actual_native_exit',False)),('float_exit',lambda x:x['pending'][0].__setitem__('actual_python_exit',0.0)),('duplicate_ordinal',lambda x:x['pending'][1].__setitem__('ordinal',966)),('gap',lambda x:x['pending'].pop())]:
  b=copy.deepcopy(live);mutate(b);check('typed_or_contiguous_negative_'+label,reject(lambda b=b:env['validate_live'](b)))
 request_ast=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_root_build_request')
 gate=next(n for n in ast.walk(request_ast) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='OUTPUT_ROOT_SCOPE')
 output_code=compile(ast.Expression(gate.args[0]),sr['path'],'eval')
 def output_gate(path):return eval(output_code,dict(output_root=Path(path),ROOT_OUTPUT_BOUNDARY=module.ROOT_OUTPUT_BOUNDARY))
 check('strict_boundary_itself_rejected',not output_gate(W))
 check('strict_child_positive',output_gate(W/'SYNTHETIC_NOT_CREATED'))
 aliaspath=W/'SYNTHETIC_NOT_CREATED'/'..'
 check('counterexample_dotdot_boundary_alias_accepted',aliaspath.resolve()==W and output_gate(aliaspath))
 examples.append(dict(id='CP370-F5',supplied_output_root=str(aliaspath),resolved_output_root=str(aliaspath.resolve()),actual='OUTPUT_ROOT_SCOPE accepts alias resolving to the entire W09-99 receipt boundary',expected='Compare resolved canonical path against boundary and require a strict child; bind one bounded output namespace'))
 for iso in (False,'bad-time','2000-01-01T00:00:00Z','2999-01-01T00:00:00'):
  check('lease_invalid_rejected_'+repr(iso),reject(lambda iso=iso:env['_future'](iso)))
 env['_future']('2999-01-01T00:00:00Z');check('future_aware_lease_positive',True)
 # Pure transform with a transparent dependency stub; no claim about final Caller acceptance.
 # This verifies the inverse and preserved history only, with Caller validation explicitly open.
 scope=dict(formal_dispatcher=True,formal_acceptance=False,parent_acceptance=False,before_canonical_refs=canon,caller_ref=rc,authorized_output_root=str(W/'SYNTHETIC_NOT_CREATED'))
 scope_ref=virtual_file(N/'synthetic-scope-not-on-disk.json',scope)
 common=dict(step_id='W09-99',slice_id=module.SLICE,state=module.STATE,scope_ref=scope_ref,output_root=scope['authorized_output_root'],routes=module.ROUTES,lease_status='ACTIVE',lease_expires_at='2999-01-01T00:00:00Z')
 owner_ref=virtual_file(N/'synthetic-owner-not-on-disk.json',dict(common,owner_id=module.ROOT,selected_worker_id=module.ROOT))
 worker_ref=virtual_file(N/'synthetic-worker-not-on-disk.json',dict(common,worker_id=module.ROOT,selected_owner_ref=owner_ref))
 facts=dict(scope_ref=scope_ref,owner_document_ref=owner_ref,worker_document_ref=worker_ref,source_hdf_ref=chdf,source_review_decision_ref=request['review_decision_ref'],created_utc='2026-10-09T12:00:00Z')
 factsref=virtual_file(N/'synthetic-facts-not-on-disk.json',facts)
 class CallerBoundary:
  @staticmethod
  def validate_scope(*args):pass
  @staticmethod
  def validate_canon_lease(*args):pass
 env['verified_module']=lambda *args:CallerBoundary
 aftercp,afterow=env['transformed_pair'](copy.deepcopy(cp),copy.deepcopy(ow),facts,live,cp,ow,factsref)
 check('pure_transform_complete_inverse_checks_pass',aftercp['revision']==370 and afterow['revision']==174,dict(final_Caller_validators='ABSTRACTED_NOT_VALIDATED',no_grant=True))
 check('pure_transform_original963_and_workers_preserved',aftercp['failure_counters'][:963]==cp['failure_counters'] and aftercp['workers'][:-1]==cp['workers'])
 builder_ast=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_root_docs')
 scope_assign=next(n for n in builder_ast.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='scope')
 actual_scope_keys={kw.arg for kw in scope_assign.value.keywords}
 check('source_Scope_definition_no_future_Canon_or_proof_cycle',not actual_scope_keys.intersection({'current_canonical_vector','registration_proof_ref','after_canonical_refs','facts_ref','build_request_ref'}))
 for r in canon:read(r)
 check('current_four_Canon_unchanged_after_controls',True)
 cr=save('controls.json',dict(schema='researchos.cp370-prepared-definition-controls.v1',evidence_kind='NON_AUTHORITATIVE_PREPARED_DEFINITION_CONTROLS',checks=checks,counterexamples=examples,final_Caller_Source='MISSING',final_Caller_validators_in_inverse_test='ABSTRACTED_ONLY',build_run=False,check_run=False,activate_run=False,Main_or_Canon_written=False,Native_or_dispatcher_run=False))
finally:
 closure=guard.close();gr=save('sourceguard.final.json',closure)
require(closure['closed'] is True and closure['retained_handles_count']==0 and not closure['errors'],'REAL_GUARD_CLOSED')
findings=[
 dict(id='CP370-F1',priority='P1',lines=[155,223],title='Final Caller and independent review manifests do not seal their claimed members',actual='Empty caller/review MF members pass; review MF is loaded but unused. Canonical Root path alias /root is also accepted as independent actor.',fix='Validate exact caller/contract/decision membership and HDF/MF association, and bind the canonical independently designated reviewer and its original handoff provenance.'),
 dict(id='CP370-F2',priority='P1',lines=[226,247,482,507],title='Activation has no separate authentic fresh postseal Root context',actual='register binds live_ref to immutable early facts and request; a new postseal ref is rejected. Earlier Source context remains admissible without timestamp/provenance checks, and created_utc accepts null/false/malformed values.',fix='Preserve the early Source context and add a separate authentic fresh postseal Root activation context bound to sealed facts/review and the current original cutoff; verify its timestamp and original Root provenance.'),
 dict(id='CP370-F3',priority='P1',lines=[240,247],title='Original failure numeric results can be fabricated',actual='Ordinal967 original outer1/Native unobserved can be supplied as outer0/Native0. Only nullable-int shape and origin file pin are verified; original envelope numeric values are not compared.',fix='Extract and bind original observed exits, preserving unknown as null and matching immutable original ordinal/event identity.'),
 dict(id='CP370-F4',priority='P1',lines=[240,247,402,413],title='Original invocation selector and exit qualification are lost',actual='The single invocation966 can be counted again as970 because dedup trusts the supplied ordinal. Exact row schema has no selector or exit_qualification. Root971/972 correctly share one original file with different selectors, which the schema cannot retain.',fix='Preserve and verify origin_selector and exit_qualification, bind immutable original ordinal to that invocation, and deduplicate (origin pin,selector) across existing/pending events. Distinct selectors sharing a file must remain legal.'),
 dict(id='CP370-F5',priority='P1',lines=[265,267],title='Output root alias admits the whole receipt boundary',actual='W09-99/SYNTHETIC_NOT_CREATED/.. passes OUTPUT_ROOT_SCOPE and normalizes to W09-99 itself.',fix='Canonicalize once, require canonical spelling and a strict child of ROOT_OUTPUT_BOUNDARY, then persist only that bounded canonical output root.')]
fr=save('findings.json',dict(blocking_count=len(findings),findings=findings,controls_ref=cr,registrar_ref=sr))
dr=save('prepared-definition-decision.json',dict(schema='researchos.cp370-independent-prepared-definition-decision.v1',decision='PREPARED_DEFINITION_REQUEST_CHANGES',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',source_prepared_manifest_ref=mr,registrar_ref=sr,controls_ref=cr,findings_ref=fr,actual_SourceGuard_ref=gr,retained_handles_count=0,checks=len(checks),final_Caller_SourceAccepted_inputs='MISSING',final_registration_SourceAccepted=False,RootScopeCreated=False,CanonWritten=False,NativeExecuted=False,DispatcherExecuted=False,formal_case_accepted_delta=0,parent_acceptance=False,new_original_failures=[],STOP=True,FINAL=True))
print(json.dumps(dict(decision_ref=dr,findings_ref=fr,controls_ref=cr,guard_ref=gr,checks=len(checks),held_refs=len(unique)),ensure_ascii=False))
