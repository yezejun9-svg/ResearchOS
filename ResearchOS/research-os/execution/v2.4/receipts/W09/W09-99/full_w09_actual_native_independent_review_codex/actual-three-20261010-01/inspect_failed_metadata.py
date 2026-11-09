from pathlib import Path
import types,json
p=Path(__file__).with_name('review_support.py');m=types.ModuleType('support');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
runs={'W09-G02':('28aa266121d24ad2988d578df02d23a4','bac1a29d879b51f5b47d8536929b4cc03b2e55241692223f0d14311475b70982',1692205),'A06':('ba9a185f551c4d4caf123da7eafb4245','56f55efd19445dd39aced5291e0c65a1562e47ad9c6a6bf3bcc6b5ec113eb8d1',1690610)}
claims=[];docs={}
for selector,(run,digest,size) in runs.items():
    P=m.N/('actual-'+selector+'-'+run)/'producer';ref={'path':str(P/'validation.closed.json'),'sha256':digest,'bytes':size};v=json.loads(Path(ref['path']).read_bytes());docs[selector]=v
    claims.extend([ref,*v['invocation_refs'],*[x['ref'] for x in v['guard_cleanups']]])
    if v.get('native_packet_ref'):claims.append(v['native_packet_ref'])
    for name in ('actual-compiler-input-inventory.json',):claims.append(m.pin(P/name))
    claims.append(m.pin(P.parent/'prepare.ready.json'))
g=m.guard();out={}
try:
    g.acquire(claims)
    for selector,(run,_,_) in runs.items():
        P=m.N/('actual-'+selector+'-'+run)/'producer';v=json.loads(g.get_buffer(str(P/'validation.closed.json')))
        documents={r['path']:json.loads(g.get_buffer(r['path'])) for r in claims if ('actual-'+selector+'-'+run) in r['path']}
        packet=documents[v['native_packet_ref']['path']] if v.get('native_packet_ref') else None
        out[selector]={'run_id':run,'validation_shape':{k:m.shape(vv) for k,vv in v.items()},'packet_shape':{k:m.shape(vv) for k,vv in (packet or {}).items()},'refs':list(m.refs(documents))}
    outref=m.write('failed-selectors.metadata.json',out)
    print(json.dumps({'metadata_ref':outref,'selectors':{s:{'validation_shape':v['validation_shape'],'packet_shape':v['packet_shape'],'discovered_refs':len(v['refs'])} for s,v in out.items()}},ensure_ascii=False),flush=True)
finally:
    c=g.close();ref=m.write('failed-selectors.metadata.guard.closed.json',c);print(json.dumps({'guard_ref':ref,'closed':c['closed'],'retained_handles_count':c['retained_handles_count']},ensure_ascii=False),flush=True)
