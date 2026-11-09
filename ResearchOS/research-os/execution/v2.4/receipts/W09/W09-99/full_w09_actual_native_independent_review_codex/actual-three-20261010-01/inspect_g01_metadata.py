from pathlib import Path
import types,json
p=Path(__file__).with_name('review_support.py');m=types.ModuleType('support');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
P=m.N/'actual-W09-G01-4fd62ca511684dc39d62c5571d8ddaf5/producer'
claims=[m.GREF,m.pin(P/'validation.closed.json'),m.pin(P/'native-packet.public-index.json'),
        {'path':str(P/'actual-compiler-input-inventory.json'),'sha256':'a009c52277f0ba1a72ad931eb1c52d591a4a4f88cc35e40025852128e68be07d','bytes':1042666},
        {'path':str(P/'launcher.permit.json'),'sha256':'f70637596b3a547556d1920a16709964a8a26af9501fb2d33e3b91d9673ddb8e','bytes':2885},
        {'path':str(P.parent/'prepare.ready.json'),'sha256':'4d6b283e3c55da7aec5d4b5140f7c22f334da45729f505f35357e3ff1d2cc1da','bytes':1525043},
        {'path':str(m.N/'HDF.json'),'sha256':'0b3000c9ca1d46a1df980535dfb0e57c55798d7eb5d7819c09dcab792168a447','bytes':8412},
        {'path':str(m.S/'w09.G01-native-run-final.actual-audit.root.json'),'sha256':'3db1013df8c18b6a80aba8f54d937d9a645025801f2e7c3565750cd6f5d2825c','bytes':1087}]
g=m.guard();obs={}
try:
    g.acquire(claims)
    for ref in claims[1:]:
        doc=json.loads(g.get_buffer(ref['path']));obs[Path(ref['path']).name]={'ref':ref,'shape':{k:m.shape(v) for k,v in doc.items()}}
    out=m.write('G01.metadata-shapes.json',obs)
    print(json.dumps({'metadata_ref':out,'shapes':obs},ensure_ascii=False),flush=True)
finally:
    closed=g.close();ref=m.write('G01.metadata.guard.closed.json',closed)
    print(json.dumps({'guard_ref':ref,'closed':closed['closed'],'retained_handles_count':closed['retained_handles_count']},ensure_ascii=False),flush=True)
