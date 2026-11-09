import sys
sys.dont_write_bytecode=True
import json,hashlib,re
from pathlib import Path
LOG=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
N=Path(__file__).resolve().parent
CHUNKS=('7b5b34','6444d0','bc4ba4','868a4b')
def require(value,label):
 if not value:raise ValueError(label)
def records():
 with LOG.open('r',encoding='utf-8') as f:
  for line in f:
   value=json.loads(line)
   if value.get('type')=='response_item' and isinstance(value.get('payload'),dict):yield value['payload']
def main():
 identities={};outputs={}
 for payload in records():
  if payload.get('type')!='custom_tool_call_output':continue
  for content in payload.get('output',[]):
   text=content.get('text','') if isinstance(content,dict) else ''
   if not text.startswith('{'):continue
   try:value=json.loads(text)
   except json.JSONDecodeError:continue
   chunk=value.get('chunk_id') if isinstance(value,dict) else None
   if chunk not in CHUNKS:continue
   require(chunk not in identities,'UNIQUE_ORIGINAL_CHUNK')
   identities[chunk]=payload['call_id'];outputs[chunk]=value
 require(set(identities)==set(CHUNKS),'ALL_ORIGINAL_CHUNKS')
 pairs={call_id:[] for call_id in identities.values()}
 for payload in records():
  call_id=payload.get('call_id')
  if call_id in pairs and payload.get('type') in ('custom_tool_call','custom_tool_call_output'):pairs[call_id].append(payload)
 result=[]
 for chunk in CHUNKS:
  pair=pairs[identities[chunk]]
  require(len(pair)==2 and {p['type'] for p in pair}=={'custom_tool_call','custom_tool_call_output'},'EXACT_ORIGINAL_PAIR')
  call=next(p for p in pair if p['type']=='custom_tool_call')
  require(re.search(r'sk-[A-Za-z0-9]{20,}',call.get('input','')) is None,'NO_LITERAL_SECRET')
  path=N/('producer-original-'+chunk+'.full-tool-io.root.json')
  body={'schema':'researchos.exact-original-tool-io-supplement.v1','original_chunk_id':chunk,'original_call_id':identities[chunk],'original_call_and_result':pair,'source_transcript_path':str(LOG),'original_result_only_ref':{'path':str(N.parent/'w09c19v7-producer-1a11f30/postseal-root-producer.original-tool-results.json'),'sha256':'f9a1602799f7487e80650bdd0758ccd601bb2834079de75182bcd356cf9e899f','bytes':5362},'product_rerun':False,'sealed_existing_artifacts_modified':False,'native_values_parsed_with_python_int':True}
  raw=(json.dumps(body,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
  with path.open('xb') as f:f.write(raw)
  result.append({'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
 print(json.dumps({'status':'FOUR_ORIGINAL_CALL_PAIRS_RECOVERED_EXACTLY','refs':result,'rerun':False}),flush=True)
if __name__=='__main__':main()

