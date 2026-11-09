from pathlib import Path
import json,hashlib,sys,re
N=Path(__file__).resolve().parent
P=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
targets=sys.argv[1].split(',');calls={};found={}
def pin(p):
 v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def candidates(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from candidates(v)
 elif isinstance(x,list):
  for v in x:yield from candidates(v)
 elif isinstance(x,str):
  try:v=json.loads(x)
  except (ValueError,TypeError):return
  if not isinstance(v,str):yield from candidates(v)
with P.open('rb') as f:
 header=f.readline();offset=len(header)
 for raw in f:
  row=json.loads(raw);p=row.get('payload',{});cid=p.get('call_id')
  if cid and p.get('type') in ('function_call','custom_tool_call'):calls[cid]=(offset,raw)
  if cid and p.get('type') in ('function_call_output','custom_tool_call_output'):
   for observed in candidates(p.get('output',[])):
    chunk=observed.get('chunk_id')
    if chunk in targets:found[chunk]=(calls[cid],(offset,raw),cid,observed)
  offset+=len(raw)
assert set(found)==set(targets),(set(found),set(targets))
out=[]
for chunk in targets:
 (a,ar),(b,br),cid,observed=found[chunk];rawp=N/('review-'+chunk+'.actual-host.raw.jsonl')
 with rawp.open('xb') as f:f.write(header+ar+br)
 markers=re.findall(r'ROOT_SOURCE_PYTHON_EXIT=(\d+)',observed.get('output',''))
 binding=dict(schema='researchos.actual-tool-source-binding.v1',review_actor='codex:/root/attach_fixture_source_review',original_capture_ref=pin(rawp),source_audit_path=str(P),source_prefix_size_observed=offset,source_line_offsets=[0,a,b],source_line_bytes=[len(header),len(ar),len(br)],original_line_sha256=[hashlib.sha256(v).hexdigest() for v in [header,ar,br]],original_call_id=cid,actual_chunk_id=chunk,outer_exit=observed.get('exit_code'),actual_session_id=observed.get('session_id'),python_exit=int(markers[-1]) if markers else None,formal_acceptance=False)
 bp=N/('review-'+chunk+'.actual-host.binding.json')
 with bp.open('xb') as f:f.write((json.dumps(binding,ensure_ascii=False,indent=2)+'\n').encode())
 out.append(dict(chunk=chunk,raw_ref=pin(rawp),binding_ref=pin(bp)))
print(json.dumps(out,ensure_ascii=False),flush=True);print('ROOT_SOURCE_PYTHON_EXIT=0',flush=True)
