import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
import traceback
Q=Path(__file__).resolve().parent
P=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
def main():
    targets=('eb048f','2ae9b6','dff41a','265878','78003d','7859b8')
    rows=[];tail=[];size=P.stat().st_size
    with P.open('rb') as stream:
        header=json.loads(stream.readline())
        while stream.tell()<size:
            offset=stream.tell();raw=stream.readline()
            if offset+len(raw)>size:break
            row=json.loads(raw);payload=row.get('payload');text=raw.decode('utf-8')
            if row.get('type')=='response_item' and type(payload) is dict:
                tail.append({'ordinal':row.get('ordinal'),'type':payload.get('type'),'name':payload.get('name'),'call_id':payload.get('call_id'),'keys':list(payload)})
                tail=tail[-8:]
            if row.get('type')=='response_item' and type(payload) is dict and payload.get('type') in ('custom_tool_call_output','function_call_output') and any(t in text for t in targets):
                value=payload.get('output')
                rows.append({'offset':offset,'ordinal':row.get('ordinal'),'payload_keys':list(payload),
                    'output_type':type(value).__name__,'output_shape':list(value) if type(value) is dict else [type(x).__name__ for x in value] if type(value) is list else None,
                    'public_output_preview':str(value)[:1500],'preceding_response_shapes':list(tail)})
    data={'schema':'researchos.owned-source-audit-shape.v1','header_type':header.get('type'),'header_payload_keys':list(header.get('payload',{})),
        'header_id':header.get('payload',{}).get('id'),'source_prefix_size_observed':size,'matched_output_rows':rows}
    with (Q/'owned-source-audit-shape.json').open('x',encoding='utf-8') as s:json.dump(data,s,ensure_ascii=False,indent=2);s.write('\n')
    print(json.dumps(data,ensure_ascii=False))
if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
