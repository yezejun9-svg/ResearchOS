from pathlib import Path
import types,json
p=Path(__file__).with_name('review_support.py');m=types.ModuleType('support');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
P=m.N/'actual-W09-G01-4fd62ca511684dc39d62c5571d8ddaf5/producer'
v=json.loads((P/'validation.closed.json').read_bytes());h=json.loads((m.N/'HDF.json').read_bytes());a=json.loads((m.S/'w09.G01-native-run-final.actual-audit.root.json').read_bytes())
initial=[v['request_ref'],*v['invocation_refs'],*[x['ref'] for x in v['guard_cleanups']],h['source_choice_ref'],h['compiler_blueprint_ref'],h['manifest_ref'],a['original_capture_ref']]
g=m.guard();docs={}
try:
    g.acquire(initial)
    for ref in initial:
        raw=g.get_buffer(ref['path'])
        if Path(ref['path']).suffix=='.json':docs[ref['path']]=json.loads(raw)
    observations={Path(k).name:{key:m.shape(value) for key,value in doc.items()} for k,doc in docs.items()}
    lead=list(initial)
    for doc in docs.values():
        lead.extend(m.refs(doc))
    vraw=json.loads((P/'actual-compiler-input-inventory.json').read_bytes());packet=json.loads((P/'native-packet.public-index.json').read_bytes())
    lead.extend(m.refs(vraw));lead.extend(m.refs(packet));lead.extend(m.refs(v['summary']))
    lead.extend(m.refs(json.loads((P.parent/'prepare.ready.json').read_bytes()).get('summary')))
    unique={}
    excluded=[]
    live={str(m.R/'execution/v2.4/checkpoint.json'),str(m.R/'execution/v2.4/path_ownership.json'),str(m.R/'execution/v2.4/step_state.json'),str(m.R/'execution/v2.4/commands.json')}
    for ref in lead:
        ref=m.absolute(ref)
        if ref['path'] in live:excluded.append(ref);continue
        old=unique.get(ref['path']);assert old is None or old==ref
        unique[ref['path']]=ref
    out=m.write('G01.discovered-closure.json',{'shapes':observations,'references':list(unique.values()),'excluded_live_Canon':excluded,'Source_controls_repeated':False})
    print(json.dumps({'closure_ref':out,'refs':len(unique),'unique_bytes':sum(x['bytes'] for x in unique.values()),'shapes':{k:value for k,value in observations.items() if k in ['native.request.W09-G01.json','source.choice.json','compiler-source-blueprint.json','MF.json','w09-selector-main-producer.invocation.json']}},ensure_ascii=False),flush=True)
finally:
    closed=g.close();ref=m.write('G01.discovery.guard.closed.json',closed)
    print(json.dumps({'guard_ref':ref,'closed':closed['closed'],'retained_handles_count':closed['retained_handles_count']},ensure_ascii=False),flush=True)
