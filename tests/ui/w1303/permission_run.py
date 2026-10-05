"""Actual Electron decisions against one original SDK tool, with raw provenance."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
import uuid

ROOT = Path(__file__).resolve().parents[3]

def main():
    run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    out = ROOT / 'execution/v2.4/receipts/W13/W13-03' / ('permission-' + run_id)
    out.mkdir(parents=True)
    temp = Path(tempfile.mkdtemp(prefix='researchos-w13-ui-permission-', dir=ROOT / '.local'))
    locked = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8-sig'))['tools']
    go, node = Path(locked['go']['path']), Path(locked['node']['path'])
    bundle = ROOT / '.local/w1401-mu-worker/mu-worker.mjs'
    report = {'schema':'researchos.permission-ui-observation.v1','run_id':run_id,'step_id':'W13-03','status':'EXECUTING','measurement_mode':'FIXTURE','external_provider_calls':0,'formal_cases_accepted':[],'commands':[],'source_hashes':{},'cases':[]}
    env = dict(os.environ, GOTOOLCHAIN='local', GOENV='off', RESEARCHOS_TASK_ID='W13', RESEARCHOS_NODE=str(node), RESEARCHOS_MU_BUNDLE=str(bundle))
    env.pop('ROS_DESKTOP_SMOKE',None)
    def command(argv,name,timeout=180):
        r = subprocess.run([str(a) for a in argv],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
        (out/(name+'.stdout.txt')).write_text(r.stdout,encoding='utf-8');(out/(name+'.stderr.txt')).write_text(r.stderr,encoding='utf-8')
        report['commands'].append({'argv':[str(a) for a in argv],'exit_code':r.returncode})
        if r.returncode: raise RuntimeError(f'{name} exited {r.returncode}; raw logs preserved')
        return r.stdout
    try:
        for name,binary in [('go',go),('node',node)]:
            if hashlib.sha256(binary.read_bytes()).hexdigest()!=locked[name]['sha256']: raise RuntimeError(name+' hash mismatch')
        for folder in ['apps/web/src','apps/desktop/main','apps/desktop/preload','tests/ui/w1303','internal/domain','internal/api','internal/host','adapters/runtime/mu']:
            for f in sorted((ROOT/folder).rglob('*')):
                if f.is_file() and f.suffix in ['.js','.jsx','.cjs','.mjs','.go','.py','.css']:
                    report['source_hashes'][f.relative_to(ROOT).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
        report['candidate_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        report['dirty_tracked']=subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=ROOT,text=True).splitlines()
        report['bundle_sha256']=hashlib.sha256(bundle.read_bytes()).hexdigest()
        command([node,ROOT/'apps/web/node_modules/vite/bin/vite.js','build',ROOT/'apps/web'],'web-build')
        binary = temp/'permission-fixture.exe'
        command([go,'build','-o',binary,'./tests/ui/w1303/workspace_fixture'],'fixture-build')
        report['fixture_binary_sha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
        for choice in ['ALLOW_ONCE','DENY']:
            case = out/choice.lower();case.mkdir()
            log = (case/'service.stderr.txt').open('w',encoding='utf-8')
            child = subprocess.Popen([str(binary),'--dir',str(temp/choice.lower()),'--permission'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=log,text=True,encoding='utf-8')
            try:
                lines = queue.Queue();threading.Thread(target=lambda:lines.put(child.stdout.readline()),daemon=True).start()
                ready = lines.get(timeout=70)
                (case/'service.ready.txt').write_text(ready,encoding='utf-8')
                if not ready: raise RuntimeError(f'{choice} fixture failed before ready; stderr preserved')
                fixture=json.loads(ready);report['cases'].append({'decision':choice,'fixture':fixture})
                input_file=temp/(choice+'.json');input_file.write_text(json.dumps(fixture,ensure_ascii=False),encoding='utf-8')
                env.update(RESEARCHOS_CLI_DISCOVERY=fixture['discovery_file'],RESEARCHOS_PROJECT_ID=fixture['project_id'],RESEARCHOS_DESKTOP_USER_DATA=str(temp/(choice+'-electron')))
                command([node,ROOT/'tests/ui/w1303/permission.cjs',input_file,case,choice],choice.lower()+'-ui',90)
                report['cases'][-1]['observation']=json.loads((case/'permission.json').read_text(encoding='utf-8'))
            finally:
                if child.poll() is None:
                    child.terminate()
                    try: child.wait(timeout=10)
                    except subprocess.TimeoutExpired: child.kill();child.wait(timeout=5)
                log.close()
        report['status']='PASS'
    except Exception as e:
        report['status'],report['error']='FAIL',str(e)
    finally:
        report['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();report['temporary_data']=str(temp);report['temporary_data_retained']=True
        (out/'run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'receipt':str(out/'run.json'),'error':report.get('error')},ensure_ascii=False))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
