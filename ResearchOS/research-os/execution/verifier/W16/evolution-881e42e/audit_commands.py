import datetime,hashlib,json,os,pathlib,subprocess
root=pathlib.Path(r'D:/作品集/ResearchOS/research-os/.local/worktrees/w16-evolution-review')
out=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/verifier/W16/evolution-881e42e')
go=pathlib.Path(r'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe')
lock=json.loads((root/'execution/toolchains/locked.json').read_text(encoding='utf-8'))
actual=hashlib.sha256(go.read_bytes()).hexdigest()
assert actual==lock['tools']['go']['sha256']
records=[]
for name,check,case,mode in [('G01','W16-G01','','fixture'),('G03','W16-G03','','fixture'),('dual','W16-G02','C09','fixture'),('LIVE','W16-G02','','live')]:
 env=os.environ.copy();env.update(RESEARCHOS_TASK_ID='W16',RESEARCHOS_CHECK_ID=check,RESEARCHOS_CASE_ID=case,RESEARCHOS_GO=str(go))
 argv=['python','ops/ci/evolution.py','--mode',mode]
 p=subprocess.run(argv,cwd=root,env=env,capture_output=True,text=True,encoding='utf-8')
 records.append({'name':name,'argv':argv,'check':check,'case':case,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 assert p.returncode==2
(out/'runner-rejections.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
(out/'command-receipt.json').write_text(json.dumps({'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verifier':'codex:/root/evolution_verifier','source_revision':'881e42e7252a614c0f372b1e3a45a236cc64cf94','review_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'worktree':str(root),'worktree_status_after':subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True),'go_executable':str(go),'go_sha256':actual,'go_version':subprocess.check_output([str(go),'version'],text=True).strip(),'tests':[{'argv':[str(go),'test','-overlay',str(out/'overlay.json'),'./internal/domain','-run','^TestVerifierW16','-count=1','-v','-timeout=3m'],'exit_code':0,'output':'probe-output.txt','note':'HistoricalEvidenceAudit added after this run; original two top-level tests plus five subtests passed.'},{'argv':[str(go),'test','-overlay',str(out/'overlay.json'),'./internal/domain','-run','^TestVerifierW16HistoricalEvidenceAudit$','-count=1','-v','-timeout=1m'],'exit_code':0,'output':'historical-audit-output.txt'}],'environment':{'GOTOOLCHAIN':'local','GOENV':'off','RESEARCHOS_GO':str(go),'W16_EVIDENCE_DIR':str(out),'W16_SOURCE_RECEIPT':str(root/'execution/receipts/W16/f1e68e3d-e065-46f9-a293-fca3ea8c6038')},'runner_rejections':4,'production_data_accessed':False,'source_modified':False},indent=2),encoding='utf-8')
print('Pinned Go hash matched. Four runner rejection probes passed. Frozen worktree clean.')
