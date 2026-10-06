import pathlib,json,hashlib,subprocess,os,datetime
r=pathlib.Path('.').resolve();base=r/'execution/verifier/W15/skills-2bcd6d6/p2-resolution';out=base/'fix-bb85d5e';wt=r/'.local/worktrees/skills-lifecycle'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(base/'review.json')=='45573a690b870d20436bb5e661762cb70d58a89b21fca201ebb9bc8fbe46e994';assert sha(base/'evidence-index.json')=='569213d7b2340decc45bf8f4e47c1d9c3e86af4db71dfe90d2c964813419a925'
prior={str(p.relative_to(r)):sha(p) for p in base.iterdir() if p.is_file()}
paths=subprocess.check_output(['git','ls-files','internal/domain','evaluation/skills','go.mod','go.sum'],cwd=wt,text=True).splitlines();files={p:sha(wt/p) for p in paths if (wt/p).is_file()}
(out/'before.json').write_text(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=wt,text=True).strip(),'status':subprocess.check_output(['git','status','--porcelain'],cwd=wt,text=True),'prior_files':prior,'source_files':files},indent=2),encoding='utf-8')
replace={str(wt/'internal/domain/independent_skills_test.go'):str(r/'execution/verifier/W15/skills-2bcd6d6/fix-22cb749/independent_skills_test.go'),str(wt/'internal/domain/independent_resolution_test.go'):str(base/'independent_resolution_test.go'),str(wt/'internal/domain/independent_use_delta_test.go'):str(out/'independent_use_delta_test.go')}
(out/'overlay.json').write_text(json.dumps({'Replace':replace},indent=2),encoding='utf-8')
go=r/'.local/tools/go1.27.1/go/bin/go.exe';env=dict(os.environ,RESEARCHOS_GO=str(go),GOROOT=str(go.parents[1]));argv=[str(go),'test','-json','-count=1','-timeout=3m','-overlay',str(out/'overlay.json'),'-run','^TestIndependentResolvedActiveSkillDelta$/^decision-withdrawal$','./internal/domain']
(out/'command.json').write_text(json.dumps({'argv':argv,'cwd':str(wt),'source_revision':'bb85d5ef1bbd3c795ae93479b94683fa27584a33','started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'go_sha256':sha(go),'mode':'FIXTURE','scope':'only active skill ledger fix delta; previous26 passing assertions not rerun'},indent=2),encoding='utf-8')
with (out/'stdout.jsonl').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:p=subprocess.run(argv,cwd=wt,env=env,stdout=stdout,stderr=stderr)
(out/'exit-code.json').write_text(json.dumps({'exit_code':p.returncode}),encoding='utf-8');print({'exit_code':p.returncode})
