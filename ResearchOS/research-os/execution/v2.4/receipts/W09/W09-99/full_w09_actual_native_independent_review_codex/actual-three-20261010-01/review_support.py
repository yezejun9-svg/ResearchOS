from pathlib import Path
import hashlib,json,types
R=Path(r'D:/作品集/ResearchOS/research-os')
D=Path(__file__).resolve().parent
N=R/'execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_source_codex/fullw09-20261010-03'
S=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
G=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
GREF={'path':str(G),'sha256':'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85','bytes':11404}
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,value):
    p=D/name
    with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
    return pin(p)
def inert(p,raw=None):
    p=Path(p);m=types.ModuleType(p.stem);m.__file__=str(p)
    exec(compile(p.read_bytes() if raw is None else raw,str(p),'exec'),m.__dict__);return m
def guard():
    assert pin(G)==GREF
    return inert(G).SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
def absolute(ref):
    assert type(ref) is dict and set(ref)=={'path','sha256','bytes'}
    p=Path(ref['path']);return {**ref,'path':str(p if p.is_absolute() else R/p)}
def refs(value):
    if type(value) is dict:
        if set(value)=={'path','sha256','bytes'} and type(value.get('bytes')) is int:yield value
        else:
            for v in value.values():yield from refs(v)
    elif type(value) is list:
        for v in value:yield from refs(v)
def shape(v):
    if type(v) is dict:return {'type':'dict','keys':list(v),'preview':{k:vv for k,vv in v.items() if vv is None or type(vv) in (str,int,bool,float)}}
    if type(v) is list:return {'type':'list','len':len(v),'first':[shape(x) for x in v[:2]]}
    return {'type':type(v).__name__,'value':v}
