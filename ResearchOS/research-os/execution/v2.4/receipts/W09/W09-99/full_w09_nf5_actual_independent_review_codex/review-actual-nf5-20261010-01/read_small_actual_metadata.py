import hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def read(ref):
    raw=Path(ref['path']).read_bytes()
    assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256']
    return json.loads(raw)
def main():
    b=json.loads((Q/'actual-input-shapes.json').read_bytes());c=read(b['G02_closed_ref'])
    inv=read(c['summary']['compiler_inventory_ref']);packet=read(c['native_packet_ref'])
    shapes=dict(inventory_keys=list(inv),inventory_collection_shapes={k:dict(type=type(v).__name__,length=len(v),keys=list(v)[:25]if type(v)is dict else None)for k,v in inv.items()if type(v)in(dict,list)},
        packet_keys=list(packet),packet_collection_shapes={k:dict(type=type(v).__name__,length=len(v),keys=list(v)[:25]if type(v)is dict else None)for k,v in packet.items()if type(v)in(dict,list)},
        guard_shapes=[dict(label=row['label'],ref=row['ref'],keys=list(row['observation']),entry_keys=list(row['observation']['entries'][0])if row['observation'].get('entries')else [],entry_count=len(row['observation'].get('entries',[])))for row in c['guard_cleanups']],
        invocation_shapes=[dict(label=row['label'],keys=list(row['record']),result_keys=list(row['record']['result']))for row in c['invocation_observations']])
    root=Path(c['summary']['compiler_inventory_ref']['path']).parent
    for name in ('launcher.closed.json','launcher.started.json'):
        value=json.loads((root/name).read_bytes());shapes[name]=value
    bp=read(read(b['source_hdf_ref'])['compiler_blueprint_ref'])
    shapes['blueprint_keys']=list(bp);shapes['blueprint_collection_shapes']={k:dict(type=type(v).__name__,length=len(v),keys=list(v)[:25]if type(v)is dict else None)for k,v in bp.items()if type(v)in(dict,list)}
    with(Q/'small-actual-metadata.json').open('xb')as f:f.write((json.dumps(shapes,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps({k:v for k,v in shapes.items()if k not in ('launcher.started.json',)},ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
