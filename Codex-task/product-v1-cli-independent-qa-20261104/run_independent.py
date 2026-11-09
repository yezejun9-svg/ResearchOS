from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import shutil

root = Path(__file__).resolve().parent
stage = json.loads((root/'pin-stage.json').read_text(encoding='utf-8'))
wt = Path(stage['worktree'])
repo = Path('D:/作品集/ResearchOS/research-os')
go = repo/'.local/tools/go1.27.1/go/bin/go.exe'
gofmt = go.with_name('gofmt.exe')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(go) == 'd3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
directory = root/sys.argv[1]
directory.mkdir(exist_ok=False)
for name in ['tmp','home','appdata','localappdata','programdata','cache']:
    (root/name).mkdir(exist_ok=True)
environment = {key:value for key,value in os.environ.items() if key.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','PROCESSOR_ARCHITECTURE','NUMBER_OF_PROCESSORS']}
environment.update({'PATH':str(go.parent)+';'+str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32'),
    'GOENV':'off','GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','CGO_ENABLED':'0','GOWORK':'off','GOFLAGS':'','GOMAXPROCS':'2',
    'GOPATH':str(repo/'.local/tools/gopath'),'GOMODCACHE':str(repo/'.local/tools/gopath/pkg/mod'),
    'GOCACHE':str(root/'cache'),'GOTMPDIR':str(root/'tmp'),'TEMP':str(root/'tmp'),'TMP':str(root/'tmp'),
    'USERPROFILE':str(root/'home'),'APPDATA':str(root/'appdata'),'LOCALAPPDATA':str(root/'localappdata'),'PROGRAMDATA':str(root/'programdata'),
    'RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED':'1'})
overlay = json.loads((root/'overlay.json').read_text(encoding='utf-8'))
virtual = wt/'apps/cli/independent_productv1_qa_test.go'
assert not virtual.exists()
fixture = directory/'independent_cli_test.go'
shutil.copyfile(root/'independent_cli_test.go',fixture)
overlay['Replace'][str(virtual)] = str(fixture)
(directory/'overlay.json').write_text(json.dumps(overlay,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
selector = sys.argv[2]
if selector == 'vet':
    argv = [str(go),'vet','-mod=readonly','-p=2','-overlay',str(directory/'overlay.json'),'./apps/cli']
else:
    argv = [str(go),'test','-mod=readonly','-p=2','-count=1','-parallel=1','-timeout=120s','-json','-overlay',str(directory/'overlay.json'),'-run',selector,'./apps/cli']
inputs = {str(fixture):sha(fixture)}
inputs.update({str(root/'source-snapshot'/row['path']):row['sha256'] for row in stage['exact3']})
(directory/'command.json').write_text(json.dumps({'argv':argv,'cwd':str(wt),'environment':environment,'input_pins':inputs,'fake_native_only':True,'http':'owned loopback or injected RoundTripper only'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (directory/'stdout').open('wb') as stdout,(directory/'stderr').open('wb') as stderr:
    result = subprocess.run(argv,cwd=wt,env=environment,stdout=stdout,stderr=stderr,timeout=360)
unchanged = all(sha(Path(path)) == digest for path,digest in inputs.items())
(directory/'result.json').write_text(json.dumps({'exit_code':result.returncode,'input_pins_unchanged':unchanged,'selector':selector},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'exit_code':result.returncode,'input_pins_unchanged':unchanged,'directory':str(directory)}))
raise SystemExit(result.returncode if unchanged else 2)
