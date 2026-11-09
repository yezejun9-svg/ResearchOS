import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,value):
 with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
source=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
calls={};found={}
with source.open('r',encoding='utf-8') as f:
 for ordinal,line in enumerate(f):
  item=json.loads(line);p=item.get('payload',{});cid=p.get('call_id')
  if item.get('type')!='response_item' or not cid:continue
  if p.get('type') in ('function_call','custom_tool_call'):calls[cid]=(ordinal,line,item)
  if p.get('type') not in ('function_call_output','custom_tool_call_output'):continue
  out=p.get('output','');out=out if isinstance(out,str) else json.dumps(out)
  for chunk,needle in [('85cd9f','Cannot find path'),('e11ae4','PYTHON_EXIT=0')]:
   if chunk in out and needle in out and chunk not in found:
    prior=calls[cid];found[chunk]=dict(source_path=str(source),call_ordinal=prior[0],output_ordinal=ordinal,original_call_event=prior[2],original_output_event=item,original_call_line=prior[1],original_output_line=line)
assert set(found)=={'85cd9f','e11ae4'},set(found)
failure=save('failure-85cd9f.original-tool-io.json',found['85cd9f'])
run=save('review-e11ae4.original-tool-io.json',found['e11ae4'])
ledger=save('failure-ledger.json',dict(original_failure_ordinal=990,next_failure_ordinal=991,chunk_id='85cd9f',outer_exit=1,python_exit=None,native_exit=None,dispatcher_exit=None,original_tool_io_ref=failure,reason='Reviewer read path omitted research-os layer; no write or child runner.',preserved=True))
d=json.loads((N/'source-decision.json').read_bytes());g=json.loads(Path(d['actual_SourceGuard_ref']['path']).read_bytes())
assert d['decision']=='REQUEST_CHANGES' and g['closed'] is True and g['retained_handles_count']==0 and not g['errors']
for ref in g['entries']:
 assert pin(ref['path'])=={k:ref[k] for k in ('path','sha256','bytes')}
assert not Path('D:/作品集/ResearchOS/research-os/execution/v2.4/formal_profile_w09.py').exists()
mf=save('MF.json',dict(schema='researchos.adopter-independent-source-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
hdf=save('HDF.json',dict(schema='researchos.adopter-independent-source-handoff.v1',decision=d['decision'],actor_id=d['actor_id'],manifest_ref=mf,decision_ref=pin(N/'source-decision.json'),findings_ref=d['findings_ref'],controls_ref=d['controls_ref'],source_handoff_ref=d['source_handoff_ref'],source_manifest_ref=d['source_manifest_ref'],writer_ref=d['writer_ref'],actual_SourceGuard_ref=d['actual_SourceGuard_ref'],failure_ledger_ref=ledger,retained_handles_count=0,Main_adopted=False,Canonical_writes=False,formal_case_accepted_delta=0,parent_acceptance=False,STOP=True,FINAL=True))
print(json.dumps(dict(handoff_ref=hdf,manifest_ref=mf,decision_ref=pin(N/'source-decision.json'),findings_ref=d['findings_ref'],failure_origin_ref=failure),ensure_ascii=False))
