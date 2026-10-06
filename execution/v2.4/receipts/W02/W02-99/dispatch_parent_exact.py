"""Project validated W02 parent evidence to the contract's exact gate IDs."""
import datetime as dt
import os
from pathlib import Path
import subprocess
import sys
import uuid

import dispatch_parent as bridge
from evidence_reuse import Refused,decode,read,require,save,sha,within

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
MODES={'W02-G01':'DEVELOPMENT','W02-G02':'DEVELOPMENT','W02-G03':'FIXTURE'}


def ids_and_count(value):
    ids=value.get('assertion_ids');count=value.get('assertions')
    require(isinstance(ids,list) and bool(ids) and all(isinstance(x,str) and bool(x) for x in ids),'EMPTY_OR_INVALID_IDS')
    require(len(ids)==len(set(ids)),'DUPLICATE_IDS')
    require(type(count) is int and count==len(ids),'ASSERTION_COUNT_MISMATCH')
    return ids


def verify_child(stdout,selector):
    require(selector in MODES,'UNKNOWN_PARENT_SELECTOR')
    value=decode(stdout.decode('utf-8'))
    require(isinstance(value,dict) and value.get('status')=='PASS','CHILD_NOT_PASS')
    ids=ids_and_count(value)
    require(all(x==selector or x.startswith(selector+'-') for x in ids),'STDOUT_SELECTOR_MISMATCH')
    require(value.get('check_id',selector)==selector,'STDOUT_CHECK_ID_MISMATCH')
    receipt_name=value.get('receipt')
    require(isinstance(receipt_name,str) and bool(receipt_name),'MISSING_RECEIPT_REFERENCE')
    path=Path(receipt_name).resolve()
    # Do this before opening any child-named file or following its manifest.
    require(path.is_relative_to(HERE.resolve()) and path.name=='receipt.json','RECEIPT_OUTSIDE_CARD')
    require(path.is_file(),'MISSING_CHILD_RECEIPT')
    report=read(path)
    require(isinstance(report,dict),'INVALID_CHILD_RECEIPT')
    require(report.get('check_id')==selector and report.get('mode')==MODES[selector],'RECEIPT_SELECTOR_OR_MODE_MISMATCH')
    require(report.get('status')=='PASS','RECEIPT_NOT_PASS')
    require(ids_and_count(report)==ids,'RECEIPT_IDS_MISMATCH')
    checks=report.get('checks')
    require(isinstance(checks,list) and all(isinstance(x,dict) for x in checks) and
            [x.get('id') for x in checks]==ids and all(x.get('ok') is True for x in checks),'RECEIPT_CHECKS_NOT_TRUE')
    require(report.get('owned_acceptance_ids')==[] and report.get('formal_cases_accepted')==[] and report.get('whole_card_accepted') is False,'RECEIPT_SCOPE_CHANGED')
    manifest=path.parent/'manifest.json';require(manifest.is_file(),'MISSING_MANIFEST')
    hashes=read(manifest);require(isinstance(hashes,dict) and bool(hashes),'EMPTY_MANIFEST')
    actual={p.relative_to(path.parent).as_posix() for p in path.parent.rglob('*') if p.is_file() and p!=manifest}
    require(actual==set(hashes) and 'receipt.json' in hashes,'MANIFEST_INVENTORY_MISMATCH')
    validated=[]
    for rel,expected in hashes.items():
        raw=within(path.parent,rel)
        require(raw.is_file() and isinstance(expected,str) and sha(raw)==expected,'MANIFEST_RAW_HASH_MISMATCH')
        validated.append({'path':str(raw),'sha256':expected})
    revalidation=path.parent/'revalidation.json'
    if revalidation.is_file():
        replay=read(revalidation)
        require(isinstance(replay,dict),'INVALID_REVALIDATION')
        require(replay.get('gate')==selector and replay.get('mode')==MODES[selector],'REPLAY_SELECTOR_OR_MODE_MISMATCH')
        original_ids=replay.get('source_assertion_ids');conditions=replay.get('recomputed_conditions')
        require(isinstance(original_ids,list) and bool(original_ids) and len(original_ids)==len(set(original_ids)) and
                isinstance(conditions,dict) and set(conditions)==set(original_ids) and all(x is True for x in conditions.values()),'REPLAY_CONDITIONS_INVALID')
        require(report.get('original_internal_assertion_ids')==original_ids and
                type(report.get('original_internal_assertion_count')) is int and report['original_internal_assertion_count']==len(original_ids),'REPLAY_COUNT_MISMATCH')
        # These are already verified by the child; close the projection window
        # by checking every referenced original raw byte once more.
        for item in replay.get('validated_inputs_and_raw',[]):
            if item.get('kind') not in ('original_raw','original_manifest'):continue
            raw=Path(item['path']).resolve()
            require(raw.is_relative_to(HERE.resolve()),'REPLAY_RAW_OUTSIDE_CARD')
            require(raw.is_file() and sha(raw)==item['sha256'],'REPLAY_RAW_CHANGED')
            validated.append({'path':str(raw),'sha256':item['sha256']})
        for command in replay.get('original_actual_commands',[]):
            raw=Path(command['path']).resolve()
            require(raw.is_relative_to(ROOT.resolve()),'COMMAND_RAW_OUTSIDE_REPOSITORY')
            require(raw.is_file() and sha(raw)==command['sha256'],'COMMAND_RAW_CHANGED')
            for name in ('stdout','stderr'):
                stream=raw.parent/(name+'.txt') if 'invocation_id' in command else Path(command[name]['path']).resolve()
                require(stream.is_relative_to(ROOT.resolve()),'COMMAND_STREAM_OUTSIDE_REPOSITORY')
                require(stream.is_file() and sha(stream)==command[name]['sha256'],'COMMAND_STREAM_CHANGED')
    return {'status':'PASS','check_id':selector,'mode':MODES[selector],
            'scope':'W02_EXACT_PARENT_GATE_PROJECTION','assertions':1,'assertion_ids':[selector],
            'internal_assertion_ids':ids,'internal_assertion_count':len(ids),
            'reused_original_assertion_count':report.get('original_internal_assertion_count',0),
            'receipt':str(path),'receipt_sha256':sha(path),'source_manifest':str(manifest),'source_manifest_sha256':sha(manifest),
            'validated_raw':validated,'owned_acceptance_ids':[],'formal_cases_accepted':[],'whole_card_accepted':False}


def main():
    kind,args,_=bridge.route(os.environ)
    if kind!='parent':return bridge.main()
    selector=os.environ.get('RESEARCHOS_CHECK_ID','')
    out=HERE/('projection-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:12]);out.mkdir()
    argv=[sys.executable,*args]
    child=subprocess.run(argv,cwd=ROOT,env=dict(os.environ),stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
    (out/'child.stdout.txt').write_bytes(child.stdout);(out/'child.stderr.txt').write_bytes(child.stderr)
    command={'argv':argv,'cwd':str(ROOT),'exit_code':child.returncode,
             'stdout':{'path':'child.stdout.txt','sha256':sha(out/'child.stdout.txt')},
             'stderr':{'path':'child.stderr.txt','sha256':sha(out/'child.stderr.txt')}}
    save(out/'child.command.json',command)
    projection=None;reason=None
    if child.returncode==0:
        try:projection=verify_child(child.stdout,selector)
        except (OSError,ValueError,TypeError,KeyError,IndexError,AttributeError) as exc:
            reason=str(exc) if isinstance(exc,Refused) else type(exc).__name__
    else:reason='CHILD_NONZERO_EXIT'
    audit={'status':'PASS' if projection else 'FAIL','check_id':selector,'mode':MODES[selector],
           'assertions':1 if projection else 0,'assertion_ids':[selector] if projection else [],'reason':reason,
           'child_exit_code':child.returncode,'projection':projection,'source_sha256':{name:sha(HERE/name) for name in
           ('dispatch_parent_exact.py','dispatch_parent.py','parent_driver.py','evidence_reuse.py')},
           'owned_acceptance_ids':[],'formal_cases_accepted':[],'whole_card_accepted':False}
    save(out/'receipt.json',audit)
    save(out/'manifest.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()})
    if child.returncode!=0:
        sys.stdout.buffer.write(child.stdout);sys.stderr.buffer.write(child.stderr)
        return child.returncode
    if projection:
        projection=dict(projection);projection.pop('validated_raw')
        projection.update(projection_receipt=str(out/'receipt.json'),projection_receipt_sha256=sha(out/'receipt.json'))
    else:projection={'status':'FAIL','check_id':selector,'assertions':0,'assertion_ids':[],
                     'reason':reason,'projection_receipt':str(out/'receipt.json'),'projection_receipt_sha256':sha(out/'receipt.json')}
    print(__import__('json').dumps(projection))
    sys.stderr.buffer.write(child.stderr)
    return 0 if audit['status']=='PASS' else 1


if __name__=='__main__':sys.exit(main())
