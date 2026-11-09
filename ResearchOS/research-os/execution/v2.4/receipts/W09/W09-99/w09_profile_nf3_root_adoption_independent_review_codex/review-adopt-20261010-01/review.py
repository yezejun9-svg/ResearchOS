"""Task78 finite independent Source review. Runtime branches remain closed."""
import ast,copy,hashlib,json,ntpath,types
from datetime import datetime,timezone
from pathlib import Path
D=Path(__file__).resolve().parent;W=D.parent.parent
S=W/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-01'
ROOT_LOG=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
ACTOR='codex:/root/full_w09_source_review';ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
checks=[];findings=[]
def pin(path):
 path=Path(path);raw=path.read_bytes();return dict(path=path.as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(path):return json.loads(Path(path).read_bytes())
def save(name,value):
 with (D/name).open('xb') as stream:stream.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(D/name)
def module(path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(Path(path).read_bytes(),str(path),'exec'),m.__dict__);return m
def documents(value):
 out=[]
 if type(value) is dict:
  out.append(value)
  for child in value.values():out.extend(documents(child))
 elif type(value) is list:
  for child in value:out.extend(documents(child))
 elif type(value) is str:
  try:out.extend(documents(json.loads(value)))
  except (ValueError,TypeError):
   for line in value.splitlines():
    try:out.extend(documents(json.loads(line)))
    except (ValueError,TypeError):pass
 return out
def note(name,passed,**detail):
 value=dict(name=name,passed=bool(passed),**detail);checks.append(value)
 with (D/'checks.progress.jsonl').open('ab') as stream:stream.write((json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n').encode())
def reject(name,action,code):
 try:action()
 except (ValueError,KeyError,TypeError) as exc:note(name,code in str(exc),observed=str(exc),expected=code,Source_only=True)
 else:note(name,False,observed='UNEXPECTED_ALLOW')
def key(ref):return ntpath.normcase(ntpath.normpath(ref['path'])),ref['sha256'],ref['bytes']
def normalized(ref):return dict(path=str(Path(ref['path'])),sha256=ref['sha256'],bytes=ref['bytes'])
def check_root_peer(offsets,ordinal,actor,name):
 size=ROOT_LOG.stat().st_size
 with ROOT_LOG.open('rb') as stream:
  header=stream.readline();lines=[header]
  for offset in offsets[1:]:stream.seek(offset);lines.append(stream.readline())
 first,last=[json.loads(line) for line in lines[1:]]
 assert json.loads(header)['payload']['id']==ROOT_THREAD and first['ordinal']+1==last['ordinal']==ordinal
 assert last['payload']['author']==actor.removeprefix('codex:') and last['payload']['recipient']=='/root' and last['metadata']['client_authored'] is False
 with (D/(name+'.raw.jsonl')).open('xb') as stream:stream.write(b''.join(lines))
 raw=pin(D/(name+'.raw.jsonl'))
 obs=save(name+'.observation.json',dict(schema='researchos.independent-actual-peer-observation.v1',observed_by=ACTOR,root_thread_id=ROOT_THREAD,
  source_audit_path=ROOT_LOG.as_posix(),source_prefix_size_observed=size,source_line_offsets=offsets,source_line_bytes=[len(x) for x in lines],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],
  original_capture_ref=raw,peer_actor=actor,message_id=last['payload']['id'],received_at=last['timestamp'],issued_by_Root=False,Root_witness=False,execution_grant=False,formal_acceptance=False))
 return first,last,raw,obs

def main():
 h=doc(S/'HDF.json');mf=doc(S/'MF.json');p=doc(h['input_pins_ref']['path']);pins=p['refs']
 assert pin(S/'HDF.json')['sha256']=='fae54fd911b86b8e11cb617c4fb35b22907609d69214d941728742635be45f9a' and pin(S/'HDF.json')['bytes']==5083
 assert pin(S/'MF.json')['sha256']=='868655ac82c62186414cc58ce05ed8b82d9f4acd88d5c62fe9dc9fd20e19be0b' and pin(S/'MF.json')['bytes']==9548
 reg=module(S/'register_w09_adoption.source.py','adoption_Source_readonly')
 core=module(S/'adoption_core.source.py','adoption_Source_values')
 pair=module(S/'main_pair_bytes.source.py','adoption_Source_pair_specs')
 gm=module(pins['guard']['path'],'adoption_review_source_guard')
 refs=[pin(S/'HDF.json'),pin(S/'MF.json')]+mf['members']+list(pins.values())+list(p['peer_audit_refs'].values())+[x['snapshot_ref'] for x in p['baseline'].values()]
 unique={key(ref)[0]:normalized(ref) for ref in refs}
 assert not set(unique)&{ntpath.normcase(ntpath.normpath(str(x))) for x in reg.CANON}
 guard=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 try:
  guard.acquire(list(unique.values()))
  note('full new Source MF and explicit dependency/archive pins held',True,members=len(mf['members']),held_refs=len(unique),live_Canon_held=0)
  for field in ('caller_ref','core_ref','main_pair_ref','contract_ref'):
   reg.read_ref(h[field]);note('actual package read_ref '+field,True,ref=h[field])
  contract=doc(h['contract_ref']['path'])
  note('actual Source schema and author/contract identities',h['actor_id']==contract['source_author']==core.AUTHOR==reg.AUTHOR and contract['root_thread_id']==ROOT_THREAD)
  controls=doc(h['controls_ref']['path']);note('author68 sealed evidence reused without rerun',controls['passed']==68 and controls['failed']==0,author68_reexecuted=False,Q_NF3_controls_reexecuted=False)
  for ref in h['source_guard_refs']:
   value=doc(ref['path']);note('author Source guard closed0 '+Path(ref['path']).name,value['closed'] and value['retained_handles_count']==0 and not value['errors'])
  cps=p['baseline']['checkpoint'];ows=p['baseline']['path_ownership']
  cp=doc(cps['snapshot_ref']['path']);ow=doc(ows['snapshot_ref']['path']);ss=doc(p['baseline']['step_state']['snapshot_ref']['path'])
  pending=doc(pins['baseline_pending']['path']);current=[p['baseline'][name]['current_ref'] for name in ('checkpoint','path_ownership','step_state','commands')]
  merged,stop=core.merge_pending(cp,pending,current)
  suffix=merged[len(cp['failure_counters']):]
  reconstructed=[]
  for entry in suffix:
   v=entry['original_payload'];row={k:v[k] for k in core.EXIT_FIELDS}
   row.update(ordinal=v['observed_ordinal'],origin_ref=v['immutable_origin_ref'],origin_selector=v['origin_selector'],capture_binding_ref=v['capture_binding_ref'],description=v['diagnostic'])
   if 'capture_completeness' in v:row['capture_completeness']=v['capture_completeness']
   reconstructed.append(row)
  note('all actual22 required pending fields exactly recoverable and old prefix intact',reconstructed==pending['pending'] and merged[:len(cp['failure_counters'])]==cp['failure_counters'],row_count=len(suffix),next_counter=stop,original_pending_ref=pins['baseline_pending_original'])
  mapping_keys={key(row['capture_binding_ref']) for row in pending['pending']}
  note('all actual pending standard-binding triples retained',{key(entry['original_payload']['capture_binding_ref']) for entry in suffix}==mapping_keys)
  mutations=[('bool next',{'next_original_failure_ordinal':True}),('empty rollback',{'pending':[],'next_original_failure_ordinal':cp['work_in_progress']['root_next_failure_ordinal_live']-1}),('bool cutoff',{'source_cutoff_original_failure_ordinal':True})]
  for label,changes in mutations:
   value=copy.deepcopy(pending);value.update(changes);reject('independent counter '+label,lambda value=value:core.merge_pending(cp,value,current),'COUNTER_NONDECREASE_AND_LENGTH')
  before=copy.deepcopy(cp);operation=dict(path=['work_in_progress','Source_only_independent_missing_nullable_probe'],before_exists=False,before=None,after_exists=True,after=None)
  # Use the actual operation format from the named pure value functions.
  tree=ast.parse(Path(h['core_ref']['path']).read_bytes());fn={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
  inverse_source=ast.get_source_segment(Path(h['core_ref']['path']).read_text(),fn['inverse_operations'])
  note('inverse explicitly distinguishes before_exists from nullable values',"before_exists" in inverse_source and 'reversed(' in inverse_source)
  note('nullable SS untouched by core and registrar inverse',ss.get('revision') is None and 'step_state' not in ast.get_source_segment(Path(h['core_ref']['path']).read_text(),fn['canonical_changes']),SS_archive_ref=p['baseline']['step_state']['snapshot_ref'])
  profile=Path(pins['Q_profile']['path']).read_bytes();cm39=doc(pins['CM39_archive']['path']);proposal=doc(pins['Q_commands']['path'])
  commands=reg.project_commands(profile,cm39)
  actual_time='2026-10-09T19:00:30.428Z';after=core.cm40_document(cm39,proposal,actual_time,commands)
  note('exact CM40 32commands and proposal change limited to actual issuance time',len(commands)==32 and after==dict(proposal,updated_at=actual_time),Source_only_timestamp_fixture=True)
  changed_commands=[name for name in cm39['commands'] if cm39['commands'][name]!=commands[name]]
  note('exact four declared command changes',len(changed_commands)==4,changed_commands=changed_commands)
  wrong=copy.deepcopy(proposal);wrong['commands'].pop(next(iter(wrong['commands'])))
  reject('CM40 missing command rejects',lambda:core.cm40_document(cm39,wrong,actual_time,commands),'EXACT_32_COMMAND_PROJECTION')
  fake=pin(S/'HDF.json');target_refs=[dict(fake,path=str(path)) for path in pair.TARGETS]
  pair.validate_pair_spec(target_refs,[b'profile',b'commands']);note('fixed two-target Main spec Source interface',True,Source_only=True,actual_exclusive_write=False)
  reject('Main third target forbidden',lambda:pair.validate_pair_spec(target_refs+[fake],[b'profile',b'commands']),'EXACT_TWO_EXPECTED_REFS')
  bad=copy.deepcopy(target_refs);bad[0]['bytes']=True
  reject('Main bool byte size forbidden',lambda:pair.validate_pair_spec(bad,[b'profile',b'commands']),'FIXED_MAIN_TARGET_REF')
  intent=pair.intent_document(target_refs,target_refs,target_refs);partial=pair.partial_document('Source fixture',[0],[],[])
  note('Main intent/partial preserve fixed ownership and reconciliation',intent['mandatory_share_mode']==0 and intent['complete_before_after_archives'] and intent['automatic_inverse'] is False and partial['automatic_retry'] is False and partial['requires_root_reconciliation'])
  pair_tree=ast.parse(Path(h['main_pair_ref']['path']).read_bytes());pair_fn=next(x for x in pair_tree.body if isinstance(x,ast.FunctionDef) and x.name=='replace_exact_pair')
  creates=[x for x in ast.walk(pair_fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='create']
  note('Win32 Main open uses mandatory share0/open-existing/readwrite',len(creates)==1 and ast.literal_eval(creates[0].args[2])==0 and ast.literal_eval(creates[0].args[4])==3 and isinstance(creates[0].args[1],ast.BinOp),actual_Win32_calls=0)
  source_text=Path(h['main_pair_ref']['path']).read_text()
  note('Main archives and durable intent precede first write/readback precedes commit',source_text.index("journal/'intent.json'")<source_text.index('for i,(handle,raw)')<source_text.index("'MAIN_READBACK_DRIFT'")<source_text.index("journal/'committed.while-owned.json'"))
  reg_tree=ast.parse(Path(h['caller_ref']['path']).read_bytes());reg_fn={x.name:x for x in reg_tree.body if isinstance(x,ast.FunctionDef)}
  stage=ast.get_source_segment(Path(h['caller_ref']['path']).read_text(),reg_fn['check_or_activate'])
  note('activate excludes live CP/OW guard and delegates pinned TP',"excluded=set(CANON[:2]) if mode=='activate'" in stage and "tp.update_pair(plan['before_canonical_refs'][:2]" in stage and contract['shared_canonical_transaction_ref']==pins['TP'])
  owned=ast.get_source_segment(Path(h['caller_ref']['path']).read_text(),reg_fn['apply_profile'])
  note('Main stage excludes both Main targets and compares owned before/after exact vectors',"Path(r['path']) not in set(MAIN)" in owned and 'zip(MAIN,before)' in owned and 'zip(MAIN,after)' in owned and 'CANON[:3]' in owned)
  finalize=ast.get_source_segment(Path(h['caller_ref']['path']).read_text(),reg_fn['finalize_native_requests'])
  note('Native requests need postactivation scope audit and actual Current4',"'COMPLETE_ACTIVATION_RETURN_PRECEDES_NATIVE_REQUEST'" in finalize and "'FINALIZE_CURRENT4'" in finalize and '.validate_authority(' in finalize)
  runtime_tree=ast.parse(Path(pins['NF_runtime']['path']).read_bytes());audit_fn=next(x for x in runtime_tree.body if isinstance(x,ast.FunctionDef) and x.name=='actual_audit')
  branches=[x for x in audit_fn.body if isinstance(x,ast.If)]
  peer_branch=next(x.orelse for x in branches if isinstance(x.test,ast.Compare) and ast.unparse(x.test)=='actor == ROOT_ACTOR')
  condition=next(x.value.args[0] for x in peer_branch if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='ACTUAL_PEER_DELIVERY' for a in x.value.args))
  compiled=compile(ast.Expression(condition),'<exact accepted NF3 Source peer predicate>','eval')
  first,last,author_raw,author_obs=check_root_peer([0,275272408,275272542],62876,h['actor_id'],'actual-Task75-Source-author')
  note('current actual Task75 author satisfies pinned NF3 peer predicate',eval(compiled,{'call':first,'result':last,'last':last['payload'],'host_author':h['actor_id'].removeprefix('codex:')}),observation_ref=author_obs,raw_ref=author_raw)
  note('current Task75 full Source HDF SHA actually delivered',pin(S/'HDF.json')['sha256'] in last['payload']['content'][0]['text'])
  first2,last2,platform_raw,platform_obs=check_root_peer([0,273574422,273574556],62778,ACTOR,'actual-Task76-platform-time-limit')
  observed=eval(compiled,{'call':first2,'result':last2,'last':last2['payload'],'host_author':ACTOR.removeprefix('codex:')})
  note('actual other-component 1ms peer rejection documented as known limitation',observed is False and first2['timestamp']=='2026-10-09T18:48:49.566Z' and last2['timestamp']=='2026-10-09T18:48:49.567Z',current_adoption_input_blocker=False,observation_ref=platform_obs)
  # Current review cannot pretend its future Root-received FINAL has been observed.
  limitation=dict(id='PINNED_NF3_PEER_TIMESTAMP_EQUALITY',applies_to='Actual Task76 old21 peer 62777/62778; current Task75 Source author and four pre-reviewed Q/NF3 peers satisfy the pinned helper.',
   future_own_review_Final_time='UNOBSERVED_ROOT_MUST_CHECK_AFTER_DELIVERY',minimum_if_actual_failure='New adoption Source-only finite adapter for canonical nondecreasing parsed aware timestamps; retain all actual actor/Rootthread/adjacency/client metadata/source offsets/hash/original-byte/digest gates. Do not modify accepted old NF3.')
  note('original1090 Source failure retained unchanged',doc(h['original_failure_refs'][0]['path'])['ordinal']==1090)
  if any(not x['passed'] for x in checks):raise ValueError('UNEXPECTED_INDEPENDENT_SOURCE_CHECK_FAILED')
  result_ref=save('finite-Source-checks.json',dict(schema='researchos.w09-root-adoption-independent-finite-review.v1',actor_id=ACTOR,status='ACCEPTED_SOURCE_ONLY',
   source_handoff_ref=pin(S/'HDF.json'),source_manifest_ref=pin(S/'MF.json'),passed=len(checks),failed=0,checks=checks,blocking_findings=findings,known_limitations=[limitation],
   actor_Source_author_observation_ref=author_obs,actor_Source_author_raw_ref=author_raw,platform_comparison_ref=platform_obs,
   author68_reexecuted=False,Q_NF3_previous_controls_reexecuted=False,actual_propose_check_activate_apply_TP_NF3_Go_SQL_model_calls=0,
   Source_fixture_conditions_only=True,RootScope_lease_qualification_grant_written=False,live_Canon_held=0,execution_grant=False,formal_acceptance=False))
 finally:
  closed=guard.close();guard_ref=save('independent-Source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
 print(json.dumps(dict(status='ACCEPTED_SOURCE_ONLY',passed=len(checks),failed=0,result_ref=result_ref,guard_ref=guard_ref,closed0=True,execution_grant=False,formal_acceptance=False),ensure_ascii=False))
if __name__=='__main__':main()
