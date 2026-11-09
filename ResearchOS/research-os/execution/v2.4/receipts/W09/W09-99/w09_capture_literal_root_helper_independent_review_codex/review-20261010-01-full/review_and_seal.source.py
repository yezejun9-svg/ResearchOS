from pathlib import Path
import ast, copy, datetime, hashlib, json, types

R=Path(r'D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
SUPPORT=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
raw=SUPPORT.read_bytes()
assert len(raw)==4940 and hashlib.sha256(raw).hexdigest()=='567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s=types.ModuleType('capture_literal_review_support');s.__file__=str(SUPPORT)
exec(compile(raw,str(SUPPORT),'exec'),s.__dict__);s.D=D
assert not (D/'HDF.json').exists()
source_ref=s.exact_ref(S/'correct_capture_literal.source.root.py','7e0eae36f3282d00daa464910154d542e9d496bc0ba035a83e795a7098234c58',4571)
main_ref=s.exact_ref(R/'execution/v2.4/formal_profile_w09.py','1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087',71403)
old_proposal_ref=s.exact_ref(W/'w09_br8_actual_root/actual-20261010-01/capture-a7067db724ce4a34a71a01055c9e00c8/result.json','8a9e3a2915c12bd67df0768f13696e9a087704fbf72f1c5ba22cef68ff1c884f',6058)
old_proposal=json.loads(Path(old_proposal_ref['path']).read_bytes())
def absolute(ref):
 p=Path(ref['path']);p=p if p.is_absolute() else R/p
 return {'path':str(p),'sha256':ref['sha256'],'bytes':ref['bytes']}
input_refs=[source_ref,main_ref,old_proposal_ref]+[absolute(old_proposal[k]) for k in ['capture_payload_ref','payload_ref','issuance_ref','origin_payload_ref']]
checks=[]
def check(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
g=s.guard()
try:
 g.acquire(input_refs+[s.pin(SUPPORT),s.pin(Path(__file__))])
 helper_raw=g.get_buffer(source_ref['path']);main_raw=g.get_buffer(main_ref['path'])
 tree=ast.parse(helper_raw);main_tree=ast.parse(main_raw)
 literal_values=[ast.literal_eval(n.value) for n in main_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ROOT_SOURCE_AUDIT_LOG' for t in n.targets)]
 check('literal_from_one_fixed_Main_AST_assignment',len(literal_values)==1 and 'ast.literal_eval(n.value)' in helper_raw.decode() and "'1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087'" in helper_raw.decode())
 literal=literal_values[0]
 capture,index,issuance=[json.loads(g.get_buffer(input_refs[i]['path'])) for i in (3,4,5)]
 original=g.get_buffer(input_refs[6]['path']);lines=original.splitlines(keepends=True)
 check('existing_real_capture_origin_bytes_remain_original_three_LF',len(lines)==3 and [hashlib.sha256(x).hexdigest() for x in lines]==capture['original_line_sha256'])
 ns={'__name__':'source_review_pure_correct','Path':Path,'copy':copy}
 pure=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='correct')
 exec(compile(ast.Module(body=[pure],type_ignores=[]),str(source_ref['path']),'exec'),ns)
 before=copy.deepcopy(capture);changed=ns['correct'](old_proposal,capture,index,issuance,literal)
 changed_fields=[k for k in before if before[k]!=changed[k]]
 inverse=copy.deepcopy(changed);inverse['source_audit_path']=before['source_audit_path']
 check('one_literal_field_changed_complete_inverse_original_unmutated',changed_fields==['source_audit_path'] and inverse==before and capture==before and changed['source_audit_path']==literal)
 rejected=[]
 for label,value in [('already_correct',changed),('different_physical_path',dict(before,source_audit_path=str(Path(literal).parent/'unrelated.jsonl')))]:
  try:ns['correct'](old_proposal,value,index,issuance,literal)
  except AssertionError:rejected.append(label)
 check('reject_already_correct_or_unrelated_source_path',rejected==['already_correct','different_physical_path'])
 event=capture['message_id'];entry=next(x for x in index['entries'] if x['event_id']==event)
 check('original_index_and_issuance_bind_same_capture_and_origin',entry['capture_ref']==issuance['delivery_ref'] and entry['origin_ref']==issuance['origin_event_ref'])
 mock_fixed={'path':old_proposal['capture_fixed_path'],'sha256':hashlib.sha256((json.dumps(changed,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest(),'bytes':len((json.dumps(changed,ensure_ascii=False,indent=2)+'\n').encode())}
 older_entry={'event_id':'SOURCE_ONLY_NONPUBLISHED_PREFIX_FIXTURE','capture_ref':{'path':'SOURCE_ONLY','sha256':'0'*64,'bytes':0},'origin_ref':{'path':'SOURCE_ONLY','sha256':'1'*64,'bytes':0}}
 fixture_index=copy.deepcopy(index);fixture_index['entries'].insert(0,older_entry)
 main_body=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main').body
 delta_nodes=[n for n in main_body if n.lineno in (42,43,44)]
 env={'copy':copy,'index':fixture_index,'event':event,'fixed':mock_fixed,'oldentry':copy.deepcopy(entry),'issuance':copy.deepcopy(issuance)}
 exec(compile(ast.Module(body=delta_nodes,type_ignores=[]),str(source_ref['path']),'exec'),env)
 newindex,newissuance=env['newindex'],env['newissuance']
 restored_index=copy.deepcopy(newindex);next(x for x in restored_index['entries'] if x['event_id']==event)['capture_ref']=entry['capture_ref']
 restored_issuance=copy.deepcopy(newissuance);restored_issuance['delivery_ref']=issuance['delivery_ref']
 check('two_ref_bindings_inverse_and_unchanged_prior_index_prefix',restored_index==fixture_index and restored_issuance==issuance and newindex['entries'][0]==older_entry and next(x for x in newindex['entries'] if x['event_id']==event)['capture_ref']==newissuance['delivery_ref']==mock_fixed)
 text=helper_raw.decode('utf-8')
 check('Root_metadata_output_CREATE_NEW_and_no_fixed_Canon_Main_or_origin_write',"with p.open('xb')" in text and "os.fsync(f.fileno())" in text and "not out.exists()" in text and 'os.replace' not in text and 'write_bytes' not in text and "save(out/'" in text and not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any(a.name in ('subprocess','sqlite3') for a in n.names) for n in ast.walk(tree)))
 check('source_does_not_run_Main_or_reissue_actual_review_and_preserves_raw_frame_checks',"ast.parse(main_raw)" in text and "with Path(literal).open('rb')" in text and "f.readline()==line" in text and "events[1]['timestamp']==events[2]['timestamp']" in text and "events[2]['metadata']['client_authored'] is False" in text and "inverse==issuance" in text and "MAIN.read_bytes()==main_raw" in text)
 result={'schema':'researchos.w09-capture-literal-independent-source-checks.v1','checks':checks,'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],
  'source_ref':source_ref,'Main_ref':main_ref,'existing_input_proposal_ref':old_proposal_ref,'input_refs':input_refs,
  'pure_interface_used':'correct plus source AST statements42-44; main() not invoked',
  'prior_prefix_and_new_digest_fixture':'SOURCE_ONLY_IN_MEMORY_NOT_PUBLISHED_NOT_ISSUANCE_OR_ROOT_GRANT',
  'changed_capture_field':'source_audit_path','from_literal':before['source_audit_path'],'to_Main_literal':literal,
  'new_actual_Source8_result_or_Backup_delivery_created':False,'raw_log_content_not_modified':True,
  'old_capture_index_or_proposal_written':False,'actual_Main_check_executed':False,'product_calls':0}
finally:
 closed=g.close();guard_ref=s.write('source-review-guard.closed.json',closed)
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['failure'] is None and closed['errors']==[]
checks_ref=s.write('independent-source-checks.json',result)
decision_ref=s.write('review-decision.json',{
 'schema':'researchos.w09-root-capture-literal-independent-source-decision.v1','verdict':'ACCEPTED_SOURCE_ONLY',
 'decision':'SOURCE_ACCEPTED_FOR_NEW_ROOT_METADATA_CAPTURE_PUBLICATION_PAYLOAD',
 'review_author':'codex:/root/full_w09_source_review','review_author_backend':'/root/full_w09_source_review',
 'source_author':'codex:/root','independent_non_author':True,'source_ref':source_ref,'Main_ref':main_ref,
 'checks_ref':checks_ref,'guard_ref':guard_ref,'passed_new_pure_checks':len(checks),
 'execution_preconditions':['Root invokes this exact helper only with a genuinely new Source8 capture result binding a newly received real Backup delivery event. The old proposal used in finite Source checks is historical and is not authorization to republish an old event.',
  'New capture/index/issuance/result are saved under a fresh absent Root output directory. All old proposals, published bad index, origin3LF and Main remain original.',
  'The new immutable payload must receive actual independent publication verification before Root writes any fixed index/capture path.',
  'Root prospective owner time must be real and no earlier than the new issuance observed_at; any changed owner bytes require approval bound to the new exact owner hash.'],
 'scope':'One capture source_audit_path literal plus its exact capture-ref digests in index and issuance; all other structures and original event bytes preserved by full structural inverse.',
 'no_whole_live_audit_log_guard_or_hash':True,'retained_handles_count':0,'live_Canon_guard_handles':0,
 'Root_metadata_helper_main_executed':False,'Native_Go_SQL_TP_dispatcher_model_calls':0,
 'old_Source_or_product_controls_replayed':False,'execution_grant':False,'formal_acceptance':False,'STOP':True})
members=[source_ref,main_ref,checks_ref,guard_ref,decision_ref,s.pin(Path(__file__))]
manifest_ref=s.write('MF.json',{'schema':'researchos.independent-source-review-manifest.v1','members':members,'Source_only':True,'execution_grant':False,'formal_acceptance':False})
hdf_ref=s.write('HDF.json',{'schema':'researchos.w09-root-capture-literal-independent-source-review-handoff.v1','status':'ACCEPTED_SOURCE_ONLY',
 'review_author':'codex:/root/full_w09_source_review','review_author_backend':'/root/full_w09_source_review','source_author':'codex:/root','independent_non_author':True,
 'source_ref':source_ref,'Main_ref':main_ref,'manifest_ref':manifest_ref,'decision_ref':decision_ref,'checks_ref':checks_ref,'guard_ref':guard_ref,
 'passed_new_pure_checks':len(checks),'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
 'retained_handles_count':0,'live_Canon_guard_handles':0,'execution_grant':False,'formal_acceptance':False,'STOP':True})
print(json.dumps({'review_refs':[hdf_ref,manifest_ref,decision_ref],'source_ref':source_ref,'checks_ref':checks_ref,'guard_ref':guard_ref,'passed':len(checks),'retained_handles_count':0,'product_calls':0},ensure_ascii=False))
