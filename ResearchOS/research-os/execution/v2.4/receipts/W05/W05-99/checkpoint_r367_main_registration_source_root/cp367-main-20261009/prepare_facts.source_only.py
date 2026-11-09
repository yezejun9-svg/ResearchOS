import sys
sys.dont_write_bytecode=True
import copy,hashlib,json,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
N=Path(__file__).resolve().parent
def ref(p):
 p=Path(p).resolve(strict=True);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def pinned(p,sha,size):
 v=ref(p)
 if v['sha256']!=sha or v['bytes']!=size:raise ValueError('EXACT_PIN:'+str(p))
 return v
def load(v):
 if ref(v['path'])!=v:raise ValueError('CURRENT_REF')
 return json.loads(Path(v['path']).read_bytes())
def save(name,v):
 with (N/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return ref(N/name)
def module(p):
 m=types.ModuleType('source_only_cp367');m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def main():
 m=module(N/'register_cp367.source.py');cn=[{'path':str(p.resolve()),'sha256':sha,'bytes':size} for p,(sha,size) in zip(m.CANON,m.BEFORE)]
 before=[load(v) for v in cn[:2]]
 mainns=W/'main_c19_source_registry_integration_codex/mainc19-1a11f84'
 mainh=pinned(mainns/'HDF.json','ba6898a98c3bbd62eb8447938122ace9f95b6baad73b0cff9d1ebe597ed590eb',7346)
 mainmf=pinned(mainns/'MF.json','1087530d763b1f601509d568957d59a820ad6f385d01fef4d724da00caead004',6382)
 main=load(mainh);contractref=pinned(mainns/'root-calling-contract.json','a5415247a34fed0c9396f02dd7130e3109d0825539e29efcbba6c61d8d961403',9609);contract=load(contractref)
 reviewns=W/'main_c19_source_registry_independent_review_codex/review-1a11fa1'
 rh=pinned(reviewns/'HDF.json','563d7a0902ab4b02ab1515a731dfa37c8fffe40cad0c97e939a375da1fb276bd',2730)
 rm=pinned(reviewns/'MF.json','7d9f38f2e494fb20562f1e0293d9268e96e9dfc2fca55e0514ee79d6d919de5c',2491);review=load(rh)
 scope={'schema':contract['root_scope_schema'],'status':contract['root_scope_status'],'issued_by':'codex:/root','executor':'codex:/root','caller_ref':main['caller_ref'],'change_set_ref':main['change_set_ref'],'source_handoff_ref':mainh,'source_manifest_ref':mainmf,'exact_targets':contract['exact_targets'],'journal_root':contract['runtime_journal_root'],'formal_case_accepted_delta':0,'formal_dispatcher':False,'formal_acceptance':False,'producer_rerun':False,'copy_native_packet':False,'new_Go_SQL_API_model_calls':0,'checkpoint_write':False,'ownership_write':False,'step_state_write':False,'consumer_closed_ref':contract['original_consumer_closed_ref'],'source_review_handoff_ref':rh,'source_review_manifest_ref':rm,'source_review_decision_ref':review['source_decision_ref'],'component_review_handoff_ref':contract['component_review_handoff_ref'],'component_review_manifest_ref':contract['component_review_manifest_ref']}
 assert set(scope)==set(contract['scope_required_fields'])
 scope_ref=save('main-seven-target.scope-registration.root.json',scope)
 pairs=[(mainh,mainmf),(rh,rm),(contract['component_review_handoff_ref'],contract['component_review_manifest_ref']),(main['producer_actual_review_handoff_ref'],main['producer_actual_review_manifest_ref'])]
 for path,sha,size,msha,msize in [
  (B/'restored21_session_receipt_v2_source_codex/r21receipt2-1a11f5e','c82ce472df31f2634565a29374da101898044755517364f731b317c72837c11a',5047,'b8f6399f0e071d7a29407351251173551892c242c347173133d06f8d3febceb6',10025),
  (B/'restored21_session_receipt_v2_independent_review_codex/r21v2r-01a11f6b','fba6ef5db6ae2ae79e1d298c2b0eea9202f6db5f2a2aca764e967b1252e00731',3766,'b156701830ac04bacfb01753ca649914bd6fbeeedc681459bfc3fdc97f6f2441',3809),
  (B/'restored21_session_runtime_caller_source_codex/r21v2caller-20261009-01','b19c49a10fccdeb115ca1dad956bfa9d550df89b9dd28d7716599907e203a2a1',2659,'d04e059361e1f16764d93d29208c8614f0dfe16db0eeb701f68ba05ebfc014a2',2861),
  (B/'restored21_session_runtime_caller_independent_review_codex/r21callr-01a11f6b','223a0edbe263afd0aeca7aab2ecf5955b6886f44f1ea268b95116148ca16d161',4694,'998a62078ebde4975c6b0c0a2d05b8200a0e8063914dadc98e34c89a2b1b0ec1',6802),
  (B/'checkpoint_r366_v7_actual_independent_review_codex/admin-r366-01a11f5b','eaa7372ddbbea7491668c65511d551f3e60f9e693579ca4eee408a28c49e7e8f',3363,'266d5d8b246d03556dc5bffee8980b886b7a99bb508f285debf2bbc798436e6a',5328)]:
  pairs.append((pinned(path/'HDF.json',sha,size),pinned(path/'MF.json',msha,msize)))
 origin_specs=[
  (937,W/'w09_c19_consumer_v7_independent_review_codex/cv7r-01a11f6b/failure-origin.937.original-tool-io.json','42bf4caf417e6d67310c03b94c906c440c2dd1ba1b3d36e9864a4b320b425d72',1097,1,None,'Source read path omitted research-os; exact corrected review passed.'),
  (938,B/'checkpoint_r366_v7_v3_binding_independent_review_codex/review-20261009-01a11f5b/failure-origin.938.registration.json','db43410331a5675f6605a4a5d97ed94313eacee474f2cb36b05b88978b8d872c',2003,1,1,'Source review assumed uniform historical origin_key; corrected checker retained original mixed historical rows.'),
  (939,B/'restored21_session_profile_independent_review_codex/r21r-01a11f6b/r21_run.original-tool-io.json','61c9c69f27a244bde3ca5028624a69bd0bfae74fb301a72c908c6d92b18223fe',2314,1,1,'Source review first-index ordering assertion matched unrelated occurrence; corrected Source review passed.'),
  (940,B/'checkpoint_r366_v7_actual_independent_review_codex/admin-r366-01a11f5b/failure-origin.940.registration.json','4ed02b9d09fa1ee2980f6840584accb7bbe5923a1ae7567d0263d3ef180f513b',807,1,None,'Read-only glob no match; exact file later supplied, no Canon writer or Native failure.'),
  (941,B/'restored21_session_receipt_v2_source_codex/r21receipt2-1a11f5e/seal-syntax.original-tool-io.json','8072b969d9f6a2402c358555bd867848bcf8ce4716bb9f88a3be81e6b2aad60e',1820,1,1,'Source seal syntax error before execution; sealed ordinal null retained, Root assigned this same call 941 once.'),
  (942,W/'formal_adoption_mapping_readonly_codex/map-1a11f84/d6aca1.original-tool-io.json','f700151837af2539006038371ae7387b0a7f396b6993a1c58709fe322c63d501',30696,1,None,'Final read-only rg no-match produced shell1 after successful source reads.'),
  (943,W/'formal_adoption_mapping_readonly_codex/map-1a11f84/a277b9.original-tool-io.json','0e2d77038d86b66342a453dd3fec1278796ff2637e87b3baff63539b6e4fe48f',4066,1,None,'Diagnostic call-pair substring selection included locator itself; corrected exact call_id recovery succeeded.'),
  (944,W/'integration_codex/w09c19v7-root-scope-20261009/failure-origin.944.original-tool-io.root.json',None,None,1,1,'Root read-only original IO recovery used wrong transcript; corrected Root transcript recovered exact four pairs without rerun.'),
  (945,B/'restored21_session_runtime_caller_source_codex/r21v2caller-20261009-01/original-failure.945.json','4ac8ff0550fea4e430f5f6f46db3678252929420e770c8896fe76fa573da3394',1730,None,None,'Source PowerShell parser diagnostic; original forwarded only output, chunk/outer numeric envelope unretained and NULL.'),
  (946,W/'w09c19_v7_consumers_actual_independent_review_codex/consumer-review-37dedbd890c44a93975558f2851d8675/failure-origin.946.original-tool-io.json','7a55095e8aec4fd57295c30f96f01de9a2119817fba9814fa19f1d193a0a3a8d',2418,1,1,'Actual component review seal Python syntax error before any body execution; corrected seal passed without consumer rerun.'),
  (947,B/'restored21_session_runtime_caller_independent_review_codex/r21callr-01a11f6b/review-failed.original-tool-io.json','bcb9251b1a732a03a4f7fcb36c2189b5494441a06a6f9be15a4e9c3e3434bb6c',1405,1,1,'Review rejected-source count expected18 but complete predicate rejects20; corrected pure control preserved three P1 findings.')]
 diagnostics=[]
 for ordinal,path,sha,size,outer,python,description in origin_specs:
  v=pinned(path,sha,size) if sha is not None else ref(path)
  diagnostics.append({'ordinal':ordinal,'origin_ref':v,'actual_outer_exit':outer,'actual_python_exit':python,'actual_native_exit':None,'description':description,'origin_selector':'One original invocation; original IO or explicit registration links original IO.','exit_qualification':'Numeric only observed outer/enclosed explicit Python marker; product Native/model NULL. 945 has no retained numeric envelope; 941/943 sealed null ordinal is Root-assigned without mutation.'})
 actual=[main['consumer_closed_ref'],main['source21_report_ref'],pinned(W/'integration_codex/w09c19v7-producer-1a11f30/validation.closed.json','305551f1fa3c4a2bd5f04795fcff205a66038de4c16d861aa619a3a42ae09384',4271)]
 facts={'schema':'researchos.root-cp367-main-c19-registration-facts.v1','formal_acceptance':False,'canonical_refs':cn,'calling_contract_ref':contractref,'scope_ref':scope_ref,'reviews':[{'handoff_ref':h,'manifest_ref':f} for h,f in pairs],'diagnostics':diagnostics,'highest_observed_ordinal':947,'next_failure_ordinal':948,'registered_after':945,'actual_refs':actual,'work_in_progress':{'status':'ROOT_MAIN7_SOURCE_REVIEWED_PENDING_ACTUAL_ADOPTION','producer_component_qualified':True,'two_consumers_component_verified':True,'producer_run_id':'37dedbd890c44a93975558f2851d8675','Source21_Main_missing':3,'Source21_Main_drift':3,'Main_adopted':False,'formal_delta':0,'formal_current_count':0,'W09_remaining':['Main6 source + commands adoption','Real dispatcher two C19 receipts','Production W09 formal profile','A06','W09-G01','W09-G02'],'W05_A21_profile_v2_source_accepted':True,'W05_A21_runtime_caller_v1':'REQUEST_CHANGES_3P1_2P2_NO_ACTUAL','W05_A21_v2_caller_correction':'SOURCE_IN_PROGRESS_AFTER_CUTOFF','original_provider_financial_closed':False,'new_provider_trial':False,'parents_accepted':6,'required_parents':22,'required_formal':42,'source_and_review_pairs':[{'handoff_ref':h,'manifest_ref':f} for h,f in pairs],'counter_reset':False},'checkpoint_note':'CP367/OW171 register narrowly reviewed Root seven-target Main C19 source/registry adoption; Source-cut947 diagnostics appended once, old934 immutable. Both v7 component consumers qualified, Main/formal not accepted. Original provider financial closure and W05 caller qualification remain OPEN.'}
 fr=save('checkpoint.execution.facts.json',facts)
 inputs=[*cn,ref(__file__),ref(N/'register_cp367.source.py'),fr,scope_ref,contractref,*actual,*[d['origin_ref'] for d in diagnostics]]
 for h,f in pairs:
  inputs += [h,f]
  members=load(f)['members'];members=list(members.values()) if isinstance(members,dict) else members
  inputs += [{'path':str(Path(x['path']).resolve(strict=True)),'sha256':x['sha256'].removeprefix('sha256:'),'bytes':x['bytes']} for x in members]
 unique={}
 for item in inputs:
  m.read(item);k=item['path'].casefold()
  assert k not in unique or unique[k]==item
  unique[k]=item
 gp={'path':str(m.GP.resolve()),'sha256':'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85','bytes':11404}
 gm=m.module(m.GP,m.read(gp));guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
 guard.acquire(list(unique.values()))
 try:
  _,owner,worker=m.facts_scope(facts)
  c,o=m.transform(copy.deepcopy(before[0]),copy.deepcopy(before[1]),facts,fr,before[0],before[1],owner,worker,'SOURCE_PREVIEW_TIMESTAMP')
  cr=save('checkpoint.proposed.source.json',c);orr=save('ownership.proposed.source.json',o)
  proof=save('source-preview-proof.json',{'status':'PURE_TRANSFORM_OLD934_PREFIX_PRESERVED_NEW11_OWNER_WORKER_EXACT_COMPLETE_INVERSE_PASS','canonical_written':False,'Main_written':False,'scope_ref':scope_ref,'facts_ref':fr,'writer_ref':ref(N/'register_cp367.source.py'),'proposed_checkpoint_ref':cr,'proposed_ownership_ref':orr,'input_ref_count':len(unique),'new_ordinals':list(range(937,948)),'registered_after':945,'high_at_cutoff':947,'next_at_cutoff':948,'later948_pending':True,'Root_live_next_at_source_prepare':949,'formal_acceptance':False})
 finally:
  cleanup=guard.close();cleanupref=save('facts-source-guard.cleanup.actual.json',cleanup)
  assert cleanup['closed'] is True and not cleanup['errors'] and cleanup['retained_handles_count']==0
 mf=save('MF.json',{'schema':'researchos.root-cp367-main-registration-source-manifest.v1','members':[ref(N/'register_cp367.source.py'),ref(__file__),fr,scope_ref,contractref,cr,orr,proof,cleanupref]})
 hdf=save('HDF.json',{'schema':'researchos.root-cp367-main-registration-source-handoff.v1','actor_id':'codex:/root','status':'SOURCE_PREPARED_PENDING_INDEPENDENT_ADMIN_REVIEW_NO_ACTUAL','manifest_ref':mf,'facts_ref':fr,'scope_ref':scope_ref,'writer_ref':ref(N/'register_cp367.source.py'),'source_preview_ref':proof,'source_guard_cleanup_ref':cleanupref,'expected_before_revisions':[366,170],'expected_after_revisions':[367,171],'new_ordinals':list(range(937,948)),'counter_reset':False,'old934_unchanged':True,'formal_acceptance':False,'Main_adopted':False})
 print(json.dumps({'handoff_ref':hdf,'manifest_ref':mf,'facts_ref':fr,'scope_ref':scope_ref,'proof_ref':proof,'source_guard_cleanup_ref':cleanupref,'actual_Canon_Main_written':False}),flush=True)
if __name__=='__main__':main()

