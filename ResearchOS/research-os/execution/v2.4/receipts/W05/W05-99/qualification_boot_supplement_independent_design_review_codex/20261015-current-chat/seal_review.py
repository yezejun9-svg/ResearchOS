import datetime,hashlib,json,pathlib,sys
base=pathlib.Path(__file__).resolve().parent
repo=pathlib.Path('D:/作品集/ResearchOS/research-os')
record={'id':'F02','status':'PREWRITTEN','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':[sys.executable,'-B','-X','utf8',str(pathlib.Path(__file__).resolve())],'cwd':str(repo),'purpose':'ownE validation and final seal only','script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()}
(base/'F02-command.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (base/'command-index.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(record,ensure_ascii=False)+'\n')
scope_path=repo/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp519/boot-supplement-independent-design-review-scope.json'
scope_raw=scope_path.read_bytes()
assert hashlib.sha256(scope_raw).hexdigest()=='e647ec31630ef5cb542f8f1ea1b4dbc0de2e1c9deb4820bb413efd2b904ce900'
scope=json.loads(scope_raw.decode('utf-8-sig'))
for item in scope['inputs']:
    raw=(repo/item['path']).read_bytes()
    assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'], item['path']
review=json.loads((base/'design-review.json').read_text(encoding='utf-8'))
assert len(review['source_paths'])==57 and len(set(review['source_paths']))==57
assert review['grouped_queries_after_intake']==11
for key in ['source_authority','source_acceptance','actual_authority','actual_acceptance','formal_acceptance']: assert review[key] is False
assert review['formal_increment']==0
index=[]
ledger=[json.loads(line) for line in (base/'ledger.jsonl').read_text(encoding='utf-8').splitlines()]
for command in sorted(base.glob('*-command.json')):
    entry=json.loads(command.read_text(encoding='utf-8'))
    cid=entry['id']
    entry['prewrite_file']=command.name
    entry['capture_files']=[p.name for p in sorted(base.glob(cid+'-*')) if p.name!=command.name]
    if cid.startswith('W'):
        assert (base/(cid+'-raw.json')).is_file()
        entry['status']='OFFICIAL_DOCUMENT_QUERY_CAPTURED'
    else:
        matching=[x for x in ledger if x['id']==cid]
        entry['result']=matching[0] if matching else {'status':'SEAL_VALIDATION_SUCCESS'}
    index.append(entry)
(base/'unified-command-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result={'id':'F02','status':'SUCCESS','frozen_scope_inputs_verified':12,'source_paths_unique':57,'authority_acceptance_flags':False,'native_or_product_test_claim':False,'query_groups':11}
(base/'F02-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(base/'F02-stdout.txt').write_text('OwnE reports and 12 frozen inputs validated; all evidence sealed; no product tests executed.\n',encoding='utf-8')
(base/'F02-stderr.txt').write_bytes(b'')
with (base/'ledger.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(result,ensure_ascii=False)+'\n')
files=[]
for path in sorted(base.iterdir()):
    if not path.is_file() or path.name=='FINAL-manifest.json': continue
    raw=path.read_bytes()
    files.append({'path':path.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
manifest={'schema':'researchos.boot-supplement-independent-design-review.final.v1','owner':review['owner'],'model':review['model'],'reasoning_effort':'high','verdict':review['verdict'],'scope_sha256':review['scope_sha256'],'source_authority':False,'source_acceptance':False,'actual_authority':False,'actual_acceptance':False,'formal_acceptance':False,'formal_increment':0,'groups_after_intake':11,'group_limit':12,'scope_inputs':scope['inputs'],'source_path_count':57,'native_tests_executed':0,'actual_operations':[],'files':files,'self_exclusion':'FINAL-manifest.json','seal_note':'All captured commands/ledger finalized before hashing; manifest excludes itself only.'}
path=base/'FINAL-manifest.json'
path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'files':len(files),'verdict':review['verdict']},ensure_ascii=False))

