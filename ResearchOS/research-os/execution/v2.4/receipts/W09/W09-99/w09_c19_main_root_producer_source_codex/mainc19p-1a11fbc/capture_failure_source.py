"""Preserve one exact original tool call/output from this worker's known session."""
import hashlib
import json
from pathlib import Path

N=Path(__file__).resolve().parent
session=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-37-14-01a11025-2db1-79b3-8271-ef21135931f2.jsonl')
rows=[]
for line in session.read_text(encoding='utf-8').splitlines():
    row=json.loads(line);p=row.get('payload',{})
    if row.get('type')=='response_item' and p.get('type') in ('custom_tool_call','custom_tool_call_output','function_call','function_call_output'):
        rows.append(row)
matches=[r for r in rows if r['payload']['type'] in ('custom_tool_call_output','function_call_output')
         and 'b2f026' in str(r['payload'].get('output',''))]
assert len(matches)==1, 'EXACT_ORIGINAL_OUTPUT_REQUIRED'
output=matches[0];call_id=output['payload']['call_id']
calls=[r for r in rows if r['payload'].get('call_id')==call_id and r['payload']['type'] in ('custom_tool_call','function_call')]
assert len(calls)==1, 'EXACT_ORIGINAL_CALL_REQUIRED'
value=dict(schema='researchos.original-tool-failure-exact-pair.v1',root_assigned_ordinal=952,
           original_chunk_id='b2f026',outer_exit=1,SourcePython_exit=None,Go_exit=None,Native_exit=None,Model_exit=None,
           full_original_call=calls[0],full_original_output=output,complete_original_pair=True,
           cause='Last Get-Content queried absent old Mainv2 seal_source.py; prior reads succeeded; no mutation or execution.',
           root_live_after_assignment=953,counter_reset=False)
raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
p=N/'failure952.original-tool-io.json'
with p.open('xb') as f:f.write(raw)
print(json.dumps(dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),root_assigned_ordinal=952)))
