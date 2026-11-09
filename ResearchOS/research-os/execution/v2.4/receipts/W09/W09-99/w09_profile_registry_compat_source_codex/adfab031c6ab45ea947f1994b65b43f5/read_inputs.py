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
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W09/W09-99'

def pin(path,raw):
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

class Guard:
    def __init__(self):
        self.held=[]
    def read(self,path,expected=None):
        path=Path(path).resolve(strict=True)
        api=ctypes.WinDLL('kernel32',use_last_error=True)
        api.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
        api.CreateFileW.restype=wintypes.HANDLE
        handle=api.CreateFileW(str(path),0x80000000,1,None,3,0x80,None)
        if handle==ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        stream=os.fdopen(msvcrt.open_osfhandle(int(handle),os.O_RDONLY|os.O_BINARY),'rb')
        before=os.fstat(stream.fileno())
        raw=stream.read()
        actual=pin(path,raw)
        self.held.append((stream,actual,(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)))
        if expected is not None:
            assert (actual['sha256'],actual['bytes'])==(expected['sha256'].removeprefix('sha256:'),expected['bytes']),'source pin differs: '+str(path)
        return raw,actual
    def close(self):
        rows=[]
        try:
            for stream,actual,before in self.held:
                stream.seek(0)
                raw=stream.read()
                after=os.fstat(stream.fileno())
                assert before==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
                assert hashlib.sha256(raw).hexdigest()==actual['sha256']
                rows.append({'ref':actual,'volume_device_decimal':str(after.st_dev),'file_identity_decimal':str(after.st_ino),'mtime_ns_decimal':str(after.st_mtime_ns),'end_identity_and_bytes_equal':True,'guard':'GENERIC_READ FILE_SHARE_READ only; deny write/delete'})
        finally:
            for stream,actual,before in self.held:
                stream.close()
        return {'schema':'researchos.finite-source-read-guard.v1','records':rows,'all_handles_closed':all(stream.closed for stream,_,_ in self.held),'retained_handles':0}

def save(name,raw):
    path=Q/name
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:
        assert stream.write(raw)==len(raw)
    return pin(path,raw)

def savejson(name,value):
    return save(name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))

def main():
    guard=Guard()
    finished=False
    try:
        gapbase=B/'full_w09_native_gap_source_review_codex'
        hraw,href=guard.read(gapbase/'HDF.json')
        hdf=json.loads(hraw)
        mraw,mref=guard.read(hdf['manifest_ref']['path'],hdf['manifest_ref'])
        mf=json.loads(mraw)
        graw,gref=guard.read(hdf['source_gap_report_ref']['path'],hdf['source_gap_report_ref'])
        assert (gref['sha256'],gref['bytes'])==('9b7bb0a54314560e285f5245d95d0ce44cb5c2510c31ef5bff3996f1602e93e5',73083)
        gap=json.loads(graw)
        save('inputs/Source-gap-report.json',graw)
        before={}
        for label in ('Main_formal_case_index','Main_formal_profile','Main_router','CM39','frozen_plan','frozen_acceptance','C19_reusable_actual_decision','C19_actual_mode_actor_evidence','registration_mechanism_reference','registration_contract_reference'):
            ref=mf['source_input_refs'][label]
            raw,actual=guard.read(ref['path'],ref)
            name={'Main_formal_profile':'formal_profile_w09.before.py','Main_formal_case_index':'formal_case_index.before.py','CM39':'commands.CM39.before.json'}.get(label,label+Path(ref['path']).suffix)
            snapshot=save('inputs/'+name,raw)
            before[label]={'original_ref':actual,'snapshot_ref':snapshot}
        v4base=B/'w09_formal_profile_v4_source_codex/profv4-01a12c10'
        vraw,vref=guard.read(v4base/'HDF.json')
        vhdf=json.loads(vraw)
        vmraw,vmref=guard.read(vhdf['manifest_ref']['path'],vhdf['manifest_ref'])
        vmf=json.loads(vmraw)
        for label,path in [('v4_controls',v4base/'source_controls_v4.py'),('v4_contract',v4base/'source-contract.json')]:
            ref=next(x for x in vmf['members'] if Path(x['path']).name==path.name)
            raw,actual=guard.read(path,ref)
            before[label]={'original_ref':actual,'snapshot_ref':save('inputs/'+path.name,raw)}
        goalpath=Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/08_AGENT_EXECUTION_GOAL.md')
        raw,actual=guard.read(goalpath)
        before['frozen_goal']={'original_ref':actual,'snapshot_ref':save('inputs/frozen-08_AGENT_EXECUTION_GOAL.md',raw)}
        report={'schema':'researchos.w09-profile-compatibility-input-discovery.v1','authority':'NONE','gap_HDF_ref':href,'gap_MF_ref':mref,'gap_report_ref':gref,'v4_HDF_ref':vref,'v4_MF_ref':vmref,'current_before':before,'gap_top_level_keys':sorted(gap),'gap_input_refs':mf['source_input_refs']}
        result_ref=savejson('input-discovery.json',report)
        closed=guard.close();finished=True
        guard_ref=savejson('input-source-guard.closed.json',closed)
        print(json.dumps({'result_ref':result_ref,'guard_ref':guard_ref,'gap_top_level_keys':sorted(gap),'current_before':before,'gap_summary_fields':{k:v for k,v in gap.items() if not isinstance(v,(dict,list))}},ensure_ascii=False))
    finally:
        if not finished:
            for stream,_,_ in guard.held:
                stream.close()

if __name__=='__main__':
    code=0
    try:
        main()
    except Exception:
        traceback.print_exc()
        code=1
    print('ROOT_PYTHON_EXIT='+str(code))
    sys.exit(code)
