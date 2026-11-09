import pathlib,json,hashlib,subprocess,sys
E=pathlib.Path(__file__).resolve().parent
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
W=R/'.local/worktrees/owned-core-stop-authority-r4-20261015'
scope=json.loads((R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp520/owned-core-stop-r4-independent-review-scope.json').read_text(encoding='utf-8'))
manifest=json.loads((R/scope['inputs'][0]['path']).read_text(encoding='utf-8'))
result={}
for name,args in [('head',['rev-parse','HEAD']),('tree',['rev-parse','HEAD^{tree}']),('status',['status','--porcelain']),('delta',['diff','--name-only','2816daacdb2c08ae8ee1d62c91bcd3f571d40737','HEAD']),('whole19',['diff','--name-only','4f4023c956f84d65743f39ce77d6c8899a21ada1','HEAD'])]:
 argv=[sys.executable,'-B','-X','utf8',str(E/'reviewer_logger.py'),'git','-c','maintenance.auto=0','-c','gc.auto=0',*args]
 done=subprocess.run(argv,cwd=W,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 assert done.returncode==0,(name,done.stderr)
 result[name]=done.stdout.decode('utf-8').strip()
assert result['head']==scope['source_commit'];assert result['tree']==scope['source_tree'];assert result['status']==''
assert sorted(result['delta'].splitlines())==sorted(scope['delta_paths_readonly'])
assert sorted(result['whole19'].splitlines())==sorted(scope['source_allowlist_readonly'])
result['source_pins']={}
for rel in scope['source_allowlist_readonly']:
 raw=(W/rel).read_bytes();sha=hashlib.sha256(raw).hexdigest()
 assert sha==manifest['source_pins'][rel]['sha256'],rel
 result['source_pins'][rel]={'sha256':sha,'bytes':len(raw)}
root_evidence=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp520/root-r4-command-capture-verification.json'
result['root_author_capture_verification']={'path':str(root_evidence),'sha256':hashlib.sha256(root_evidence.read_bytes()).hexdigest()}
assert result['root_author_capture_verification']['sha256']=='136d9977524898fddc9947589192ab809c32250483672b08136e77b910a8c922'
(E/'final-source-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
