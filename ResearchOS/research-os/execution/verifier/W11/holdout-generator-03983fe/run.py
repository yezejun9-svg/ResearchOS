import datetime,hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[4]
OUT=pathlib.Path(__file__).resolve().parent
WT=ROOT/'.local/worktrees/jev-labels'
GO=ROOT/'.local/tools/go1.27.1/go/bin/go.exe'
def sha(p):return 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source=sorted((WT/'evaluation/holdout/jev').glob('*'))+[WT/'go.mod',WT/'go.sum']
manifest={str(p.relative_to(WT)).replace('\\','/'):sha(p) for p in source if p.is_file()}
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT).decode().strip()
dirty=subprocess.check_output(['git','status','--porcelain'],cwd=WT).decode()
assert revision=='03983fe8fc96d2f17b607b0e0babce3ab24773e7' and not dirty
argv=[str(GO),'test','./evaluation/holdout/jev','-count=1','-v']
save(OUT/'before.json',dict(source_revision=revision,dirty=dirty,started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_manifest=manifest,argv=argv,cwd=str(WT),scope='PUBLIC_FIXTURE_SOURCE_TEST_ONLY',formal_data_generated=False,formal_seed_generated=False,formal_service_installed=False,real_provider_called=False,role='INDEPENDENT_LABELER_IMPLEMENTATION_NOT_EXECUTION_VERDICT'))
run=subprocess.run(argv,cwd=WT,capture_output=True)
(OUT/'stdout.txt').write_bytes(run.stdout);(OUT/'stderr.txt').write_bytes(run.stderr)
checks=[]
for n,l in enumerate(run.stdout.decode().splitlines(),1):
 if l.startswith('HOLDOUT_CODE_ASSERTION '):
  parts=l.split();checks.append(dict(id=parts[1],status=parts[2],scope=parts[3],raw_evidence=dict(path='stdout.txt',line=n,sha256=sha(OUT/'stdout.txt'))))
drift=[p for p,h in manifest.items() if sha(WT/p)!=h]
for p in source:
 if p.is_file():
  dest=OUT/'source-snapshot'/(str(p.relative_to(WT))+'.txt');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
report=dict(schema='W11_INDEPENDENT_LABELER_SOURCE_RECEIPT_V1',source_revision=revision,status='PASS' if run.returncode==0 and len(checks)==8 and all(c['status']=='PASS' for c in checks) and not drift else 'FAIL',exit_code=run.returncode,assertions=checks,assertion_count=len(checks),source_drift=drift,formal_G04='BLOCKED',formal_A08='BLOCKED',formal_holdout_count=0,formal_seed_generated=False,real_provider_called=False,automatic_authority='NONE',role='INDEPENDENT_LABELER_IMPLEMENTATION_NOT_EXECUTION_VERDICT',qualification_note='New rubric has distinct qualification keys; no old development counts transferred. Formal batch is designed for 15 cases per language, below 30 per-key holdout minimum; future run remains FAILED/ADVISORY.',scope='PUBLIC_FIXTURE_SOURCE_TEST_ONLY',raw_hashes={p:sha(OUT/p) for p in ['before.json','stdout.txt','stderr.txt']})
save(OUT/'report.json',report)
save(OUT/'evidence-index.json',{str(p.relative_to(OUT)).replace('\\','/'):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='evidence-index.json'})
print(json.dumps(dict(status=report['status'],assertions=len(checks),report_sha256=sha(OUT/'report.json'),index_sha256=sha(OUT/'evidence-index.json'))))
raise SystemExit(0 if report['status']=='PASS' else 1)
