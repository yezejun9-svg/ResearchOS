"""Run named T1-T7 gates against the clean combined candidate with raw receipts."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = ROOT / '.local/worktrees/schema25-core-composition-20261015'
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/builds/schema25-core-composition-20261015'
MAP = ROOT / 'execution/v2.4/receipts/W17/W17-03/composition_map_independent_codex/20261015-current-chat/COMPOSITION-MAP.json'
GO = ROOT / '.local/tools/go1.27.1/go/bin/go.exe'
NODE = Path('C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe')
ASSETS = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m1-wire-20261014/.local/m1-01')
M1_MANIFEST = ASSETS / 'manifest.json'
HEAD = '2a2d939c5f1e86156c4f5fe55e07b3a5d4fd4b02'
TREE = 'ad73440fdc98416687a75a8cb3ff23eff2cb0253'
ENV_KEYS = ('GOTOOLCHAIN','GOENV','GOROOT','GOPATH','GOMODCACHE','GOCACHE','GOTMPDIR',
            'GOPROXY','GOSUMDB','GOFLAGS','GOWORK','TEMP','TMP')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def git(*args):
    return subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0',*args], cwd=SOURCE).decode().strip()

def guard(plan):
    wanted = dict(plan['bounded_builder_scope']['expected_final_blobs'])
    wanted.update({r['path']:r['main'] for r in plan['main']['protected']})
    actual = []
    for rel, expected in sorted(wanted.items()):
        path = SOURCE / rel
        if not path.is_file() or path.is_symlink() or path.stat().st_size != expected['bytes'] or sha(path) != expected['sha256']:
            raise RuntimeError('candidate guard failed: ' + rel)
        actual.append({'path': rel, 'bytes': path.stat().st_size, 'sha256': sha(path)})
    if (git('rev-parse','HEAD') != HEAD or git('rev-parse','HEAD^{tree}') != TREE or
        git('status','--porcelain=v1','--untracked-files=no') != ''):
        raise RuntimeError('candidate Git guard failed')
    return actual

def env_for():
    BUILD.mkdir(parents=True, exist_ok=True)
    for name in ('go-cache','go-tmp','bin'):
        (BUILD / name).mkdir(exist_ok=True)
    env = dict(os.environ)
    env.update(GOTOOLCHAIN='local', GOENV='off', GOROOT=str(GO.parent.parent),
               GOPATH=str(ROOT / '.local/tools/gopath'), GOMODCACHE=str(ROOT / '.local/tools/gopath/pkg/mod'),
               GOCACHE=str(BUILD / 'go-cache'), GOTMPDIR=str(BUILD / 'go-tmp'),
               GOPROXY='off', GOSUMDB='off', GOFLAGS='-buildvcs=true', GOWORK='off',
               TEMP=str(BUILD / 'go-tmp'), TMP=str(BUILD / 'go-tmp'))
    return env

def run(name, argv, plan, env, timeout=600, expect=0):
    prefix = HERE / name
    if (prefix.with_suffix('.json')).exists():
        raise RuntimeError('attempt receipt exists: ' + name)
    before = guard(plan)
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        proc = subprocess.run(list(map(str, argv)), cwd=SOURCE, env=env, capture_output=True, timeout=timeout)
        code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        code, stdout, stderr = 124, e.stdout or b'', e.stderr or b''
    out, err = HERE / (name + '.stdout.raw'), HERE / (name + '.stderr.raw')
    out.write_bytes(stdout); err.write_bytes(stderr)
    after = guard(plan)
    row = {'schema':'researchos.schema25-combined-native-invocation/1','label':name,
           'argv':list(map(str,argv)),'cwd':str(SOURCE),'started_at':started,
           'ended_at':dt.datetime.now(dt.timezone.utc).isoformat(),'native_exit':code,'expected_exit':expect,
           'environment_allowlist':{k:env.get(k) for k in ENV_KEYS},
           'stdout':ref(out),'stderr':ref(err),'source_guard_count':len(before),
           'source_guard_before_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
           'source_guard_after_sha256':hashlib.sha256(json.dumps(after,sort_keys=True).encode()).hexdigest(),
           'source_guard_drift':before != after,'formal_increment':0}
    if argv and 'test' in str(argv[1:3]) and '-json' in argv:
        events = []
        for line in stdout.splitlines():
            try: events.append(json.loads(line))
            except json.JSONDecodeError: pass
        tests = [x for x in events if x.get('Test') and '/' not in x['Test'] and x.get('Action') in ('pass','fail','skip')]
        row['go_test_top_level'] = {key:sum(x['Action']==key for x in tests) for key in ('pass','fail','skip')}
        row['go_test_top_level_names'] = [x['Test'] for x in tests]
    write(prefix.with_suffix('.json'), row)
    print(json.dumps({'label':name,'exit':code,'expected':expect,'tests':row.get('go_test_top_level')},ensure_ascii=False),flush=True)
    if code != expect:
        raise RuntimeError(name + ' native exit ' + str(code))
    return row

def build_phase(plan, env):
    if (HERE/'T1-go-list.json').exists():
        raise RuntimeError('T1 already started')
    package_names = ['./apps/control','./ops/backup','./ops/supervisor/recovery_root',
                     './ops/supervisor/recovery_enrollment','./apps/runtime-verifier']
    run('T1-go-list',[GO,'list','-deps','-compiled','-json',*package_names],plan,env,180)
    built = []
    for name,pkg in [('control',package_names[0]),('backup',package_names[1]),
                     ('recovery-root',package_names[2]),('recovery-enrollment',package_names[3]),
                     ('runtime-verifier',package_names[4])]:
        binary = BUILD/'bin'/(name+'.exe')
        if binary.exists(): raise RuntimeError('build output already exists: '+name)
        run('T1-build-'+name,[GO,'build','-mod=readonly','-buildvcs=true','-o',binary,pkg],plan,env,600)
        run('T1-buildinfo-'+name,[GO,'version','-m',binary],plan,env,30)
        stamp = (HERE/('T1-buildinfo-'+name+'.stdout.raw')).read_text(encoding='utf-8',errors='replace')
        if 'vcs.revision='+HEAD not in stamp or 'vcs.modified=false' not in stamp:
            raise RuntimeError('buildinfo source stamp: '+name)
        built.append({'name':name,'package':pkg,'binary':ref(binary)})
    plan_sql = SOURCE/'internal/domain/contracts/runtime_pause_activations.sql'
    mig_sql = SOURCE/'migrations/sqlite/0025_runtime_pause_activations.sql'
    if plan_sql.read_bytes()!=mig_sql.read_bytes(): raise RuntimeError('embedded/schema SQL differs')
    if git('diff','--check',HEAD+'^',HEAD)!='': raise RuntimeError('diff check failed')
    delta=git('diff','--name-only','4f4023c956f84d65743f39ce77d6c8899a21ada1',HEAD).splitlines()
    if delta!=sorted(plan['bounded_builder_scope']['source_paths']): raise RuntimeError('exact53 changed paths')
    write(HERE/'T1-summary.json',{'status':'PASS','source_commit':HEAD,'source_tree':TREE,
          'built':built,'embedded_sql':ref(plan_sql),'migration_sql':ref(mig_sql),
          'changed_paths':delta,'protected_main_count':len(plan['main']['protected']),
          'formal_increment':0})

def test_phase(phase, plan, env):
    common=[GO,'test','-mod=readonly','-json']
    def go(name, package, pattern, timeout='8m', extra=None):
        argv=[*common,package,'-run',pattern,'-count=1','-timeout='+timeout]
        if extra: argv += ['-args',*extra]
        return run(phase+'-'+name,argv,plan,env,timeout=int(timeout[:-1])*60+90)
    if phase=='T2':
        run('T2-desktop-coding',[NODE,'--test','tests/ui/desktop/coding-authorization-boundary.test.mjs'],plan,env,180)
        go('verifier-host','./internal/host','^TestRuntimeVerifierReplacement',timeout='8m')
    elif phase=='T3':
        go('domain-backup','./internal/domain','^Test(PauseMigration|PauseHandoff|PreparedUpgrade|ConfigurationUpgrade)',timeout='10m')
        go('backup-cli','./ops/backup','^TestPauseHandoff',timeout='3m')
        go('recovery-authority','./internal/recoveryauthority','^TestPauseMigration',timeout='3m')
        go('recovery-root','./ops/supervisor/recovery_root','^TestPauseRoot',timeout='3m')
    elif phase=='T4':
        go('private-entry','./apps/control','^Test(PausePrivateControl|RuntimeVerifierReplacement)',timeout='8m')
    elif phase=='T5':
        go('domain-pause','./internal/domain','^Test(RuntimePause|RuntimeLocalLaunch|W06TaskControls)',timeout='8m')
        native_dir=HERE/'T5-host-native-evidence'
        native_dir.mkdir(exist_ok=False)
        go('host-eight','./internal/host',
           '^TestProductMu(Pause(Resume|Cancel|PreparedLeaseRecovery|ToolPublishAfterPause)|SecondPause(Resume|ModelAcrossHeartbeat|ToolAcrossHeartbeat|RevocationAcrossHeartbeat))Native$',
           timeout='12m',extra=['-pause-candidate-assets-dir',str(ASSETS),
           '-local-runtime-verifier-executable',str(BUILD/'bin/runtime-verifier.exe'),
           '-pause-native-evidence-dir',str(native_dir)])
        go('queue-three','./internal/domain',
           '^TestRuntimeClientQueue(ActualMuSameProcess|ActualMuCancelUnknownEffect|GoalCancelClaimOrdering)$',timeout='5m')
    elif phase=='T6':
        go('bridge-legacy-v1','./adapters/runtime',
           '^Test(BridgeCheckpoint|BridgeQueueEmpty|BridgeControlIdentity|BridgeProductionPauseCheckpointNative|PauseCheckpointFileBounds)',
           timeout='6m',extra=['-pause-worker-node',str(ASSETS/'node.exe'),
                               '-pause-worker-bundle',str(ASSETS/'mu-worker.mjs')])
        go('legacy-core','./internal/domain',
           '^TestRuntimeCoordinatorCheckpoint(Resume|CrashRecovery)$',timeout='5m')
    elif phase=='T7':
        go('fresh-schema25','./internal/domain','^TestPauseStorage',timeout='6m')
        go('future26-restore','./internal/domain',
           '^Test(PreparedUpgradeBackupRejectsFuture26|PauseMigrationReleaseAndOldPlanRemainExact|PauseMigrationPublicBackupRehearsalPreservesOriginal)$',timeout='6m')
    else: raise RuntimeError('unknown phase')

def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ('T1','T2','T3','T4','T5','T6','T7'):
        raise SystemExit('usage: run-bounded.py T1..T7')
    phase=sys.argv[1]
    plan=json.loads(MAP.read_bytes())
    guard(plan)
    env=env_for()
    if phase=='T1': build_phase(plan,env)
    else: test_phase(phase,plan,env)

if __name__=='__main__':
    main()
