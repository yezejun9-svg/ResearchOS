"""Build a new, source-bound Desktop development tree; never overwrite a release."""
import argparse, datetime, hashlib, json, os, pathlib, shutil, subprocess, sys, uuid
ROOT = pathlib.Path(__file__).resolve().parents[2]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')

def stream_json(text):
    decoder=json.JSONDecoder(); offset=0
    while offset<len(text):
        while offset<len(text) and text[offset].isspace(): offset+=1
        if offset==len(text): break
        value,end=decoder.raw_decode(text,offset); yield value; offset=end

def main():
    parser=argparse.ArgumentParser()
    for flag in ['go','node','electron','module-cache','web-modules','output','receipts']:
        parser.add_argument('--'+flag,required=True)
    args=parser.parse_args()
    output=pathlib.Path(args.output).resolve(); receipts=pathlib.Path(args.receipts).resolve()
    if not output.is_relative_to(ROOT) or output.exists() or not receipts.is_relative_to(ROOT) or receipts.exists():
        raise SystemExit('new output and receipt directories must belong to this worktree')
    output.mkdir(parents=True); receipts.mkdir(parents=True)
    go=pathlib.Path(args.go).resolve(); goroot=go.parent.parent
    env={**os.environ,'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(goroot),'GOPATH':str(pathlib.Path(args.module_cache).resolve().parent.parent),
         'GOMODCACHE':str(pathlib.Path(args.module_cache).resolve()),'GOCACHE':str(output/'go-cache'),'GOTMPDIR':str(output/'go-tmp'),'GOPROXY':'off','GOSUMDB':'off'}
    pathlib.Path(env['GOTMPDIR']).mkdir()
    invocations=[]
    def run(name, argv, cwd=ROOT, timeout=120, *, decode_stdout=True):
        start=datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            proc=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,timeout=timeout); code=proc.returncode; stdout=proc.stdout; stderr=proc.stderr
        except subprocess.TimeoutExpired as e:
            code=124;stdout=e.stdout or b'';stderr=e.stderr or b''
        (receipts/(name+'.stdout')).write_bytes(stdout);(receipts/(name+'.stderr')).write_bytes(stderr)
        row={'actualargv':[str(x) for x in argv],'cwd':str(cwd),'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':code,
             'stdout':name+'.stdout','stderr':name+'.stderr','environment':{k:env[k] for k in ['GOTOOLCHAIN','GOENV','GOROOT','GOPATH','GOMODCACHE','GOCACHE','GOTMPDIR','GOPROXY','GOSUMDB']}}
        put(receipts/(name+'.invocation.json'),row);invocations.append(row)
        if code:
            put(receipts/'stopped.json',{'first_unexpected':row,'source_acceptance':False});raise SystemExit(code)
        return stdout.decode('utf-8') if decode_stdout else stdout
    tools=[]
    for name,p in [('go',go),('node',pathlib.Path(args.node)),('electron',pathlib.Path(args.electron)),('python',pathlib.Path(sys.executable))]:
        tools.append({'name':name,'path':str(p.resolve()),'sha256':digest(p),'bytes':p.stat().st_size})
    powershell=pathlib.Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    tools.append({'name':'powershell-public-module-audit','path':str(powershell),'sha256':digest(powershell),'bytes':powershell.stat().st_size})
    put(receipts/'tools.before.json',tools)
    expected={'go':'d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490','node':'5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6','electron':'8d205e25b40da3ada4a08c92f32bfbd8e8d38edb4bfe443deea77fc9de685bac'}
    if any(x['name'] in expected and x['sha256']!=expected[x['name']] for x in tools):raise SystemExit('locked tool mismatch')
    run('go-version',[str(go),'version'])
    run('node-version',[args.node,'--version'])
    # Electron version is captured from its locked package metadata; invoking it
    # here would launch an unregistered GUI process. Actual fixture launch owns it.
    packages=list(stream_json(run('go-list',[str(go),'list','-deps','-test','-compiled','-json','./apps/desktop/validator'])))
    fixture_dir=output/'fixtures';fixture_dir.mkdir()
    fixture_source=fixture_dir/'negative-child.go'
    fixture_source.write_text('package main\nimport("os";"time";"path/filepath";"encoding/json";"encoding/base64";"crypto/sha256";"fmt";"io";"os/exec")\nvar binding string\nfunc main(){\n if len(os.Args)>1&&os.Args[1]=="--hold-public-pipe"{time.Sleep(12*time.Second);return}\n executable,_:=os.Executable();modeBytes,_:=os.ReadFile(filepath.Join(filepath.Dir(executable),"fixture-mode.txt"));mode:=string(modeBytes)\n raw,_:=io.ReadAll(io.LimitReader(os.Stdin,33555461));var p map[string]interface{};json.Unmarshal(raw,&p)\n if mode=="nonzero"{os.Exit(7)}\n if mode=="hang"{time.Sleep(40*time.Second);return}\n if mode=="stderr-cap"{os.Stderr.Write(make([]byte,16385));time.Sleep(time.Second);return}\n if mode=="output-cap"{os.Stdout.Write(make([]byte,67108865));return}\n if mode=="truncated"{fmt.Print("{\\"schema\\":");return}\n req,_:=base64.StdEncoding.DecodeString(fmt.Sprint(p["request_raw_base64"]));res,_:=base64.StdEncoding.DecodeString(fmt.Sprint(p["response_raw_base64"]))\n v:=map[string]interface{}{"schema":"researchos.desktop.http-validation/1","phase":p["phase"],"nonce":p["nonce"],"http_status":p["http_status"],"request_sha256":fmt.Sprintf("%x",sha256.Sum256(req)),"response_sha256":fmt.Sprintf("%x",sha256.Sum256(res)),"schema_sha256_pair":[]string{"8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b","b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54"},"build_input_digest":binding,"outcome":"VALID","reason":"","value":nil}\n switch mode{case "version":v["schema"]="wrong";case "nonce":v["nonce"]="wrong";case "request-digest":v["request_sha256"]="wrong";case "response-digest":v["response_sha256"]="wrong";case "http-status":v["http_status"]=200;case "phase":v["phase"]="RESPONSE"}\n if mode=="unreaped"{c:=exec.Command(executable,"--hold-public-pipe");c.Stdout=os.Stdout;c.Stderr=os.Stderr;if c.Start()!=nil{os.Exit(9)};fmt.Fprintf(os.Stderr,"PUBLIC_FIXTURE_PIPE_HOLDER_PID=%d\\n",c.Process.Pid)}\n b,_:=json.Marshal(v);if mode=="nbsp"{os.Stdout.Write([]byte{0xc2,0xa0})};os.Stdout.Write(b)\n if mode=="two-values"{os.Stdout.Write([]byte(" {}"))}\n}\n',encoding='utf-8',newline='\n')
    packages.extend(stream_json(run('go-list-negative-fixture',[str(go),'list','-deps','-compiled','-json',str(fixture_source)])))
    paths={ROOT/'go.mod',ROOT/'go.sum',fixture_source}
    for package in packages:
        module=package.get('Module') or {}
        if module.get('GoMod'):paths.add(pathlib.Path(module['GoMod']))
        directory=pathlib.Path(package.get('Dir',''))
        if not directory.is_dir():continue
        # All platform variants and tests, not only the current build's selected list.
        paths.update(directory.glob('*.go'))
        for field in ['GoFiles','CompiledGoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles']:
            for name in package.get(field,[]):
                p=pathlib.Path(name); paths.add(p if p.is_absolute() else directory/p)
    paths.update(p for p in (goroot/'pkg/tool').rglob('*') if p.is_file())
    for base in [ROOT/'apps/desktop/main',ROOT/'apps/desktop/preload',ROOT/'apps/desktop/validator',ROOT/'apps/web/src']:
        paths.update(p for p in base.rglob('*') if p.is_file())
    paths.add(pathlib.Path(__file__).resolve())
    paths.add(ROOT/'spec/v2.0/ui/design-tokens.json')
    # main.js resolves the published route table at runtime in the bound tree.
    paths.add(ROOT/'spec/v2.0/contracts/openapi.json')
    paths.add(ROOT/'tests/contracts/fixtures/client_protocol_v2_fixtures.json')
    paths.add(ROOT/'tests/ui/desktop/w13-react.test.js')
    paths.update(p for p in (ROOT/'apps/web').glob('*') if p.is_file())
    paths.update(p for p in (ROOT/'apps/web/public').rglob('*') if p.is_file())
    paths.update(p for p in (ROOT/'tests/ui/desktop').glob('*.mjs') if p.is_file())
    paths.update(p for p in (ROOT/'apps/desktop/tests').glob('*.js') if p.is_file())
    for p in [ROOT/'apps/desktop/package.json',ROOT/'apps/desktop/package-lock.json',ROOT/'apps/web/package.json',ROOT/'apps/web/package-lock.json']:
        paths.add(p)
    # Record actual available Electron/Node dependencies used by fixture/renderer.
    for base in [pathlib.Path(args.electron).resolve().parent,pathlib.Path(args.web_modules).resolve()]:
        paths.update(p for p in base.rglob('*') if p.is_file())
    inputs=[{'path':str(p.resolve()),'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(paths) if p.is_file()]
    put(receipts/'inputs.before.json',inputs)
    bound=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    app=output/'apps/desktop'; resource=app/'resources/client-wire';resource.mkdir(parents=True)
    binary=resource/'researchos-client-wire-validator.exe'
    run('go-build',[str(go),'build','-mod=readonly','-work','-x','-ldflags','-X main.buildInputDigest='+bound,'-o',str(binary),'./apps/desktop/validator'])
    run('negative-child-build',[str(go),'build','-mod=readonly','-work','-x','-ldflags','-X main.binding='+bound,'-o',str(fixture_dir/'negative-child.exe'),str(fixture_source)])
    run('go-test-build',[str(go),'test','-c','-mod=readonly','-work','-x','-o',str(output/'validator.test.exe'),'./apps/desktop/validator'])
    workfiles=[]
    for p in sorted((output/'go-tmp').rglob('*')):
        if p.is_file():workfiles.append({'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size})
    # Include cached archives referenced by generated importcfg, preserving full files.
    archives=set()
    for p in (output/'go-tmp').rglob('importcfg*'):
        for line in p.read_text(encoding='utf-8').splitlines():
            if line.startswith('packagefile ') and '=' in line:
                a=pathlib.Path(line.split('=',1)[1]);
                if a.is_file():archives.add(a)
    put(receipts/'compiler-work-archive.json',{'WORK':workfiles,'archives':[{'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(archives)]})
    for name in ['main','preload']:
        shutil.copytree(ROOT/'apps/desktop'/name,app/name)
    shutil.copy2(ROOT/'apps/desktop/package.json',app/'package.json')
    (output/'spec/v2.0/ui').mkdir(parents=True)
    shutil.copy2(ROOT/'spec/v2.0/ui/design-tokens.json',output/'spec/v2.0/ui/design-tokens.json')
    (output/'spec/v2.0/contracts').mkdir(parents=True)
    shutil.copy2(ROOT/'spec/v2.0/contracts/openapi.json',output/'spec/v2.0/contracts/openapi.json')
    web=output/'apps/web';shutil.copytree(ROOT/'apps/web/src',web/'src')
    for name in ['index.html','package.json','package-lock.json']:
        if (ROOT/'apps/web'/name).is_file():shutil.copy2(ROOT/'apps/web'/name,web/name)
    for p in (ROOT/'apps/web').glob('vite.config.*'):shutil.copy2(p,web/p.name)
    if (ROOT/'apps/web/public').is_dir():shutil.copytree(ROOT/'apps/web/public',web/'public')
    # A new junction in our new output tree, targeting only an existing public
    # package cache. No package manager, install scripts or source mutation.
    run('web-module-junction',['cmd','/c','mklink','/J',str(web/'node_modules'),str(pathlib.Path(args.web_modules).resolve())],decode_stdout=False)
    run('react-build',[args.node,str(pathlib.Path(args.web_modules)/'vite/bin/vite.js'),'build','--outDir',str(web/'dist')],cwd=web)
    modules=[{'path':p.relative_to(app).as_posix(),'sha256':digest(p)} for folder in [app/'main',app/'preload'] for p in sorted(folder.rglob('*')) if p.is_file()]
    assets=[{'path':p.relative_to(web/'dist').as_posix(),'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted((web/'dist').rglob('*')) if p.is_file()]
    descriptor={'schema':'researchos.desktop.client-wire-release/1','release_id':uuid.uuid4().hex,'child_protocol':'researchos.desktop.http-validation/1','binary_sha256':digest(binary),'binary_bytes':binary.stat().st_size,
      'schema_sha256_pair':['8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b','b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54'],'build_input_digest':bound,
      'exact_module_source_inventory':modules,'compiled_React_asset_inventory':assets,'tools':tools,'compile_receipts':str(receipts),'qualification_fixture_binary':{'path':str(fixture_dir/'negative-child.exe'),'sha256':digest(fixture_dir/'negative-child.exe'),'source_sha256':digest(fixture_source),'mode':'PUBLIC_SYNTHETIC_NEGATIVE_ONLY'}}
    descriptor['go_tool_ref']=next(x for x in tools if x['name']=='go')
    for key,name in [('compile_invocation_ref','go-build.invocation.json'),('full_input_manifest_ref','inputs.before.json'),('compiler_generated_importcfg_archives_ref','compiler-work-archive.json')]:
        p=receipts/name;descriptor[key]={'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size}
    descriptor['legacy_HTML_sha256']=digest(app/'main/workbench.html')
    descriptor['public_openapi_sha256']=digest(output/'spec/v2.0/contracts/openapi.json')
    put(resource/'descriptor.json',descriptor)
    after=[{**row,'current_sha256':digest(pathlib.Path(row['path']))} for row in inputs]
    drift=[x for x in after if x['sha256']!=x['current_sha256']]
    put(receipts/'inputs.after.json',after);put(receipts/'result.json',{'status':'BUILT_NOT_TESTED','source_acceptance':False,'drift':drift,'descriptor':str(resource/'descriptor.json'),'binary_sha256':digest(binary),'build_input_digest':bound,'invocations':invocations})
    if drift:raise SystemExit('source drift: build not current')
    print(json.dumps({'descriptor':str(resource/'descriptor.json'),'input_count':len(inputs),'build_input_digest':bound,'binary_sha256':digest(binary)}))
if __name__=='__main__':main()
