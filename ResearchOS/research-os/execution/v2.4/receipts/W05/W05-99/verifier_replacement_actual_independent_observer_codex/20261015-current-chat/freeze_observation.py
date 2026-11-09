import pathlib,json,hashlib,sys,datetime
E=pathlib.Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
label=sys.argv[1]
paths=[p for p in E.iterdir() if p.is_file() and (p.name.startswith(label) or p.suffix in ['.py','.ps1'] or p.name=='00-readonly-wal-precheck.json')]
target=E/(label+'-manifest.json')
with target.open('x',encoding='utf-8') as f:json.dump({'schema':'researchos.actual-replacement-independent-observation-manifest/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':label,'observer':'codex:/root/verifier_revision_review','source_commit':'4f4023c956f84d65743f39ce77d6c8899a21ada1','evidence':[pin(p) for p in sorted(paths)],'signed_acceptance':False,'schema_migration_performed':False,'formal_increment':0},f,ensure_ascii=False,indent=2)
print(json.dumps(pin(target),ensure_ascii=False))
