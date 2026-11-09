from pathlib import Path
import json,hashlib,os,re
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;U=O.name
N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r339-'+U)
def p(v):
    z=Path(v);return z if z.is_absolute() else R/z
def ref(v,rel=False):
    z=p(v);b=z.read_bytes();return {'path':z.relative_to(R).as_posix() if rel else str(z),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def doc(v):return json.loads(p(v).read_bytes())
def save(n,v):
    with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
a=doc(O/'audit.json');su=doc(O/'supplement.json');f=doc(O/'final-checks.json');ab=doc(O/'abi-caller.json');pre=doc(O/'literal-precheck.json')
assert not a['failed_checks'] and not su['failed'] and not f['failed'] and not ab['failed']
assert len(pre['failed'])==1 and 'PROPSYS.dll' in pre['failed'][0]['name']
assert any(x['passed'] and x['check']=='PROPSYS original-case predicate superseded by physical-path equality' for x in ab['checks'])
s=doc(N/'scope_registration.json');b=doc(N/'binding.pre-review.json');q=doc(N/'root-construction.parameters.desktop58.json')
sr=ref(N/'scope_registration.json',True)
assert sr==ab['scope_ref'] and sr['sha256']=='c8f9b66b22b2fd3092bd7161f3dd30cd927bc5bc192bb6e9ebece38582db9859'
assert p(s['controller_review_path'])==O/'review.json'
before=doc(p(b['canonical_before_ref']['path']))['entries'];current=[]
for row in before:
    assert p(row['canonical_path']).read_bytes()==p(row['ref']['path']).read_bytes()
    current.append(ref(row['canonical_path'],True))
assert [doc(current[0]['path'])['revision'],doc(current[1]['path'])['revision'],len(doc(current[0]['path'])['failure_counters'])]==[338,166,635]
fresh=[s[k] for k in ('output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root')]+[str(R/'execution/v2.4/receipts/W13/W13-03/desktop58_root_terminal_closure_codex/fd6fec9e9d2a482d98203421ac21a82b')]
assert all(not os.path.lexists(p(v)) for v in fresh)
assert all(not (N/v).exists() for v in ('binding.json','prepare.started.json','prepared_refs.json','canonical-write.intent.json'))
head=(R/'.git/HEAD').read_text().strip();head=(R/'.git'/head[5:]).read_text().strip() if head.startswith('ref: ') else head
assert head==s['source_commit']
annex=N/'tool-observations.seventh-inputs-scope-caller.closed.original.json';ar=ref(annex)
assert ar['sha256']=='debad74df9a069ae525249fae2e4edb3e835df418b2c734e4c33514acfffdf2a' and ar['bytes']==39277
tool=[]
def collect(x):
    if isinstance(x,dict):
        if 'chunk_id' in x and 'output' in x:tool.append({'chunk_id':x['chunk_id'],'session_id':x.get('session_id'),'exit_code':x.get('exit_code'),'explicit_exit_markers':re.findall(r'ACTUAL_[A-Z_]*EXIT[=:]\s*(-?\d+)',x['output'])})
        for v in x.values():collect(v)
    elif isinstance(x,list):
        for v in x:collect(v)
collect(doc(annex))
assert any(x['chunk_id']=='ee4f93' and x['exit_code']==0 and '0' in x['explicit_exit_markers'] for x in tool)
assert any(x['chunk_id']=='8dcf36' and x['exit_code']==0 for x in tool)
save('final-observations.json',{'schema':'researchos.desktop58-scope7-final-readonly-observations.v1','canonical_refs':current,'head_direct_read':head,'fresh_absent':fresh,'scope_ref':sr,'root_original_tool_annex_ref':ar,'original_tool_facts':tool,'native_unobserved_is_null':True,'new_failure_origins':[ref(O/'failure-origin.17b9ae.json')]})
audits=['audit.json','supplement.json','final-checks.json','abi-caller.json','literal-precheck.json','tool-facts.json','final-observations.json']
limits={k:s[k] for k in ('node_cases','Go_top_cases','native_top_command_cap','loopback_HTTP_max','offscreen_Electron_controls','installed_visible_GUI_calls','SDK_model_external_paid_calls','process_cap','active_job_processes','image_cap','cleanup_seconds','inner_seconds','outer_seconds','builder_seconds','controller_evidence_reserve_seconds','launcher_evidence_reserve_seconds')}
report={'schema':'researchos.desktop58-whole-bound-scope-independent-report.v1','reviewer':'codex:/root/w05_merge_review','source_author':'codex:/root','non_author_of_scope_controller_gate_launcher_caller':True,'scope_ref':sr,'actual_root_request_ref':ref(N/'root-construction.parameters.desktop58.json'),'actual_root_inputs_ref':ref(N/'root-inputs.desktop58.pre-review.json'),'actual_binding_ref':ref(N/'binding.pre-review.json'),'resource_catalog_ref':s['resource_catalog_ref'],'resources':{'independently_hashed_files':23874,'independently_hashed_Main_source_files':639,'source_Go_files':559,'compiler_files':22138,'runtime_files':1303,'static_images':17,'membership':a['membership_results'],'delta':'Conhost and five static DLL dependencies added to resource/runtime catalog; only conhost is added to static process images. Unknown runtime modules still stop execution.','actual_dynamic_runtime_qualification':False},'full_projection_reconstructed':True,'Root_input_refs_checked':11,'metadata_refs_checked':8,'canonical_scope_ref_spelling':'ROOT_RELATIVE exact path/sha256/bytes retained for prepare and grant','runtime_observation_paths_spelling':'canonical ABS ordered three phases; no global normalization','current_CLI2_evidence':{'qualification_ref':s['current58_CLI2_qualification_ref'],'manifest_counts':{'qualification':19,'executor':125,'launcher':7,'aggregate_Root':169},'cases':su['cases'],'native_cases':[0,0],'CLI_expected_exits':[0,3],'does_not_qualify_Desktop':True},'Root_caller_ref':ab['caller_ref'],'caller_wholebyte_inverse_five_literals':True,'caller_budgets':ab['caller_budget_declaration'],'caller_OS_lifecycle_qualification':False,'caps':limits,'current_before':[338,166,635],'future_after':[339,167,645],'fixed_original_origins':10,'old_lease_closed':True,'formal_increment':0,'source_acceptance':False,'actual_candidate_execution':False,'actual_registration_executed':False,'checks':{'main':len(a['checks']),'CLI_and_wrapper_supplement':len(su['checks']),'final_guards':len(f['checks']),'ABI_and_caller':len(ab['checks']),'precheck_original':len(pre['checks'])},'preserved_static_false_positive':{'audit_ref':ref(O/'literal-precheck.json'),'original_failed_predicate':pre['failed'],'correction_ref':ref(O/'abi-caller.json'),'reason':'Windows PROPSYS.dll and propsys.dll resolve to the same canonical physical path and identical SHA/bytes; exact raw path-case equality was not a constructor requirement.','actual_tool_failure':False},'reused_scope6_audit_algorithms_but_scope7_actual_inputs_reread':True,'source_status_and_index':'Source closure frozen raw facts reused; Main HEAD directly read, no new native Git invoked.','authorship_disclosure':'Reviewer previously authored failed-lease CAS proposal; this review does not self-approve that proposal. Live canonical lease closure is checked as an existing input; actual scope/caller are Root-authored.','open_gates':['Root actual reviewed final binding and registration draft','Root actual CAS/seal and unique grant','Root one fresh caller execution with runtime observations/Job lifecycle proof','Fresh 169 Node plus Go3 outcomes and independent qualification','Installed visible GUI/NVDA/P02/SDK and whole-suite/formal acceptance remain open'],'audit_refs':[ref(O/x) for x in audits],'root_tool_observations_ref':ar,'requested_changes':[],'new_failure_origins':[ref(O/'failure-origin.17b9ae.json')]}
save('report.json',report)
review={'schema':'researchos.desktop58-controller-static-review.v1','reviewer':'codex:/root/w05_merge_review','source_author':'codex:/root','non_author':True,'decision':'READY_FOR_ROOT_CURRENT58_DESKTOP169_GO3_ONCE','requested_changes':[],'scope_ref':sr,'scope_sha256':sr['sha256'],'controller_sha256':s['controller_ref']['sha256'],'launcher_sha256':s['launcher_ref']['sha256'],'gate_sha256':s['authorization_verifier_ref']['sha256'],'source_commit':s['source_commit'],'expected_before':b['before'],'expected_after':b['after'],'binding_ref':ref(N/'binding.pre-review.json'),'root_inputs_ref':ref(N/'root-inputs.desktop58.pre-review.json'),'actual_root_request_ref':ref(N/'root-construction.parameters.desktop58.json'),'Root_caller_ref':ab['caller_ref'],'Root_caller_budget_declaration':ab['caller_budget_declaration'],'caller_OS_lifecycle_qualification':False,'report_ref':ref(O/'report.json'),'audit_refs':[ref(O/x) for x in audits],'root_original_tool_annex_ref':ar,'effective_all_checks_passed':True,'actual_registration_executed':False,'actual_execution':False,'execution_grant_issued':False,'source_acceptance':False,'formal_increment':0,'whole_suite_qualified':False,'readiness_boundary':'Preparation reviewed only. Root actual CAS, seal, unique grant and once-only caller remain mandatory; this review is not a grant or runtime qualification.','open_gates':report['open_gates'],'new_failure_origins':[ref(O/'failure-origin.17b9ae.json')]}
save('review.json',review)
save('handoff.json',{'schema':'researchos.independent-review-handoff.v1','reviewer':'codex:/root/w05_merge_review','decision':review['decision'],'review_ref':ref(O/'review.json'),'report_ref':ref(O/'report.json'),'scope_ref':sr,'manifest_path':str(O/'manifest.json'),'status':'STOPPED','new_failure_origins':[ref(O/'failure-origin.17b9ae.json')],'actual_candidate_execution':False,'source_acceptance':False,'formal_increment':0})
members=[ref(z) for z in sorted(O.iterdir()) if z.is_file() and z.name!='manifest.json']
save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':members,'count':len(members),'self_excluded':True})
print(json.dumps({'review_ref':ref(O/'review.json'),'manifest_ref':ref(O/'manifest.json'),'handoff_ref':ref(O/'handoff.json'),'report_ref':ref(O/'report.json'),'new_failure_count':1},ensure_ascii=False))
