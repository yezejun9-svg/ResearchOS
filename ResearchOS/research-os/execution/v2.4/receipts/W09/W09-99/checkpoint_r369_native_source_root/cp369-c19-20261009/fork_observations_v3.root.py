import ast
from pathlib import Path
N=Path(__file__).resolve().parent
old=N/'archive_actual_observations_v2.root.py'
raw=old.read_bytes().decode()
a="""def parsed_outputs(value):
    if isinstance(value,list):
        for x in value:yield from parsed_outputs(x)
    elif isinstance(value,dict) and isinstance(value.get('text'),str):
        try:yield json.loads(value['text'])
        except ValueError:pass
    elif isinstance(value,str):
        try:yield json.loads(value)
        except ValueError:pass
"""
b="""def parsed_outputs(value):
    if isinstance(value,list):
        for x in value:yield from parsed_outputs(x)
    elif isinstance(value,dict):
        if 'chunk_id' in value:yield value
        else:
            for x in value.values():yield from parsed_outputs(x)
    elif isinstance(value,str):
        try:parsed=json.loads(value)
        except ValueError:return
        yield from parsed_outputs(parsed)
"""
assert raw.count(a)==1
new=raw.replace(a,b,1)
ast.parse(new)
with (N/'archive_actual_observations_v3.root.py').open('xb') as f:f.write(new.encode())
print('Forked source with observed nested output protocol; no archive or Native executed.',flush=True)
