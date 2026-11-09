"""Only IO/AST edits of immutable receipt source; never imports any candidate."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
P13=HERE.parents[1]
OLD=P13/'fresh58_desktop169_go3_controller_preparation_codex/52998fc9c4d64166b10aa02e6eca11e4'
REVIEW=P13/'fresh58_desktop169_go3_independent_source_review_codex/14818767d60a485885f7c5e0e36135cd'


def ref(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}


def put(name,value):
    with (HERE/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())


review=json.loads((REVIEW/'review.json').read_bytes())
assert ref(REVIEW/'review.json')['sha256']=='f6158ce83e4b06e1ed2167dcf0dc63139d047d0b8397f8348c4dc3423f6ebc1d'
selected=review['selected_refs']
inputs=list(selected.values())+[ref(REVIEW/'review.json'),ref(OLD/'manifest.json')]
for x in inputs:assert ref(Path(x['path']))==x
put('inputs.before.json',{'files':inputs})
all_proofs=[]


def edit_source(key,newname,edits):
    oldp=Path(selected[key]['path']);base=oldp.read_bytes();candidate=base
    newline='\r\n' if b'\r\n' in base else '\n'
    proof=[]
    for before,after,count in edits:
        a=before.replace('\n',newline).encode();b=after.replace('\n',newline).encode()
        assert candidate.count(a)==count,(key,before[:90],candidate.count(a))
        candidate=candidate.replace(a,b)
        proof.append({'old':a.decode(),'new':b.decode(),'occurrences':count})
    inverse=candidate
    for e in reversed(proof):
        a,b=e['old'].encode(),e['new'].encode()
        assert inverse.count(b)==e['occurrences']
        inverse=inverse.replace(b,a)
    assert inverse==base
    original_tree=ast.parse(base);new_tree=ast.parse(candidate)
    olddefs={x.name:x for x in original_tree.body if isinstance(x,ast.FunctionDef)}
    newdefs={x.name:x for x in new_tree.body if isinstance(x,ast.FunctionDef)}
    unchanged=[];changed=[]
    for name,node in olddefs.items():
        if ast.dump(node,include_attributes=False)==ast.dump(newdefs[name],include_attributes=False):
            assert ast.get_source_segment(base.decode(),node)==ast.get_source_segment(candidate.decode(),newdefs[name])
            unchanged.append(name)
        else:changed.append(name)
    with (HERE/newname).open('xb') as f:f.write(candidate)
    with (HERE/(key+'.diff')).open('xb') as f:
        f.write(''.join(difflib.unified_diff(base.decode().splitlines(True),candidate.decode().splitlines(True),fromfile=str(oldp),tofile=newname)).encode())
    record={'baseline_ref':selected[key],'candidate_ref':ref(HERE/newname),'edits':proof,'whole_byte_inverse':True,
            'unchanged_definitions_byte_AST':unchanged,'changed_definitions':changed,'new_definitions':sorted(set(newdefs)-set(olddefs))}
    put(key+'.inverse.json',record);all_proofs.append(record)
    return ref(HERE/newname)


lifecycle='''def observer_lifecycle(rows,parent,seen_pids):
    need(rows and rows[0]['kind']=='observer-start' and rows[-1]['kind']=='observer-exit','Observer lifetime missing')
    pid=rows[0]['pid']
    need(type(pid) is int and pid>0 and parent.name==str(pid) and pid not in seen_pids,'Duplicate/foreign observer PID')
    seen_pids.add(pid)
    need(all(type(r['pid']) is int and r['pid']==pid and type(r['sequence']) is int for r in rows),'Observer PID/sequence type')
    need([r['sequence'] for r in rows]==list(range(1,len(rows)+1)),'Observer sequence gap/duplicate')
    requests={}
    for event in rows[1:-1]:
        kind=event['kind'];rid=event.get('id')
        need(kind in ['request-received','request-body-complete','response-call-returned','response-finish','response-close'],
             'Unknown/error/incomplete observer event')
        need(type(rid) is int and rid>0,'Request id type')
        if kind=='request-received':
            need(rid not in requests and rid==len(requests)+1,'Duplicate/out-of-order request admission')
            requests[rid]={'received':event,'body':None,'finish':None,'close':None,'writes':{}}
            continue
        need(rid in requests,'Orphan request event')
        item=requests[rid]
        if kind=='response-call-returned':
            ordinal=event['ordinal']
            need(type(ordinal) is int and ordinal>0 and ordinal not in item['writes'] and event['method'] in ['write','end'],
                 'Duplicate/invalid response method ordinal')
            need('accepted_argument' in event and event['actual_socket_bytes'] is None,'Response raw boundary missing')
            item['writes'][ordinal]=event
            continue
        key={'request-body-complete':'body','response-finish':'finish','response-close':'close'}[kind]
        need(item[key] is None,'Duplicate request lifecycle event')
        if key=='body':
            need('raw' in event and item['close'] is None,'Missing body raw or body completes after close: OPEN')
        elif key=='finish':
            need(item['close'] is None and type(event['reader_complete']) is bool and
                 event['reader_complete']==(item['body'] is not None),'Finish/reader order mismatch')
        else:
            need(item['finish'] is not None and item['body'] is not None and event['finished'] is True and
                 event['reader_complete'] is True,'Premature/incomplete response close: OPEN')
        item[key]=event
    for item in requests.values():
        need(all(item[k] is not None for k in ['body','finish','close']),'Missing body/finish/close')
        need(sorted(item['writes'])==list(range(1,len(item['writes'])+1)),'Response method ordinal gap')
    final=rows[-1]
    need(type(final['code']) is int and final['code']==0 and final['errors']==0 and final['active']==0,'Observer exit/outstanding failure')
    need(type(final['requests_received']) is int and type(final['response_finished']) is int and
         final['requests_received']==final['response_finished']==len(requests),'Exact lifecycle counters disagree')
    return {'pid':pid,'requests':len(requests),'complete':True,'request_ids':sorted(requests),
            'body_end_vs_finish_order':'EITHER; both must precede close','socket_bytes':None}

'''
oldblock="""    received=0;finished=0;observer_pids=[]
    for p in observers:
        rows=[json.loads(x) for x in p.read_bytes().splitlines()]
        need(rows and rows[0]['kind']=='observer-start' and rows[-1]['kind']=='observer-exit','Observer lifetime end missing')
        need([x['sequence'] for x in rows]==list(range(1,len(rows)+1)),'Observer sequence gap')
        final=rows[-1];need(final['code']==0 and final['errors']==0 and final['active']==0,'Observer failure/outstanding response')
        need(not any('overflow' in x['kind'] or 'error' in x['kind'] for x in rows),'Observer incomplete evidence')
        incoming=[x for x in rows if x['kind']=='request-received'];ends=[x for x in rows if x['kind']=='response-finish']
        need(final['requests_received']==len(incoming) and final['response_finished']==len(ends),'Counter mismatch')
        for item in rows:
            for key in ['raw','accepted_argument','attempted']:
                if key in item:
                    rp=Path(item[key]['path']);need(rp.parent==p.parent,'Observer raw foreign path');verify(rp,item[key])
        received+=len(incoming);finished+=len(ends);observer_pids.append(final['pid'])
"""
newblock="""    received=0;finished=0;observer_pids=[];seen_pids=set();lifecycles=[]
    for p in observers:
        rows=[json.loads(x) for x in p.read_bytes().splitlines()]
        for item in rows:
            for key in ['raw','accepted_argument','attempted']:
                if key in item:
                    rp=Path(item[key]['path']);need(rp.parent==p.parent,'Observer raw foreign path');verify(rp,item[key])
        try:report=observer_lifecycle(rows,p.parent,seen_pids)
        except (RuntimeError,KeyError,TypeError,ValueError) as exc:
            return {'qualified':False,'source_assertions_preserved':True,'source_assertions_passed':True,
                    'transport_complete':False,'transport_qualification':'OPEN','lifecycle_error':str(exc),
                    'observer_path':str(p),'completed_observer_lifecycles':lifecycles,'files':files,
                    'socket_transmitted_byte_count':None,'auto_Date_ContentLength':None,
                    'expected_abort_exception_authorized':False}
        lifecycles.append(report);received+=report['requests'];finished+=report['requests'];observer_pids.append(report['pid'])
"""
evaluator=edit_source('evaluator','fixture_evaluator.v2.proposed.py',[
    ('def validate_case(state,leaf,case,export,job,scope):',lifecycle+'def validate_case(state,leaf,case,export,job,scope):',1),
    (oldblock,newblock,1),
    ("'server_received':received,'server_finished':finished,","'transport_complete':True,'observer_lifecycles':lifecycles,\n        'server_received':received,'server_finished':finished,",1)])

controller=edit_source('controller','desktop_controller.v3.proposed.py',[
    ("scope['cleanup_seconds']==5,'Explicit finite allocation')",
     "scope['cleanup_seconds']==5,'Explicit finite allocation')\n    need(type(scope['controller_evidence_reserve_seconds']) is int and scope['controller_evidence_reserve_seconds']>0, 'Root controller evidence IO reserve required')",1),
    ("stage=label;remaining=deadline-time.monotonic()-5\n            need(remaining>0 and native<scope['native_top_command_cap'],'Native/time allocation exhausted')\n            native+=1;timeout=min(seconds,remaining)",
     "stage=label;remaining=deadline-time.monotonic()\n            reserve=25+scope['cleanup_seconds']+scope['controller_evidence_reserve_seconds']\n            need(remaining>reserve and native<scope['native_top_command_cap'],'Native/time allocation exhausted before process start')\n            native+=1;timeout=min(seconds,remaining-reserve)\n            helper_deadline=deadline-scope['controller_evidence_reserve_seconds']",1),
    ("'remaining_before_start':remaining,'future_images':futures,",
     "'remaining_before_start':remaining,'helper_finalization_reserve':25,'cleanup_reserve':scope['cleanup_seconds'],\n                 'controller_evidence_reserve':scope['controller_evidence_reserve_seconds'],'helper_absolute_deadline':helper_deadline,'future_images':futures,",1),
    ('future_images=futures,future_context=context)',
     'future_images=futures,future_context=context,absolute_deadline=helper_deadline)',1),
    ("                    try:fn()\n                    except BaseException as exc:",
     "                    try:\n                        fn();need(time.monotonic()<=deadline,'Root inner deadline exceeded during evidence finalization')\n                    except BaseException as exc:",1),
    ("            evaluation=module(scope['fixture_evaluator_ref'],'desktop58_fixture_evaluator').validate_case(state,leaf if index else None,case,export,job,scope)\n            need(evaluation['qualified'] is True and evaluation['source_assertions_preserved'] is True,'Fixture evidence incomplete')",
     "            state['source_assertions_passed']=True\n            evaluation=module(scope['fixture_evaluator_ref'],'desktop58_fixture_evaluator').validate_case(state,leaf if index else None,case,export,job,scope)\n            save(case/'fixture-verdict.json',evaluation)\n            need(evaluation['qualified'] is True and evaluation['source_assertions_preserved'] is True,'Fixture evidence incomplete')",1),
    ("            save(case/'fixture-verdict.json',evaluation);state.update(state='QUALIFIED',qualified=True);rows.append(dict(state))",
     "            state.update(state='QUALIFIED',qualified=True);rows.append(dict(state))",1)])

helper=edit_source('helper','windows_debug_job_tree.future_images.deadline.proposed.py',[
    ('future_images=None, future_context=None):','future_images=None, future_context=None, absolute_deadline=None):',1),
    ("            raise ValueError('timeout must be a finite positive number')",
     "            raise ValueError('timeout must be a finite positive number')\n        if isinstance(absolute_deadline,bool) or not isinstance(absolute_deadline,(int,float)) or not math.isfinite(absolute_deadline):\n            raise ValueError('Explicit Root absolute helper deadline required')\n        result['requested_process_timeout_seconds']=timeout\n        result['absolute_deadline']=absolute_deadline\n        result['success_finalization_reserve_seconds']=25\n        result['failure_cleanup_reserve_seconds']=5\n        remaining=absolute_deadline-started\n        timeout=min(timeout,remaining-25.0-5.0)\n        result['effective_process_timeout_seconds']=timeout\n        result['remaining_at_helper_entry_seconds']=remaining\n        if timeout<=0:\n            raise TimeoutError('No process budget remains after finalization and cleanup reservation')",1),
    ('deadline = time.monotonic() + 5.0','deadline = min(time.monotonic() + 5.0, absolute_deadline)',1),
    ("finalization_deadline = time.monotonic() + 25.0\n                result['evidence_finalization_timeout_seconds'] = 25",
     "finalization_deadline = min(time.monotonic() + 25.0, absolute_deadline)\n                result['evidence_finalization_deadline'] = finalization_deadline\n                result['evidence_finalization_timeout_seconds'] = 25\n                deadline_check(finalization_deadline, 'evidence finalization entry')",1),
    ('                for proc in generations:\n                    ph = HANDLE',
     "                for proc in generations:\n                    deadline_check(finalization_deadline, 'process generation evidence')\n                    ph = HANDLE",1),
    ("        result['elapsed_seconds'] = time.monotonic() - started\n    return result",
     "        result['elapsed_seconds'] = time.monotonic() - started\n        if isinstance(absolute_deadline,(int,float)) and not isinstance(absolute_deadline,bool) and math.isfinite(absolute_deadline):\n            try:deadline_check(absolute_deadline, 'helper final owned-handle closure')\n            except BaseException as exc:\n                debug['complete']=False\n                cleanup['errors'].append(error_text(exc))\n                record_error(exc)\n    return result",1)])

launcher=edit_source('launcher','desktop_launch.v2.proposed.py',[
    ("phase='ALLOCATE';candidate=util.safe(s['outer_output_root'],ROOT/'execution/v2.4/receipts/W13/W13-03',True)",
     "need(type(s['inner_seconds']) is int and s['inner_seconds']>0 and type(s['outer_seconds']) is int and\n             type(s['launcher_evidence_reserve_seconds']) is int and s['launcher_evidence_reserve_seconds']>0 and\n             s['outer_seconds']>s['inner_seconds']+25+5+s['launcher_evidence_reserve_seconds'],'Root complete outer phase allocation')\n        outer_deadline=started+s['outer_seconds']\n        need(outer_deadline-time.monotonic()>s['inner_seconds']+25+5+s['launcher_evidence_reserve_seconds'],'Outer preparation consumed allocation')\n        phase='ALLOCATE';candidate=util.safe(s['outer_output_root'],ROOT/'execution/v2.4/receipts/W13/W13-03',True)",1),
    ("        need(type(s['outer_seconds']) is int and s['outer_seconds']>s['inner_seconds']+5,'Root finite outer allocation')",
     "        remaining=outer_deadline-time.monotonic()\n        effective_timeout=remaining-5-s['launcher_evidence_reserve_seconds']\n        need(effective_timeout>s['inner_seconds']+25,'Root outer budget exhausted before owned child')",1),
    ("'timeout':s['outer_seconds'],'automatic_retry':False",
     "'timeout':effective_timeout,'requested_outer_seconds':s['outer_seconds'],'remaining_before_start':remaining,'cleanup_reserve':5,'launcher_evidence_reserve':s['launcher_evidence_reserve_seconds'],'absolute_outer_deadline':outer_deadline,'automatic_retry':False",1),
    ("result=normal.run_owned(argv,str(ROOT),env,so,se,s['outer_seconds'])",
     "result=normal.run_owned(argv,str(ROOT),env,so,se,effective_timeout)",1),
    ("            try:save(out/'result.json',{'first_error':first,",
     "            if time.monotonic()>outer_deadline:\n                item={'phase':'outer-evidence-deadline','error':'Root outer budget exceeded','actual_native_exit':None}\n                if first is None:first=item\n                else:secondary.append(item)\n            try:save(out/'result.json',{'first_error':first,",1),
    ("            except BaseException:traceback.print_exc();return 1\n    return 1 if first else 0",
     "            except BaseException:traceback.print_exc();return 1\n            if time.monotonic()>outer_deadline:\n                print('Root outer deadline exceeded after final result IO',file=sys.stderr);return 1\n    return 1 if first else 0",1)])

scope=json.loads(Path(selected['scope']['path']).read_bytes())
for key,value in [('controller_ref',controller),('launcher_ref',launcher),('debug_helper_ref',helper),('fixture_evaluator_ref',evaluator)]:scope[key]=value
scope['controller_evidence_reserve_seconds']=None
scope['launcher_evidence_reserve_seconds']=None
put('scope.v2.proposed.json',scope)
put('inverse-index.json',{'files':all_proofs,'all_inverse_exact':True,
    'unchanged_observer_ref':selected['observer'],'unchanged_roster_ref':selected['roster'],
    'unchanged_builder_ref':selected['builder'],'old_helper_remains_unchanged':True})
after=[ref(Path(x['path'])) for x in inputs];assert after==inputs
put('inputs.after.json',{'files':after,'drift':[]})
print(json.dumps({'selected':{'controller':controller,'launcher':launcher,'helper':helper,'evaluator':evaluator},
                  'scope':ref(HERE/'scope.v2.proposed.json'),'old_inputs':len(inputs),'candidate_imports':0},ensure_ascii=False))
