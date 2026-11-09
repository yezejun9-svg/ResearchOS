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
    received=0;finished=0;observer_pids=[]
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
        'server_received':received,'server_finished':finished,'original_harness_HTTP':harness_http,'original_harness_children':harness_children,
        'observer_PIDs':observer_pids,'harness_refs':harness_refs,'files':files,'alias_usage':alias_usage,'socket_transmitted_byte_count':None,
        'auto_Date_ContentLength':None,'unobserved_client_outbound_calls':None,'Python_lifecycle_proof':False,
        'offscreen_renderer_controls':1 if renderer else 0,'visible_installed_GUI_calls':0}
