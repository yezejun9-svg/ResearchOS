from pathlib import Path
import argparse, datetime, hashlib, json, os, subprocess, sys
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.local' / 'paperclip'
EVIDENCE = ROOT / 'qualification/core/evidence'
SHA = 'd554c4789ed3930f8a53ac9fdf6503b3187097da'
TAG = 'v2026.916.1'
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def command(name, argv, cwd=ROOT, timeout=180, env=None):
    dest = EVIDENCE/name
    if (dest/'command.json').exists():
        raise SystemExit(f'Refusing to overwrite evidence: {dest}; select --evidence-dir')
    dest.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    launch = argv
    if os.name == 'nt' and argv[0].endswith('.cmd'):
        launch = ['cmd.exe', '/d', '/s', '/c', subprocess.list2cmdline(argv)]
    cleanup = None
    try:
        with (dest/'stdout.txt').open('wb') as output, (dest/'stderr.txt').open('wb') as errors:
            process = subprocess.Popen(launch, cwd=cwd, stdout=output, stderr=errors, env=env)
            try:
                code = process.wait(timeout=timeout)
                status = 'EXITED'
            except subprocess.TimeoutExpired:
                kill_argv = ['taskkill', '/PID', str(process.pid), '/T', '/F'] if os.name == 'nt' else ['kill', str(process.pid)]
                killed = subprocess.run(kill_argv, capture_output=True)
                cleanup = {'argv':kill_argv,'exit_code':killed.returncode,'stdout':killed.stdout.decode('utf-8',errors='replace'),'stderr':killed.stderr.decode('utf-8',errors='replace')}
                process.wait(timeout=20)
                code, status = process.returncode, 'TIMEOUT'
        out, err = (dest/'stdout.txt').read_bytes(), (dest/'stderr.txt').read_bytes()
    except OSError as exc:
        out, err, code = b'', str(exc).encode('utf-8'), None
        status = 'LAUNCH_ERROR'
    (dest/'stdout.txt').write_bytes(out)
    (dest/'stderr.txt').write_bytes(err)
    record = {'argv': launch, 'requested_argv': argv, 'cwd': str(cwd), 'started_at': started, 'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exit_code': code, 'process_status': status, 'cleanup':cleanup, 'stdout_sha256':sha(dest/'stdout.txt'), 'stderr_sha256':sha(dest/'stderr.txt')}
    write(dest/'command.json', record)
    print(json.dumps({'name': name, **record}, ensure_ascii=False), flush=True)
    print(out.decode('utf-8', errors='replace')[-4500:], flush=True)
    print(err.decode('utf-8', errors='replace')[-2500:], flush=True)
    return record
if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage', choices=['fetch','install','start','inspect','probe','repair','repair-execute','policy','documented-start','check','final-state'])
    parser.add_argument('--evidence-dir', type=Path, default=EVIDENCE)
    args=parser.parse_args()
    EVIDENCE=args.evidence_dir.resolve()
    if args.stage == 'fetch':
        command('environment', [sys.executable,'-X','utf8','-c','import platform,sys; print(platform.platform()); print(sys.version); print(sys.executable)'])
        command('node-version',['node','--version'])
        command('pnpm-version',['pnpm.cmd','--version'])
        if SOURCE.exists():
            raise SystemExit('Source already exists: do not silently repeat fetch or replace evidence')
        r=command('clone',['git','clone','--depth','1','--branch',TAG,'https://github.com/paperclipai/paperclip.git',str(SOURCE)], timeout=180)
        if r['exit_code'] != 0: raise SystemExit(1)
        command('source-head',['git','rev-parse','HEAD'],SOURCE)
        command('source-tag',['git','rev-parse',TAG+'^{commit}'],SOURCE)
        command('source-status',['git','status','--short'],SOURCE)
        actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE, encoding='utf-8').strip()
        assert actual == SHA, (actual,SHA)
        write(ROOT/'qualification/core/source.json',{'repository':'https://github.com/paperclipai/paperclip','tag':TAG,'commit':actual,'lockfile_sha256':sha(SOURCE/'pnpm-lock.yaml'),'scope':'UPSTREAM_SOURCE_IDENTITY_ONLY'})
    elif args.stage == 'install':
        command('install',['pnpm.cmd','install','--frozen-lockfile'],SOURCE,timeout=360)
    elif args.stage == 'start':
        env=os.environ.copy()
        env['PAPERCLIP_HOME']=str(ROOT/'.local'/'paperclip-home')
        env['PORT']='13179'
        env['HOST']='127.0.0.1'
        env['PAPERCLIP_OPEN_ON_START']='false'
        command('start',['pnpm.cmd','--filter','@paperclipai/server','dev'],SOURCE,timeout=45,env=env)
    elif args.stage == 'inspect':
        command('source-search',['rg','-n','executionPolicy|before.*done|win32|postgres','server/src/routes/issues.ts','server/src/services/issue-execution-policy.ts','cli/src/services/service-manager.ts','server/src/index.ts'],SOURCE)

    elif args.stage == 'probe':
        command('health-probe', [sys.executable,'-X','utf8','-c',"import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:13179/api/health',timeout=3).read().decode('utf-8'))"])

    elif args.stage == 'repair':
        download = """from pathlib import Path
import urllib.request,hashlib,zipfile,json
base=Path.cwd()/'.local'/'tools'; base.mkdir(parents=True,exist_ok=True)
name='node-v24.11.0-win-x64.zip'
checks=urllib.request.urlopen('https://nodejs.org/dist/v24.11.0/SHASUMS256.txt',timeout=60).read()
(base/'SHASUMS256.txt').write_bytes(checks)
archive=base/name
with urllib.request.urlopen('https://nodejs.org/dist/v24.11.0/'+name,timeout=60) as response:
    archive.write_bytes(response.read())
expected=next(line.split()[0] for line in checks.decode('utf-8').splitlines() if line.endswith('  '+name))
actual=hashlib.sha256(archive.read_bytes()).hexdigest()
assert actual==expected,(actual,expected)
with zipfile.ZipFile(archive) as bundle: bundle.extractall(base)
print(json.dumps({'url':'https://nodejs.org/dist/v24.11.0/'+name,'sha256':actual,'verified':True}))
"""
        fetched=command('repair-node-download',[sys.executable,'-X','utf8','-c',download],timeout=180)
        if fetched['exit_code'] != 0: raise SystemExit(1)
        node_dir=ROOT/'.local/tools/node-v24.11.0-win-x64'
        env=os.environ.copy(); env['PATH']=str(node_dir)+os.pathsep+env['PATH']; env['CI']='true'
        command('repair-node-version',[str(node_dir/'node.exe'),'--version'],env=env)
    elif args.stage == 'repair-execute':
        node_dir=ROOT/'.local/tools/node-v24.11.0-win-x64'
        pnpm=Path(os.environ['LOCALAPPDATA'])/'node/corepack/v1/pnpm/9.15.4/bin/pnpm.cjs'
        (node_dir/'pnpm.cmd').write_text('@echo off\n'+chr(34)+'%~dp0node.exe'+chr(34)+' '+chr(34)+str(pnpm)+chr(34)+' %*\n',encoding='utf-8')
        runner=[str(node_dir/'node.exe'),str(pnpm)]
        env=os.environ.copy(); env['PATH']=str(node_dir)+os.pathsep+env['PATH']; env['CI']='true'
        command('repair-execute-install',runner+['install','--frozen-lockfile','--virtual-store-dir='+str(ROOT/'.local/v'),'--config.virtual-store-dir-max-length=32','--store-dir='+str(ROOT/'.local/store')],SOURCE,timeout=360,env=env)
        env['PAPERCLIP_HOME']=str(ROOT/'.local/paperclip-home')
        env['PORT']='13179'; env['HOST']='127.0.0.1'; env['PAPERCLIP_OPEN_ON_START']='false'
        command('repair-execute-start',runner+['--filter','@paperclipai/server','dev'],SOURCE,timeout=45,env=env)
        command('repair-execute-health-probe',[sys.executable,'-X','utf8','-c',"import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:13179/api/health',timeout=3).read().decode('utf-8'))"])

    elif args.stage in ('policy','documented-start'):
        node_dir=ROOT/'.local/tools/node-v24.11.0-win-x64'
        env=os.environ.copy(); env['PATH']=str(node_dir)+os.pathsep+env['PATH']
        if args.stage == 'policy':
            command('policy-probe',[str(node_dir/'node.exe'),str(SOURCE/'server/node_modules/tsx/dist/cli.mjs'),str(ROOT/'qualification/core/probe-policy.ts')],SOURCE,timeout=45,env=env)
        else:
            env['PAPERCLIP_HOME']=str(ROOT/'.local/paperclip-home');env['PORT']='13179';env['HOST']='127.0.0.1';env['PAPERCLIP_OPEN_ON_START']='false'
            pnpm=Path(os.environ['LOCALAPPDATA'])/'node/corepack/v1/pnpm/9.15.4/bin/pnpm.cjs'
            command('documented-start',[str(node_dir/'node.exe'),str(pnpm),'dev:once'],SOURCE,timeout=90,env=env)

    elif args.stage == 'check':
        command('evidence-check',[sys.executable,'-X','utf8',str(ROOT/'qualification/core/verify_evidence.py')])
    elif args.stage == 'final-state':
        command('final-source-status',['git','status','--short'],SOURCE)
        command('final-health-probe',[sys.executable,'-X','utf8','-c',"import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:13179/api/health',timeout=3).read().decode('utf-8'))"])
