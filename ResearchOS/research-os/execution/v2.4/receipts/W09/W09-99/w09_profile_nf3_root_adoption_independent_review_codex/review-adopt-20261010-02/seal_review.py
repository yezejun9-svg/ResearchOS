"""Seal AD02 independent Source review; no Root audit, Scope or product grant."""
import ast,copy,hashlib,json,types
from datetime import datetime,timezone
from pathlib import Path
D=Path(__file__).resolve().parent;S=D.parent.parent/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-02';OLD=D.parent/'review-adopt-20261010-01'
ACTOR='codex:/root/full_w09_source_review';AUTHOR='codex:/root/backup_regression_resources'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(name,value):
 with (D/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(D/name)
def module(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def main():
 h=doc(S/'HDF.json');mf=doc(S/'MF.json');inputs=doc(h['input_pins_ref']['path']);reg=module(h['caller_ref']['path'],'AD02_seal_registrar');core=module(h['core_ref']['path'],'AD02_seal_core');gm=module(inputs['refs']['guard']['path'],'AD02_seal_guard')
 controls=doc(D/'finite-delta-controls.json');resolved=doc(D/'finite-delta-controls.resolved.json')
 assert controls['passed']==40 and controls['failed']==1 and resolved['new_controls_passed']==1 and resolved['new_controls_failed']==0
 guards=[pin(D/x) for x in ('independent-delta-Source-guard.closed.json','continuation-Source-guard.closed.json')]+h['source_guard_refs']
 for ref in guards:
  g=doc(ref['path']);assert g['closed'] and g['retained_handles_count']==0 and not g['errors']
 href=reg.pin(S/'HDF.json');mref=reg.pin(S/'MF.json');bindings={k:h[k] for k in ('caller_ref','core_ref','main_pair_ref','contract_ref')}
 assert href['sha256']=='265747939bf081d26225de5937e8cca7e5787d23320c1d59b7f4ff6c004f1a92' and href['bytes']==6617 and mref==h['manifest_ref']
 assert h['actor_id']==reg.AUTHOR==core.AUTHOR==AUTHOR
 refs=[href,mref,*mf['members'],*[pin(x) for x in D.iterdir() if x.is_file()]];unique={str(Path(x['path'])).casefold():dict(x,path=str(Path(x['path']))) for x in refs}
 assert not set(unique)&{str(x).casefold() for x in reg.CANON}
 guard=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 try:
  guard.acquire(list(unique.values()))
  hosts=module(OLD/'seal_review.py','AD02_own_actual_host_capture');hosts.D=D
  continuation=hosts.own_host('e187e6')
  host_ref=save('independent-actual-host-evidence.json',dict(schema='researchos.w09-adoption-independent-actual-host-evidence.v1',actor_id=ACTOR,successful_finite_continuation=continuation,
   original1112_refs=dict(raw_ref=pin(D/'original-1112.raw.jsonl'),binding_ref=pin(D/'original-1112.binding.json')),original1109_observation_ref=pin(D/'original-Root1109.observation.json'),
   original1090_refs=h['original_failure_refs'],original1112_retained_once=True,counter_reset=False,actual_product_calls=0,execution_grant=False,formal_acceptance=False))
 finally:
  closed=guard.close();seal_guard=save('seal-Source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors'];guards.append(seal_guard)
 contract=doc(h['contract_ref']['path'])
 decision=dict(schema='researchos.w09-root-adoption-independent-source-decision.v1',decision='SOURCE_ACCEPTED_FOR_ROOT_W09_ADOPTION',status='SOURCE_ACCEPTED_FOR_ROOT_ADOPTION',verdict='SOURCE_ACCEPTED_FOR_ROOT_ADOPTION',
  actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',actor_thread_id='01a1215b-7210-7613-b033-756b9d553b83',source_author_id=AUTHOR,source_handoff_ref=href,source_manifest_ref=mref,**bindings,
  created_utc=datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z'),original_contributor=h['original_contributor'],independent_non_author=True,
  source_delta='Caller AUTHOR14 and path_checked47; Core AUTHOR6 only. Complete byte inverse restores AD01; Main pair and input pins remain byte-identical.',
  prior_Task78_review_ref=pin(OLD/'Source-decision.json'),original_40check_result_ref=pin(D/'finite-delta-controls.json'),resolved_check_ref=pin(D/'finite-delta-controls.resolved.json'),
  actual_author_observation_ref=pin(D/'actual-Backup-author.observation.json'),actual_author_raw_ref=pin(D/'actual-Backup-author.raw.jsonl'),actual_host_evidence_ref=host_ref,
  Source_guard_closed_refs=guards,all_Source_guards_closed=True,retained_handles_count=0,live_Canon_held=0,actual_executed=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,programme_qualification=False,formal_case_accepted_delta=0,
  new_independent_checks_passed=40,resolved_capture_check_passed=1,original_failed_check_preserved=True,old68_reexecuted=False,author25_reexecuted=False,Task78_controls_reexecuted=False,Q_NF3_controls_reexecuted=False,
  blocking_findings=[],known_limitations=[dict(id='UNCHANGED_NF3_PEER_TIMESTAMP_EQUALITY',current_Backup_actual_Final_satisfies=True,Root_metadata_Final_ordinals=[63970,63971],actual_timestamp='2026-10-09T20:20:06.855Z',future_review_Final='Root must independently observe this actual delivery before issuing its request; future metadata timing has not been observed by this reviewer.')],
  preserved_originals=[1090,1109,1112],required_next=dict(root_request_schema=contract['root_request']['schema'],exact_request_fields=contract['root_request']['exact_fields'],
   source_author_audit='Root captures actual Backup FINAL and binds AD02 HDF SHA, replacing the old Native author audit only for this Source.',source_review_audit='Root captures this actual non-author FINAL and binds complete decision SHA with original offsets/hash/bytes.',
   authority='Root alone issues a fresh current NATIVE_SCOPES request, complete pending suffix and bounded leases, plus completed actual request toolpair; Source is no grant.',
   old1109='Retain original failed AD01 request/propose/Root hostpair. Do not rerun it or reset counters.',
   actual_stages='After Source binding Root performs actual propose/check/activate and postactivation scope audits, then finalize and unchanged NF3 prepare/run under their own gates.',formal_acceptance=False,execution_grant=False))
 assert core.validate_own_review(decision,href,mref,bindings)==ACTOR
 dref=save('Source-decision.json',decision)
 members=[pin(x) for x in sorted(D.iterdir(),key=lambda x:x.name) if x.is_file() and x.name not in ('HDF.json','MF.json')]
 mreview=save('MF.json',dict(schema='researchos.w09-root-adoption-independent-source-manifest.v1',actor_id=ACTOR,source_author_id=AUTHOR,status='SOURCE_ACCEPTED_FOR_ROOT_ADOPTION',members=members,excluded_self=['HDF.json','MF.json'],
  postseal_publication_proof='Actual published own_source-prefix proof and its closed guard are emitted after immutable HDF/MF/decision.',execution_grant=False,formal_acceptance=False))
 hreview=save('HDF.json',dict(schema='researchos.w09-root-adoption-independent-source-handoff.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=AUTHOR,status='SOURCE_ACCEPTED_FOR_ROOT_ADOPTION',manifest_ref=mreview,source_decision_ref=dref,source_handoff_ref=href,source_manifest_ref=mref,**bindings,
  prior_Task78_review_ref=pin(OLD/'Source-decision.json'),finite_delta_controls_ref=pin(D/'finite-delta-controls.json'),finite_delta_resolution_ref=pin(D/'finite-delta-controls.resolved.json'),actual_host_evidence_ref=host_ref,
  Source_guard_closed_refs=guards,all_Source_guards_closed=True,retained_handles_count=0,live_Canon_held=0,new_independent_checks_passed=40,resolved_capture_check_passed=1,old68_author25_Task78_Q_NF3_reexecuted=False,
  original1112_refs=resolved['original1112_refs'],preserved_originals=[1090,1109,1112],actual_executed=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,programme_qualification=False,formal_case_accepted_delta=0,required_next=decision['required_next']))
 tree=ast.parse(Path(h['caller_ref']['path']).read_bytes());fn=copy.deepcopy(next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='own_source'));stop=next(i for i,x in enumerate(fn.body) if isinstance(x,ast.For));fn.body=fn.body[:stop]+[ast.Return(value=ast.Constant(value=True))];fn.name='published_own_source_prefix';ast.fix_missing_locations(fn)
 env=reg.__dict__.copy();exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual AD02 published Source prefix; Root audit loops excluded>','exec'),env)
 fixture=dict(source_handoff_ref=href,source_manifest_ref=mref,source_review_handoff_ref=hreview,source_review_manifest_ref=mreview,source_review_decision_ref=dref)
 pg=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 try:
  pg.acquire([href,mref,hreview,mreview,dref,*bindings.values()]);assert env['published_own_source_prefix'](fixture,None,core) is True
  assert pin(D/'HDF.json')==hreview and pin(D/'MF.json')==mreview and pin(D/'Source-decision.json')==dref
 finally:
  pclosed=pg.close();pguard=save('published-prefix-Source-guard.closed.json',pclosed)
 assert pclosed['closed'] and pclosed['retained_handles_count']==0 and not pclosed['errors']
 proof=save('published-own-source-prefix.verified.json',dict(schema='researchos.w09-adoption-published-Source-interface-review.v1',review_refs=dict(HDF=hreview,MF=mreview,decision=dref),actual_exact_foreign_ref_objects_preserved=True,actual_published_own_source_prefix=True,
  actual_new_Backup_author_bound=True,Source_interface_fixture_only=True,Root_audit_loops_executed=False,RootScope_lease_grant_written=False,guard_ref=pguard,retained_handles_count=0,live_Canon_held=0,actual_product_calls=0,execution_grant=False,formal_acceptance=False))
 print(json.dumps(dict(status='SOURCE_ACCEPTED_FOR_ROOT_ADOPTION',decision='SOURCE_ACCEPTED_FOR_ROOT_W09_ADOPTION',review_refs=dict(HDF=hreview,MF=mreview,decision=dref),publication_proof_ref=proof,
  all_Source_guards_closed=True,retained_handles_count=0,actual_product_calls=0,execution_grant=False,formal_acceptance=False),ensure_ascii=False))
if __name__=='__main__':main()
