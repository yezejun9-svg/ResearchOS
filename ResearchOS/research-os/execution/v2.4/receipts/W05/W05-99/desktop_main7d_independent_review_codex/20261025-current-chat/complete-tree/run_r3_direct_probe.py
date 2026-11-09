import hashlib,json,os,pathlib,shutil,subprocess
E=pathlib.Path(__file__).parent
temp=E/'r3-direct-probe-temp';temp.mkdir(exist_ok=False)
out=E/'r3-direct-probe';out.mkdir(exist_ok=False)
env={k:v for k,v in os.environ.items() if k.upper() not in ['NODE_OPTIONS','NODE_PATH']}
env.update({'TEMP':str(temp),'TMP':str(temp),'TMPDIR':str(temp)})
argv=['C:/nvm4w/nodejs/node.exe',str(E/'r3-direct-byte-probe.mjs')]
(out/'recipe.json').write_text(json.dumps({'argv':argv,'cwd':str(E),'mode':'NO_NODE_TEST_RUNNER_MOCK_ONE_BYTE_STDOUT_CHUNKS','temp':str(temp)},indent=2),encoding='utf-8')
p=subprocess.run(argv,cwd=E,env=env,capture_output=True)
(out/'stdout.raw').write_bytes(p.stdout);(out/'stderr.raw').write_bytes(p.stderr)
result={'native_exit':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()}
(out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
lines=p.stdout.decode('utf-8',errors='strict').splitlines()
assert len(lines)==3 and '\ufffd' not in '\n'.join(lines)
ready=json.loads(lines[0].removeprefix('ROS_DESKTOP_REPORT '));probe=json.loads(lines[2].removeprefix('INDEPENDENT_PROBE '))
assert ready['renderer']['mounted_title']==probe['renderer_title']=='研究工作台🙂é'
assert p.returncode==0 and probe['status']=='PASS'
rows=[]
for path in temp.rglob('*'):
    assert path.resolve().is_relative_to(temp.resolve())
    if path.is_file():rows.append({'path':path.relative_to(temp).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
(out/'fixture-inventory.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
assert temp.resolve().is_relative_to(E.resolve()) and temp.name=='r3-direct-probe-temp'
shutil.rmtree(temp)
summary={'result':result,'probe':probe,'raw_utf8_valid':True,'replacement_characters':0,'native_gui_or_core_starts':0}
(E/'R3-direct-byte-probe-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
