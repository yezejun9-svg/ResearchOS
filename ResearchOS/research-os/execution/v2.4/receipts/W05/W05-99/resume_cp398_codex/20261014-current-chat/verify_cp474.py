import hashlib,json,subprocess,sys
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent/'continuation-cp474'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf8').strip()
baseline=read(R/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')
protected=[{'path':x['path'],'expected':x['sha256'],'actual':sha(R/x['path'])} for x in baseline['protected_source']]
assert len(protected)==9 and all(x['actual']==x['expected'] for x in protected)
assert sha(R/'execution/project_identity.json')=='03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
assert sha(R/'.git/config')=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
assert git('rev-parse','HEAD')=='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2'
assert git('config','user.name')=='ResearchOS Codex' and git('config','user.email')=='researchos-codex@localhost'
state=R/'execution/v2.4/step_state.json';before=state.read_bytes()
argv=[sys.executable,'-B','-X','utf8',str(R/'.local/worktrees/v24-continuation/spec/v2.4/tools/task_packet.py'),'next','--state',str(state)]
p=subprocess.run(argv,cwd=R,capture_output=True)
for name,raw in [('task-packet.stdout.raw.json',p.stdout),('task-packet.stderr.raw.txt',p.stderr)]:
 with (O/name).open('xb') as f:f.write(raw)
assert p.returncode==0;result=json.loads(p.stdout);assert result['state_source']=='VALIDATED_FILE';assert state.read_bytes()==before
new(O/'verification.json',{'head':git('rev-parse','HEAD'),'identity_sha256':sha(R/'execution/project_identity.json'),'git_config_sha256':sha(R/'.git/config'),'protected':protected,'argv':argv,'native_exit':p.returncode,'state_source':result['state_source'],'state_sha256':sha(state),'stdout_sha256':sha(O/'task-packet.stdout.raw.json'),'formal_increment':0})
print(json.dumps({'native_exit':p.returncode,'state_source':result['state_source'],'state_sha256':sha(state),'protected':len(protected),'result_keys':list(result)}))
