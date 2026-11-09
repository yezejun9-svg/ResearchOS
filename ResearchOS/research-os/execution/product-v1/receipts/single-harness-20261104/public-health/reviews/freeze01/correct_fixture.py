from pathlib import Path
import hashlib,json
from qa import run
R=Path(__file__).resolve().parent
old=R/'independent.test.mjs';text=old.read_text(encoding='utf-8')
new=text.replace("handlers.get('statusHealth')","handlers.get('ros:statusHealth')").replace("handlers.get('statusHost')","handlers.get('ros:statusHost')")
before="test('independent failed actual ensureCore health probe cannot be replaced by a synthetic ready body',async()=>{\n const f=fixture({probeStatus:500});const reply=await ipc.callCore(f.deps,'status','health',{});assert.equal(reply.ok,false);assert.equal(f.calls.transport.length,0);assert.equal(f.calls.principal,0);assert.equal(f.calls.spawn,0);assert.notEqual(startup.healthFromReply(reply).state,'ready');\n});"
after="test('independent valid discovered Host can recover through a new actual health response after failed pre-probe',async()=>{\n const f=fixture({probeStatus:500});const reply=await ipc.callCore(f.deps,'status','health',{});assert.equal(reply.ok,true);assert.equal(f.calls.transport.length,1);assert.deepEqual(f.calls.transport[0],['GET','http://127.0.0.1:12345/healthz',{},{}]);assert.equal(f.calls.principal,0);assert.equal(f.calls.spawn,0);assert.equal(startup.healthFromReply(reply).state,'ready');\n});"
assert new.count(before)==1;new=new.replace(before,after)
target=R/'independent02.test.mjs';assert not target.exists();target.write_text(new,encoding='utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'classification':'REVIEW_FIXTURE_CORRECTION_ONLY_NO_PRODUCTION_SOURCE_CHANGE','original_sha256':sha(old),'corrected_sha256':sha(target),'original_raw_preserved':True,'changes':['Use actual registered ros: flat channel prefix','Correct mistaken pre-probe assumption: existing ensureCore preserves valid discovery when DOWN_NO_LAUNCH; a subsequent fixed public GET may honestly return fresh ready. Assert exact fixed request/no principal/no spawn instead of forbidding observation.'],'formal_increment':0}
p=R/'fixture-correction.json';assert not p.exists();p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
raise SystemExit(run('independent-tests-02',['--test','--test-reporter=tap',str(target)]))
