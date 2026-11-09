import datetime, hashlib, json, os, pathlib, subprocess, sys

ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT=pathlib.Path(__file__).resolve().parent
GO=ROOT/'.local/tools/go1.27.1/go/bin/go.exe'
FILES=['adapters/decision/qualification_audit.go','adapters/decision/qualification_audit_test.go','tests/jev/w1102_check.py','tests/jev/w1102_probe/main.go','tests/jev/test_w1102_dispatch.py','tests/jev/admit_frozen_live.py','execution/v2.4/commands.json','execution/commands.json']
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):
 with (OUT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)

before={f:digest(ROOT/f) for f in FILES}
assert before['tests/jev/w1102_check.py']=='13bb56593fe91a5cd7bd0a32a979898ea0cac45f35a38eda8b103a705f52866b'
assert digest(GO)=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
assert digest(pathlib.Path(sys.executable))=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
save('source-before.json',before)
commands=[]
env=dict(os.environ,GOTOOLCHAIN='local',GOENV='off',GOPATH=str(ROOT/'.local/gopath'),GOCACHE=str(ROOT/'.local/gocache'),TEMP=str(OUT/'tmp'),TMP=str(OUT/'tmp'))

def run(name,argv,want=0):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 p=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:stdout,stderr=p.communicate(timeout=180)
 finally:
  if p.poll() is None:
   subprocess.run([str(pathlib.Path(os.environ['SystemRoot'])/'System32/taskkill.exe'),'/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=10)
   p.wait(timeout=10)
 for suffix,raw in [('stdout',stdout),('stderr',stderr)]:
  with (OUT/(name+'.'+suffix)).open('xb') as f:f.write(raw)
 commands.append({'name':name,'argv':argv,'cwd':str(ROOT),'started_at':start,'exit_code':p.returncode,'expected_exit_code':want,'stdout_sha256':digest(OUT/(name+'.stdout')),'stderr_sha256':digest(OUT/(name+'.stderr'))})
 assert p.returncode==want,(name,p.returncode)
 return stdout

try:
 raw=run('go-audit40',[str(GO),'test','./adapters/decision','-run','^TestW1102QualificationAudit$','-count=1','-timeout=60s','-json'])
 events=[json.loads(x) for x in raw.decode().splitlines()]
 assert [e['Action'] for e in events if not e.get('Test') and e['Action'] in ('pass','fail')]==['pass']
 assert not any(e['Action'] in ('skip','fail') for e in events)
 lines=''.join(e.get('Output','') for e in events).splitlines()
 rows=[json.loads(x[len('W11_ASSERTION '):]) for x in lines if x.startswith('W11_ASSERTION ')]
 sys.path.insert(0,str(ROOT/'tests/jev'));import w1102_check
 ids=[r['assertion_id'] for r in rows]
 assert len(ids)==len(set(ids))==40 and set(ids)==w1102_check.EXPECTED and all(r['status']=='PASS' and r['expected']==r['actual'] for r in rows)
 save('audit40-rows.json',rows)
 original=subprocess.check_output(['git','show','b0d63bc2cf985b5ee54f742f89d13379f19ed246:adapters/decision/qualification_audit.go'],cwd=ROOT)
 with (OUT/'original-audit.go').open('xb') as f:f.write(original)
 save('original-overlay.json',{'Replace':{str(ROOT/'adapters/decision/qualification_audit.go'):str(OUT/'original-audit.go')}})
 run('original-nonfinite-counterexample',[str(GO),'run','-overlay',str(OUT/'original-overlay.json'),str(OUT/'audit_boundary.go')],1)
 fresh=run('fixed-independent-boundaries',[str(GO),'run',str(OUT/'audit_boundary.go')])
 independent=[json.loads(x[len('INDEPENDENT_ASSERTION '):]) for x in fresh.decode().splitlines() if x.startswith('INDEPENDENT_ASSERTION ')]
 assert len(independent)==len({x['assertion_id'] for x in independent})==13 and all(x['status']=='PASS' for x in independent)
 save('independent-boundary-rows.json',independent)
 raw=run('wrapper-instrumented',[sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests/jev','-p','test_w1102_dispatch.py','-v'])
 compat=[json.loads(x[len('W1102_DISPATCH_ASSERTION '):]) for x in raw.decode().splitlines() if x.startswith('W1102_DISPATCH_ASSERTION ')]
 assert len(compat)==len({x['assertion_id'] for x in compat})==12 and all(x['status']=='PASS' and x['real_child_executed'] is False for x in compat)
 save('wrapper-instrumented-rows.json',compat)
 assert before=={f:digest(ROOT/f) for f in FILES}
 save('source-after.json',{f:digest(ROOT/f) for f in FILES})
 print(json.dumps({'status':'PASS_IN_SCOPE','producer_fixture_assertions':40,'independent_boundary_assertions':13,'independent_confusion_matrices':64,'wrapper_synthetic_assertions':12,'original_nonfinite_failure_reproduced':True,'formal_live_qualified':False}))
finally:save('commands.json',commands)
