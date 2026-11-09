import hashlib,json
from pathlib import Path
Q=Path(__file__).resolve().parent
audit=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
try:
    calls=[];outputs={};offset=0
    with audit.open('rb') as f:
        for line in f:
            row=json.loads(line);p=row.get('payload',{})
            if type(p) is dict:
                typ=p.get('type');cid=p.get('call_id')
                if typ in ('function_call','custom_tool_call') and 'store("task91_actual_controls_revision_patch_input",patch)' in str(p.get('input',p.get('arguments',''))):calls.append(dict(call_id=cid,offset=offset,row_type=row['type'],payload_type=typ,line_sha256=hashlib.sha256(line).hexdigest()))
                if cid and typ in ('function_call_output','custom_tool_call_output'):outputs[cid]=dict(offset=offset,row_type=row['type'],payload_type=typ,output=p.get('output'),line_sha256=hashlib.sha256(line).hexdigest())
            offset+=len(line)
    result=[dict(call=x,actual_return=outputs.get(x['call_id'])) for x in calls]
    with (Q/'actual-tool-rejection-discovery.json').open('xb') as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(result,ensure_ascii=False))
except BaseException:
    print('ROOT_PYTHON_EXIT=1',flush=True);raise
else:print('ROOT_PYTHON_EXIT=0',flush=True)
