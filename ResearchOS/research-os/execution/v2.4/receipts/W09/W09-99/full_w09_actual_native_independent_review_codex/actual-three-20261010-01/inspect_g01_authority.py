from pathlib import Path
import types,json
p=Path(__file__).with_name('review_support.py');m=types.ModuleType('support');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
P=m.N/'actual-W09-G01-4fd62ca511684dc39d62c5571d8ddaf5/producer'
request=json.loads((m.R/'execution/v2.4/receipts/W09/W09-99/w09_profile_nf3_root_adoption_root/646e71a406c74abda1990f72fb0a34e6/native.request.W09-G01.json').read_bytes())
lead=[request['scope_ref'],request['canonical_vector_ref'],request['scope_audit_ref']]
g=m.guard();out={}
try:
    g.acquire(lead)
    for ref in lead:out[Path(ref['path']).name]=json.loads(g.get_buffer(ref['path']))
    observed=m.write('G01.authority-observation.json',out)
    print(json.dumps({'observation_ref':observed,'documents':out},ensure_ascii=False),flush=True)
finally:
    c=g.close();ref=m.write('G01.authority.guard.closed.json',c)
    print(json.dumps({'guard_ref':ref,'closed':c['closed'],'retained_handles_count':c['retained_handles_count']},ensure_ascii=False),flush=True)
