from pathlib import Path
import json,hashlib
N=Path(__file__).parent
S=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v,raw=False):
 p=N/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def values(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from values(x)
 elif isinstance(v,list):
  for x in v:yield from values(x)
 elif isinstance(v,str):
  try:x=json.loads(v)
  except (ValueError,TypeError):return
  if not isinstance(x,str):yield from values(x)
prefix=S.stat().st_size;start=max(0,prefix-32*1024*1024);calls={};found={}
with S.open('rb') as f:
 h=f.readline();f.seek(start)
 if start:f.readline()
 while f.tell()<prefix:
  off=f.tell();line=f.readline()
  if not line or f.tell()>prefix:break
  try:v=json.loads(line)
  except ValueError:continue
  p=v.get('payload',{});t=p.get('type');cid=p.get('call_id')
  if t in ('function_call','custom_tool_call'):calls[cid]=(off,line)
  if t not in ('function_call_output','custom_tool_call_output') or cid not in calls:continue
  for d in values(p.get('output')):
   chunk=d.get('chunk_id')
   if chunk not in ('a27c9f','81ce7e') or chunk in found:continue
   if d.get('exit_code')!=1:continue
   call=calls[cid]
   # Original operation, not later evidence replication.
   text=json.loads(call[1]).get('payload',{})
   inp=str(text.get('input',text.get('arguments','')))
   if 'capture_originals.py' in inp or 'original-' in inp:continue
   found[chunk]=(cid,call,(off,line),d)
out=[]
for chunk,ordinal in [('a27c9f',1227),('81ce7e',1228)]:
 cid,call,result,d=found[chunk];rows=[(0,h),call,result]
 raw=save('diagnostic-appendix/original-'+str(ordinal)+'.raw.jsonl',b''.join(x[1] for x in rows),True)
 out.append(save('diagnostic-appendix/original-'+str(ordinal)+'.binding.json',dict(
  Root_assigned_ordinal=ordinal,source_audit_path=str(S),source_prefix_size=prefix,finite_tail_start=start,
  source_line_offsets=[x[0] for x in rows],source_line_bytes=[len(x[1]) for x in rows],
  source_line_sha256=[hashlib.sha256(x[1]).hexdigest() for x in rows],original_call_id=cid,
  original_capture_ref=raw,original_result=d,outer_exit=1,Python_exit=None,Native_exit=None,
  SQL_exit=None,non_product_diagnostic=True,successful_prefix_preserved=True,original_not_rerun=True)))
print(json.dumps(dict(status='TWO_ORIGINALS_CAPTURED',bindings=out),ensure_ascii=False))

