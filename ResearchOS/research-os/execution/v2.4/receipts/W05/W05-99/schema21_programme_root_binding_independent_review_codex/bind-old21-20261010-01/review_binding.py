"""Finite read-only review of the completed Root OLD21 programme binding."""
from pathlib import Path
import ast,datetime,hashlib,json,ntpath,re,types,traceback
N=Path(__file__).resolve().parent;R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
S=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
ROOT='01a11007-5233-7ca1-b71f-9e9e5ce84c98';ACTOR='codex:/root/attach_fixture_source_review'
PYTHON='C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
REF_KEYS={'path','sha256','bytes'};checks=[]
def need(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def key(r):return ntpath.normcase(ntpath.normpath(r['path'])),r['sha256'],r['bytes']
def exact(r):
 need(type(r) is dict and set(r)==REF_KEYS and type(r['bytes']) is int and r['bytes']>=0,'EXACT_REF_SHAPE')
 p=Path(r['path']);need(p.is_absolute() and not p.is_symlink() and not p.is_junction(),'REGULAR_ABSOLUTE_REF')
 v=p.read_bytes();need(len(v)==r['bytes'] and hashlib.sha256(v).hexdigest()==r['sha256'],'EXACT_REF_BYTES');return v
def doc(r):return json.loads(exact(r))
def save(name,x):
 p=N/name
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def clean(g):
 need(g['verification']=='PASSED' and g['closed'] is True and type(g['retained_handles_count']) is int and g['retained_handles_count']==0 and g['errors']==[],'GUARD_CLOSED_ZERO')
def original(binding_ref,raw_ref,label):
 binding=doc(binding_ref);raw=exact(raw_ref);parts=[]
 need(binding['original_capture_ref']==raw_ref and binding['root_thread_id']==ROOT and binding['issued_by']=='codex:/root','ROOT_CAPTURE_IDENTITY_'+label)
 need(type(binding['source_prefix_size_observed']) is int and binding['source_prefix_size_observed']>0,'EXACT_SOURCE_PREFIX_'+label)
 offsets=binding['source_line_offsets'];sizes=binding['source_line_bytes'];digests=binding['original_line_sha256']
 need(len(offsets)==len(sizes)==len(digests)==3 and offsets[0]==0 and offsets==sorted(offsets),'THREE_ORIGINAL_LINES_'+label)
 with Path(binding['source_audit_path']).open('rb') as f:
  need(Path(binding['source_audit_path']).stat().st_size>=binding['source_prefix_size_observed'],'SOURCE_PREFIX_STILL_PRESENT_'+label)
  for off,size,digest in zip(offsets,sizes,digests):
   need(type(off) is int and type(size) is int and size>0 and 0<=off<off+size<=binding['source_prefix_size_observed'],'BOUNDED_SOURCE_OFFSET_'+label)
   f.seek(off);v=f.read(size);need(len(v)==size and hashlib.sha256(v).hexdigest()==digest and v.endswith(b'\n') and v.count(b'\n')==1,'EXACT_ORIGINAL_LF_LINE_'+label);parts.append(v)
 need(b''.join(parts)==raw and raw.count(b'\n')==3,'EXACT_FULL_THREE_LINE_CAPTURE_'+label)
 rows=[json.loads(x) for x in parts];need(rows[0]['type']=='session_meta' and rows[0]['payload']['id']==ROOT,'REAL_ROOT_HEADER_'+label)
 return rows,binding
def actual_exec(rows,chunk):
 call,result=rows[1],rows[2]
 need(call['payload']['type']=='custom_tool_call' and call['payload']['name']=='exec' and result['payload']['type']=='custom_tool_call_output' and call['payload']['call_id']==result['payload']['call_id'],'ACTUAL_TOOL_CALL_RESULT_PAIR_'+chunk)
 matches=[]
 for block in result['payload']['output']:
  t=block.get('text','')
  if not t.startswith('{'):continue
  try:x=json.loads(t)
  except ValueError:continue
  if type(x) is dict and x.get('chunk_id')==chunk:matches.append(x)
 need(len(matches)==1,'UNIQUE_ACTUAL_TOOL_RESULT_'+chunk);return matches[0]
guard=None;closed=None;error=None;result={};allrefs={}
try:
 boundref=pin(S/'old21.programme.qualification.bound.actual.root.json')
 need((boundref['sha256'],boundref['bytes'])==('8b5d6565586e51be741fa25b2f79cf41c55d0f8733c43d0f6a60f2ebca738a70',5911),'EXACT_TASK_BOUND_RECORD')
 bound=doc(boundref);payload=doc(bound['payload_ref']);issuance=doc(bound['root_issuance_binding_ref']);peer=doc(bound['independent_peer_delivery_binding_ref'])
 inputref=pin(S/'old21.programme.root-binding.observer-input.json');need((inputref['sha256'],inputref['bytes'])==('f3b605d9ee53962d73e314387fdd65ee3cee3ad63b7e34f2cddde7dc6e0f1cf4',43589),'EXACT_OBSERVER_INPUT_PIN')
 request=doc(inputref);rootguard=doc(payload['delivery_guard_ref']);proof=doc(bound['qualification_ref'])
 observerref=pin(S/'old21.programme.typed-observer.compact.root.py');need((observerref['sha256'],observerref['bytes'])==('3339e5812ecdbe7a0660456273803da16cc105e6694ac5b0b434656bc37527d3',1240),'COMPACT_OBSERVER_SOURCE_PIN')
 truncationref=pin(S/'old21.programme.initial-observer.API-truncation.root.json');truncation=doc(truncationref)
 diagnostic_binding_ref=pin(S/'original1111.actual-host.binding.root.json');diagnostic_binding=doc(diagnostic_binding_ref)
 archives=[pin(S/('historical.cp375.before-native.'+n)) for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']]
 live={key(x)[0] for x in bound['current_canonical_refs']}
 guardref=dict(path=str(B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404)
 finite=[pin(__file__),boundref,inputref,observerref,truncationref,guardref,bound['payload_ref'],bound['root_issuance_binding_ref'],issuance['original_capture_ref'],bound['independent_peer_delivery_binding_ref'],peer['original_capture_ref'],diagnostic_binding_ref,diagnostic_binding['original_capture_ref']]+archives+truncation['original_pair_refs']+request['observed_refs']
 for r in finite:
  k=key(r)[0]
  if k in live:continue
  need(k not in allrefs or key(allrefs[k])==key(r),'CONSISTENT_FINITE_SOURCE_PIN');allrefs[k]=r
 gm=types.ModuleType('root_binding_source_guard');exec(compile(exact(guardref),guardref['path'],'exec'),gm.__dict__)
 guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=256*1024*1024);guard.acquire(list(allrefs.values()))
 need(len(request['observed_refs'])==len({key(x)[0] for x in request['observed_refs']})==136,'EXACT_136_UNIQUE_REQUESTED_REFS')
 need(request['operation']=='OLD21_PROGRAMME_QUALIFICATION_BINDING' and request['peer_actor']==ACTOR and request['payload_ref']==bound['payload_ref'],'REQUEST_PAYLOAD_OPERATION_PEER')
 clean(rootguard);need(rootguard['share_mode']=='FILE_SHARE_READ_ONLY' and rootguard['failure'] is None and len(rootguard['entries'])==133,'ROOT_133_SOURCE_GUARD')
 entryrefs=[{k:x[k] for k in REF_KEYS} for x in rootguard['entries']]
 need(all(x['verified'] is True and x['final_path_match'] is True and x['closed'] is True for x in rootguard['entries']),'ALL_ROOT_SOURCE_ENTRIES_CLOSED_VERIFIED')
 need({key(x) for x in request['observed_refs']}=={key(x) for x in entryrefs+[bound['payload_ref'],bound['independent_peer_delivery_binding_ref'],payload['delivery_guard_ref']]},'REQUEST_IS_EXACT_ROOT_GUARD_PLUS_THREE_BINDINGS')
 need(payload['current_canonical_refs']==bound['current_canonical_refs'],'EXACT_HISTORICAL_CANON_VECTOR')
 for live_ref,archive in zip(bound['current_canonical_refs'],archives):need((live_ref['sha256'],live_ref['bytes'])==(archive['sha256'],archive['bytes']),'FULL_HISTORICAL_CANON_ARCHIVE_MATCH')
 need([doc(archives[i])['revision'] for i in [0,1,3]]==[375,179,40],'HISTORICAL_375_179_40_REVISIONS')
 peerrows,pb=original(bound['independent_peer_delivery_binding_ref'],peer['original_capture_ref'],'peer_FINAL')
 meta,message=peerrows[1],peerrows[2]
 need(meta['type']=='inter_agent_communication_metadata' and meta['payload']['trigger_turn'] is False and message['ordinal']==meta['ordinal']+1,'ACTUAL_ADJACENT_FINAL_METADATA')
 need(message['type']=='response_item' and message['payload']['type']=='agent_message' and message['payload']['id']==pb['message_id'] and message['payload']['author']=='/root/attach_fixture_source_review' and message['payload']['recipient']=='/root' and message['metadata']['client_authored'] is False,'BACKEND_AUTHORED_TRUE_REVIEWER_FINAL')
 ts=lambda t:datetime.datetime.fromisoformat(t.replace('Z','+00:00'))
 gap=(ts(message['timestamp'])-ts(meta['timestamp'])).total_seconds()
 need(0<=gap<=1 and gap==pb['actual_metadata_to_final_gap_seconds']==0.001 and message['timestamp']==pb['received_at'],'REAL_ONE_MILLISECOND_FINAL_GAP')
 content=message['payload']['content'];need(len(content)==1 and content[0]['type']=='input_text','ONE_COMPLETE_FINAL_CONTENT')
 prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/attach_fixture_source_review\nPayload:\n'
 need(content[0]['text'].startswith(prefix),'REAL_FINAL_DELIVERY_ENVELOPE');final=json.loads(content[0]['text'][len(prefix):])
 need(final['schema']=='researchos.old21-actual-programme-review-delivery.v1' and final['review_author']==ACTOR and final['root_thread_id']==ROOT and final['verdict']=='QUALIFIED_OLD21_BUILD_PENDING_ROOT_BINDING','EXACT_REVIEWER_FINAL_TYPE')
 need(final['review_refs']==payload['review_refs']==bound['review_refs'] and final['complete_hostpair_seal_ref']==payload['review_complete_seal_ref'],'ACTUAL_FINAL_REFS_EXACTLY_BOUND')
 need([x['sha256'] for x in final['review_refs']]==['ac73253e94fb0bf8b4980021946d2fdf6d5933296fcb2a8ee9254c425fe4f210','76222867cf25db836e2babab071012f8786af34822d81ad5055147533ff43331','efc83f5b76761f158e7254bf4d3935b407bf9d7a7b4479a70b1963d47d8d14c3','a390f4705ceb1e554bca8ce28f0cb8670041246523b837e13286941414e4cd5e'],'ORIGINAL_TASK83_FOUR_IMMUTABLE_PINS')
 need(bound['qualification_ref']==final['review_refs'][3] and final['successful_prefix_checks']==31132 and final['successful_continuation_checks']==465 and final['successful_authority_checks']==192,'REUSED_COMPLETED_REVIEW_BOUNDARY')
 rows,ib=original(bound['root_issuance_binding_ref'],issuance['original_capture_ref'],'compact_issuance');actual=actual_exec(rows,'7ba7fd')
 need(ib['operation']=='OLD21_PROGRAMME_QUALIFICATION_BINDING' and ib['original_call_id']==rows[1]['payload']['call_id'],'ISSUANCE_OPERATION_CALL_ID')
 js=rows[1]['payload']['input'];need(len(re.findall(r'tools\.exec_command\s*\(',js))==1 and len(re.findall(r'tools\.[A-Za-z_]+\s*\(',js))==1,'EXACTLY_ONE_REAL_EXEC_CALL')
 m=re.search(r'const args=\{cmd:("(?:\\.|[^"\\])*"),workdir:("(?:\\.|[^"\\])*"),max_output_tokens:(\d+)\};',js)
 need(m is not None,'STRICT_ACTUAL_EXEC_ARGUMENT_SHAPE')
 cmd=json.loads(m.group(1));cwd=json.loads(m.group(2));budget=int(m.group(3))
 expected="& '"+PYTHON+"' -I -S -B -X utf8 '"+(S/'old21.programme.typed-observer.compact.root.py').as_posix()+"' '"+(S/'old21.programme.root-binding.observer-input.json').as_posix()+"'\n$taskPythonExit=$LASTEXITCODE\nWrite-Output ('ROOT_SOURCE_PYTHON_EXIT='+$taskPythonExit)\nexit $taskPythonExit"
 need(cmd==expected and ntpath.normcase(ntpath.normpath(cwd))==ntpath.normcase(ntpath.normpath(str(R))) and budget==1800,'EXACT_FIXED_PYTHON_READONLY_OBSERVER_COMMAND')
 need(type(actual['exit_code']) is int and actual['exit_code']==0 and actual.get('session_id') is None and actual['original_token_count']==287,'ACTUAL_COMPACT_OUTER_ZERO_COMPLETE')
 lines=actual['output'].splitlines();need(len(lines)==2 and lines[1]=='ROOT_SOURCE_PYTHON_EXIT=0' and 'truncat' not in actual['output'].lower(),'COMPLETE_JSON_PLUS_EXACT_PYTHON_ZERO_MARKER')
 observed=json.loads(lines[0]);need(set(observed)=={'schema','issued_by','observer_actor','root_thread_id','operation','source','observer_input_ref','observed_ref_count','all_requested_refs_read_and_verified','payload_ref','peer_actor','formal_acceptance','parent_acceptance','execution_grant'},'EXACT_TYPED_COMPACT_RESULT_FIELDS')
 need(observed['schema']=='researchos.root-old21-programme-compact-capture-result.v1' and observed['issued_by']==observed['observer_actor']=='codex:/root' and observed['root_thread_id']==ROOT and observed['source']=='tools.exec_command','ACTUAL_ROOT_OBSERVER_IDENTITY')
 need(observed['operation']==request['operation'] and observed['observer_input_ref']==inputref and observed['payload_ref']==bound['payload_ref'] and observed['peer_actor']==ACTOR,'COMPACT_RESULT_EXACT_REQUEST_AND_PAYLOAD')
 need(type(observed['observed_ref_count']) is int and observed['observed_ref_count']==136 and observed['all_requested_refs_read_and_verified'] is True,'TYPED_136_ALL_REQUESTED_VERIFIED')
 source=exact(observerref).decode();tree=ast.parse(source)
 need(inputref['sha256'] in source and str(inputref['bytes']) in source and "request['observed_refs']" in source and "hashlib.sha256(data).hexdigest()==ref['sha256']" in source,'SOURCE_OBSERVER_BINDS_AND_READS_FINITE_REQUEST')
 need(not any(isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id in {'exec','eval','compile','__import__'}) or (isinstance(n.func,ast.Attribute) and n.func.attr in {'write_bytes','write_text','unlink','mkdir','run','Popen','system'})) for n in ast.walk(tree)),'SOURCE_OBSERVER_HAS_NO_WRITE_OR_PRODUCT_LAUNCH')
 need(ts(message['timestamp'])<ts(payload['created_utc'])<ts(rows[1]['timestamp'])<ts(rows[2]['timestamp'])<ts(bound['created_utc']),'TRUE_FINAL_PAYLOAD_OBSERVATION_BINDING_CAUSAL_ORDER')
 need(bound['schema']=='researchos.root-old21-programme-qualification.v1' and bound['status']=='QUALIFIED_OLD21_BUILD' and bound['issued_by']==bound['build_executor']=='codex:/root' and bound['root_thread_id']==ROOT and bound['review_author']==ACTOR,'ROOT_BOUND_PROGRAMME_IDENTITY')
 need(bound['source_author']==proof['source_author']=='codex:/root/native_temp_independent_review' and bound['caller_source_author']==proof['caller_source_author']=='codex:/root/backup_regression_resources' and bound['independent_non_author'] is True,'NONAUTHOR_SOURCE_AND_CALLER_IDENTITIES')
 need(bound['program_refs']==payload['program_refs']==proof['program_refs'] and bound['provenance_ref']==proof['provenance_ref'],'EXACT_TWO_PROGRAMMES_AND_BUILD_PROVENANCE')
 need(bound['source_commit']==proof['source_commit']=='f6e4a0ed54d697c7214a75743cd1b83dc3685ddb' and bound['source_tree']==proof['source_tree']=='9696c3a456a4786cbb5518c75ead66e6d8120a83','EXACT_GENUINE_ORIGINAL_COMMIT_TREE')
 need(type(bound['source_schema_version']) is int and bound['source_schema_version']==proof['source_schema_version']==21 and bound['database_schema_observation'] is None,'SOURCE21_WITHOUT_DATABASE_CLAIM')
 need(bound['actual_Go_primary_exits']==proof['actual_Go_primary_exits']==[0]*9 and all(type(x) is int for x in bound['actual_Go_primary_exits']) and bound['all_owned_jobs_idle_and_closed'] is True,'REUSED_NINE_GO_ACTUALS_NO_RERUN')
 for obj in [bound,payload,observed,final]:need(all(obj[k] is False for k in ['formal_acceptance','parent_acceptance','execution_grant']),'NO_FORMAL_PARENT_OR_EXECUTION_AUTHORITY')
 need(bound['programme_qualification'] is True and type(bound['formal_case_accepted_delta']) is int and bound['formal_case_accepted_delta']==0 and bound['public_bootstrap_executed'] is bound['backup_restore_executed'] is False and bound['formal_old21_case']==bound['full20to24']=='OPEN','PROGRAMME_ONLY_QUALIFICATION_BOUNDARY')
 need(bound['original_diagnostic_ordinals']==final['original_diagnostic_ordinals']==[1101,1102,1108] and bound['original_API_process_stdout_truncated'] is True and bound['original_process_stdout_complete'] is bound['original_stdout_reconstructed'] is False,'ORIGINAL_BUILD_LIMITATIONS_AND_DIAGNOSTICS_PRESERVED')
 trrows,trbind=original(truncation['original_pair_refs'][1],truncation['original_pair_refs'][0],'initial_truncated_observer');old=actual_exec(trrows,'ce7571')
 need(old['exit_code']==0 and 'truncat' in old['output'].lower() and truncation['original_API_response_truncated'] is True and truncation['original_stdout_reconstructed'] is False and truncation['original_full_process_stdout_asserted'] is False,'INITIAL_OBSERVER_TRUNCATION_RETAINED')
 need(truncation['compact_completed_observer_binding_ref']==bound['root_issuance_binding_ref'] and truncation['Go_or_Native_rerun'] is False,'COMPACT_REOBSERVATION_NOT_PRODUCT_RERUN')
 drows,db=original(diagnostic_binding_ref,diagnostic_binding['original_capture_ref'],'original1111');oldfailure=actual_exec(drows,'0f1ac2')
 need(oldfailure['exit_code']==1 and 'ROOT_SOURCE_PYTHON_EXIT=1' in oldfailure['output'],'ORIGINAL_1111_OUTER_PYTHON_ONE_PRESERVED')
 result=dict(verdict='ROOT_PROGRAMME_BINDING_VERIFIED',bound_qualification_ref=boundref,prior_programme_review_refs=bound['review_refs'],Root_issuance_binding_ref=bound['root_issuance_binding_ref'],actual_final_binding_ref=bound['independent_peer_delivery_binding_ref'],observer_input_ref=inputref,observer_source_ref=observerref,original_requested_refs=136,Root_source_guard_entries=133,metadata_to_actual_FINAL_gap_seconds=gap,actual_outer_exit=0,actual_python_exit=0,archive_refs=archives,historical_canonical_revisions=[375,179,40],initial_truncation_record_ref=truncationref,original1111_binding_ref=diagnostic_binding_ref,source_commit=bound['source_commit'],source_tree=bound['source_tree'],program_refs=bound['program_refs'],provenance_ref=bound['provenance_ref'],reused_successful_checks=dict(prefix=31132,continuation=465,authority=192),previous_controls_rerun=False,new_product_runs=0,new_Go_runs=0,new_Native_runs=0,new_SQL_runs=0,new_model_requests=0,live_canonical_read_or_held=False,Canon_written=False,formal_acceptance=False,parent_acceptance=False,execution_grant=False)
except BaseException as e:error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
finally:
 if guard is not None:closed=guard.close()
gr=save('review-Source-guard.closed.json',closed)
if closed is not None:clean(closed)
report=save('review-checks.json',dict(status='ROOT_PROGRAMME_BINDING_VERIFIED' if error is None else 'CHANGES_REQUIRED',check_count=len(checks),checks=checks,error=error,result=result,guard_ref=gr,held_ref_count=len(allrefs),held_ref_manifest=list(allrefs.values()),formal_acceptance=False,parent_acceptance=False,execution_grant=False))
print(json.dumps(dict(report_ref=report,guard_ref=gr,check_count=len(checks),held_ref_count=len(allrefs),error=error),ensure_ascii=False),flush=True)
print('ROOT_SOURCE_PYTHON_EXIT='+str(1 if error else 0),flush=True);raise SystemExit(1 if error else 0)
