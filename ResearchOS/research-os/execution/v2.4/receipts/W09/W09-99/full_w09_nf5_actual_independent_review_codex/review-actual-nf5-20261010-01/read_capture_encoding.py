import json,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
shapes=json.loads((Q/'G02-Root-capture-shapes.json').read_bytes())
result={}
for stage,item in shapes.items():
    blocks=item['output_value'];docs=[]
    for block in blocks:
        try:value=json.loads(block.get('text',''))
        except(ValueError,TypeError):continue
        if type(value)is dict and'chunk_id'in value:docs.append(value)
    result[stage]=dict(call_input=item['call'].get('input'),tool_result=docs,
        output_prefix_codepoints=[ord(c)for c in docs[0].get('output','')[:18]]if docs else [])
with(Q/'G02-Root-encoding.json').open('xb')as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(result,ensure_ascii=False));print('ROOT_PYTHON_EXIT=0')
