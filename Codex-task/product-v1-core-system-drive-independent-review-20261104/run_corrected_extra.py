from pathlib import Path
import hashlib,json,os,subprocess,re
R=Path(__file__).resolve().parent
D=R/'attempt-03';D.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=R/'attempt-02/fixture/tests/ui/desktop/independent.test.mjs'
new=old.with_name('independent-corrected.test.mjs');assert not new.exists()
new.write_text(old.read_text().replace('\\','/'),encoding='utf-8')
node=Path('C:/nvm4w/nodejs/node.exe');assert sha(node)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
env={k:os.environ[k] for k in ['SystemRoot','WINDIR','COMSPEC','TEMP','TMP'] if k in os.environ};env['PATH']=str(node.parent)
argv=[str(node),'--test','--test-reporter=tap',str(new)]
(D/'command.json').write_text(json.dumps({'argv':argv,'environment':env,'node_sha256':sha(node),'old_fixture_sha256':sha(old),'corrected_fixture_sha256':sha(new),'change':'Independent fixture paths use forward slash to avoid unintended JS escape semantics. Production extraction and original 34-case suite unchanged; only two extra cases rerun.'},indent=2)+'\n',encoding='utf-8')
with (D/'stdout.raw').open('xb') as out,(D/'stderr.raw').open('xb') as err:code=subprocess.run(argv,cwd=R/'attempt-02/fixture',env=env,stdout=out,stderr=err,timeout=20).returncode
raw=(D/'stdout.raw').read_text();counts={k:int(v) for k,v in re.findall(r'^# (tests|pass|fail|cancelled|skipped) (\d+)$',raw,re.M)}
(D/'result.json').write_text(json.dumps({'exit_code':code,'counts':counts,'stdout_sha256':sha(D/'stdout.raw'),'stderr_sha256':sha(D/'stderr.raw')},indent=2)+'\n',encoding='utf-8')
assert code==0 and counts['pass']==2 and counts['fail']==0
print(json.dumps({'exit_code':code,'counts':counts}))
