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
SOURCE=Q.parents[1]/'public22_existing_observation_root_caller_source_codex/recheckroot-20261009-01'
def pin(path,raw):return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value):
    path=Q/name;raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as stream:assert stream.write(raw)==len(raw)
    return pin(path,raw)
class Guard:
    def __init__(self):self.held=[]
    def read(self,path,expected):
        path=Path(path).resolve(strict=True)
        api=ctypes.WinDLL('kernel32',use_last_error=True)
        api.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
        api.CreateFileW.restype=wintypes.HANDLE
        handle=api.CreateFileW(str(path),0x80000000,1,None,3,0x80,None)
        if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
        stream=os.fdopen(msvcrt.open_osfhandle(int(handle),os.O_RDONLY|os.O_BINARY),'rb')
        before=os.fstat(stream.fileno());raw=stream.read();actual=pin(path,raw)
        self.held.append((stream,actual,(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)))
        assert (actual['sha256'],actual['bytes'])==(expected['sha256'],expected['bytes'])
        return raw,actual
    def close(self):
        rows=[]
        try:
            for stream,ref,before in self.held:
                stream.seek(0);raw=stream.read();after=os.fstat(stream.fileno())
                assert before==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
                assert hashlib.sha256(raw).hexdigest()==ref['sha256']
                rows.append({'ref':ref,'volume_device_decimal':str(after.st_dev),'file_identity_decimal':str(after.st_ino),
                    'mtime_ns_decimal':str(after.st_mtime_ns),'end_identity_bytes_equal':True})
        finally:
            for stream,_,_ in self.held:stream.close()
        return {'schema':'researchos.finite-independent-source-guard.v1','records':rows,'all_handles_closed':all(x.closed for x,_,_ in self.held),'retained_handles':0,'live_Canon_handles':0}
def main():
    guard=Guard();closed=False
    try:
        hraw,href=guard.read(SOURCE/'HDF.json',{'sha256':'da51313af844f6db610e38f62da3a46528d94076c5ad903dcf02263dff0f372e','bytes':8609})
        mraw,mref=guard.read(SOURCE/'MF.json',{'sha256':'98c2e1ff235f6831e31d730ccdc73bb8b41d4617b45e545bd5a742d6df498a9c','bytes':19873})
        hdf=json.loads(hraw);mf=json.loads(mraw)
        assert hdf['source_author']!='codex:/root/backup_regression_resources'
        assert hdf['manifest_ref']==mref
        values={}
        for ref in mf['members']:
            raw,actual=guard.read(ref['path'],ref);values[Path(ref['path']).name]=(raw,actual)
        contract=json.loads(values['root-calling-contract.source.json'][0])
        assert values['root-calling-contract.source.json'][1]['sha256']=='50702a4abd0bf487623d334b6eef8068b270d25efe15097ae9f07136ce6821bf'
        item=save('verified-source-basis.index.json',{'schema':'researchos.public22-existing-independent-source-basis.v1',
            'review_author':'codex:/root/backup_regression_resources','source_hdf_ref':href,'source_mf_ref':mref,
            'source_author':hdf['source_author'],'caller_ref':hdf['caller_ref'],'calling_contract_ref':hdf['calling_contract_ref'],
            'members':mf['members'],'HDF_fields':list(hdf),'contract_fields':list(contract),
            'source_json_shapes':{name:{'keys':list(json.loads(raw)),'type':type(json.loads(raw)).__name__} for name,(raw,ref) in values.items() if name in ('source-inputs.json','source-controls.json','identity-and-scope-controls.json','runtime-resources.complete.json','runtime-closure-control.json','source-final-guard.closed.json','source-tool-capture-index.json')},
            'all_member_pins_valid':True,'Source_only':True,'actual_product_calls':None})
        closure=guard.close();closed=True;cref=save('source-basis.guard.closed.json',closure)
        print(json.dumps({'basis_ref':item,'guard_ref':cref,'members':len(mf['members']),
            'member_names':sorted(values),'source_json_shapes':{name:list(json.loads(raw)) for name,(raw,ref) in values.items() if name in ('source-inputs.json','source-controls.json','identity-and-scope-controls.json','runtime-resources.complete.json','runtime-closure-control.json')},'retained_handles':0},ensure_ascii=False))
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()
if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
