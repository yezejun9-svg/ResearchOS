"""Capture exact original mechanical failures; no counter registration."""
import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
S=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def put(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
raw=S.read_bytes();rows=raw.splitlines(keepends=True);parsed=[json.loads(x) for x in rows]
assert parsed[0]['payload']['id']=='01a11e0c-eef6-7363-a5b1-da61d6ae7f4c'
out=[]
for ordinal,chunk,description in ((1140,'950b1e','Exact two-line caller replacement expected CRLF but source did not match; core and input pins preserved.'),
 (1141,'9fecd1','Continuation dedent changed a multiline string replacement indentation; caller not reached; previous successful source preserved.')):
 candidates=[i for i,x in enumerate(parsed) if x.get('type')=='response_item' and x.get('payload',{}).get('type') in ('function_call_output','custom_tool_call_output') and chunk in rows[i].decode('utf-8')]
 assert len(candidates)==1,(chunk,candidates)
 ri=candidates[0];callid=parsed[ri]['payload']['call_id']
 ci=[i for i,x in enumerate(parsed[:ri]) if x.get('type')=='response_item' and x.get('payload',{}).get('type') in ('function_call','custom_tool_call') and x['payload'].get('call_id')==callid]
 assert len(ci)==1
 indices=[0,ci[0],ri];capture=N/('original-'+str(ordinal)+'.raw.jsonl');capture.write_bytes(b''.join(rows[i] for i in indices))
 origin=dict(schema='researchos.Source-original-mechanical-diagnostic.v1',actor_id='codex:/root/attach_restore_independent_review',
 original_ordinal=ordinal,original_tool_chunk=chunk,source_session_id=parsed[0]['payload']['id'],source_audit_path=str(S),
 source_line_indices=indices,source_line_offsets=[sum(map(len,rows[:i])) for i in indices],
 original_line_sha256=[hashlib.sha256(rows[i]).hexdigest() for i in indices],source_prefix_size_observed=len(raw),
 original_capture_ref=ref(capture),actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,
 actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,
 registered_in_current_canon=False,counter_reset=False,automatic_retry=False,description=description)
 op=N/('original-'+str(ordinal)+'.origin.json');put(op,origin)
 binding=N/('original-'+str(ordinal)+'.binding.json')
 put(binding,dict(schema='researchos.Source-original-diagnostic-binding.v1',source_author='codex:/root/attach_restore_independent_review',
 original_ordinal=ordinal,original_origin_ref=ref(op),original_capture_ref=ref(capture),original_bytes_unchanged=True,formal_authority=False))
 out.append(dict(ordinal=ordinal,origin_ref=ref(op),raw_ref=ref(capture),binding_ref=ref(binding)))
put(N/'original-diagnostics.json',out)
print(json.dumps(out,ensure_ascii=False))

