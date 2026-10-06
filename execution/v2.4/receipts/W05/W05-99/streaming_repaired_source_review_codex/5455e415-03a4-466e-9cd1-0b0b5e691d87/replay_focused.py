import pathlib,json,subprocess,os,datetime,hashlib,collections
R=pathlib.Path.cwd();O=pathlib.Path(__file__).resolve().parent;W=R/'.local/worktrees/codex-w0599-model-stream';P=W/'execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/closure-86d60d4092df4d1896858f6001034b37'
pinned=json.loads((P/'environment.json').read_text(encoding='utf-8'));env=os.environ.copy();env.update(pinned);env['RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR']=str(O/'actual-fixtures')
for n,selector,pkg in [('focused-core','^TestModelStream(Quarantine|InterruptedActualBackupRestore|BackupRejectsChangedCanonicalEvidence|CancelRequiresBothDurableSDKFacts|OriginalActualFinalProof)','./internal/domain'),('focused-cli','^TestCLIModelStream(CausalDurableJSONL|SemanticSecretQuarantine)$','./apps/cli')]:
 cmd=[pinned['RESEARCHOS_GO'],'test','-count=1','-json','-run',selector,pkg];start=datetime.datetime.now(datetime.timezone.utc).isoformat();a=subprocess.run(cmd,cwd=W,env=env,capture_output=True);(O/(n+'.stdout')).write_bytes(a.stdout);(O/(n+'.stderr')).write_bytes(a.stderr);counts=collections.Counter()
 for line in a.stdout.decode(errors='replace').splitlines():
  try:x=json.loads(line)
  except ValueError:continue
  if x.get('Test') and x.get('Action') in ('pass','fail','skip'):counts[x['Action']]+=1
 fact={'argv':cmd,'cwd':str(W),'started_at':start,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':a.returncode,'environment_pinned':pinned,'evidence_dir':env['RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR'],'counts':dict(counts),'stdout_sha256':hashlib.sha256(a.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(a.stderr).hexdigest()};(O/(n+'.invocation.json')).write_text(json.dumps(fact,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(n,a.returncode,dict(counts),flush=True)
