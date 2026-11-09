import pathlib,json,hashlib,re,collections
B=pathlib.Path(__file__).parent
R=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
paths=[
R/'execution/v2.4/receipts/W05/W05-99/qualification_official_entry_resource_map_codex/20261015-current-chat/file-ancestor-metadata.json',
R/'execution/v2.4/receipts/W05/W05-99/qualification_boot_supplement_independent_design_review_codex/20261015-current-chat/design-review.md',
R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp521/boot-proposal-adopted-limits.json']
refs=[]
for p in paths:
 raw=p.read_bytes();refs.append({'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
assert refs[0]['sha256']=='f4c58e80940d0dc81ce9c0bac70a1131030238c27cfe7e9347e749ac33d71cc5'
assert refs[1]['sha256']=='3965106935192d75a8bff39d5c21edd3d98e63417f1ed19067c8a36d2e2f290c'
m=json.loads(paths[0].read_text(encoding='utf-8-sig'))
rows=[]
for n,x in enumerate(m['records']):
 acl=x.get('acl') or {};sd=acl.get('sddl') or ''
 flags=re.search(r'D:([^()]*)',sd)
 rows.append({'record_index':n,'path':x['path'],'kind':x.get('kind'),'directory':x.get('directory'),'acl_status':acl.get('status'),'dacl_control':flags.group(1) if flags else None,'has_AI':bool(flags and 'AI' in flags.group(1)),'sddl_sha256':hashlib.sha256(sd.encode()).hexdigest() if sd else None})
result={'class':'HISTORICAL_METADATA_ONLY_NOT_CURRENT_NATIVE_PROOF','refs':refs,'records':rows,'kind_counts':dict(collections.Counter(x['kind'] for x in rows))}
out=B/'HISTORICAL-v7-sddl-contract-extract.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=2))
print('ADOPTED_LIMITS\n'+paths[2].read_text(encoding='utf-8-sig'))

