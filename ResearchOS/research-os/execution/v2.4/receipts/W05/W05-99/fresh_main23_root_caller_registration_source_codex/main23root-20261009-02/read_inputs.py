import sys
sys.dont_write_bytecode=True
import ctypes
from ctypes import wintypes
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import traceback

Q=Path(__file__).resolve().parent
B=Q.parents[1]
R=Path('D:/作品集/ResearchOS/research-os')
BASE=B/'fresh_main23_root_caller_registration_source_codex/main23root-20261009-01'
REVIEW=B/'fresh_main23_root_caller_registration_independent_source_review_codex/review-20261009-01'
def pin(path,raw):return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,raw):
    path=Q/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:assert stream.write(raw)==len(raw)
    return pin(path,raw)
def savejson(name,value):return save(name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))

class Guard:
    def __init__(self):self.held=[]
    def read(self,path,expected=None):
        path=Path(path).resolve(strict=True)
        api=ctypes.WinDLL('kernel32',use_last_error=True)
        api.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
        api.CreateFileW.restype=wintypes.HANDLE
        handle=api.CreateFileW(str(path),0x80000000,1,None,3,0x80,None)
        if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
        stream=os.fdopen(msvcrt.open_osfhandle(int(handle),os.O_RDONLY|os.O_BINARY),'rb')
        before=os.fstat(stream.fileno());raw=stream.read();actual=pin(path,raw)
        self.held.append((stream,actual,(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)))
        if expected is not None:assert (actual['sha256'],actual['bytes'])==(expected['sha256'],expected['bytes']),str(path)
        return raw,actual
    def close(self):
        rows=[]
        try:
            for stream,actual,before in self.held:
                stream.seek(0);raw=stream.read();after=os.fstat(stream.fileno())
                assert before==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
                assert hashlib.sha256(raw).hexdigest()==actual['sha256']
                rows.append({'ref':actual,'volume_device_decimal':str(after.st_dev),'file_identity_decimal':str(after.st_ino),'mtime_ns_decimal':str(after.st_mtime_ns),'end_identity_and_bytes_equal':True,'guard':'GENERIC_READ FILE_SHARE_READ only; deny write/delete'})
        finally:
            for stream,_,_ in self.held:stream.close()
        return {'schema':'researchos.finite-source-read-guard.v1','records':rows,'all_handles_closed':all(s.closed for s,_,_ in self.held),'retained_handles':0}

def main():
    guard=Guard();closed=False
    try:
        expected=[(BASE/'HDF.json','cdd7ee41b811dfe1e2ef55841ceed164ee327a7950e2b1c4b94358141f8a46ae',6113),(BASE/'MF.json','fa674c527e6ec1ea28099596aa2ac91580e6d9a199f61f5b3a0b0356ab7b5154',3950),(REVIEW/'HDF.json','f8a66c7d8ef6c29b3663dc180507ffac5ca02671b51dc02a1700636684292d88',3511),(REVIEW/'MF.json','300408433407d99b98828ea449a1e9e4629033477eaf80035e26b6e4935dacda',3859)]
        roots={};source_inputs=[]
        for path,sha,size in expected:
            raw,ref=guard.read(path,{'sha256':sha,'bytes':size})
            label=('base' if path.parent==BASE else 'review')+'_'+path.stem
            roots[label]={'ref':ref,'value':json.loads(raw),'snapshot_ref':save('inputs/'+label+'.json',raw)}
            source_inputs.append(ref)
        members={Path(ref['path']).name:ref for ref in roots['base_MF']['value']['members']}
        for name in ('main23_root.source.py','source_controls.py','source-inputs.json','root-calling-contract.source.json','source-controls.final.json','source-facts.json'):
            raw,ref=guard.read(members[name]['path'],members[name]);source_inputs.append(ref)
            save('inputs/base-'+name,raw)
        members={Path(ref['path']).name:ref for ref in roots['review_MF']['value']['members']}
        for name in ('source-findings.json','source-decision.json','source-controls-actual-fullhostpair.jsonl','source-controls-actual-fullhostpair.binding.json'):
            raw,ref=guard.read(members[name]['path'],members[name]);source_inputs.append(ref)
            save('inputs/review-'+name,raw)
        findings=json.loads((Q/'inputs/review-source-findings.json').read_text(encoding='utf-8'))
        assert pin(Path(members['source-findings.json']['path']),(Q/'inputs/review-source-findings.json').read_bytes())['sha256']=='b2428b3c382e1d84580199dc76b94ab8a93281b589c61751636aeee33ce78b68'
        current=[]
        canonical=[('checkpoint','667f1515a5b62e2d7ee4948bf17055b7f9a0cce6391ad66c76ea70dde99255ba',4533514),('path_ownership','4e294919209b1d65b5f869f613ada3a706a16ccaa8fb194dfca1d8982ddb7d3a',211140),('step_state','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),('commands','28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968)]
        for name,sha,size in canonical:
            raw,ref=guard.read(R/'execution/v2.4'/ (name+'.json'),{'sha256':sha,'bytes':size})
            snapshot=save('inputs/current-'+name+'.json',raw)
            current.append({'original_ref':ref,'snapshot_ref':snapshot,'revision':json.loads(raw).get('revision')})
        saved=savejson('input-discovery.json',{'schema':'researchos.main23-root-v2-input-discovery.v1','authority':'NONE','source_author':'codex:/root/backup_regression_resources','previous_caller_author':roots['base_HDF']['value']['source_author'],'previous_builder_author':roots['base_HDF']['value']['source_author'],'roots':{k:{x:v[x] for x in ('ref','snapshot_ref')} for k,v in roots.items()},'Source_inputs':source_inputs,'current_creation_baseline':current,'blocking_findings':findings['findings'],'future_qualification_ref':None,'future_request_ref':None,'public22_actual_status':'FAIL_PUBLIC_RESTORE_SCHEMA_MISMATCH_NOT_ACCEPTED','Main_writes':0,'Canon_writes':0})
        closure=guard.close();closed=True
        cref=savejson('input-source-guard.closed.json',closure)
        print(json.dumps({'input_ref':saved,'guard_ref':cref,'pins':len(closure['records']),'retained_handles':0,'current_revisions':[x['revision'] for x in current]},ensure_ascii=False))
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()

if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
