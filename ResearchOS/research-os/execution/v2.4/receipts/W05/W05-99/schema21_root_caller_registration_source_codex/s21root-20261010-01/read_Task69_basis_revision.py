from __future__ import annotations
import ast, ctypes, hashlib, json, msvcrt, os, sys
from ctypes import wintypes
from pathlib import Path
Q=Path(__file__).resolve().parent
B=Q.parent.parent
M4=B/'fresh_main23_root_caller_registration_source_codex/main23root-20261010-04'
S=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009')
def pin(path,raw=None):
    path=Path(path)
    if raw is None:raw=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    p=Q/name
    with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
class Guard:
    def __init__(self):self.held=[]
    def read(self,path,expected):
        path=Path(path).resolve(strict=True);api=ctypes.WinDLL('kernel32',use_last_error=True)
        api.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
        api.CreateFileW.restype=wintypes.HANDLE
        handle=api.CreateFileW(str(path),0x80000000,1,None,3,0x80,None)
        if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
        stream=os.fdopen(msvcrt.open_osfhandle(int(handle),os.O_RDONLY|os.O_BINARY),'rb');before=os.fstat(stream.fileno());raw=stream.read();actual=pin(path,raw)
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
                rows.append(dict(ref=ref,volume_device_decimal=str(after.st_dev),file_identity_decimal=str(after.st_ino),mtime_ns_decimal=str(after.st_mtime_ns),end_identity_bytes_equal=True))
        finally:
            for stream,_,_ in self.held:stream.close()
        return dict(schema='researchos.finite-source-guard.v1',records=rows,all_handles_closed=all(x.closed for x,_,_ in self.held),retained_handles=0,live_Canon_handles=0)
def main():
    guard=Guard();closed=False;refs=[]
    def hold(ref):
        raw,actual=guard.read(ref['path'],ref);refs.append(actual);return raw
    try:
        hold(dict(path=sys.executable,sha256='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b',bytes=106328))
        href=dict(path=str(M4/'HDF.json'),sha256='348034a2f2f23342f6a309ed14ffe64183a3bbb031ed79d6c8ed5facf34c0fd3',bytes=32853)
        mref=dict(path=str(M4/'MF.json'),sha256='dd65dabdff33ccc10b229222992cf7db5702837c60cd7ed565769248c09e88c1',bytes=22750)
        h=json.loads(hold(href));mf=json.loads(hold(mref));assert h['manifest_ref']==mref
        keys=('caller_ref','contract_ref','inverse_ref','finite37_controls_ref')
        for key in keys:
            assert any(x==h[key] for x in mf['members']);hold(h[key])
        archive=[]
        for key,rev in [('checkpoint',373),('path_ownership',177),('step_state',None),('commands',39)]:
            p=S/('historical.cp373.'+key+'.json');ref=pin(p);value=json.loads(hold(ref));assert value.get('revision')==rev
            archive.append(dict(key=key,revision=rev,snapshot_ref=ref))
        native=B/'schema21_programme_builder_source_codex/main21b-20261010-01'
        nhref=dict(path=str(native/'HDF.json'),sha256='355407c30d1d0081a5fac90d32e8c7c47f95ddb0d56681768d8688bf2684ef84',bytes=3255)
        nmref=dict(path=str(native/'MF.json'),sha256='6e40bbe378edf370ac8cb870f581d76cd8b48b3c127534855068787c66188069',bytes=103057)
        nh=json.loads(hold(nhref));nm=json.loads(hold(nmref));assert nh['manifest_ref']==nmref
        for key in ('builder_ref','contract_ref','input_manifest_ref','frozen_source_manifest_ref'):
            assert any(x==nh[key] for x in nm['members']);hold(nh[key])
        contract=json.loads(hold(nh['contract_ref']))
        basis=save('source-inputs.basis.json',dict(schema='researchos.old21-caller-basis.v1',source_author='codex:/root/backup_regression_resources',M4_base_hdf_ref=href,M4_base_mf_ref=mref,M4_caller_ref=h['caller_ref'],M4_contract_ref=h['contract_ref'],M4_inverse_ref=h['inverse_ref'],M4_controls37_ref=h['finite37_controls_ref'],builder_source_hdf_ref=nhref,builder_source_mf_ref=nmref,builder_source_refs={k:nh[k] for k in ('builder_ref','contract_ref','input_manifest_ref','frozen_source_manifest_ref')},builder_contract_fields=list(contract),historical_cp373_full4=archive,references=refs,Root_Task69_declared_M4_protocol_Sourceaccepted=True,actual_future_Source_qualification=None,actual_future_RootScope=None,actual_future_lease=None,actual_future_current4=None,authority='NONE',live_Canon_read=False))
        closure=guard.close();closed=True;closedref=save('basis-input.guard.closed.json',closure)
        print(json.dumps(dict(basis_ref=basis,guard_ref=closedref,builder_contract_fields=list(contract),retained_handles=0,live_Canon_handles=0),ensure_ascii=False),flush=True)
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1',flush=True);raise
    print('ROOT_PYTHON_EXIT=0',flush=True)
