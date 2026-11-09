"""Proposed single Go-component evidence run. No product launch before exact grant checks."""
import argparse
import ast
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def ref(path):
    p = Path(path).resolve(strict=True)
    return {'path':p.as_posix(), 'sha256':digest(p), 'bytes':p.stat().st_size}

def checked(reference):
    p = Path(reference['path']).resolve(strict=True)
    if digest(p) != reference['sha256']:
        raise RuntimeError('Pinned input mismatch: '+str(p))
    return p

def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())

def python_inputs(helper):
    # Actual imported Python paths + actual currently loaded process modules.
    # No PE import-directory expansion is called an actual load observation.
    paths = {Path(sys.executable).resolve(), HERE/'run_go3.py', HERE/'windows_debug_owned_process.py'}
    for module in list(sys.modules.values()):
        for attribute in ('__file__', '__cached__'):
            value = getattr(module, attribute, None)
            if value:
                p = Path(value)
                if p.is_file():
                    paths.add(p.resolve())
    paths.update(Path(p) for p in helper.runtime_resource_paths())
    return [ref(p) for p in sorted(paths, key=lambda p:str(p).casefold())]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--grant-path', required=True)
    parser.add_argument('--grant-sha256', required=True)
    args = parser.parse_args()
    grant_path = checked({'path':args.grant_path,'sha256':args.grant_sha256})
    grant = json.loads(grant_path.read_text(encoding='utf-8'))
    if grant.get('authorized') is not True or grant.get('issuer') != 'codex:/root':
        raise RuntimeError('An explicit Root grant is required; proposal/template is not authority')
    spec_path = checked(grant['spec_ref'])
    if spec_path != HERE/'spec.json':
        raise RuntimeError('Grant must bind this proposal spec')
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    for name in ('runner_ref','helper_ref'):
        checked(spec[name])
        if grant[name] != spec[name]:
            raise RuntimeError('Grant does not bind exact '+name)
    if grant.get('operation') != 'GO3_SINGLE_DEBUG_EVENT_COMPONENT_EVIDENCE' or grant.get('max_executions') != 1:
        raise RuntimeError('Missing explicit one-run debug-event scope')
    if grant.get('source_commit') != spec['source_commit'] or grant.get('selectors') != spec['selectors']:
        raise RuntimeError('Grant source/selectors mismatch')
    if grant.get('http_cap') != 0 or grant.get('model_cap') != 0:
        raise RuntimeError('Go-only zero-service caps required')
    if os.name != 'nt' or ctypes.sizeof(ctypes.c_void_p) != 8:
        raise RuntimeError('Windows x64 required')
    exe = checked(spec['test_exe'])
    full_vector = json.loads(checked(spec['input_vector_ref']).read_text(encoding='utf-8'))
    for row in full_vector:
        checked(row)
    for reference in spec['compiled_evidence_refs']:
        checked(reference)
    module_spec = importlib.util.spec_from_file_location('go3_proposed_owned_debug', checked(spec['helper_ref']))
    helper = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(helper)
    before = python_inputs(helper)
    output = HERE / ('actual-'+uuid.uuid4().hex)
    output.mkdir(exist_ok=False)
    # A failed launch consumes the once claim too. No automatic retries.
    put(HERE/'execution-once.claim.json', {'grant_ref':ref(grant_path),'output':output.as_posix(),'claimed_at':time.time()})
    put(output/'python-runtime.before.json',before)
    put(output/'inputs.before.json',full_vector)
    argv = [str(exe),'-test.run',spec['anchored_selector'],'-test.v','-test.count=1','-test.failfast','-test.timeout=120s']
    # Explicit minimal Windows runtime environment; no credential variables copied or logged.
    env = {key:os.environ[key] for key in ('SystemRoot','WINDIR','SystemDrive','TEMP','TMP','ComSpec') if key in os.environ}
    env.update({'GOTOOLCHAIN':'local','GOENV':'off'})
    invocation = {'argv':argv,'cwd':spec['cwd'],'environment':env,'grant_ref':ref(grant_path),
                  'source_commit':spec['source_commit'],'spec_ref':ref(spec_path),'started_at':time.time(),
                  'http':0,'sdk_model':0,'external':0,'paid':0,'test_exe_before':ref(exe)}
    put(output/'invocation.json',invocation)
    with (output/'stdout.raw').open('xb') as stdout, (output/'stderr.raw').open('xb') as stderr:
        result = helper.run_owned(argv,spec['cwd'],env,stdout,stderr,150)
    # The runner uses file handles, not PIPE. Child exit + Job idle precede caller closes.
    result['stdout_stderr_caller_files_closed'] = stdout.closed and stderr.closed
    result['stdio_transport'] = 'EXACT_INHERITED_FILE_HANDLES_NOT_PIPES'
    put(output/'owned-child.json',result)
    after = python_inputs(helper)
    put(output/'python-runtime.after.json',after)
    drift=[]
    for row in full_vector+before:
        if digest(row['path']) != row['sha256']:
            drift.append(row['path'])
    new_python_paths=sorted(set(r['path'] for r in after)-set(r['path'] for r in before))
    put(output/'inputs.after.json',[ref(row['path']) for row in full_vector])
    stdout_text=(output/'stdout.raw').read_text(encoding='utf-8')
    passes=re.findall(r'^\s*--- PASS: ([^ ]+)',stdout_text,re.MULTILINE)
    failures=re.findall(r'^\s*--- (?:FAIL|SKIP): ([^ ]+)',stdout_text,re.MULTILINE)
    cleanup=result['job_cleanup']
    accepted_component=(result['actual_exit']==0 and not result['error'] and not result['timed_out']
        and result['debug_capture']['complete'] and cleanup['primary_exit_confirmed']
        and cleanup['job_idle_confirmed'] and cleanup['handles_closed'] and not cleanup['errors']
        and result['stdout_stderr_caller_files_closed'] and not drift and not new_python_paths
        and sorted(passes)==sorted(spec['expected_pass_records']) and not failures)
    summary={'status':'COMPONENT_EVIDENCE_RECORDED' if accepted_component else 'FAILED_OR_INCOMPLETE_COMPONENT_EVIDENCE',
             'actual_native_exit':result['actual_exit'],'source_acceptance':False,'ended_at':time.time(),
             'pass_records':passes,'fail_or_skip_records':failures,'drift':drift,'new_python_runtime_paths':new_python_paths,
             'test_exe_after':ref(exe),'http':0,'sdk_model':0,'external':0,'paid':0,
             'limitations':spec['limitations'],'historical_once_run_not_rewritten':True}
    put(output/'summary.json',summary)
    put(output/'manifest.json',[ref(p) for p in sorted(output.iterdir()) if p.is_file()])
    print(json.dumps({'output':output.as_posix(),'summary':ref(output/'summary.json')},ensure_ascii=False))
    return 0 if accepted_component else 1

if __name__=='__main__':
    raise SystemExit(main())
