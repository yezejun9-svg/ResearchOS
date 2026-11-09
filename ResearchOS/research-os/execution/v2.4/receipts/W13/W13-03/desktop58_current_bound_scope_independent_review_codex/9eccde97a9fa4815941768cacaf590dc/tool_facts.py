from pathlib import Path
import json,re,hashlib
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;U=O.name
P=R/('execution/v2.4/receipts/W13/W13-03/desktop58_root_caller_allocationseventh_source_preparation_codex/'+U+'/original-input.json')
raw=P.read_bytes();o=json.loads(raw);facts=[]
def walk(x):
    if isinstance(x,dict):
        if 'chunk_id' in x and 'output' in x:
            facts.append({'chunk_id':x['chunk_id'],'session_id':x.get('session_id'),'exit_code':x.get('exit_code'),'markers':re.findall(r'ACTUAL_[A-Z_]*EXIT[=:]\s*(-?\d+)',x['output'])})
        for v in x.values():walk(v)
    elif isinstance(x,list):
        for v in x:walk(v)
walk(o['original_tool_observations'])
d={'schema':'researchos.scope7-original-tool-facts.v1','source_ref':{'path':str(P),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'facts':facts,'native_unobserved_is_null':True}
with (O/'tool-facts.json').open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(d,ensure_ascii=False))
