import hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent;R=Path('D:/作品集/ResearchOS/research-os')
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def main():
    meta=json.loads((Q/'four-closed-metadata.json').read_text(encoding='utf-8'));out={}
    for name,row in meta.items():
        report_ref=row['packet_metadata']['original_report_ref'];report=json.loads(Path(report_ref['path']).read_text(encoding='utf-8'))
        stream=R/report['raw_evidence_references'][0];groups={}
        for line in stream.read_text(encoding='utf-8').splitlines():
            event=json.loads(line);p=event.get('Package');g=groups.setdefault(p,{'events':0,'tests':[],'package_actions':[]})
            g['events']+=1
            test=event.get('Test')
            if test is None:g['package_actions'].append(event.get('Action'))
            elif test not in g['tests']:g['tests'].append(test)
        out[name]={'report_ref':report_ref,'stdout_ref':pin(stream),'packages':groups,'selected_tests':report['selected_tests']}
    target=Q/'actual-stream-package-observations.json'
    with target.open('x',encoding='utf-8',newline='\n')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(ref=pin(target),groups=out),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
