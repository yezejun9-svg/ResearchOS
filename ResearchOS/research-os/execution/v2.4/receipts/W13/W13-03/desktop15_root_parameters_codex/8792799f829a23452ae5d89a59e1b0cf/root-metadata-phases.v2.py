"""Root orchestration of independently reviewed Desktop15 metadata phases.
The outer subprocess is observation only; owned register/Git Jobs are inside the reviewed engine.
No general OS lifecycle or product qualification is claimed."""
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,json,os,subprocess,traceback
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
REG=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/desktop15-source-integration-r332-8792799f829a23452ae5d89a59e1b0cf")
PYTHON='C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
CODE_REFS={"run.py":{"path":"D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\integration_codex\\desktop15-source-integration-r332-8792799f829a23452ae5d89a59e1b0cf\\run.py","sha256":"e05f99eb2d72fbb115bac841054125eb747d4d9ea13dd894872bceb0f069aa6a","bytes":25374},"seal.py":{"path":"D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\integration_codex\\desktop15-source-integration-r332-8792799f829a23452ae5d89a59e1b0cf\\seal.py","sha256":"6d89836241870e8e3c930a0a70525a01ce59882b26f810d238168e259209fc39","bytes":25375},"grant-producer.py":{"path":"D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\integration_codex\\desktop15-source-integration-r332-8792799f829a23452ae5d89a59e1b0cf\\grant-producer.py","sha256":"d5b77a96df03a17939f750d5b8cf5a13f58921365cd70fa54f1b123e68ac143a","bytes":25376},"prepared_refs.json":{"path":"D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\integration_codex\\desktop15-source-integration-r332-8792799f829a23452ae5d89a59e1b0cf\\prepared_refs.json","sha256":"daf3d3bd73285f77e90b5d4ab647a5fd5f6466cffde2e881273142a49654737a","bytes":2520844}}
def need(v,msg):
    if not v:raise RuntimeError(msg)
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,value):
    with (OUT/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
def invoke(label,argv,env,timeout):
    result=None;first=None;secondary=[]
    phase='request'
    refs={'stdout_ref':None,'stderr_ref':None}
    try:
        save(label+'.request.json',{'argv':argv,'cwd':str(ROOT),'environment':env,'timeout_seconds':timeout,
            'purpose':'Root metadata only','automatic_retry':False,'outer_subprocess_Job_or_OS_lifecycle_qualification':False})
        phase='open-raw'
        with (OUT/(label+'.stdout.raw')).open('xb') as stdout,(OUT/(label+'.stderr.raw')).open('xb') as stderr:
            phase='native-launch'
            result=subprocess.run(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=timeout,check=False)
        phase='native-completed'
        if result.returncode!=0:
            first={'phase':phase,'error':'Metadata child exited nonzero','actual_native_exit':result.returncode}
    except BaseException as exc:
        first={'phase':phase,'error':repr(exc),'traceback':traceback.format_exc(),
            'actual_native_exit':result.returncode if result is not None else None}
    for field,suffix in [('stdout_ref','.stdout.raw'),('stderr_ref','.stderr.raw')]:
        try:
            refs[field]=pin(OUT/(label+suffix))
        except BaseException as exc:
            secondary.append({'phase':'seal-'+field,'error':repr(exc),'actual_native_exit':None})
    invocation={'actual_native_exit':result.returncode if result is not None else None,
        'first_error':first,'secondary_errors':secondary,**refs,'automatic_retry':False,
        'counter_reset':False,'product_cases_executed':False,'outer_OS_lifecycle_qualification':False}
    try:
        save(label+'.invocation.json',invocation)
    except BaseException as exc:
        detail={'phase':'save-invocation','error':repr(exc),'actual_native_exit':None}
        if first is None:
            first=detail
        else:
            secondary.append(detail)
    if first is not None or secondary:
        if first is None:
            first=secondary.pop(0)
        print(json.dumps({'first_error':first,'secondary_errors':secondary,
            'source_metadata_may_be_partial':True,'automatic_retry':False,'counter_reset':False},
            ensure_ascii=False,allow_nan=False),file=sys.stderr)
        raise SystemExit(1)

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize and Path.cwd()==ROOT,'isolated flags/cwd')
ap=argparse.ArgumentParser()
ap.add_argument('phase',choices=['run','seal','grant'])
ap.add_argument('--review-path')
ap.add_argument('--review-sha256')
a=ap.parse_args()
filename={'run':'run.py','seal':'seal.py','grant':'grant-producer.py'}[a.phase]
need(pin(REG/filename)==CODE_REFS[filename],'exact reviewed metadata code')
need(pin(REG/'prepared_refs.json')==CODE_REFS['prepared_refs.json'],'exact reviewed prepared refs')
command=[PYTHON,'-I','-S','-X','utf8',str(REG/filename)]
if a.phase=='run':
    need(a.review_path and a.review_sha256 and len(a.review_sha256)==64,'explicit actual nonauthor metadata review')
    rr=pin(a.review_path)
    need(rr['sha256']==a.review_sha256,'review actual SHA')
    review=json.loads(Path(a.review_path).read_bytes())
    need(review['schema']=='researchos.root-registration-source-review.v1' and
        review['reviewer']=='codex:/root/w05_merge_review' and review['requested_changes']==[] and
        review['decision']=='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' and review['actual_registration_executed'] is False,'new reviewed metadata only')
    need(review['expected_before']==[331,159,509] and review['expected_after']==[332,160,516],'review actual tuples')
    command.extend([a.review_path,a.review_sha256])
else:
    need(a.review_path is None and a.review_sha256 is None,'no reused run arguments')
env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT']}
invoke('metadata-'+a.phase,command,env,1500)
print(json.dumps({'phase':a.phase,'actual_metadata_native_exit':0,'invocation_ref':pin(OUT/('metadata-'+a.phase+'.invocation.json')),
    'source_acceptance':False,'formal_increment':0,'outer_OS_lifecycle_qualification':False},ensure_ascii=False))
