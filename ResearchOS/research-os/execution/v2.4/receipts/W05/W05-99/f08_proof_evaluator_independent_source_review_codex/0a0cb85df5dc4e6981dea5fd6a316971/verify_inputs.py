import json,pathlib,hashlib,re
src=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_implementation_preparation_codex/b6b765563c9640bd8a2b9e54f643352c')
out=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_proof_evaluator_independent_source_review_codex/0a0cb85df5dc4e6981dea5fd6a316971')
def meta(path):
 b=path.read_bytes();return {'path':path.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
m=json.loads((src/'manifest.json').read_text(encoding='utf-8')); errors=[];refs=[]
for item in m['files']:
 q=pathlib.Path(item['path']); actual=meta(q)
 if actual['sha256']!=item['sha256'] or actual['bytes']!=item['bytes']:errors.append({'expected':item,'actual':actual})
 rel=q.relative_to(src);dest=out/'inputs'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(q.read_bytes())
 refs.append(actual)
assert not errors, json.dumps(errors)
(out/'inputs'/'manifest.json').write_bytes((src/'manifest.json').read_bytes())
h=json.loads((src/'handoff.json').read_text(encoding='utf-8'))
hre=[]
def walk(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=set(v):
   q=pathlib.Path(v['path'])
   if q.is_relative_to(src):
    a=meta(q);assert a['sha256']==v['sha256'] and a['bytes']==v['bytes'];hre.append(a)
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
walk(h)
record={'manifest':meta(src/'manifest.json'),'handoff':meta(src/'handoff.json'),'listed_count':len(refs),'physical_count_with_manifest':len(refs)+1,'all_listed_sha256_and_sizes_verified':True,'handoff_internal_refs_verified':len(hre),'source':h['source_ref'],'test':h['test_ref'],'files':refs,'handoff_refs':hre,'external_main_worktree_cache_reads':0}
(out/'input-verification.json').write_text(json.dumps(record,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k not in ('files','handoff_refs')},ensure_ascii=True))
for name in ('client_cancel_finalization.go.proposed.txt','client_cancel_finalization_test.v2.go.proposed.txt'):
 lines=(src/name).read_text(encoding='utf-8').splitlines()
 print('FUNCTION_INDEX',name,len(lines))
 for i,line in enumerate(lines,1):
  if line.startswith('func '):print(str(i)+':'+line)

