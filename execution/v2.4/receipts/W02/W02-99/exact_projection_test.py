"""Projection validation fixtures and intercepted legacy transport; no build."""
import contextlib
import datetime as dt
import io
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
import uuid

import dispatch_parent_exact as target
from evidence_reuse import Refused,save,sha

HERE=Path(__file__).resolve().parent


def fixture(out,name,change=None):
    folder=out/name;folder.mkdir()
    ids=['W02-G02-INTERNAL'];report={'status':'PASS','check_id':'W02-G02','mode':'DEVELOPMENT',
        'assertions':1,'assertion_ids':ids,'checks':[{'id':ids[0],'ok':True}],
        'scope':'PROJECTION_VALIDATOR_FIXTURE_ONLY','owned_acceptance_ids':[],
        'formal_cases_accepted':[],'whole_card_accepted':False}
    envelope={'status':'PASS','assertions':1,'assertion_ids':ids,'receipt':str(folder/'receipt.json')}
    if change:change(report,envelope)
    save(folder/'receipt.json',report);(folder/'raw.txt').write_bytes(b'projection fixture raw\n')
    save(folder/'manifest.json',{p.name:sha(p) for p in folder.iterdir() if p.is_file()})
    return folder,json.dumps(envelope).encode()


def main():
    out=HERE/('projection-tests-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:12]);out.mkdir()
    rows=[]
    folder,envelope=fixture(out,'valid_internal_report')
    valid=target.verify_child(envelope,'W02-G02')
    rows.append({'case':'valid_exact_projection','ok':valid['assertion_ids']==['W02-G02'] and valid['assertions']==1 and
                 valid['internal_assertion_ids']==['W02-G02-INTERNAL'] and valid['internal_assertion_count']==1})
    cases=[
      ('zero',lambda r,e:e.update(assertions=0,assertion_ids=[]),'EMPTY_OR_INVALID_IDS'),
      ('duplicate',lambda r,e:e.update(assertions=2,assertion_ids=['W02-G02-X','W02-G02-X']),'DUPLICATE_IDS'),
      ('false_check',lambda r,e:r['checks'][0].update(ok=False),'RECEIPT_CHECKS_NOT_TRUE'),
      ('count',lambda r,e:e.update(assertions=2),'ASSERTION_COUNT_MISMATCH'),
      ('boolean_count',lambda r,e:e.update(assertions=True),'ASSERTION_COUNT_MISMATCH'),
      ('stdout_selector',lambda r,e:e.update(check_id='W02-G01'),'STDOUT_CHECK_ID_MISMATCH'),
      ('receipt_selector',lambda r,e:r.update(check_id='W02-G01'),'RECEIPT_SELECTOR_OR_MODE_MISMATCH'),
      ('receipt_mode',lambda r,e:r.update(mode='FIXTURE'),'RECEIPT_SELECTOR_OR_MODE_MISMATCH'),
      ('outside_receipt',lambda r,e:e.update(receipt=str(HERE.parent/'receipt.json')),'RECEIPT_OUTSIDE_CARD'),
      ('missing_receipt',None,'MISSING_CHILD_RECEIPT'),
      ('missing_manifest',None,'MISSING_MANIFEST'),
      ('changed_raw',None,'MANIFEST_RAW_HASH_MISMATCH'),
    ]
    for name,change,expected in cases:
        folder,envelope=fixture(out,name,change)
        if name=='missing_receipt':(folder/'receipt.json').unlink()
        elif name=='missing_manifest':(folder/'manifest.json').unlink()
        elif name=='changed_raw':(folder/'raw.txt').write_bytes(b'tampered fixture raw\n')
        (out/(name+'.child-stdout.txt')).write_bytes(envelope)
        try:target.verify_child(envelope,'W02-G02');reason='UNEXPECTED_PASS'
        except Refused as exc:reason=str(exc)
        rows.append({'case':name,'ok':reason==expected,'expected':expected,'actual':reason})
    # The four legacy/v24 calls are intercepted at the original bridge's
    # subprocess boundary. No historical product build handler is executed.
    for task,check,expected_args in [('W02','','v24'),('W02','W02-03','v24'),('W03','W03-G01','legacy'),('W03','W02-G01','legacy')]:
        env={'RESEARCHOS_TASK_ID':task,'RESEARCHOS_CHECK_ID':check,'ELECTRON_OVERRIDE_DIST_PATH':'synthetic-electron-dir'}
        calls=[]
        def intercept(argv,**kwargs):calls.append((argv,kwargs));return 17
        with patch.dict(os.environ,env,clear=True),patch.object(target.bridge.subprocess,'call',side_effect=intercept):code=target.main()
        expected=['apps/cli/build_check.py'] if expected_args=='v24' else ['-X','utf8','ops/ci/build.py']
        forwarded_env=calls[0][1]['env'] if len(calls)==1 else {}
        env_ok=forwarded_env==env if expected_args=='v24' else forwarded_env=={'RESEARCHOS_TASK_ID':task,'RESEARCHOS_CHECK_ID':check,'RESEARCHOS_EXECUTOR_ID':'codex:/root'}
        rows.append({'case':'legacy_transport_'+task+'_'+(check or 'default'),'ok':code==17 and len(calls)==1 and calls[0][0]==[sys.executable,*expected] and env_ok,
                     'intercepted':True,'historical_handler_executed':False,'returned_exit':code,'captured_argv':calls[0][0] if calls else None})
    # Real tiny Python child: PASS-looking output plus exit17 must remain failed,
    # with exact original stdout/stderr bytes. The product driver is not run.
    passed={'status':'PASS','assertions':1,'assertion_ids':['W02-G01']}
    text=json.dumps(passed);child_code='import sys;print('+repr(text)+');sys.stderr.write("synthetic-child-error");sys.exit(17)'
    output=io.BytesIO();error=io.BytesIO()
    stdout=io.TextIOWrapper(output,encoding='utf-8',write_through=True)
    stderr=io.TextIOWrapper(error,encoding='utf-8',write_through=True)
    env={k:os.environ[k] for k in ('SystemRoot','SYSTEMROOT','PATH','TEMP','TMP') if k in os.environ}
    env.update(RESEARCHOS_TASK_ID='W02',RESEARCHOS_CHECK_ID='W02-G01')
    before=set(HERE.glob('projection-*'))
    with patch.dict(os.environ,env,clear=True),patch.object(target.bridge,'route',return_value=('parent',['-c',child_code],{})),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
        code=target.main()
    stdout.flush();stderr.flush();actual_out=output.getvalue();actual_err=error.getvalue()
    new_paths=sorted(set(HERE.glob('projection-*'))-before)
    rows.append({'case':'nonzero_child_pass_json','ok':code==17 and actual_out==(text+os.linesep).encode() and actual_err==b'synthetic-child-error',
                 'actual_child_exit':code,'real_python_fixture_child':True,'product_driver_executed':False,
                 'projection_audit':[str(p/'receipt.json') for p in new_paths]})
    (out/'nonzero-child.stdout.txt').write_bytes(actual_out);(out/'nonzero-child.stderr.txt').write_bytes(actual_err)
    result={'status':'PASS' if all(r['ok'] for r in rows) else 'FAIL','scope':'EXACT_PROJECTION_VALIDATOR_TESTS_ONLY',
            'checks':rows,'check_count':len(rows),'wrapper_sha256':sha(HERE/'dispatch_parent_exact.py'),
            'helper_sha256':sha(HERE/'evidence_reuse.py'),'test_source_sha256':sha(Path(__file__)),
            'argv':[sys.executable,*sys.orig_argv[1:]],'cwd':str(Path.cwd()),
            'new_product_tests':0,'old_14_tests_rerun':False,'new_dispatcher_fixture_children':0,'real_projection_fixture_children':1}
    save(out/'receipt.json',result)
    (out/'exact_projection_test.py').write_bytes(Path(__file__).read_bytes())
    save(out/'manifest.json',{p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()})
    print(json.dumps({'status':result['status'],'checks':len(rows),'receipt':str(out/'receipt.json')}))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':sys.exit(main())
