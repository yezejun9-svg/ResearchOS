"""Read-only, bounded raw fixture evidence evaluator. Future execution only."""
import hashlib,json,os
from pathlib import Path
def need(value,why):
    if not value:raise RuntimeError(why)
def read(p):
    return json.loads(p.read_bytes())
def rawref(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verify(p,row):
    r=rawref(p);need(r['sha256']==row['sha256'] and r['bytes']==row['bytes'],'Fixture raw digest mismatch');return r
def observer_lifecycle(rows,parent,seen_pids):
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

def validate_case(state,leaf,case,export,job,scope):
    case=Path(case);evidence=case/'evidence';files=[]
    need(state['native_exit']==0 and job['actual_exit']==0,'Observed primary native exit required')
    if state['lane']=='go3':
        return {'qualified':True,'source_assertions_preserved':True,'evidence_boundary':'EXACT_FROZEN_GO3_RAW_PASS_PLUS_OWNED_PROCESS_TREE','HTTP':0,'HTTP_basis':'Frozen pure parser selectors; no HTTP fixture invoked','files':[]}
    need(evidence.is_dir(),'Node observation directory absent')
    for p in evidence.rglob('*'):
        need(not p.is_symlink() and not(getattr(os.lstat(p),'st_file_attributes',0)&0x400),'Receipt reparse')
        if p.is_file():files.append(rawref(p))
    observers=list((evidence/'legacy-observer').glob('*/events.jsonl'))
    need(observers,'Actual observer child/parent records absent')
    received=0;finished=0;observer_pids=[];seen_pids=set();lifecycles=[]
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
    harness_http=0;harness_children=0;harness_refs=[]
    for p in evidence.rglob('observations.json'):
        doc=read(p);need(doc['external']==0 and doc['model']==0,'Unexpected fixture network/model metadata')
        for i,row in enumerate(doc['http']):verify(p.parent/('request-'+str(i)+'.raw'),row)
        for i,row in enumerate(doc['responses']):verify(p.parent/('response-'+str(i)+'.raw'),row)
        for i,row in enumerate(doc['children']):
            for ext in ['input','stdout','stderr']:need((p.parent/('child-'+str(i)+'.'+ext)).is_file(),'Child raw missing')
        harness_http+=len(doc['http']);harness_children+=len(doc['children']);harness_refs.append(rawref(p))
    renderer=state['name'].startswith('desktop-renderer/')
    legacy='argv' in leaf
    if renderer:
        facts=read(evidence/'renderer-facts.json');inv=read(evidence/'electron.invocation.json')
        need(facts['kind']==state['name'].split('/')[-1].split('-')[0] and facts['pass'] is True and facts['actualElectron'],'Actual requested renderer missing')
        need(facts['model']==0 and facts['external']==0 and facts['http']==harness_http,'Renderer HTTP binding')
        need(inv['mode']=='ACTUAL_OFFSCREEN_PUBLIC_FIXTURE' and inv['exit']==0 and inv['exited'] and inv['stdoutClosed'] and inv['stderrClosed'],'Actual Electron process not closed')
        http=harness_http;boundary='ACTUAL_ELECTRON_ORIGINAL_HTTP_FIXTURE_RECORDS'
    elif legacy:
        http=received;boundary='ACTUAL_FIXTURE_SERVER_RECEIVE_AND_RESPONSE_METHOD_RECORDS'
    else:
        need(received==harness_http,'Independent received count differs from original fixture evidence')
        http=harness_http;boundary='ORIGINAL_FIXTURE_RAW_PLUS_SERVER_OBSERVER'
    cap=leaf.get('http_request_cap',leaf.get('http_cap'))
    need(type(cap) is int and http<=cap,'Original per-case observed HTTP cap')
    if 'pure_child_cap' in leaf:need(harness_children<=leaf['pure_child_cap'],'Original child observation cap')
    alias_rows=read(Path(scope['alias_roster_ref']['path']))['rows']
    selected=[x for x in alias_rows if x['name']==state['name']]
    alias_usage=None
    admissions=job['debug_capture']['future_image_admissions']
    if selected:
        row=selected[0];used=read(evidence/'negative-alias.used.json')
        plan=case/'negative-alias-plan.json';need(used['plan_sha256']==rawref(plan)['sha256'],'Alias original plan hash')
        root=Path(export)/'.local/desktop-wire-negative'/(scope['run_uuid']+'-'+str(row['allocation_ordinal']).zfill(2))
        image=root/'resources/client-wire/researchos-client-wire-validator.exe'
        need(used['root']==str(root) and used['case_name']==state['name'] and used['mode']==row['mode'] and used['ordinal']==row['allocation_ordinal'],'Exact allocated alias')
        need(len(admissions)==row['expected_image_creates'] and all(x['path']==str(image) and x['case_name']==state['name'] and x['checked_before_debug_continue'] is True for x in admissions),'Exact alias launch usage')
        alias_usage={'allocation_roots':1,'root':str(root),'exact_image_path':str(image),'actual_CREATE_count':len(admissions),'expected_CREATE_count':row['expected_image_creates'],'unused_launch_path':len(admissions)==0,'PID_count_is_not_clone_count':True}
    else:need(not admissions,'Unexpected future-image use by unrelated case')
    return {'qualified':True,'source_assertions_preserved':True,'evidence_boundary':boundary,'HTTP':http,'HTTP_cap':cap,
        'transport_complete':True,'observer_lifecycles':lifecycles,
        'server_received':received,'server_finished':finished,'original_harness_HTTP':harness_http,'original_harness_children':harness_children,
        'observer_PIDs':observer_pids,'harness_refs':harness_refs,'files':files,'alias_usage':alias_usage,'socket_transmitted_byte_count':None,
        'auto_Date_ContentLength':None,'unobserved_client_outbound_calls':None,'Python_lifecycle_proof':False,
        'offscreen_renderer_controls':1 if renderer else 0,'visible_installed_GUI_calls':0}
