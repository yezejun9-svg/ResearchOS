"""One-shot historical pin and Main4f baseline checks for the T3 failures."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

HERE = Path(__file__).resolve().parent
b = runpy.run_path(str(HERE / 'run-bounded.py'))
ROOT = b['ROOT']
GO = b['GO']
MAP = b['MAP']
BASE = ROOT / '.local/worktrees/verifier-replacement-20261014'
RESOURCE = ROOT / 'execution/v2.4/receipts/W05/W05-99/backup_regression_resource_readonly_codex/9e4a05cf0d514cfcacd6cfd74acdb609/resource-report.json'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def git(cwd, *args):
    return subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0',*args], cwd=cwd).decode().strip()

def baseline_guard():
    if git(BASE,'rev-parse','HEAD') != '4f4023c956f84d65743f39ce77d6c8899a21ada1':
        raise RuntimeError('Main4f verifier worktree HEAD changed')
    if git(BASE,'status','--porcelain=v1','--untracked-files=no'):
        raise RuntimeError('Main4f verifier worktree tracked changes')
    paths = ['internal/domain/backup_configuration_upgrade_test.go',
             'internal/domain/client_command_identity.go',
             'internal/domain/client_protocol.go',
             'migrations/sqlite/0023_host_model_configuration.sql']
    return {'head':git(BASE,'rev-parse','HEAD'),
            'tree':git(BASE,'rev-parse','HEAD^{tree}'),
            'files':{p:digest(BASE/p) for p in paths}}

def baseline():
    name='T3B-main4f-active-queue'
    if (HERE/(name+'.json')).exists():
        raise RuntimeError('baseline already attempted')
    before=baseline_guard()
    argv=[str(GO),'test','-mod=readonly','-json','./internal/domain',
          '-run','^TestConfigurationUpgradeActiveQueueRecovery$','-count=1','-timeout=10m']
    env=b['env_for']()
    started=dt.datetime.now(dt.timezone.utc).isoformat()
    proc=subprocess.run(argv,cwd=BASE,env=env,capture_output=True,timeout=690)
    (HERE/(name+'.stdout.raw')).write_bytes(proc.stdout)
    (HERE/(name+'.stderr.raw')).write_bytes(proc.stderr)
    after=baseline_guard()
    result={'schema':'researchos.schema25-baseline-diagnostic/1','label':name,
            'argv':argv,'cwd':str(BASE),'started_at':started,
            'ended_at':dt.datetime.now(dt.timezone.utc).isoformat(),
            'native_exit':proc.returncode,'environment_allowlist':{k:env.get(k) for k in b['ENV_KEYS']},
            'source_before':before,'source_after':after,'source_drift':before!=after,
            'stdout':b['ref'](HERE/(name+'.stdout.raw')),
            'stderr':b['ref'](HERE/(name+'.stderr.raw')),'formal_increment':0}
    save(name+'.json',result)
    print(json.dumps({'label':name,'exit':proc.returncode,'drift':before!=after}),flush=True)

def historical():
    plan=json.loads(MAP.read_bytes())
    b['guard'](plan)
    report=json.loads(RESOURCE.read_bytes())
    pins=report['env']
    source=pins['RESEARCHOS_CONFIGURATION_OLD_CONTROL']
    target=pins['RESEARCHOS_CONFIGURATION_TARGET_PROGRAM']
    root=pins['RESEARCHOS_CONFIGURATION_OLD_ROOT']
    entries=[source,target,*root['members']]
    for item in entries:
        path=Path(item['path'])
        if not path.is_file() or path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise RuntimeError('historical pin mismatch '+str(path))
    save('T3R-historical-pins.json',{'schema':'researchos.schema25-historical-pin-check/1',
         'source_report':b['ref'](RESOURCE),'program_source22':source,
         'program_target23':target,'frozen_root':{'path':root['root'],
         'count':len(root['members']),'numbered_sql_count':root['numbered_sql_count'],
         'manifest_sha256_from_report':root['manifest_sha256']},
         'verified_entries':len(entries),'formal_increment':0})
    env=b['env_for']()
    env.update(RESEARCHOS_CONFIGURATION_OLD_CONTROL=source['path'],
               RESEARCHOS_CONFIGURATION_OLD_ROOT=root['root'],
               RESEARCHOS_CONFIGURATION_TARGET_PROGRAM=target['path'])
    b['run'].__globals__['ENV_KEYS'] += ('RESEARCHOS_CONFIGURATION_OLD_CONTROL',
        'RESEARCHOS_CONFIGURATION_OLD_ROOT','RESEARCHOS_CONFIGURATION_TARGET_PROGRAM')
    for label,test in [('frozen22-lock','TestConfigurationUpgradeFrozen22ProgramLock'),
                       ('native23-cli','TestConfigurationUpgradeNativeCLI')]:
        b['run']('T3R-'+label,[GO,'test','-mod=readonly','-json','./internal/domain',
            '-run','^'+test+'$','-count=1','-timeout=10m'],plan,env,timeout=690)

def remainder():
    plan=json.loads(MAP.read_bytes())
    env=b['env_for']()
    for label,package,pattern in [
        ('backup-cli','./ops/backup','^TestPauseHandoff'),
        ('recovery-authority','./internal/recoveryauthority','^TestPauseMigration'),
        ('recovery-root','./ops/supervisor/recovery_root','^TestPauseRoot')]:
        b['run']('T3R-'+label,[GO,'test','-mod=readonly','-json',package,
            '-run',pattern,'-count=1','-timeout=3m'],plan,env,timeout=270)

def queue():
    plan=json.loads(MAP.read_bytes())
    manifest=b['M1_MANIFEST']
    data=json.loads(manifest.read_bytes())
    assets=b['ASSETS']
    checked=[]
    for name in ('node.exe','mu-worker.mjs'):
        item=data['files'][name]
        path=assets/name
        if path.stat().st_size != item['bytes'] or digest(path)!=item['sha256']:
            raise RuntimeError('M1 asset mismatch '+name)
        checked.append({'path':str(path),'bytes':item['bytes'],'sha256':item['sha256']})
    save('T5R-queue-assets.json',{'schema':'researchos.schema25-resourced-queue-assets/1',
         'manifest':b['ref'](manifest),'checked':checked,'formal_increment':0})
    env=b['env_for']()
    env['RESEARCHOS_MU_BUNDLE']=str(assets/'mu-worker.mjs')
    env['PATH']=str(assets)+os.pathsep+env.get('PATH','')
    b['run'].__globals__['ENV_KEYS'] += ('RESEARCHOS_MU_BUNDLE',)
    b['run']('T5R-queue-three',[GO,'test','-mod=readonly','-json','./internal/domain',
        '-run','^TestRuntimeClientQueue(ActualMuSameProcess|ActualMuCancelUnknownEffect|GoalCancelClaimOrdering)$',
        '-count=1','-timeout=8m'],plan,env,timeout=570)

if __name__ == '__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ('baseline','historical','remainder','queue'):
        raise SystemExit('usage: run-supplemental.py baseline|historical|remainder|queue')
    {'baseline':baseline,'historical':historical,'remainder':remainder,'queue':queue}[sys.argv[1]]()
