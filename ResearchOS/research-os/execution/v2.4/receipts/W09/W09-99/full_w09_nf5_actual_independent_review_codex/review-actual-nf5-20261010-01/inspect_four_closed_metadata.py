import hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
N=R/'execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_source_codex/fullw09-20261010-05'
def pin(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def dec(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    choice=dec(N/'source.choice.json');out={}
    for name,partial in choice['selectors'].items():
        c=dict(choice['common'],**partial);receipt=Path(c['receipt_root'])
        cp=receipt/'producer/validation.closed.json';rp=receipt/'prepare.ready.json'
        d=dec(cp);ready=dec(rp)
        row={'choice_selector':c['selector'],'run_id':c['run_id'],'prepare_ref':pin(rp),'producer_closed_ref':pin(cp),
             'closed_keys':list(d),'prepare_status':ready['status'],'expected_go_argv':[c['tool_refs']['go']['path'],*c['go_test_argv_suffix']],
             'status':d.get('status'),'stage':d.get('stage'),'error':d.get('error'),'original_exception_type':d.get('original_exception_type'),
             'diagnostics':d.get('diagnostics'),'summary':d.get('summary'),'native_packet_ref':d.get('native_packet_ref'),
             'cleanup_errors':d.get('cleanup_errors'),'all_guards_closed':d.get('all_guards_closed'),'all_owned_jobs_closed':d.get('all_owned_jobs_closed'),
             'invocations':[{'label':v['label'],'ref':v['ref'],'record_keys':list(v['record']),
                 'actual_outer_exit':v['record']['actual_outer_exit'],'result':v['record']['result'],
                 'individual_child_numeric_exit':v['record']['individual_child_numeric_exit']} for v in d['invocation_observations']]}
        nr=d.get('native_packet_ref')
        if nr is not None:
            packet=dec(Path(nr['path']));row['packet_keys']=list(packet)
            row['packet_metadata']={k:v for k,v in packet.items()if k!='raw_copy_mapping'}
            row['packet_raw_count']=len(packet.get('raw_copy_mapping',[]))
            ref=packet.get('original_report_ref')
            if ref is not None:
                report=dec(Path(ref['path']));row['report_keys']=list(report)
                row['report_fields']={k:report.get(k)for k in ['status','exit_code','actual_invocation','selected_tests','assertion_ids','formal_case_accepted_delta','run_id','started_at','ended_at','raw_evidence_references']}
        out[name]=row
    path=Q/'four-closed-metadata.json'
    with path.open('x',encoding='utf-8',newline='\n')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'output_ref':pin(path),'groups':out},ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
