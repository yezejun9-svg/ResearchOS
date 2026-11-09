import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (N/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/n)
inputs=json.loads((N/'source-inputs.json').read_bytes());source=N/'w09_evidence_closure.v7.proposed.py';provenance=json.loads((N/'source-provenance.json').read_bytes())
gp=Path(inputs['guard_ref']['path']);assert pin(gp)==inputs['guard_ref']
gm=types.ModuleType('v7_control_read_guard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(gp.read_bytes(),str(gp),'exec'),gm.__dict__)
refs=inputs['refs']+[pin(source),pin(__file__),pin(N/'source-inputs.json'),pin(N/'source-provenance.json')]
refs=list({v['path']:v for v in refs}.values());guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
checks=[]
def check(name,ok):
 checks.append(dict(name=name,passed=bool(ok)));assert ok,name
def reject(name,func,kind=ValueError,code=None):
 error=None
 try:func()
 except kind as exc:error=exc
 check(name,error is not None and (code is None or str(error)==code))
try:
 guard.acquire(refs)
 raw=guard.get_buffer(str(source));tree=ast.parse(raw);oldraw=guard.get_buffer(inputs['original_source_ref']['path']);oldtree=ast.parse(oldraw)
 nodes={v.name:v for v in tree.body if isinstance(v,ast.FunctionDef)}
 namespace={'json':json}
 exec(compile(ast.Module(body=[nodes['require'],nodes['_go_assertions']],type_ignores=[]),'<v7-pure-parser>', 'exec'),namespace)
 parse=namespace['_go_assertions']
 events=[json.loads(line) for line in guard.get_buffer(inputs['actual_stdout_ref']['path']).decode('utf-8').splitlines()]
 report=json.loads(guard.get_buffer(inputs['actual_report_ref']['path']));selected=report['selected_tests'];stdout_ref=report['raw_evidence_references'][0]
 actual=parse(events,selected,stdout_ref)
 check('actual_old_JSONL_all_five_records_exact_report',actual==report['assertion_results'] and len(actual)==5)
 check('actual_C19_05_spans_events22_23',len(events[22]['Output'])==1018 and not events[22]['Output'].endswith('\n') and events[23]['Output'].endswith('\n') and events[22]['Package']==events[23]['Package'] and events[22]['Test']==events[23]['Test'])
 check('actual_C19_05_exact_report_record',actual[-1]==report['assertion_results'][-1] and actual[-1]['assertion_id']=='C19-05')
 baseline='def old_parser(events, selected, refs):\n'+provenance['old_parser_block']+'    return assertions\n'
 exec(compile(baseline,'<v6-old-pure-parser>','exec'),namespace)
 reject('baseline_v6_known_P1_reproduced_in_pure_parser_only',lambda:namespace['old_parser'](events,selected,[stdout_ref]),json.JSONDecodeError)
 # Exercise the exact unchanged roster and strict report replay statements from verify_native.
 native=nodes['verify_native'];event_assignment=next(i for i,n in enumerate(native.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='events' for t in n.targets))
 lock_assignment=next(i for i,n in enumerate(native.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='locked_path' for t in n.targets))
 wrapper=ast.parse('def verify_replay_prefix(events, selected, expected, report, refs, run_id):\n    pass\n').body[0]
 wrapper.body=copy.deepcopy(native.body[event_assignment+1:lock_assignment])+[ast.Return(value=ast.Name(id='assertions',ctx=ast.Load()))]
 ast.fix_missing_locations(wrapper);exec(compile(ast.Module(body=[wrapper],type_ignores=[]),'<exact-native-replay-prefix>','exec'),namespace)
 def replay(es=events,rp=report):return namespace['verify_replay_prefix'](es,selected,report['assertion_ids'],rp,[stdout_ref,report['raw_evidence_references'][1]],report['run_id'])
 check('actual_exact_verify_native_replay_prefix_PASS',replay()==report['assertion_results'])
 altered=copy.deepcopy(report);altered['assertion_results'][0]['status']='FAIL';reject('strict_report_value_difference_rejected',lambda:replay(rp=altered),code='STDOUT_ASSERTION_REPLAY_MISMATCH')
 altered=copy.deepcopy(report);altered['assertion_results'].reverse();reject('strict_report_order_difference_rejected',lambda:replay(rp=altered),code='STDOUT_ASSERTION_REPLAY_MISMATCH')
 for action in ('fail','skip'):
  altered=copy.deepcopy(events)+[dict(Action=action,Package='p',Test=selected[0])]
  reject('existing_roster_reject_'+action,lambda es=altered:replay(es=es),code='GO_TEST_ROSTER_NOT_PASS')
 altered=copy.deepcopy(events)+[dict(Action='pass',Package='p',Test='ForeignTest')];reject('existing_foreign_test_rejected',lambda:replay(es=altered),code='FOREIGN_GO_TEST')
 altered=copy.deepcopy(events);altered.append(copy.deepcopy(events[10]));reject('duplicate_actual_assertion_rejected',lambda:replay(es=altered),code='STDOUT_ASSERTION_REPLAY_MISMATCH')
 line=events[22]['Output']+events[23]['Output']
 cuts=sorted({0,1,7,12,13,14,15,31,1017,1018,1019,len(line)-2,len(line)-1,len(line)})
 for cut in cuts:
  es=copy.deepcopy(events[:22])+[dict(events[22],Output=line[:cut]),dict(events[23],Output=line[cut:])]+copy.deepcopy(events[24:])
  check('real_C19_05_cut_'+str(cut),parse(es,selected,stdout_ref)==actual)
 es=copy.deepcopy(events[:22])+[dict(events[22],Output=character) for character in line]+copy.deepcopy(events[24:])
 check('real_C19_05_one_character_fragments',parse(es,selected,stdout_ref)==actual)
 def item(test,aid,text='plain'):
  return dict(assertion_id=aid,test_name=test,status='PASS',run_id='SYNTHETIC',evidence=dict(text=text))
 def encoded(value):return 'W09_ASSERTION '+json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n'
 def event(output,test='A',package='pkg'):return dict(Action='output',Package=package,Test=test,Output=output)
 def expected(value):return dict(value,raw_evidence_reference='SYNTHETIC_RAW')
 a=item('A','synthetic-A','汉字🙂\u2028\u0085 embedded\nnewline');b=item('B','synthetic-B');la,lb=encoded(a),encoded(b)
 check('Unicode_and_JSON_escaped_newline_preserved',parse([event(la)],['A'],'SYNTHETIC_RAW')==[expected(a)])
 check('multi_line_output_with_logs_blank_lines',parse([event('log\n\n'+la+la)],['A'],'SYNTHETIC_RAW')==[expected(a),expected(a)])
 check('same_test_CRLF_line_supported',parse([event(la[:-1]+'\r'),event('\n')],['A'],'SYNTHETIC_RAW')==[expected(a)])
 check('empty_and_missing_Output_supported',parse([event(''),dict(Action='pass',Package='pkg',Test='A'),event(la),event('')],['A'],'SYNTHETIC_RAW')==[expected(a)])
 check('interleaved_tests_keep_owner_and_completion_order',parse([event(la[:17]),event(lb,test='B'),event(la[17:])],['A','B'],'SYNTHETIC_RAW')==[expected(b),expected(a)])
 other=item('A','synthetic-other-package');lo=encoded(other)
 check('interleaved_packages_same_test_kept_separate',parse([event(la[:19],package='one'),event(lo,package='two'),event(la[19:],package='one')],['A'],'SYNTHETIC_RAW')==[expected(other),expected(a)])
 check('package_level_log_stream_does_not_join_test_stream',parse([event('package ',test=None),event(la),event('log\n',test=None)],['A'],'SYNTHETIC_RAW')==[expected(a)])
 check('multi_line_and_following_partial_same_owner',parse([event(la+la[:13]),event(la[13:])],['A'],'SYNTHETIC_RAW')==[expected(a),expected(a)])
 for label,outputs in [('partial_marker',['W09_AS']),('partial_json',['W09_ASSERTION {']),('complete_json_without_terminator',[la[:-1]]),('ordinary_log_tail',['unterminated log']),('complete_then_dangling',[la+'W09_ASSERTION '])]:
  reject('reject_dangling_'+label,lambda values=outputs:parse([event(s) for s in values],['A'],'SYNTHETIC_RAW'),code='GO_OUTPUT_DANGLING_FRAGMENT')
 reject('reject_malformed_JSON',lambda:parse([event('W09_ASSERTION {bad}\n')],['A'],'SYNTHETIC_RAW'),json.JSONDecodeError)
 reject('reject_truncated_JSON_with_newline',lambda:parse([event('W09_ASSERTION {"a":\n')],['A'],'SYNTHETIC_RAW'),json.JSONDecodeError)
 reject('reject_nonobject_JSON',lambda:parse([event('W09_ASSERTION []\n')],['A'],'SYNTHETIC_RAW'),code='ASSERTION_STDOUT_OWNER_MISMATCH')
 reject('reject_Test_owner_mismatch',lambda:parse([event(lb)],['A','B'],'SYNTHETIC_RAW'),code='ASSERTION_STDOUT_OWNER_MISMATCH')
 reject('reject_unselected_Test',lambda:parse([event(lb,test='B')],['A'],'SYNTHETIC_RAW'),code='ASSERTION_STDOUT_OWNER_MISMATCH')
 reject('reject_cross_Test_fragment_join',lambda:parse([event(la[:17]),event(la[17:],test='B')],['A','B'],'SYNTHETIC_RAW'),code='GO_OUTPUT_DANGLING_FRAGMENT')
 reject('reject_cross_Package_fragment_join',lambda:parse([event(la[:17],package='one'),event(la[17:],package='two')],['A'],'SYNTHETIC_RAW'),code='GO_OUTPUT_DANGLING_FRAGMENT')
 reject('reject_nontext_Output',lambda:parse([event(None)],['A'],'SYNTHETIC_RAW'),code='GO_OUTPUT_NOT_TEXT')
 reject('reject_unhashable_Package_owner',lambda:parse([event(la,package=[])],['A'],'SYNTHETIC_RAW'),code='GO_OUTPUT_OWNER_NOT_TEXT')
 reject('reject_unhashable_Test_owner',lambda:parse([event(la,test=[])],['A'],'SYNTHETIC_RAW'),code='GO_OUTPUT_OWNER_NOT_TEXT')
 inverse=raw.decode().replace(provenance['added_helper'],'',1).replace(provenance['new_parser_call'],provenance['old_parser_block'],1)
 check('full_v6_byte_inverse',inverse.encode()==oldraw)
 check('all_nonparser_AST_exact',ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(oldtree,include_attributes=False))
 for name,node in {n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)}.items():
  if name!='verify_native':check('unchanged_function_'+name,ast.dump(node,include_attributes=False)==ast.dump(nodes[name],include_attributes=False))
 check('only_one_added_helper',set(nodes)-{n.name for n in oldtree.body if isinstance(n,ast.FunctionDef)}=={'_go_assertions'})
 for ref in refs:check('input_unchanged_'+ref['path'],pin(ref['path'])==ref)
 result=save('source-controls.json',dict(status='PASS',count=len(checks),checks=checks,candidate_source_ref=pin(source),actual_old_stdout_ref=inputs['actual_stdout_ref'],actual_old_report_ref=inputs['actual_report_ref'],real_raw_unchanged=True,real_report_unchanged=True,real_records_equal=5,real_event_count=len(events),execution_kind='EXTRACTED_PURE_PARSER_AND_NATIVE_REPLAY_PREFIX_ONLY',actual_router_or_full_consumer_executed=False,Native_Git_Go_SQL_API_model_executed=False,old_v6_expected_P1_is_handled_control_not_new_failure=True))
 print(json.dumps(dict(status='PASS',check_count=len(checks),controls_ref=result,candidate_ref=pin(source),actual_replayed_records=5)),flush=True)
finally:
 cleanup=guard.close();save('controls-source-guard.cleanup.json',cleanup)
 assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
