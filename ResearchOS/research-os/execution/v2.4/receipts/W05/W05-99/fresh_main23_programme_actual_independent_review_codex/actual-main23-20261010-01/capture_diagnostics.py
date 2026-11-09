from pathlib import Path
import json,hashlib
N=Path(__file__).resolve().parent
P=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
targets={'8cdcf5':1068,'5cf215':1069,'37effd':1070};calls={};found={}
def pin(p):
 v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
with P.open('rb') as f:
 header=f.readline();offset=len(header)
 for raw in f:
  row=json.loads(raw);p=row.get('payload',{});cid=p.get('call_id')
  if cid and p.get('type') in ('function_call','custom_tool_call'):calls[cid]=(offset,raw)
  if cid and p.get('type') in ('function_call_output','custom_tool_call_output'):
   output=str(p.get('output',''))
   for chunk in targets:
    if '"chunk_id":"'+chunk+'"' in output or '"chunk_id": "'+chunk+'"' in output or 'Chunk ID: '+chunk in output:
     found[chunk]=(calls[cid],(offset,raw),cid)
  offset+=len(raw)
assert set(found)==set(targets),(set(found),set(targets))
out=[]
for chunk,((a,ar),(b,br),cid) in found.items():
 rawp=N/('failure-'+chunk+'.actual-host.raw.jsonl')
 with rawp.open('xb') as f:f.write(header+ar+br)
 binding=dict(schema='researchos.actual-tool-source-binding.v1',review_actor='codex:/root/attach_fixture_source_review',original_failure_ordinal=targets[chunk],original_capture_ref=pin(rawp),source_audit_path=str(P),source_prefix_size_observed=offset,source_line_offsets=[0,a,b],source_line_bytes=[len(header),len(ar),len(br)],original_line_sha256=[hashlib.sha256(v).hexdigest() for v in [header,ar,br]],original_call_id=cid,outer_exit=0 if chunk=='37effd' else 1,python_exit=None,rg_exit=None,product_exit=None,formal_acceptance=False)
 bp=N/('failure-'+chunk+'.actual-host.binding.json')
 with bp.open('xb') as f:f.write((json.dumps(binding,ensure_ascii=False,indent=2)+'\n').encode())
 out.append(dict(chunk=chunk,ordinal=targets[chunk],raw_ref=pin(rawp),binding_ref=pin(bp)))
print(json.dumps(out,ensure_ascii=False),flush=True)
