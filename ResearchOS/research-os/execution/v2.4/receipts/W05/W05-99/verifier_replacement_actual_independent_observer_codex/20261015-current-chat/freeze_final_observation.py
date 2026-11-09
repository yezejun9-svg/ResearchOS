import pathlib,json,hashlib,datetime
E=pathlib.Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
for name in ['01-baseline-manifest.json','02-preflight-manifest.json']:
 m=json.loads((E/name).read_text(encoding='utf-8'))
 for ref in m['evidence']:assert pin(pathlib.Path(ref['path']))==ref
target=E/'FINAL-manifest.json'
with target.open('x',encoding='utf-8') as f:json.dump({'schema':'researchos.actual-verifier-registration-independent-final/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'LIMITED_ACTUAL_REGISTRATION_ACCEPTED','reviewer':'codex:/root/verifier_revision_review','model':'gpt-6-astra','reasoning_effort':'high','operation_id':'86b256fde9424ebb810537650136ad29','evidence':[pin(p) for p in sorted(E.iterdir()) if p.is_file() and p!=target],'scope':'single actual maintenance only','schema_migration_performed':False,'product_formal_acceptance':False,'formal_increment':0,'formal_accepted':0,'formal_total':42,'parents_open':22},f,ensure_ascii=False,indent=2)
for ref in json.loads(target.read_text(encoding='utf-8'))['evidence']:assert pin(pathlib.Path(ref['path']))==ref
print(json.dumps({'manifest':pin(target),'report':pin(E/'FINAL-OBSERVATION.md'),'review':pin(E/'03-postcommit-review.json')},ensure_ascii=False))
