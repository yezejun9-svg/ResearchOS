import json,re,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent;B=Q.parent.parent
N=B/'full_w09_main_native_producer_source_codex/fullw09-20261010-05'
def main():
    bundle=json.loads((B/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/nf5-four-closed-actual-input02.root.json').read_text(encoding='utf-8'))
    choice=json.loads((N/'source.choice.json').read_text(encoding='utf-8'));out={}
    for name,row in bundle['groups'].items():
        c=dict(choice['common'],**choice['selectors'][name]);closed=json.loads(Path(row['producer_closed_ref']['path']).read_text(encoding='utf-8'))
        req=closed['request_ref'];out[name]={}
        for stage in('prepare','run'):
            b=json.loads(Path(row[stage+'_initial_Root_capture_ref']['path']).read_text(encoding='utf-8'))
            lines=Path(b['original_capture_ref']['path']).read_bytes().splitlines();call=json.loads(lines[1])['payload']
            text=call.get('input','');out[name][stage]={'exec_command':'exec_command'in text,'Source_script_exact':str(N/(stage+'_full_w09.source.py'))in text,
                'selector_literal':c['selector_key']in text,'request_path_exact':req['path']in text,'request_SHA_exact':req['sha256']in text,
                'request_bytes_exact':bool(re.search(r'\b'+str(req['bytes'])+r'\b',text)),'actual_call_input':text}
    with(Q/'Root-call-gate-fields.json').open('x',encoding='utf-8',newline='\n')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:{a:{x:y for x,y in v.items()if x!='actual_call_input'}for a,v in rows.items()}for k,rows in out.items()},ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
