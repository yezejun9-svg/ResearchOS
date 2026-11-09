from pathlib import Path
import ast,copy,datetime,hashlib,json,math,re,types
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent;N=B/'public23_to24_composition_helper_source_codex/source-20261010-01'
SUP=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
assert hashlib.sha256(SUP.read_bytes()).hexdigest()=='567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s=types.ModuleType('support');s.__file__=str(SUP);exec(compile(SUP.read_bytes(),str(SUP),'exec'),s.__dict__);s.D=D
assert not (D/'HDF.json').exists()
h_ref=s.exact_ref(N/'HDF.json','2b7b682d997ce9465b4e8a34491b707ed7194664615b45168d0aff4db4f51a1d',5216)
m_ref=s.exact_ref(N/'MF.json','99a67a8f15f6c395c352a5d46f9860e7603aa1aeddaa6760860479211dab8254',8034)
source_ref=s.exact_ref(N/'compose_main24.source.py','e2e70ce36c9bfd473bb24c5d23aa18e2e9da238cab77f5b98a26e4970854e373',26668)
contract_ref=s.exact_ref(N/'ROOT-EXECUTION-CONTRACT.md','0975a1a913c47d24eb1ce972139dcb6f3ace017410494741a6ecb90589c6eb43',4997)
handoff=json.loads(Path(h_ref['path']).read_bytes());manifest=json.loads(Path(m_ref['path']).read_bytes())
mapping=json.loads(Path(handoff['merge_map_ref']['path']).read_bytes())
def pinref(ref):
    actual=s.pin(Path(ref['path']));assert actual['sha256']==ref['sha256'] and ('bytes' not in ref or actual['bytes']==ref['bytes']);return actual
refs=[h_ref,m_ref,source_ref,contract_ref,s.pin(SUP),s.pin(Path(__file__)),s.pin(s.G),*manifest['files'],handoff['merge_map_ref']]
refs.extend(handoff[k] for k in ('request_template_ref','grant_template_ref','future_result_template_ref','new_pure_controls_ref'))
request=json.loads(Path(handoff['request_template_ref']['path']).read_bytes());refs.append(request['project_identity_ref'])
composition=json.loads(Path(mapping['composition_ref']['path']).read_bytes());refs.append(mapping['composition_ref'])
for row in mapping['files']:
    refs.append(row['expected_composed_ref'])
    if row['current_ref'] is not None:refs.extend([row['current_ref'],row['byte_edit_suggestion_ref'],row['source_ancestor_evidence']['evidence_ref']])
for layer in composition['tiers']:
    refs.extend([layer['HDF_ref'],layer['MF_ref']]);refs.extend(item['source_ref'] for item in layer['files'])
refs.extend(item['candidate_ref'] for item in composition['handoff_targets'])
refs=list({x['path']:pinref(x) for x in refs}.values());g=s.guard();checks=[];findings=[];error=None;facts={}
def raw(ref):return g.get_buffer(str(Path(ref['path'])))
def document(ref):return json.loads(raw(ref))
def record(name,ok,details=None):
    checks.append({'name':name,'passed':bool(ok),'details':details});assert ok,name
def selected(tree,names,ns):
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names];assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<SOURCE_ONLY_EXTRACTED_PURE_METADATA>','exec'),ns)
try:
    g.acquire(refs);text=raw(source_ref).decode();tree=ast.parse(text);definitions={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    h=document(h_ref);mf=document(m_ref);mm=document(h['merge_map_ref']);cm=document(mm['composition_ref']);rq=document(h['request_template_ref']);gt=document(h['grant_template_ref']);future=document(h['future_result_template_ref'])
    target_node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PATHS' for t in n.targets));targets=ast.literal_eval(target_node.value)
    record('Source_HDF_MF_and_author_exact',h['source_helper_ref']==source_ref and h['contract_ref']==contract_ref and mf['HDF_ref']==h_ref and h['author']=='codex:/root/attach_restore_independent_review' and h['prepare_executed'] is False and h['apply_executed'] is False)
    rows=mm['files'];existing=[x for x in rows if x['current_ref'] is not None];new=[x for x in rows if x['current_ref'] is None]
    record('forty_ordered_unique_targets_and_selected_native',len(targets)==len(set(targets))==len(rows)==40 and tuple(x['repo_relative_path'] for x in rows)==targets and mm['selected_native_revision']==h['selected_native_revision']=='b1599aaf259c435db5a0a5313ab0ea65')
    record('ten_current_targets_thirty_absent_additions',len(existing)==10 and len(new)==30 and all(x['action']=='APPLY_PINNED_INCREMENT' and Path(x['current_ref']['path'])==R/x['repo_relative_path'] for x in existing) and all(x['action']=='ADD_ONLY_IF_STILL_ABSENT' and not (R/x['repo_relative_path']).exists() for x in new))
    edit_shapes=[]
    for row in existing:
        ed=document(row['byte_edit_suggestion_ref']);assert ed['repo_relative_path']==row['repo_relative_path'] and ed['required_current_ref']==row['current_ref'] and ed['expected_result_ref']==row['expected_composed_ref'];edit_shapes.append({'path':row['repo_relative_path'],'actions':len(ed['edits'])})
    record('metadata_increment_and_final_Source_bindings',all(cm['proposed_final_files'][x['repo_relative_path']]['source_ref']==x['expected_composed_ref'] for x in rows),edit_shapes)
    prep=ast.get_source_segment(text,definitions['prepare']);apply=ast.get_source_segment(text,definitions['apply']);write=ast.get_source_segment(text,definitions['WriteHandle']);preflight=ast.get_source_segment(text,definitions['preflight']);edits=ast.get_source_segment(text,definitions['apply_edits'])
    record('ten_whole_archives_forty_desired_and_inverse_before_apply',"save(out/'before'/ (stem+'.raw'), originals[rel])" in prep and "save(out/'desired'/ (stem+'.raw'), desired[rel])" in prep and "automatic_rollback=False,not_an_execution_grant=True" in prep and "preflight(rows, edits)" in prep and "grant_ref=None,TargetProgram=None,build_result_ref=None,test_result_ref=None,Main_applied=False" in prep)
    record('deny_write_delete_handle_CAS_and_create_new_order',"create_file(str(path),0x80000000|0x40000000,1,None,1 if create else 3,0x80,None)" in write and apply.index('handles[rel]=WriteHandle(target(rel))')<apply.index('preflight(rows,edits,handles)')<apply.index("document(out/'intent.json'") and "handle=WriteHandle(path,create=True)" in apply and "LATE_MAIN_BASE_DRIFT:" in apply and "HANDLE_PATH_MISMATCH" in write and "HANDLE_SINGLE_LINK" in write)
    record('complete_increment_inverse_and_late_archive_gate',"need(restored == original, 'COMPLETE_BYTE_INVERSE')" in edits and "need(new == source, 'EDIT_NOT_FINAL_SOURCE')" in preflight and "'EXACT_INVERSE_ARCHIVE_BINDING'" in apply and "'OLD_ARCHIVE_DRIFT'" in apply and "'COMPLETE_INVERSE_DOCUMENT'" in apply)
    record('partial_primary_and_cleanup_preserved_no_auto_retry_rollback',"status='STOPPED_PRESERVE_PARTIAL'" in apply and "automatic_rollback=False,automatic_retry=False" in apply and "'NO_RETRY_OUTPUT_EXISTS'" in apply and "cleanup.append(dict(stage='target_handle_close'" in apply and "cleanup.append(dict(stage='source_guard_close'" in apply and "if primary or cleanup:" in apply and "return 1" in apply and not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('unlink','remove','replace') for n in ast.walk(definitions['apply'])))
    record('actual_results_and_execution_authority_templates_NULL',rq['output_directory'] is None and all(gt[k] is None for k in ('operation_id','prepared_ref','independent_source_review_ref','root_authorization_observation_ref','issued_at','expires_at')) and tuple(gt['target_paths'])==targets and all(future[k] is None for k in ('request_ref','prepared_ref','grant_ref','TargetProgram','apply_result_ref','build_result_ref','test_result_ref','independent_actual_review_ref')) and future['formal_acceptance'] is False and future['Main_applied'] is False and future['Canon_written'] is False)
    top_calls=[n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)]
    imports=[n.name for node in tree.body if isinstance(node,ast.Import) for n in node.names]
    record('no_importtime_product_or_Canon_business_write',not top_calls and all(x not in imports for x in ('subprocess','sqlite3','socket')) and tuple(x for x in targets if x.startswith('execution/'))==() and "Canon_written=False" in apply and "TargetProgram=None,build_result_ref=None,test_result_ref=None" in apply)
    # New independent counterexample: project UUID/path accepts the same result
    # with no Git baseline observation. No .git path or Main write is touched.
    identity_raw=raw(rq['project_identity_ref']);ns={'Path':Path,'REPO':R,'PROJECT':'aede0678-7308-43dc-b9f2-cfe3d90cfdfb','json':json,'math':math,'hashlib':hashlib}
    selected(tree,{'Refusal','need','sha','decode','identity','parse_stamp'},ns)
    ns['checked']=lambda reference:(Path(reference['path']),identity_raw)
    accepted_identity=ns['identity'](rq['project_identity_ref']);identity_body=ast.get_source_segment(text,definitions['identity'])
    git_absent=not any(value in text.lower() for value in ('.git','gitdir','commondir','git_baseline','git_identity','git_head'))
    record('counterexample_identity_accepts_without_Git_baseline',accepted_identity['project_id']==ns['PROJECT'] and git_absent and set(accepted_identity).isdisjoint({'git_baseline','git_identity','git_head'}),{'Source_line':150,'checks_only':['project_id','repository_root'],'Git_baseline_checked':False})
    findings.append({'priority':'P1','code':'GIT_IDENTITY_BASELINE_NOT_ENFORCED','path':source_ref['path'],'line':150,'end_line':155,'impact':'Pinned project UUID/repository_root does not verify current Git common-dir/worktree/HEAD/config identity before the forty-target mutation.','minimum_fix':'Freeze explicit current Git identity baseline and verify it before apply and under its write boundary, or require an independently reviewed frozen Root wrapper that performs the same gate and refuses direct standalone apply.'})
    # Execute only the Source grant validation statements through add_ref. The
    # prepared/request/proofs below are Source-only in-memory counterexamples,
    # never Root-issued files, scopes, grants, or product receipts.
    grant_nodes=[n for n in definitions['apply'].body if 355<=n.lineno<=363]
    grant_ns={'datetime':datetime.datetime,'timezone':datetime.timezone,'re':re,'PATHS':targets,'PROJECT':ns['PROJECT'],'need':ns['need'],'decode':ns['decode'],'parse_stamp':ns['parse_stamp']}
    fake_prepared_ref={'path':'SOURCE_ONLY_IN_MEMORY/prepared.json','sha256':'1'*64,'bytes':1}
    fake_review_ref={'path':'SOURCE_ONLY_IN_MEMORY/review.json','sha256':'2'*64,'bytes':1}
    fake_authorization_ref={'path':'SOURCE_ONLY_IN_MEMORY/Root-proof.json','sha256':'3'*64,'bytes':1}
    now=datetime.datetime.now(datetime.timezone.utc);fake_grant=dict(gt,operation_id='9'*32,prepared_ref=fake_prepared_ref,independent_source_review_ref=fake_review_ref,root_authorization_observation_ref=fake_authorization_ref,issued_at=(now-datetime.timedelta(seconds=1)).isoformat(),expires_at=(now+datetime.timedelta(minutes=5)).isoformat())
    observed_refs=[];unaccepted_proofs={'review':{'verdict':'CHANGES_REQUIRED','review_author':h['author']},'authorization':{'actor_id':'codex:/other','operation':'UNRELATED','actual_Root_toolpair':None}}
    grant_ns.update(grant_ref={'path':'SOURCE_ONLY_IN_MEMORY/grant.json','sha256':'4'*64,'bytes':1},prepared_ref=fake_prepared_ref,req=rq,refs={},checked=lambda reference:(Path(reference['path']),json.dumps(fake_grant).encode()),add_ref=lambda refs,reference:observed_refs.append(reference))
    exec(compile(ast.Module(body=grant_nodes,type_ignores=[]),'<SOURCE_ONLY_GRANT_BINDING_PREFIX_NOT_APPLY>','exec'),grant_ns)
    record('counterexample_grant_prefix_pins_unaccepted_and_unrelated_proofs',fake_review_ref in observed_refs and fake_authorization_ref in observed_refs and unaccepted_proofs['review']['verdict']=='CHANGES_REQUIRED' and unaccepted_proofs['authorization']['actor_id']!='codex:/root',{'Source_lines':[355,363],'fixture_kind':'SOURCE_ONLY_IN_MEMORY_NOT_ROOT_GRANT','proof_bodies_never_decoded_by_Source_prefix':True})
    findings.append({'priority':'P1','code':'ACTUAL_APPROVAL_AND_ROOT_AUTHORIZATION_NOT_VERIFIED','path':source_ref['path'],'line':362,'end_line':363,'impact':'Refs are pinned without checking independent accepted verdict/non-author/source binding or real Root original actor/offset/call-result and exact operation authorization. Wrong or unrelated proof contents do not fail these gates.','minimum_fix':'Validate both actual proof schemas, independent verdict/actor/source and Root original call-result/offset/operation bindings before Main mutation, or require a reviewed frozen Root wrapper as the only callable entry and bind its exact dependency closure.'})
    record('author_fourteen_successful_controls_reused_only',document(h['new_pure_controls_ref']) is not None and h['prior_successful_Source_controls_replayed']==0,{'replayed_by_this_review':0,'reused_ref':h['new_pure_controls_ref']})
    facts={'source_author':h['author'],'source_handoff_ref':h_ref,'source_manifest_ref':m_ref,'source_ref':source_ref,'contract_ref':contract_ref,'merge_map_ref':h['merge_map_ref'],'composition_ref':mm['composition_ref'],'targets':list(targets),'existing_targets':10,'new_targets':30,'source_member_count':len(mf['files']),'guard_input_count':len(refs),'Git_gate_missing':True,'actual_authority_proof_gate_missing':True,'Root_proof_future_inputs_NULL':True,'counterexamples_are_Source_only_in_memory':True,'no_source_apply_or_prepare_called':True,'no_Windows_WriteHandle_instances':True,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
except BaseException as exc:
    error=type(exc).__name__+': '+str(exc);raise
finally:
    closed=g.close();guard_ref=s.write('source-review-guard.closed.json',closed);checks_ref=s.write('independent-metadata-checks.json',{'schema':'researchos.main24-composition-independent-source-metadata-checks.v1','checks':checks,'passed':sum(x['passed'] for x in checks),'error':error,'old_author_controls_replayed':0,'prepare_apply_calls':0,'product_calls':0})
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[] and closed['failure'] is None
findings_ref=s.write('findings.json',{'schema':'researchos.main24-composition-helper-source-findings.v1','findings':findings,'required_before_Root_prepare_apply':True})
facts_ref=s.write('source-review-facts.json',facts)
decision_ref=s.write('review-decision.json',{'schema':'researchos.main24-composition-helper-independent-source-decision.v1','verdict':'CHANGES_REQUIRED','status':'NEEDS_CHANGES','review_author':'codex:/root/full_w09_source_review','review_author_backend':'/root/full_w09_source_review','source_author':h['author'],'independent_non_author':True,'source_handoff_ref':h_ref,'source_manifest_ref':m_ref,'source_ref':source_ref,'calling_contract_ref':contract_ref,'findings_ref':findings_ref,'facts_ref':facts_ref,'checks_ref':checks_ref,'guard_ref':guard_ref,'preserved_implementation':'40 ordered targets; ten full archives and held deny-write/delete handles; thirty CREATE_NEW; complete byte inverse and immutable prepared archives; partial state/primary/cleanup preserved without automatic retry/rollback.','unresolved':['GIT_IDENTITY_BASELINE_NOT_ENFORCED','ACTUAL_APPROVAL_AND_ROOT_AUTHORIZATION_NOT_VERIFIED'],'allowed_revision_boundary':'Implement the missing gates directly or through an independently reviewed frozen wrapper-only entry; preserve current forty-target CAS/inverse/partial mechanics and re-use unchanged author14 controls. Root must not use the current standalone apply before that review.','prepare_executed':False,'apply_executed':False,'actual_resource_qualification_issued':False,'execution_grant':False,'formal_acceptance':False,'all_guards_closed':True,'retained_handles_count':0,'STOP':True})
review_manifest=s.write('MF.json',{'schema':'researchos.main24-composition-helper-independent-source-review-manifest.v1','members':[decision_ref,findings_ref,facts_ref,checks_ref,guard_ref,s.pin(Path(__file__))],'input_refs':refs,'self_hash_not_embedded':True})
review_handoff=s.write('HDF.json',{'schema':'researchos.main24-composition-helper-independent-source-review-handoff.v1','status':'NEEDS_CHANGES','verdict':'CHANGES_REQUIRED','review_author':'codex:/root/full_w09_source_review','source_author':h['author'],'independent_non_author':True,'source_handoff_ref':h_ref,'source_manifest_ref':m_ref,'source_ref':source_ref,'calling_contract_ref':contract_ref,'decision_ref':decision_ref,'manifest_ref':review_manifest,'findings_ref':findings_ref,'facts_ref':facts_ref,'checks_ref':checks_ref,'guard_ref':guard_ref,'passed_new_metadata_checks':len(checks),'blockers':len(findings),'old_author_controls_replayed':0,'all_guards_closed':True,'retained_handles_count':0,'execution_grant':False,'formal_acceptance':False})
print(json.dumps({'review_refs':[review_handoff,review_manifest,decision_ref],'source_ref':source_ref,'findings_ref':findings_ref,'checks_ref':checks_ref,'guard_ref':guard_ref,'passed_new_metadata_checks':len(checks),'blockers':len(findings),'verdict':'CHANGES_REQUIRED','retained_handles_count':0,'product_calls':0,'execution_grant':False,'formal_acceptance':False},ensure_ascii=False))
