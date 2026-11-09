import hashlib,json,pathlib,subprocess,sys
E=pathlib.Path(__file__).parent
tag,command=sys.argv[1:3];D=E/tag;D.mkdir(exist_ok=False)
argv=['pwsh','-NoLogo','-NoProfile','-Command',command]
(D/'recipe.json').write_text(json.dumps({'argv':argv,'cwd':'D:/作品集/ResearchOS/research-os','mode':'DESKTOP_COMPLETE_TREE_INDEPENDENT_PREPARATION_NO_GUI_CORE'},ensure_ascii=False,indent=2),encoding='utf-8')
p=subprocess.run(argv,cwd='D:/作品集/ResearchOS/research-os',capture_output=True)
(D/'stdout.raw').write_bytes(p.stdout);(D/'stderr.raw').write_bytes(p.stderr)
(D/'result.json').write_text(json.dumps({'native_exit':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()},indent=2),encoding='utf-8')
sys.stdout.buffer.write(p.stdout);sys.stderr.buffer.write(p.stderr);print('\nNATIVE_EXIT='+str(p.returncode));sys.exit(p.returncode)
