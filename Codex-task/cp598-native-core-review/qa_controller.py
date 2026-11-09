import datetime, hashlib, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
WT = ROOT / '.local/worktrees/w14-native-create-core-20261104'
RECEIPT = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/core'
HERE = Path(__file__).resolve().parent
RUN = HERE / 'run-01'
GO = ROOT / '.local/tools/go1.27.1/go/bin/go.exe'
MOD = HERE.parent / 'cp586-continuation/production-binding-review/run-01/private/gopath/pkg/mod'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name, value):
    p = RUN / name
    assert not p.exists(), 'Do not overwrite evidence: ' + str(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')

def prepare():
    assert not RUN.exists(), 'Run already exists; inspect before retry'
    RUN.mkdir()
    pins = {
      'source-manifest.json':'094f93e01cb1c97df643a6a45f781f94e77557fdf9ddc8d1b322d8f5330c54f0',
      'construction-freeze.json':'84cce3bcec5842de68a80fef4393493f19a531ee32c5f16323e9549f4ee2401e',
      'author-summary.json':'078f71d56f43439b7ee3ef7ae134b11057f10b3ca427b55a708e395788546f85',
      'diagnostics.json':'5fdde825d75d4a069ef7634d7d7ab9407b16d28de8268350d4a03d31ebbab11c'}
    for name, digest in pins.items():
        p = RECEIPT / 'author' / name
        assert sha(p) == digest, name
        (RUN / ('author-' + name)).write_bytes(p.read_bytes())
    manifest = json.loads((RUN / 'author-source-manifest.json').read_bytes())
    scope = json.loads((RECEIPT / 'scope.json').read_bytes())
    assert sha(RECEIPT / 'scope.json') == manifest['scope_sha256']
    assert manifest['construction_frozen'] and not manifest['source_modification_permitted']
    files = manifest['source_files']
    assert len(files) == 22 and set(x['path'] for x in files) == set(scope['production_paths'] + scope['test_paths'])
    for item in files:
        p = WT / item['path']
        assert sha(p) == item['sha256'] and p.stat().st_size == item['bytes'], item['path']
        target = RUN / 'frozen-source' / item['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(p.read_bytes())
    assert sha(GO) == 'd3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
    assert MOD.is_dir()
    save('inputs.json', {'manifest_sha256':pins['source-manifest.json'], 'source_sha256':{x['path']:x['sha256'] for x in files}, 'tool_go':str(GO), 'tool_go_sha256':sha(GO), 'go_mod_sha256':sha(WT/'go.mod'), 'go_sum_sha256':sha(WT/'go.sum'), 'module_inputs':str(MOD), 'network':False, 'formal_increment':0})
    print(json.dumps({'prepared':True,'source_count':len(files),'run':str(RUN)}))

def run(phase, args):
    assert (RUN / 'inputs.json').exists()
    for p in ('private/cache','private/tmp','private/profile','private/appdata','private/localappdata','private/gopath'):
        (RUN / p).mkdir(parents=True, exist_ok=True)
    env = {k:os.environ[k] for k in ('SystemRoot','WINDIR','COMSPEC') if k in os.environ}
    env.update({'PATH':str(GO.parent) + os.pathsep + str(Path(env['SystemRoot'])/'System32'),
       'USERPROFILE':str(RUN/'private/profile'),'APPDATA':str(RUN/'private/appdata'),'LOCALAPPDATA':str(RUN/'private/localappdata'),
       'TEMP':str(RUN/'private/tmp'),'TMP':str(RUN/'private/tmp'),'GOTMPDIR':str(RUN/'private/tmp'),
       'GOCACHE':str(RUN/'private/cache'),'GOPATH':str(RUN/'private/gopath'),'GOMODCACHE':str(MOD),
       'GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GOENV':'off','GOWORK':'off','CGO_ENABLED':'0','GOTELEMETRY':'off','GOVCS':'*:off','GOFLAGS':'-mod=readonly'})
    cmd = [str(GO)] + args
    save(phase+'.command.json',{'argv':cmd,'cwd':str(WT),'environment':env,'execution_class':'FRESH_SQLITE_RECORDER_INJECTED_PEER_NO_NATIVE_MODEL_OR_LISTENER','formal_increment':0})
    save(phase+'.started.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    with (RUN/(phase+'.stdout.raw')).open('wb') as out, (RUN/(phase+'.stderr.raw')).open('wb') as err:
        p = subprocess.Popen(cmd,cwd=WT,env=env,stdout=out,stderr=err)
        code = p.wait()
    counts = {'run':0,'pass':0,'fail':0,'skip':0,'top_pass':0,'sub_pass':0}
    roster = []
    for line in (RUN/(phase+'.stdout.raw')).read_bytes().splitlines():
        try: item=json.loads(line)
        except (ValueError,UnicodeError): continue
        name=item.get('Test')
        action=item.get('Action')
        if name and action in counts: counts[action]+=1
        if name and action in ('pass','fail','skip'):
            roster.append({'package':item.get('Package'),'test':name,'action':action})
            if action=='pass': counts['sub_pass' if '/' in name else 'top_pass']+=1
    result={'exit_code':code,'counts':counts,'roster':roster,'stdout_sha256':sha(RUN/(phase+'.stdout.raw')),'stderr_sha256':sha(RUN/(phase+'.stderr.raw')),'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'formal_increment':0}
    save(phase+'.result.json',result)
    print(json.dumps({'phase':phase,'exit_code':code,'counts':counts}))
    return code

if __name__=='__main__':
    if sys.argv[1]=='prepare': prepare()
    elif sys.argv[1]=='focused': sys.exit(run('independent-focused',['test','-json','-count=1','-vet=off','-timeout=120s','-p=1','-parallel=1','-run','^Test(NativeCreate|NativeWriterOrigin|NativeOriginStore|PreparedNativeOrigin)','./internal/domain','./internal/host','./internal/api']))
    elif sys.argv[1]=='attacks': sys.exit(run('independent-attacks',['test','-json','-count=1','-vet=off','-timeout=120s','-p=1','-parallel=1','-overlay='+str(RUN/'overlay.json'),'-run','^TestIndependentNative','./internal/domain']))
    elif sys.argv[1]=='vet': sys.exit(run('independent-vet',['vet','-p=1','./internal/domain','./internal/host','./internal/api','./apps/control']))
    else: raise SystemExit('unknown phase')
