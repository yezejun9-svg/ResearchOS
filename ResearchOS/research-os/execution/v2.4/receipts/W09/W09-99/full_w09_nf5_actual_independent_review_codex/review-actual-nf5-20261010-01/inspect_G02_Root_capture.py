import hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
S=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009')
def main():
    result={}
    for stage in('initial','completed'):
        p=S/('w09.nf5-G02-run-'+stage+'.actual-audit.root.json');raw=p.read_bytes();b=json.loads(raw)
        ref=b['original_capture_ref'];original=Path(ref['path']).read_bytes()
        assert len(original)==ref['bytes']and hashlib.sha256(original).hexdigest()==ref['sha256']
        rows=[json.loads(x)for x in original.splitlines()]
        output=rows[2]['payload'];value=output.get('output')
        result[stage]=dict(binding_ref=dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)),binding=b,
            call=rows[1]['payload'],output_keys=list(output),output_value_type=type(value).__name__,output_value=value)
    with(Q/'G02-Root-capture-shapes.json').open('xb')as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps({k:dict(binding_ref=v['binding_ref'],call_keys=list(v['call']),output_keys=v['output_keys'],output_value_type=v['output_value_type'],output_prefix=str(v['output_value'])[:900])for k,v in result.items()},ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
