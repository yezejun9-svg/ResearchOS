import hashlib,json,sys
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
Q=Path(__file__).resolve().parent
W=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.public22-main23-continuation-source.actual-audit.root.json'
w=json.loads(W.read_bytes())
raw=Path(w['original_capture_ref']['path']).read_bytes()
final=json.loads(raw.splitlines()[2])
text='\n'.join(v['text']for v in final['payload']['content']if v['type']=='input_text')
marker='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/attach_restore_independent_review\nPayload:\n'
doc=json.loads(text[len(marker):]if text.startswith(marker)else text)
def refs(v):
    if type(v)is dict:
        if set(v)=={'path','sha256','bytes'}:yield v
        for child in v.values():yield from refs(child)
    elif type(v)is list:
        for child in v:yield from refs(child)
result=dict(schema='researchos.actual-source-Final-field-observation.v1',actual_final_top_keys=list(doc),exact_published_refs=list(refs(doc)),Root_witness_contract_binding=w['binding_sha256'],raw_ref=w['original_capture_ref'])
p=Q/'actual-author-Final-field-observation.json'
with p.open('xb')as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(result,ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0')
