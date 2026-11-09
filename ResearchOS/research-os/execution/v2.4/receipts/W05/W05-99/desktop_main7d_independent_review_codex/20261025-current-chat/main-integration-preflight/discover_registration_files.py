import json,pathlib,subprocess
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
files=[p.decode('utf-8') for p in subprocess.run(['git','--no-optional-locks','-C',str(R),'ls-files','-z'],capture_output=True,check=True).stdout.split(b'\0') if p]
exclude=('execution/receipts/','execution/verifier/','execution/invocations/','execution/v2.4/receipts/','third_party/','apps/desktop/node_modules/','apps/web/node_modules/')
matches=[p for p in files if not p.startswith(exclude) and ('manifest' in pathlib.PurePosixPath(p).name.lower() or 'path_map' in pathlib.PurePosixPath(p).name.lower())]
print(json.dumps({'registration_candidates':matches,'dispatcher_files':[p for p in files if p.startswith('execution/command_dispatcher/')],'apps_root':[p for p in files if p.startswith('apps/') and p.count('/')==1]},indent=2))
