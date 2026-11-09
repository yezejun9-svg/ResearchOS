import pathlib,json,hashlib,difflib,re
out=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_queue_absence_independent_revision_review_codex/1cff95bc559c45d68414e44d5553c7a1');src=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_queue_absence_revision_preparation_codex/b9a560ed59c24bef9b9e01d2d91c4b84')
def meta(p):
 b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
h=json.loads((src/'handoff.json').read_text(encoding='utf-8'));mf=meta(src/'manifest.json')
assert mf['sha256']=='0d7982363d2b77ea8ac5117dd014bb434e8d580b07d5c413ccb9f8433db4095f' and mf['bytes']==7773
assert meta(src/'handoff.json')['sha256']=='1828343f3ff153bf91907307ee7e95ecd4fb9f78b45b9946a31ce87882b10138'
m=json.loads((src/'manifest.json').read_text(encoding='utf-8'));assert isinstance(m['files'],list) and len(m['files'])==25
records=[]
for ref in m['files']:
 q=pathlib.Path(ref['path']);actual=meta(q);assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
 dest=out/'inputs'/q.relative_to(src);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(q.read_bytes());records.append(actual)
(out/'inputs'/'manifest.json').write_bytes((src/'manifest.json').read_bytes())
external_refs=[]
def walk(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=set(v):
   q=pathlib.Path(v['path']);a=meta(q);assert a['sha256']==v['sha256'] and a['bytes']==v['bytes']
   if not q.is_relative_to(src):
    external_refs.append(a)
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
walk(h)
base=pathlib.Path(h['base_source_ref']['path']);old=base.read_bytes();new=pathlib.Path(h['source_ref']['path']).read_bytes()
(out/'base').mkdir(exist_ok=True);(out/'base'/'client_cancel_finalization.go.proposed.txt').write_bytes(old)
oldtest=base.parent/'client_cancel_finalization_test.v2.go.proposed.txt';(out/'base'/oldtest.name).write_bytes(oldtest.read_bytes())
diff=''.join(difflib.unified_diff(old.decode('utf-8').splitlines(keepends=True),new.decode('utf-8').splitlines(keepends=True),fromfile='base-b50',tofile='revision-9d7'))
(out/'actual-source-diff.txt').write_text(diff,encoding='utf-8')
record={'listed_members':25,'physical_with_manifest':26,'manifest':mf,'handoff':meta(src/'handoff.json'),'all25_sha_and_bytes_verified':True,'source':h['source_ref'],'base':h['base_source_ref'],'test':h['test_proposal_ref'],'external_handoff_refs_verified':external_refs,'new_source_lines':len(new.decode('utf-8').splitlines()),'new_source_full_bytes_loaded':True,'source_no_compile_run':True,'files':records}
(out/'input-verification.json').write_text(json.dumps(record,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k not in ('files','external_handoff_refs_verified')},ensure_ascii=True))
print('DIFF');print(diff)
for name in ('queue-absence-tests.go.proposed.txt','IMPLEMENTATION-STATUS.md','coverage-and-open-matrix.json'):
 print('FILE',name)
 for i,line in enumerate((out/'inputs'/name).read_text(encoding='utf-8').splitlines(),1):print(str(i)+':'+line)

