import hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
S=Q.parent.parent/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def docs(v):
    if type(v)in(dict,list):
        yield v
        for x in(v.values()if type(v)is dict else v):yield from docs(x)
    elif type(v)is str:
        for text in dict.fromkeys((v,*v.splitlines())):
            try:p=json.loads(text)
            except(ValueError,TypeError):continue
            if p!=v:yield from docs(p)
def main():
    bundle=json.loads((S/'nf5-four-closed-actual-input02.root.json').read_text(encoding='utf-8'));out={}
    for name,row in bundle['groups'].items():
        out[name]={}
        for label in('prepare_initial_Root_capture_ref','prepare_completed_Root_capture_ref','run_initial_Root_capture_ref','run_completed_Root_capture_ref'):
            ref=row[label];b=json.loads(Path(ref['path']).read_text(encoding='utf-8'));rawref=b['original_capture_ref']
            lines=Path(rawref['path']).read_bytes().splitlines();last=json.loads(lines[2])['payload']
            observed=[x for x in docs(last)if type(x)is dict and type(x.get('chunk_id'))is str and'output'in x]
            text=last.get('output');out[name][label]={'binding_ref':ref,'schema':b['schema'],'binding_keys':list(b),
                'expected_host_chunk':b.get('actual_host_chunk_id'),'payload_type':type(text).__name__,
                'payload_excerpt':str(text)[:1100],'observed_host_shapes':[{'chunk_id':x['chunk_id'],'keys':list(x),
                    'exit_code':x.get('exit_code'),'session_id':x.get('session_id')}for x in observed]}
    guard=json.loads((Q/'actual-review-v5-guard.closed.json').read_text(encoding='utf-8'))
    out['review_v5_guard']={'ref':pin(Q/'actual-review-v5-guard.closed.json'),'closed':guard['closed'],
        'retained_handles_count':guard['retained_handles_count'],'failure':guard['failure'],'errors':guard['errors'],'entries':len(guard['entries'])}
    p=Q/'Root-capture-return-shapes.json'
    with p.open('x',encoding='utf-8',newline='\n')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(ref=pin(p),groups=out),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
