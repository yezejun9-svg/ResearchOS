from __future__ import annotations
import ctypes, hashlib, json, msvcrt, os, sys
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
undefined
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
            if key=='checkpoint':assert value['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
            if key=='path_ownership':assert value['active_integrator']['id']=='codex:/root'
            archive.append(dict(key=key,revision=rev,snapshot_ref=ref))
        basis=save('source-inputs.basis.json',dict(schema='researchos.old21-caller-basis.v1',source_author='codex:/root/backup_regression_resources',M4_base_hdf_ref=href,M4_base_mf_ref=mref,M4_caller_ref=h['caller_ref'],M4_contract_ref=h['contract_ref'],M4_inverse_ref=h['inverse_ref'],M4_controls37_ref=h['finite37_controls_ref'],historical_cp373_full4=archive,references=refs,Root_Task69_declared_M4_protocol_Sourceaccepted=True,actual_future_Source_qualification=None,actual_future_RootScope=None,actual_future_lease=None,actual_future_current4=None,authority='NONE',live_Canon_read=False))
        closure=guard.close();closed=True;closedref=save('basis-input.guard.closed.json',closure)
        print(json.dumps(dict(basis_ref=basis,guard_ref=closedref,archive_revisions=[373,177,None,39],retained_handles=0,live_Canon_handles=0),ensure_ascii=False),flush=True)
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1',flush=True);raise
    print('ROOT_PYTHON_EXIT=0',flush=True)

