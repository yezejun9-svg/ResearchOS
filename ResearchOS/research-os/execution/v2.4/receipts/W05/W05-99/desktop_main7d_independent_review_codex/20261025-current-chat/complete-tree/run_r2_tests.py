import hashlib,json,os,pathlib,subprocess,sys
E=pathlib.Path(__file__).parent
S=E/'source-r2'
W=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/desktop-main7d-native-20261025')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((E/'r2-fixed-inputs/source-freeze-02.json').read_bytes())
def check_source():
    for name,row in freeze['seven_file_hashes'].items():
        assert sha(S/name)==row['sha256'],name
check_source()
name='execution/toolchains/locked.json'
base=subprocess.run(['git','-C',str(W),'show',freeze['base_commit']+':'+name],capture_output=True,check=True).stdout
assert base==(W/name).read_bytes()
target=S/name;target.parent.mkdir(parents=True,exist_ok=True)
with target.open('xb') as out: out.write(base)
lock=json.loads(base)
node=pathlib.Path('C:/nvm4w/nodejs/node.exe')
assert sha(node)==lock['tools']['node']['sha256']
assert sha(pathlib.Path(sys.executable))==lock['tools']['python']['sha256']
temp=E/'r2-test-temp';temp.mkdir(exist_ok=False)
env={key:value for key,value in os.environ.items() if key.upper() not in ['NODE_OPTIONS','NODE_PATH','RESEARCHOS_DEVELOPMENT_BUNDLE','PYTHONPATH','PYTHONHOME']}
env.update({'TEMP':str(temp),'TMP':str(temp),'TMPDIR':str(temp),'PYTHONDONTWRITEBYTECODE':'1'})
results=[]
for label,argv in [('node-focused',[str(node),'--test',str(S/'tests/ui/desktop/development-launcher.test.mjs'),str(S/'tests/ui/desktop/development-smoke.test.mjs')]),('python-focused',[sys.executable,'-B','-X','utf8',str(S/'tests/ui/desktop/development-bundle.test.py'),'-v'])]:
    out=E/('r2-'+label);out.mkdir(exist_ok=False)
    (out/'recipe.json').write_text(json.dumps({'argv':argv,'cwd':str(S),'temp':str(temp),'tool_sha256':sha(pathlib.Path(argv[0])),'mode':'INDEPENDENT_FROZEN_SOURCE_MOCK_NO_GUI_NO_CORE'},indent=2),encoding='utf-8')
    result=subprocess.run(argv,cwd=S,env=env,capture_output=True)
    (out/'stdout.raw').write_bytes(result.stdout);(out/'stderr.raw').write_bytes(result.stderr)
    row={'native_exit':result.returncode,'stdout_sha256':sha(out/'stdout.raw'),'stderr_sha256':sha(out/'stderr.raw')}
    (out/'result.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
    print(label,json.dumps(row));sys.stdout.buffer.write(result.stdout);sys.stderr.buffer.write(result.stderr)
    results.append(row)
check_source()
assert not list(temp.iterdir()),'test fixture cleanup incomplete'
temp.rmdir()
(E/'R2-focused-test-summary.json').write_text(json.dumps({'results':results,'source_stable':True,'test_input':{'path':name,'sha256':sha(target),'origin':freeze['base_commit']},'native_gui_or_core_starts':0},indent=2),encoding='utf-8')
assert all(row['native_exit']==0 for row in results)
