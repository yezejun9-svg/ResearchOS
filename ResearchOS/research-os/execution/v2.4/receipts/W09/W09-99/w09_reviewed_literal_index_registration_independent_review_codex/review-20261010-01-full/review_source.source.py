from pathlib import Path
import ast,copy,datetime,hashlib,json,types
R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99';B=R/'execution/v2.4/receipts/W05/W05-99'
D=Path(__file__).resolve().parent;S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
SUP=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
assert hashlib.sha256(SUP.read_bytes()).hexdigest()=='567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s=types.ModuleType('support');s.__file__=str(SUP);exec(compile(SUP.read_bytes(),str(SUP),'exec'),s.__dict__);s.D=D
assert not (D/'HDF.json').exists()
SOURCE=S/'register_reviewed_literal_index.source.root.py'
CORE=W/'w09_nf6_root_registration_source_codex/register-20261010-01/adoption_core.source.py'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
RUNTIME=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-03/full_w09_runtime.source.py'
A=S/'cp397-diagnostics1250-capture-literal-repair-pending-live1251/canonical-journal/close.transaction.ca4aae8cc555446e9348454f1a5a4d18'
RUN=W/'w09_br8_actual_root/actual-20261010-01'
cp_ref=s.exact_ref(A/'0.after.proposed.json','f785c7face581a574e34d78699cc3540c5117be2a363a21b08e9c7bb7b3ec8a5',5114553)
ow_ref=s.exact_ref(A/'1.after.proposed.json','b949831cc4827ae2cadae77235188dfff0776a0c8074a57714c1445e16c32a86',295352)
old_index_ref=s.exact_ref(RUN/'literal02-fixed-publication.root/index.before.raw.json','ce0424c83c54d08e82682382be3fbdd1c856fff8c2f697b8104a5a761962d9cb',756)
index_ref=s.exact_ref(R/'execution/v2.4/root_delivery_captures/W09/W09-99/index.json','6bdb7a703934007dae8e50e368d0e41b00b4a132ba5998158255881c21ed520d',1340)
proposal_ref=s.exact_ref(RUN/'capture-7d7d176970554ad3b9cdb72bc3b1ce8a/root-corrected-publication01/result.json','04f15daf5921e4955859af90b39bde8f6283128c91da7db6713f1e5e8c433ce8',6146)
approval_ref=s.exact_ref(W/'w09_capture_literal_actual_publication_independent_review_codex/review-20261010-01-full/review-decision.json','1e71d800b2eec0599f9f38fff3d0297461f4b4adb39a06ba0f002d32d9389af1',4084)
audit_path=S/'w09.literal-publication-actual-review01.actual-audit.root.json'
audit_ref=s.exact_ref(audit_path,'1cc4e9076b85fb86555fbc629668759e80046c1ac51e0fbd2ff744840a9106be',len(audit_path.read_bytes()))
core_ref=s.exact_ref(CORE,'2c99ef66d3ee2c25302858fef715ad46096c750bd5ebff58faa95f0cdd4ead4f',len(CORE.read_bytes()))
tp_ref=s.exact_ref(TP,'094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9',len(TP.read_bytes()))
runtime_ref=s.exact_ref(RUNTIME,'1709bc96848fb52fe4ddde8591fe063576515aaabdc63d35630b1023a82ccc08',len(RUNTIME.read_bytes()))
source_ref=s.pin(SOURCE);audit=json.loads(Path(audit_ref['path']).read_bytes());index=json.loads(Path(index_ref['path']).read_bytes())
def absolute(p):
    p=Path(p);return p if p.is_absolute() else R/p
def pinned(ref):
    actual=s.pin(absolute(ref['path']));assert actual['sha256']==ref['sha256'] and ('bytes' not in ref or actual['bytes']==ref['bytes']);return actual
refs=[source_ref,cp_ref,ow_ref,old_index_ref,index_ref,proposal_ref,approval_ref,audit_ref,pinned(audit['original_capture_ref']),core_ref,tp_ref,runtime_ref,s.pin(s.G),s.pin(SUP),s.pin(Path(__file__))]
for entry in index['entries']:
    for key in ('capture_ref','origin_ref'):refs.append(pinned(entry[key]))
refs=list({x['path']:x for x in refs}.values());g=s.guard();controls=[];error=None;facts={}
def raw(ref):return g.get_buffer(str(absolute(ref['path'])))
def require(ok,code):
    if not ok:raise AssertionError(code)
def selected(raw_source,names,namespace):
    tree=ast.parse(raw_source);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<SOURCE_ONLY_PURE_FUNCTIONS>','exec'),namespace)
try:
    g.acquire(refs)
    source=raw(source_ref);cpraw=raw(cp_ref);owraw=raw(ow_ref);cp=json.loads(cpraw);ow=json.loads(owraw)
    before_index=json.loads(raw(old_index_ref));after_index=json.loads(raw(index_ref));proposal=json.loads(raw(proposal_ref));approval=json.loads(raw(approval_ref));a=json.loads(raw(audit_ref))
    assert approval['verdict']=='ACCEPTED_ACTUAL_PUBLICATION_PAYLOAD' and approval['approved_corrected_result_ref']==proposal_ref
    assert proposal['payload_ref']['sha256']==index_ref['sha256'] and proposal['payload_ref']['bytes']==index_ref['bytes'] and a['binding_sha256']==approval_ref['sha256']
    # Read only the already-issued exact audit lines. No actual_audit or Root stage is invoked.
    lines=raw(pinned(a['original_capture_ref'])).splitlines(keepends=True);rows=[json.loads(x) for x in lines]
    assert len(lines)==3 and rows[0]['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98' and rows[1]['type']=='inter_agent_communication_metadata'
    assert rows[1]['timestamp']==rows[2]['timestamp'] and rows[2]['ordinal']==rows[1]['ordinal']+1 and rows[2]['payload']['author']=='/root/full_w09_source_review' and rows[2]['payload']['recipient']=='/root' and rows[2]['metadata']['client_authored'] is False
    assert approval_ref['sha256'] in rows[2]['payload']['content'][0]['text']
    with Path(a['source_audit_path']).open('rb') as stream:
        for offset,line,digest in zip(a['source_line_offsets'],lines,a['original_line_sha256']):
            assert type(offset) is int and offset+len(line)<=a['source_prefix_size_observed'];stream.seek(offset);assert stream.read(len(line))==line and hashlib.sha256(line).hexdigest()==digest
    core_ns={'copy':copy,'require':require};selected(raw(core_ref),{'value_at','put','inverse_operations'},core_ns);core=types.SimpleNamespace(**core_ns)
    source_ns={'copy':copy};selected(source,{'transform_value'},source_ns);transform=source_ns['transform_value']
    tp_ns={'json':json};selected(raw(tp_ref),{'encoded'},tp_ns);encoded=tp_ns['encoded']
    canonical_index_path='execution/v2.4/root_delivery_captures/W09/W09-99/index.json'
    old=dict(old_index_ref,path=canonical_index_path);new=dict(index_ref,path=canonical_index_path)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    result,unchanged,ops=transform(cp,ow,old,new,core,now)
    controls.append({'name':'correct_historical_slot_succeeds_against_new_file_pin','passed':result['work_in_progress']['w09_root_delivery_capture_index_ref']==new and cp['work_in_progress']['w09_root_delivery_capture_index_ref']==old and old['sha256']!=new['sha256'],'input_kind':'IMMUTABLE_CP397_OW197_IN_MEMORY_TRANSFORM_NO_TP'})
    assert controls[-1]['passed']
    bad=copy.deepcopy(cp);bad['work_in_progress']['w09_root_delivery_capture_index_ref']=new;bad_before=copy.deepcopy(bad);rejected=False
    try:transform(bad,ow,old,new,core,now)
    except AssertionError:rejected=True
    controls.append({'name':'wrong_historical_slot_rejected_without_mutation','passed':rejected and bad==bad_before,'input_kind':'SOURCE_ONLY_IN_MEMORY_NEGATIVE'})
    assert controls[-1]['passed']
    inverse=core.inverse_operations(result,ops);expected=copy.deepcopy(cp)
    expected['work_in_progress']['w09_root_delivery_capture_index_ref']=new;expected['revision']=cp['revision']+1;expected['expected_previous_revision']=cp['revision'];expected['updated_at']=now;expected['updated_by']='codex:/root'
    exact_paths=[['work_in_progress','w09_root_delivery_capture_index_ref'],['revision'],['expected_previous_revision'],['updated_at'],['updated_by']]
    prefix_ok=after_index['entries'][:-1]==before_index['entries'] and len(after_index['entries'])==len(before_index['entries'])+1
    controls.append({'name':'old_prefix_all_counters_complete_inverse_and_OW_bytes_preserved','passed':prefix_ok and result==expected and inverse==cp and encoded(inverse)==cpraw and unchanged==ow and encoded(unchanged)==owraw and [x['path'] for x in ops]==exact_paths,'input_kind':'REUSE_CONTROL1_RESULT_IN_MEMORY_NO_TP'})
    assert controls[-1]['passed']
    text=source.decode();tpt=raw(tp_ref).decode();tree=ast.parse(source)
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');maintext=ast.get_source_segment(text,main)
    assert all(x in maintext for x in (cp_ref['sha256'],ow_ref['sha256'],old_index_ref['sha256'],index_ref['sha256'],proposal_ref['sha256'],approval_ref['sha256'],audit_ref['sha256']))
    assert "runtime.actual_audit(pin(audit),'codex:/root/full_w09_source_review',pin(pub)['sha256'])" in maintext
    assert "tp.update_pair([cp,ow],transform" in maintext and "'activate')" in maintext and "guard.acquire(refs)" in maintext and "finally:closed=guard.close()" in maintext
    assert 'for entry in after[\'entries\']' in maintext and "('capture_ref','origin_ref')" in maintext and "snapshot==[pin(V/'step_state.json'),pin(V/'commands.json')]" in maintext
    assert 'create(str(path),0x80000000|0x40000000,0,None,3,0x80,None)' in tpt and '!=expected_refs' in tpt and '"automatic_inverse":False' in tpt
    assert "cp398-literal-index-reviewed-registration" in maintext and "assert not out.exists()" in maintext
    facts={'source_ref':source_ref,'baseline_CP_archive_ref':cp_ref,'baseline_OW_archive_ref':ow_ref,'old_index_archive_ref':old_index_ref,'new_index_file_ref':index_ref,'publication_proposal_ref':proposal_ref,'publication_approval_ref':approval_ref,'publication_approval_actual_audit_ref':audit_ref,'core_ref':core_ref,'TP_ref':tp_ref,'runtime_audit_source_ref':runtime_ref,'patch_operations':ops,'input_CP_revision':cp['revision'],'candidate_CP_revision':result['revision'],'OW_raw_bytes_preserved_by_TP_encoding':True,'complete_CP_byte_inverse':True,'CP_changed_fields_only':exact_paths,'historical_index_prefix_preserved':True,'counter_reset':False,'checks_are_in_memory_only':True,'TP_called':False,'live_Canon_handles':0,'pending_Root_failures_retained_external_to_this_transform':[1251,1252],'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
except BaseException as exc:
    error=type(exc).__name__+': '+str(exc);raise
finally:
    closed=g.close();guard_ref=s.write('source-review-guard.closed.json',closed);controls_ref=s.write('independent-transform-controls.json',{'schema':'researchos.w09-index-slot-source-transform-controls.v1','controls':controls,'passed':sum(x['passed'] for x in controls),'error':error,'TP_called':False,'product_calls':0})
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[] and closed['failure'] is None
facts_ref=s.write('source-review-facts.json',facts)
decision_ref=s.write('review-decision.json',{'schema':'researchos.w09-reviewed-literal-index-registration-independent-source-decision.v1','verdict':'ACCEPTED_SOURCE_ONLY','decision':'SOURCE_ACCEPTED_FOR_ROOT_EXACT_REVIEWED_INDEX_SLOT_CAS','review_author':'codex:/root/full_w09_source_review','review_author_backend':'/root/full_w09_source_review','source_author':'codex:/root','independent_non_author':True,'source_ref':source_ref,'controls_ref':controls_ref,'facts_ref':facts_ref,'guard_ref':guard_ref,'passed_new_pure_controls':3,'historical_slot_is_data':True,'current_index_is_exact_file_pin':True,'CP_and_OW_TP_CAS_unchanged':True,'Root_execution_preconditions':['Execute only the exact reviewed Source helper; require CP397/OW197 hashes hard-pinned by Source and current index 6bdb exact bytes.','Root exclusive TP must recheck current canonical pair under share0; immutable archives used here are Source inputs, not current authority.','Preserve original1251/1252 and all existing ledger/counters; Root pending failure registration is a separate later transaction.','After actual TP verify CP398 exact five-field delta/full inverse and unchanged OW/SS/CM bytes; any partial failure preserves original state and journal, no automatic rollback.','A fresh actual Main precheck and independent prospective-owner approval remain required before SS acceptance.'],'execution_grant':False,'formal_acceptance':False,'all_guards_closed':True,'retained_handles_count':0,'STOP':True})
manifest_ref=s.write('MF.json',{'schema':'researchos.w09-index-slot-independent-source-review-manifest.v1','members':[decision_ref,facts_ref,controls_ref,guard_ref,s.pin(Path(__file__))],'input_refs':refs,'execution_grant':False,'formal_acceptance':False})
handoff_ref=s.write('HDF.json',{'schema':'researchos.w09-index-slot-independent-source-review-handoff.v1','status':'ACCEPTED_SOURCE_ONLY','review_author':'codex:/root/full_w09_source_review','source_author':'codex:/root','independent_non_author':True,'source_ref':source_ref,'decision_ref':decision_ref,'manifest_ref':manifest_ref,'controls_ref':controls_ref,'facts_ref':facts_ref,'guard_ref':guard_ref,'passed_new_pure_controls':3,'all_guards_closed':True,'retained_handles_count':0,'actual_TP_performed':False,'execution_grant':False,'formal_acceptance':False})
print(json.dumps({'review_refs':[handoff_ref,manifest_ref,decision_ref],'source_ref':source_ref,'controls_ref':controls_ref,'guard_ref':guard_ref,'passed_new_pure_controls':3,'retained_handles_count':0,'product_calls':0,'execution_grant':False,'formal_acceptance':False},ensure_ascii=False))
