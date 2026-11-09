import hashlib,json,pathlib,subprocess,sys
E=pathlib.Path(__file__).parent
tag,command=sys.argv[1:3];out=E/tag;out.mkdir(exist_ok=False)
argv=['pwsh','-NoLogo','-NoProfile','-Command',command]
(out/'recipe.json').write_text(json.dumps({'argv':argv,'cwd':'D:/作品集/ResearchOS/research-os','mode':'INDEPENDENT_MAIN_INTEGRATION_PREFLIGHT_READ_ONLY_NO_SOURCE_STATE_PROCESS_CHANGE'},ensure_ascii=False,indent=2),encoding='utf-8')
p=subprocess.run(argv,cwd='D:/作品集/ResearchOS/research-os',capture_output=True)
(out/'stdout.raw').write_bytes(p.stdout);(out/'stderr.raw').write_bytes(p.stderr)
(out/'result.json').write_text(json.dumps({'native_exit':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()},indent=2),encoding='utf-8')
sys.stdout.buffer.write(p.stdout);sys.stderr.buffer.write(p.stderr);print('\nNATIVE_EXIT='+str(p.returncode));sys.exit(p.returncode)
