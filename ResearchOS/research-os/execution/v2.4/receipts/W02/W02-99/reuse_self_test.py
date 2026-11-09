"""Low-cost real-process rejection tests. Mutate only per-test evidence copies."""
import copy
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

import evidence_reuse as subject

HERE=Path(__file__).resolve().parent
CASES={
    'missing_raw':'RAW_INVENTORY_CHANGED',
    'changed_raw':'RAW_HASH_CHANGED',
    'changed_manifest':'MANIFEST_HASH_CHANGED',
    'changed_check_bytes':'RAW_HASH_CHANGED',
    'false_check':'CHECKS_NOT_STRICTLY_TRUE',
    'string_truthiness':'CHECKS_NOT_STRICTLY_TRUE',
    'zero_assertions':'ASSERTION_IDS_CHANGED',
    'duplicate_assertions':'ASSERTION_IDS_CHANGED',
    'wrong_mode':'GATE_MODE_CHANGED',
    'failed_source':'SOURCE_NOT_PASS',
    'changed_product_source':'CURRENT_BUILD_SOURCE_DRIFT',
    'changed_common_helper':'COMMON_OR_GATE_DRIVER_LOGIC_CHANGED:Gate',
    'changed_g01_logic':'COMMON_OR_GATE_DRIVER_LOGIC_CHANGED:g01',
    'changed_main_logic':'MAIN_OTHER_LOGIC_CHANGED',
}


def worker(name,scratch):
    pins=subject.read(HERE/'evidence_reuse_inputs_codex.json')
    gate='W02-G03';pin=pins['gates'][gate];original=HERE/pin['run']
    report=subject.read(original/'receipt.json')
    try:
        if name in ('missing_raw','changed_raw','changed_manifest','changed_check_bytes'):
            clone=scratch/pin['run'];shutil.copytree(original,clone)
            raw=next(clone.glob('dispatcher-fixture/execution/invocations/*/stdout.txt'))
            if name=='missing_raw':raw.unlink()
            elif name=='changed_raw':raw.write_bytes(raw.read_bytes()+b'tampered')
            elif name=='changed_manifest':
                target=clone/'manifest.json';target.write_bytes(target.read_bytes()+b' ')
            else:
                target=clone/'receipt.json';data=subject.read(target);data['checks'][0]['ok']=False
                target.write_text(json.dumps(data),encoding='utf-8')
            subject.validate(gate,evidence_base=scratch)
        elif name in ('false_check','string_truthiness','zero_assertions','duplicate_assertions','wrong_mode','failed_source'):
            altered=copy.deepcopy(report)
            if name=='false_check':altered['checks'][0]['ok']=False
            elif name=='string_truthiness':altered['checks'][0]['ok']='true'
            elif name=='zero_assertions':altered.update(assertions=0,assertion_ids=[],checks=[])
            elif name=='duplicate_assertions':altered['assertion_ids'][-1]=altered['assertion_ids'][0]
            elif name=='wrong_mode':altered['mode']='LIVE'
            else:altered['status']='FAIL'
            subject.verify_report(altered,gate,pin)
        elif name=='changed_product_source':
            g01=pins['gates']['W02-G01'];primary=HERE/g01['run']
            product=subject.read(HERE/'parent_inputs_codex.json')['build_sources']
            first=next(iter(product));target=scratch/first;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((subject.ROOT/first).read_bytes()+b'\n// source drift fixture\n')
            subject.ROOT=scratch
            subject.verify_g01(primary,subject.read(primary/'receipt.json'),pins,HERE,[],[],{})
        else:
            original=HERE/pins['gates']['W02-G01']['run']/'driver-sources/parent_driver.py'
            current=(HERE/'parent_driver.py').read_text(encoding='utf-8')
            if name=='changed_common_helper':current=current.replace("'ok':ok is True","'ok':bool(ok)",1)
            elif name=='changed_g01_logic':current=current.replace("code==0 and exe.is_file()","True",1)
            else:current=current.replace('g=Gate(selector)','g=Gate(selector); print("unexpected")',1)
            target=scratch/'changed-driver.py';target.write_text(current,encoding='utf-8')
            subject.verify_driver_ast(original,target)
    except subject.Refused as exc:
        print(json.dumps({'status':'REFUSED','case':name,'reason':str(exc)}));return 3
    except Exception as exc:
        print(json.dumps({'status':'UNEXPECTED_ERROR','case':name,'type':type(exc).__name__}));return 9
    print(json.dumps({'status':'UNEXPECTED_PASS','case':name}));return 0


def main():
    if len(sys.argv)==4 and sys.argv[1]=='--case':
        name=sys.argv[2];scratch=Path(sys.argv[3]).resolve()
        if name not in CASES or not scratch.is_relative_to(HERE.resolve()):return 10
        return worker(name,scratch)
    out=HERE/('reuse-tests-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:12]);out.mkdir()
    scratch=out/'scratch';scratch.mkdir();rows=[]
    env={k:v for k,v in os.environ.items() if k in ('SystemRoot','SYSTEMROOT','TEMP','TMP','PATH','USERPROFILE','LOCALAPPDATA')}
    env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    for name,expected in CASES.items():
        case_dir=scratch/name;case_dir.mkdir()
        argv=[sys.executable,'-B',str(Path(__file__)), '--case',name,str(case_dir)]
        result=subprocess.run(argv,cwd=HERE,env=env,capture_output=True,timeout=30)
        for stream,raw in [('stdout',result.stdout),('stderr',result.stderr)]:(out/(name+'.'+stream+'.txt')).write_bytes(raw)
        value=subject.decode(result.stdout.decode('utf-8'))
        ok=result.returncode==3 and value.get('status')=='REFUSED' and value.get('reason')==expected
        row={'case':name,'argv':argv,'cwd':str(HERE),'exit_code':result.returncode,'expected_reason':expected,'ok':ok,
             'stdout':{'path':name+'.stdout.txt','sha256':subject.sha(out/(name+'.stdout.txt'))},
             'stderr':{'path':name+'.stderr.txt','sha256':subject.sha(out/(name+'.stderr.txt'))}}
        subject.save(out/(name+'.command.json'),row);rows.append(row)
    # Check the immutable originals once after every deliberate copy mutation.
    pins=subject.read(HERE/'evidence_reuse_inputs_codex.json');audit=[]
    for pin in [*pins['gates'].values(),pins['partial_g01_run']]:subject.verify_manifest(HERE/pin['run'],pin['manifest_sha256'],audit)
    resolved=scratch.resolve();subject.require(resolved.parent==out.resolve() and resolved.name=='scratch','TEST_CLEANUP_BOUNDARY')
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    cleanup=subprocess.run([str(ps),'-NoProfile','-Command',"Remove-Item -LiteralPath $env:W0299_REUSE_SCRATCH -Recurse -Force -ErrorAction Stop"],
            env={'SystemRoot':os.environ['SystemRoot'],'W0299_REUSE_SCRATCH':str(resolved)},capture_output=True)
    clean=cleanup.returncode==0 and not resolved.exists()
    subject.save(out/'cleanup.json',{'target':str(resolved),'exit_code':cleanup.returncode,'absent':not resolved.exists()})
    report={'status':'PASS' if all(r['ok'] for r in rows) and clean else 'FAIL','scope':'EVIDENCE_REUSE_VALIDATOR_TESTS_ONLY',
            'negative_cases':rows,'original_manifests_revalidated':3,'original_raw_unchanged':True,
            'new_product_tests_executed':0,'new_dispatcher_fixture_children':0,'new_validator_test_children':len(rows),
            'helper_sha256':subject.sha(HERE/'evidence_reuse.py'),'test_source_sha256':subject.sha(Path(__file__))}
    subject.save(out/'receipt.json',report)
    subject.save(out/'manifest.json',{p.name:subject.sha(p) for p in out.iterdir() if p.is_file()})
    print(json.dumps({'status':report['status'],'negative_cases':len(rows),'receipt':str(out/'receipt.json')}))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':sys.exit(main())
