"""Continue only the failed caller text transform; preserve successful core/input pins."""
import ast,copy,difflib,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent
original_builder=(N/'build_caller.py').read_text(encoding='utf-8')
prefix=original_builder[:original_builder.index("source=doc(OLD/'input-pins.json')")]
scope={'__file__':str(N/'build_caller.py'),'__name__':'nf4_caller_continuation'}
exec(compile(prefix,'<original build definitions>','exec'),scope)
def flexible_replace(s,a,b):
 if a not in s and '\r\n' in a:a=a.replace('\r\n','\n')
 assert a in s,('REPLACE_MISSING',a)
 return s.replace(a,b)
scope['replace']=flexible_replace
source=scope['doc'](N/'input-pins.json');pins=source['refs'];scope.update(source=source,pins=pins)
OLD=scope['OLD'];original=(OLD/'adoption_core.source.py').read_bytes().decode('utf-8');candidate=(N/'adoption_core.source.py').read_bytes().decode('utf-8')
edits=[]
for tag,i,j,k,l in difflib.SequenceMatcher(None,original,candidate,autojunk=False).get_opcodes():
 if tag!='equal':edits.append(dict(old_start=i,old_end=j,new_start=k,new_end=l,before=original[i:j],after=candidate[k:l]))
deltas=[dict(file='adoption_core.source.py',base_ref=scope['ref'](OLD/'adoption_core.source.py'),candidate_ref=scope['ref'](N/'adoption_core.source.py'),inverse_edits=edits)]
scope['deltas']=deltas
start=original_builder.index(" original=(OLD/'register_w09_adoption.source.py')")
end=original_builder.index('\nfinally:',start)
body='\n'.join(line[1:] if line.startswith(' ') else line for line in original_builder[start:end].splitlines())
gr=pins['guard'];raw=Path(gr['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==gr['sha256']
gm=types.ModuleType('continuation_guard');gm.__file__=gr['path'];exec(compile(raw,gr['path'],'exec'),gm.__dict__)
g=gm.SourceReadGuard(total_cap=256*1024*1024);g.acquire([scope['ref'](OLD/name) for name in ('register_w09_adoption.source.py','input-pins.json','root-calling-contract.source.json')]+[scope['ref'](N/'adoption_core.source.py'),scope['ref'](N/'input-pins.json')])
try:exec(compile(body,'<bounded caller continuation>','exec'),scope)
finally:
 closed=g.close();scope['put'](N/'source-guard-corrected.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
print(json.dumps(dict(status='NF4_REGISTRATION_SOURCE_BUILT',caller_ref=scope['ref'](N/'register_w09_adoption.source.py'),
 core_ref=scope['ref'](N/'adoption_core.source.py'),contract_ref=scope['ref'](N/'root-calling-contract.source.json')),ensure_ascii=False))

