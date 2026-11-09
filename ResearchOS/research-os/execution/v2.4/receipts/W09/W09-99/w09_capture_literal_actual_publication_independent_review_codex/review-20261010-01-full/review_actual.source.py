from pathlib import Path
import ast,copy,datetime,hashlib,json,types
R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
SUP=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
assert hashlib.sha256(SUP.read_bytes()).hexdigest()=='567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s=types.ModuleType('support');s.__file__=str(SUP);exec(compile(SUP.read_bytes(),str(SUP),'exec'),s.__dict__);s.D=D
assert not (D/'HDF.json').exists()
C=W/'w09_br8_actual_root/actual-20261010-01/capture-7d7d176970554ad3b9cdb72bc3b1ce8a'
F=C/'root-corrected-publication01'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
MAIN=R/'execution/v2.4/formal_profile_w09.py'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
SOURCE_REVIEW=W/'w09_capture_literal_root_helper_independent_review_codex/review-20261010-01-full/review-decision.json'
def path(ref):
    p=Path(ref['path']);return p if p.is_absolute() else R/p
def ref(ref):
    actual=s.pin(path(ref));assert actual['sha256']==ref['sha256'] and ('bytes' not in ref or actual['bytes']==ref['bytes']);return actual
before_ref=s.exact_ref(C/'result.json','50dda9dbc6e6c82a7d18fff53e0f1bd24f4f261d4a31d92f15e292d9d9ab54cb',6059)
after_ref=s.exact_ref(F/'result.json','04f15daf5921e4955859af90b39bde8f6283128c91da7db6713f1e5e8c433ce8',6146)
repair_ref=s.exact_ref(F/'repair.closed.json','0fc062aa6f224c510443890adf2ac409c9c64c56aa178db06996f3d756e511ef',1417)
main_ref=s.exact_ref(MAIN,'1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087',71403)
host_ref=s.exact_ref(S/'w09.capture-literal-actual-repair01.actual-audit.root.json','15daa5aed3fd40500c7d8770de9d1a8eafc622b1874e4e57a5ff73d4000c30e4',1098)
source_ref=s.exact_ref(S/'correct_capture_literal.source.root.py','7e0eae36f3282d00daa464910154d542e9d496bc0ba035a83e795a7098234c58',4571)
source_review_ref=s.exact_ref(SOURCE_REVIEW,'ec8ae6cfd15088ba45239e30313531a06fd7c3cbff2037630ada09f9cbf3a118',2920)
initial=json.loads(path(before_ref).read_bytes());corrected=json.loads(path(after_ref).read_bytes());host=json.loads(path(host_ref).read_bytes())
live_index_ref=s.exact_ref(R/initial['fixed_path'],'ce0424c83c54d08e82682382be3fbdd1c856fff8c2f697b8104a5a761962d9cb',756)
refs=[before_ref,after_ref,repair_ref,main_ref,host_ref,source_ref,source_review_ref,live_index_ref,ref(host['original_capture_ref']),s.pin(SUP),s.pin(Path(__file__))]
for proposal in (initial,corrected):
    for field in ('payload_ref','capture_payload_ref','issuance_ref','origin_payload_ref'):refs.append(ref(proposal[field]))
    for p,h in proposal['dependency_snapshot']['files'].items():refs.append(ref({'path':p,'sha256':h}))
for field in ('review_ref','context_ref'):refs.append(ref(json.loads(path(corrected['issuance_ref']).read_bytes())[field]))
unique={x['path']:x for x in refs};refs=list(unique.values())
g=s.guard();checks=[];error=None;facts={}
def record(name,ok,details=None):
    checks.append({'name':name,'passed':bool(ok),'details':details});assert ok,name
def raw(reference):return g.get_buffer(str(path(reference)))
def doc(reference):return json.loads(raw(reference))
def stamp(x):return datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
def bounded(binding,lines):
    offsets=binding['source_line_offsets'];digests=binding['original_line_sha256'];size=binding['source_prefix_size_observed']
    assert len(offsets)==len(lines)==len(digests)==3 and offsets==sorted(set(offsets)) and all(type(x) is int and x>=0 for x in offsets) and type(size) is int
    with Path(binding['source_audit_path']).open('rb') as stream:
        for offset,line,digest in zip(offsets,lines,digests):
            assert offset+len(line)<=size;stream.seek(offset);observed=stream.readline();assert observed==line and hashlib.sha256(observed).hexdigest()==digest
try:
    g.acquire(refs)
    before=doc(before_ref);after=doc(after_ref);repair=doc(repair_ref)
    bc=doc(before['capture_payload_ref']);ac=doc(after['capture_payload_ref']);bi=doc(before['payload_ref']);ai=doc(after['payload_ref']);bu=doc(before['issuance_ref']);au=doc(after['issuance_ref'])
    mainraw=raw(main_ref);tree=ast.parse(mainraw);literals=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ROOT_SOURCE_AUDIT_LOG' for t in n.targets)]
    record('fixed_Main_full_bytes_and_AST_literal',len(literals)==1 and hashlib.sha256(mainraw).hexdigest()==main_ref['sha256'] and len(mainraw)==main_ref['bytes'])
    literal=literals[0]
    sr=doc(source_review_ref)
    record('independent_Source_helper_review_exact_binding',sr['verdict']=='ACCEPTED_SOURCE_ONLY' and sr['source_ref']==source_ref and sr['independent_non_author'] is True)
    inverse=copy.deepcopy(after)
    for field in ('payload_ref','capture_payload_ref','issuance_ref'):inverse[field]=before[field]
    record('actual_proposal_exact_three_ref_inverse',inverse==before and after['schema']=='researchos.w09-capture-publication-proposal.v1' and after['formal_acceptance'] is False)
    inverse=copy.deepcopy(ac);inverse['source_audit_path']=bc['source_audit_path']
    record('actual_capture_exact_single_field_inverse',inverse==bc and ac['source_audit_path']==literal and bc['source_audit_path']!=literal and Path(bc['source_audit_path'])==Path(literal))
    event=ac['message_id'];be=[x for x in bi['entries'] if x['event_id']==event];ae=[x for x in ai['entries'] if x['event_id']==event]
    fixed_capture={'path':after['capture_fixed_path'],'sha256':after['capture_payload_ref']['sha256'],'bytes':after['capture_payload_ref']['bytes']}
    record('actual_index_and_issuance_exact_new_capture_SHA',len(be)==len(ae)==1 and ae[0]['capture_ref']==au['delivery_ref']==fixed_capture and be[0]['capture_ref']==bu['delivery_ref'])
    inverse=copy.deepcopy(ai);next(x for x in inverse['entries'] if x['event_id']==event)['capture_ref']=be[0]['capture_ref']
    record('actual_index_complete_inverse',inverse==bi)
    inverse=copy.deepcopy(au);inverse['delivery_ref']=bu['delivery_ref']
    record('actual_issuance_complete_inverse',inverse==bu)
    live=doc(live_index_ref)
    record('published_index_wholebytes_and_one_entry_prefix',len(live['entries'])==1 and len(ai['entries'])==2 and ai['entries'][:-1]==live['entries'] and {k:v for k,v in ai.items() if k!='entries'}=={k:v for k,v in live.items() if k!='entries'})
    expected_origin=f'execution/v2.4/root_original_events/W09/W09-99/{event}.jsonl';expected_capture=f'execution/v2.4/root_delivery_captures/W09/W09-99/{event}.json'
    record('fixed_targets_and_absence',after['fixed_path']=='execution/v2.4/root_delivery_captures/W09/W09-99/index.json' and after['origin_fixed_path']==expected_origin and after['capture_fixed_path']==expected_capture and not (R/expected_origin).exists() and not (R/expected_capture).exists())
    original=raw(after['origin_payload_ref']);lines=original.splitlines(keepends=True);rows=[json.loads(x) for x in lines]
    record('original_three_LF_full_bytes_unchanged',before['origin_payload_ref']==after['origin_payload_ref'] and original==raw(before['origin_payload_ref']) and len(lines)==3 and all(x.endswith(b'\n') for x in lines) and [hashlib.sha256(x).hexdigest() for x in lines]==ac['original_line_sha256'])
    header,meta,message=rows;payload=message['payload'];items=payload['content']
    record('actual_Root_header_backend_Final_adjacent_identity',header['type']=='session_meta' and header['payload']['id']==ROOT_THREAD and meta['type']=='inter_agent_communication_metadata' and meta['timestamp']==message['timestamp']==ac['received_at'] and type(meta['ordinal']) is int and message['ordinal']==meta['ordinal']+1 and payload['type']=='agent_message' and payload['id']==event and payload['author']==ac['sender']==au['issuer_id']=='/root/backup_regression_resources' and payload['recipient']==ac['recipient']=='/root' and message['metadata']['client_authored'] is False)
    record('actual_Final_content_and_same_review_context',len(items)==1 and items[0]['type']=='input_text' and hashlib.sha256(items[0]['text'].encode()).hexdigest()==ac['content_sha256'] and ac['context_ref']==au['context_ref'] and ac['review_ref']==au['review_ref'] and au['review_ref']['sha256'] in items[0]['text'] and au['context_ref']['sha256'] in items[0]['text'])
    bounded(ac,lines)
    record('actual_new_Backup_Final_exact_Root_source_offsets',ac['Root_thread_id']==ROOT_THREAD and stamp(ac['received_at'])<=stamp(ac['root_observed_at'])<=stamp(au['observed_at']),{'event_id':event,'source_line_offsets':ac['source_line_offsets'],'original_line_sha256':ac['original_line_sha256']})
    for range_ref in after['dependency_snapshot']['audit_ranges']:
        assert set(range_ref)=={'path','offset','bytes','sha256'} and type(range_ref['offset']) is int and type(range_ref['bytes']) is int
        with Path(range_ref['path']).open('rb') as stream:stream.seek(range_ref['offset']);data=stream.read(range_ref['bytes'])
        assert len(data)==range_ref['bytes'] and hashlib.sha256(data).hexdigest()==range_ref['sha256']
    record('Source8_complete_snapshot_unchanged_and_ranges_verified',before['dependency_snapshot']==after['dependency_snapshot'],{'immutable_files':len(after['dependency_snapshot']['files']),'typed_ranges':len(after['dependency_snapshot']['audit_ranges']),'Canon_files':0})
    h=doc(host_ref);hlines=raw(h['original_capture_ref']).splitlines(keepends=True);hrows=[json.loads(x) for x in hlines];bounded(h,hlines)
    hp=hrows[1]['payload'];hr=hrows[2]['payload'];results=[x for x in s.docs(hr['output']) if x.get('chunk_id')=='37f7cc']
    record('actual_repair_Root_hostpair_identity',len(hlines)==3 and hrows[0]['payload']['id']==ROOT_THREAD and h['actor_id']=='codex:/root' and h['Root_thread_id']==ROOT_THREAD and h['binding_sha256']==after_ref['sha256'] and hp['type']=='custom_tool_call' and hr['type']=='custom_tool_call_output' and hp['call_id']==hr['call_id'] and stamp(hrows[1]['timestamp'])<=stamp(hrows[2]['timestamp']) and len(results)==1)
    result=results[0];returned=json.loads(next(x for x in result['output'].splitlines() if x.startswith('{')))
    record('actual_repair_exit_and_return_exact_refs',result['exit_code']==0 and 'ROOT_ACTUAL_PYTHON_EXIT=0' in result['output'] and returned['result_ref']==repair['result_ref'] and returned['repair_ref']['sha256']==repair_ref['sha256'] and returned['repair_ref']['bytes']==repair_ref['bytes'] and returned['formal_acceptance'] is False,{'actual_chunk_id':'37f7cc','outer_exit':0,'Python_exit':0})
    record('actual_repair_exact_Source_and_input_argv','correct_capture_literal.source.root.py' in hp['input'] and before_ref['sha256'] in hp['input'] and '6059' in hp['input'] and 'root-corrected-publication01' in hp['input'] and '-I -S -B -X utf8' in hp['input'])
    record('repair_closed_exact_binding_and_boundary',ref(repair['original_proposal_ref'])==before_ref and ref(repair['result_ref'])==after_ref and repair['Main_ref']==main_ref and repair['from_value']==bc['source_audit_path'] and repair['to_value']==literal and repair['complete_structural_inverse'] is True and repair['original_3LF_unchanged'] is True and repair['prior_index_entries_unchanged'] is True and repair['Canon_written'] is False and repair['Native_replayed'] is False and repair['formal_review_replayed'] is False)
    record('inputs_held_no_publication_by_reviewer',not (R/expected_origin).exists() and not (R/expected_capture).exists() and raw(main_ref)==mainraw and raw(live_index_ref)==path(live_index_ref).read_bytes())
    facts={'event_id':event,'corrected_result_ref':after_ref,'actual_repair_ref':repair_ref,'actual_repair_hostpair_ref':host_ref,'fixed_capture_ref':fixed_capture,'fixed_origin_ref':{'path':expected_origin,'sha256':after['origin_payload_ref']['sha256'],'bytes':after['origin_payload_ref']['bytes']},'fixed_index_ref':{'path':after['fixed_path'],'sha256':after['payload_ref']['sha256'],'bytes':after['payload_ref']['bytes']},'expected_index_before_ref':live_index_ref,'new_target_observation':'BOTH_ABSENT','approved_publication_proposal':after,'Main_ref':main_ref,'source_ref':source_ref,'source_review_ref':source_review_ref,'guard_input_count':len(refs),'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
except BaseException as exc:
    error=type(exc).__name__+': '+str(exc)
    raise
finally:
    closed=g.close();guard_ref=s.write('publication-read-guard.closed.json',closed);checks_ref=s.write('actual-publication-checks.json',{'schema':'researchos.w09-actual-publication-checks.v1','checks':checks,'passed':sum(x['passed'] for x in checks),'error':error,'product_calls':0})
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[] and closed['failure'] is None
facts_ref=s.write('actual-publication-facts.json',facts)
decision_ref=s.write('review-decision.json',{'schema':'researchos.w09-capture-literal-actual-publication-independent-decision.v1','verdict':'ACCEPTED_ACTUAL_PUBLICATION_PAYLOAD','decision':'ROOT_METADATA_PUBLICATION_PAYLOAD_APPROVED','review_author':'codex:/root/full_w09_source_review','review_author_backend':'/root/full_w09_source_review','source_author':'codex:/root','independent_non_author':True,'approved_corrected_result_ref':after_ref,'actual_repair_ref':repair_ref,'actual_repair_hostpair_ref':host_ref,'facts_ref':facts_ref,'checks_ref':checks_ref,'guard_ref':guard_ref,'passed_checks':len(checks),'Root_publication_targets':{'CREATE_NEW_capture':facts['fixed_capture_ref'],'CREATE_NEW_origin':facts['fixed_origin_ref'],'wholebytes_CAS_index_expected':live_index_ref,'wholebytes_CAS_index_desired':facts['fixed_index_ref']},'Root_recheck_required':'Exclusive new target writes and index wholebytes CAS must recheck these exact values at publication; no modification of old entries or original three LF. New issuance is immutable input to prospective owner and independent approval; SS acceptance requires actual Main precheck.','Native_replayed':False,'formal_review_replayed':False,'Canon_written_by_reviewer':False,'execution_grant':False,'formal_acceptance':False,'all_guards_closed':True,'retained_handles_count':0,'STOP':True})
manifest_ref=s.write('MF.json',{'schema':'researchos.w09-independent-publication-review-manifest.v1','members':[facts_ref,checks_ref,guard_ref,decision_ref,s.pin(Path(__file__)),s.pin(D/'inspect.source.py'),s.pin(D/'inspect-host.source.py'),s.pin(D/'input-shapes.json'),s.pin(D/'host-shapes.json')],'input_refs':refs,'formal_acceptance':False})
handoff_ref=s.write('HDF.json',{'schema':'researchos.w09-independent-publication-review-handoff.v1','status':'ACCEPTED_ACTUAL_PUBLICATION_PAYLOAD','review_author':'codex:/root/full_w09_source_review','review_author_backend':'/root/full_w09_source_review','source_author':'codex:/root','independent_non_author':True,'approved_corrected_result_ref':after_ref,'decision_ref':decision_ref,'manifest_ref':manifest_ref,'facts_ref':facts_ref,'checks_ref':checks_ref,'guard_ref':guard_ref,'passed_checks':len(checks),'all_guards_closed':True,'retained_handles_count':0,'actual_publication_performed':False,'execution_grant':False,'formal_acceptance':False})
print(json.dumps({'review_refs':[handoff_ref,manifest_ref,decision_ref],'approved_corrected_result_ref':after_ref,'checks_ref':checks_ref,'facts_ref':facts_ref,'guard_ref':guard_ref,'passed_checks':len(checks),'retained_handles_count':0,'product_calls':0,'execution_grant':False,'formal_acceptance':False},ensure_ascii=False))
