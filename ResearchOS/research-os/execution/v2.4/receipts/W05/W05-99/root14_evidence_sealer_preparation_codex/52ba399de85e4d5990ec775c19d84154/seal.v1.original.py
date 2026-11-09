"""Prepared only. Root may invoke after an immutable actual outer-zero receipt exists.
No product execution, SQL, native helper or current canonical access. The pinned
authorization gate is pure read/hash and validates immutable registration copies.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import base64
from collections import Counter
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import traceback
import types

ROOT = Path('D:/作品集/ResearchOS/research-os')
DRAFT = ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-root-replay-draft'
SCOPE = DRAFT/'root_finite14_scope.v3.json'
SCOPE_SHA = '55e4c169937d2ecc4bc1aaa98e30538dab8071e9870ffd1c7c3309a636e81eda'
GATE_SHA = 'a12d165daf93687531e26a4652dcc338127f61fae63d40821d779128cbb09ba7'
RUN_UUID = '0b2ae4ec4e824c968553ff884c3fa132'
NAMES = ['NullContext','OwnedContext','ContextNotResultFilter','ExactReplayAfterCommit',
         'ChangedPayloadConflict','ChangedSIDConflict','CrossProjectContext','ForeignPrincipalContext',
         'ForeignPrincipalNullList','UnknownContext','ProjectGrantDenied','CrossProjectCursor',
         'CrossPrincipalCursor','MalformedRequest']
READS = {}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key: '+key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Non-finite JSON: '+value)
    return json.loads(raw.decode('utf-8', errors='strict'), object_pairs_hook=pairs, parse_constant=invalid)


def absolute(value):
    p = Path(value)
    return p if p.is_absolute() else ROOT/p


def key(value):
    return os.path.normcase(str(absolute(value).absolute()))


def read(path):
    p = absolute(path)
    require(p.is_file(), 'Missing regular input: '+str(p))
    raw = p.read_bytes()
    item = {'path':str(p.absolute()), 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}
    previous = READS.get(key(p))
    require(previous is None or previous == item, 'Input drift during seal: '+str(p))
    READS[key(p)] = item
    return raw


def doc(path):
    return strict(read(path))


def ref(path):
    read(path)
    return dict(READS[key(path)])


def verify(item):
    require(isinstance(item,dict) and {'path','sha256','bytes'} <= set(item), 'Invalid hash ref')
    raw = read(item['path'])
    require(type(item['bytes']) is int and len(raw) == item['bytes'] and
            hashlib.sha256(raw).hexdigest() == item['sha256'], 'Ref mismatch: '+str(item['path']))
    return raw


def save(directory, name, value):
    raw = (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    p = directory/name
    with p.open('xb') as stream:
        stream.write(raw)
    return ref(p)


def index(rows):
    require(isinstance(rows,list), 'Vector is not list')
    result = {}
    for row in rows:
        k = key(row['path'])
        require(k not in result, 'Duplicate vector path: '+row['path'])
        result[k] = row
    return result


def subset(rows, full):
    for k, item in index(rows).items():
        require(k in full and item['sha256'] == full[k]['sha256'] and
                item['bytes'] == full[k]['bytes'], 'Frozen subset mismatch: '+item['path'])


def closed_job(result):
    require(isinstance(result,dict), 'Missing actual process observation')
    require(type(result.get('actual_exit')) is int and result['actual_exit'] == 0 and
            result.get('error') is None and result.get('timed_out') is False and
            result.get('resumed') is True, 'Native result not successful')
    require(type(result.get('owned_child_pid')) is int and result['owned_child_pid'] > 0 and
            type(result.get('creation_time_100ns')) is int and result['creation_time_100ns'] > 0,
            'Missing PID/creation identity')
    cleanup = result.get('job_cleanup') or {}
    require(cleanup.get('errors') == [] and all(cleanup.get(k) is True for k in
            ['kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed',
             'job_idle_confirmed','handles_closed']), 'Incomplete actual Job cleanup')


def invocation(path, driver=True):
    d = doc(path)
    require(d['actual_exit'] == 0 and d.get('wrapper_error') is None, 'Invocation failure: '+str(path))
    closed_job(d['process_observation'] if driver else d['result'])
    if driver:
        require(d['actor'] == 'codex:/root' and d['automatic_retry'] is False, 'Actor/retry')
        for stream in ['stdout','stderr']:
            require(d[stream]['exists'] is True, 'Missing raw stream')
            verify(d[stream]['ref'])
    else:
        stem = Path(path).name.removesuffix('.invocation.json')
        read(Path(path).parent/(stem+'.stdout.raw'))
        read(Path(path).parent/(stem+'.stderr.raw'))
    require(d['started_at'] <= d['ended_at'], 'Inverted recorded invocation timestamps')
    return d


def snapshot_tree(directory):
    require(directory.is_dir() and not directory.is_symlink(), 'Missing/aliased evidence root')
    rows = []
    for p in sorted(directory.rglob('*')):
        require(not p.is_symlink() and not (getattr(p.lstat(),'st_file_attributes',0)&0x400), 'Evidence reparse point')
        if p.is_file():
            rows.append(ref(p))
    return rows


def sidecars(directory, name):
    facts = doc(directory/name)
    require(facts == {'-wal':{'exists':False,'error':None},'-shm':{'exists':False,'error':None}},
            'Sidecar observation incomplete: '+name)
    return facts


def check_case(out, name, number, full, expected, exe):
    stem = f'case-{number:02d}'
    d = out/'cases'/('TestSessionListHTTPOriginalContextIdentity__'+name)
    inv = invocation(out/(stem+'.invocation.json'))
    require(inv['argv'] == [str(exe), '-test.run',
            '^TestSessionListHTTPOriginalContextIdentity$/^'+name+'$',
            '-test.v','-test.failfast','-test.timeout=150s'], 'Exact selector/limits differ')
    text = verify(inv['stdout']['ref']).decode('utf-8', errors='strict')
    require(not re.search(r'^\s*--- (FAIL|SKIP):',text,re.M), 'FAIL/SKIP in native output')
    passes = re.findall(r'^\s*--- PASS: ([^\s]+)',text,re.M)
    require(Counter(passes) == Counter(['TestSessionListHTTPOriginalContextIdentity',
            'TestSessionListHTTPOriginalContextIdentity/'+name]), 'Native PASS roster differs')
    require(re.search(r'^PASS\s*$',text,re.M), 'No final native PASS')
    for stage in ['before_native','after_native','after_fixture_proofs']:
        require(doc(out/(stem+'.'+stage+'.inputs.json')) == full, 'Per-case frozen vector differs')
        runtime = doc(out/(stem+'.'+stage+'.runtime.json'))
        require(bool(runtime), 'Empty runtime point observation')
        subset(runtime, index(full))
    proof = doc(out/(stem+'.independent-proof.json'))
    require(proof == expected and proof['id'] == f'L{number:02d}' and proof['leaf'] == name and
            proof['actual_native_exit'] == 0 and proof['status'] == 'PASS_DEVELOPMENT_FIXTURE_ONLY', 'Case result binding')
    db = proof['database_check']
    require(absolute(db['database']['path']) == d/'closed.sqlite', 'Wrong closed database')
    verify(db['database'])
    for suffix in ['-wal','-shm']:
        require(not os.path.lexists(str(d/'closed.sqlite')+suffix), 'Closed copy acquired sidecar')
    require(db['schema_all_columns_all_typed_row_multisets_equal'] is True and
            db['readonly_bytes_unchanged'] is True and db['rowid_not_separately_exported'] is True,
            'Missing saved closed-copy proof')
    for filename in ['closed-original.sidecars.json','closed-copy.before.sidecars.json','closed-copy.after.sidecars.json']:
        observed = sidecars(d,filename)
        entry = db['go_three_closed_sidecar_observations'][filename]
        require(entry['facts'] == observed, 'Go sidecar proof mismatch')
        require(absolute(entry['evidence']['path']) == d/filename, 'Go sidecar ref path')
        verify(entry['evidence'])
    for field, filename in [('python_before_read','independent-python.before_read.sidecars.json'),
                            ('python_after_connection_close','independent-python.after_connection_close.sidecars.json')]:
        observed = sidecars(d,filename)
        require(db[field]['facts'] == observed and absolute(db[field]['evidence']['path']) == d/filename,
                'Python sidecar ref mismatch')
        verify(db[field]['evidence'])
    rows = doc(d/'closed.rows.json')
    require(rows == doc(d/'post-open.rows.json'), 'Saved row snapshots differ')
    require(set(rows['tables']) == set(rows['columns']) and
            db['table_counts'] == {k:len(v) for k,v in rows['tables'].items()}, 'Saved all-table coverage/count')
    for s in rows['schema']:
        require(len(strict(s.encode('utf-8'))) == 5, 'Saved schema row shape')
    for tab, values in rows['tables'].items():
        for value in values:
            cells = strict(value.encode('utf-8'))
            require(len(cells) == len(rows['columns'][tab]) and all(
                isinstance(c,list) and len(c)==2 and c[0] in ['null','integer','real','text','blob'] for c in cells),
                'Saved typed row shape')
    native = doc(d/'closed-proof.json')
    require(native['closed_copy_sha256'] == db['database']['sha256'] and
            all(native[k] is True for k in ['all_table_schema_multisets_equal','closed_copy_bytes_unchanged_by_read',
                                          'closed_copy_sidecars_absent']) and
            native['case_failed'] is False and native['SDK_worker_model_external_paid'] == 0, 'Native DB proof')
    request_files = sorted(d.glob('http-*.request.json'))
    require(0 < len(request_files) <= 16, 'Case HTTP cap')
    for request in request_files:
        wire_stem = request.name.removesuffix('.request.json')
        for part in ['request','response']:
            meta = doc(d/(wire_stem+'.'+part+'.json'))
            raw = read(d/(wire_stem+'.'+part+'.raw'))
            require(meta['bytes']==len(raw) and meta['sha256']==hashlib.sha256(raw).hexdigest(), 'Wire raw hash')
    assertions = doc(d/'assertions.json')
    require(assertions['case']==name and assertions['all_assertions_reached'] is True and
            assertions['HTTP_calls_including_setup']==native['HTTP_calls_including_setup']==
            proof['wire_check']['HTTP_calls_including_setup']==len(request_files), 'HTTP count disagreement')
    journals = sorted(d.glob('journal-*.json'))
    require(len(journals)==(0 if name in ['ProjectGrantDenied','MalformedRequest'] else 1), 'Journal count')
    for path in journals:
        j = doc(path)
        n = int(path.stem.split('-')[1])
        req = read(d/f'http-{n:02d}.request.raw')
        response = strict(read(d/f'http-{n:02d}.response.raw'))
        env = strict(req)
        stored = strict(j['body'].encode('utf-8'))
        header = strict(j['headers'].encode('utf-8'))
        require(base64.b64decode(header['raw_envelope_base64'],validate=True)==req and stored==response,
                'Original request/journal/response mismatch')
        require(j['command_id']==env['command_id']==stored['command_id'] and
                j['project']==env['project_id'] and j['method']==env['method']==stored['method']=='session.list' and
                env['session_id']==stored['session_id'] and stored['revision'] is None and
                env['protocol_version']==stored['protocol_version']=='researchos-client/2', 'Original journal identity')
    return len(request_files)


def seal(args, destination):
    scope_raw = read(SCOPE)
    require(hashlib.sha256(scope_raw).hexdigest()==SCOPE_SHA, 'Fixed scope SHA')
    scope = strict(scope_raw)
    require(scope['run_uuid']==RUN_UUID and scope['ordered_cases']==NAMES, 'Run/roster')
    outer_raw = read(args.outer_receipt)
    require(hashlib.sha256(outer_raw).hexdigest()==args.outer_sha256, 'Actual outer receipt SHA')
    outer = strict(outer_raw)
    require(outer['schema']=='researchos.root-finite14-outer-completion.v1' and
            outer['actor']=='codex:/root' and outer['actual_outer_exit']==0 and
            outer['run_uuid']==RUN_UUID and outer['scope_ref']['sha256']==SCOPE_SHA and
            outer['launcher_ref']==scope['launcher_ref'] and outer['automatic_retry'] is False and
            outer['counter_reset'] is False, 'No actual Root outer-zero authority')
    require(outer['actual_native_launcher_exit'] is None, 'Unobserved launcher native exit must remain null')
    require(outer['tool_initial_chunk']=='a294f6' and outer['session_id']==6787 and
            isinstance(outer['tool_completion_chunk'],str) and outer['tool_completion_chunk'] and
            outer['tool_result_ref']['bytes'] > 0, 'Missing actual outer tool evidence')
    tool = strict(verify(outer['tool_result_ref']))
    require(tool['exit_code']==0 and tool['chunk_id']==outer['tool_completion_chunk'] and
            tool.get('session_id') is None, 'Tool result is not final outer-zero completion')
    verify(outer['scope_ref'])
    require(absolute(outer['scope_ref']['path'])==SCOPE and absolute(outer['cwd'])==ROOT,
            'Outer scope/cwd binding')
    require(outer['argv'][1:5]==['-I','-S','-X','utf8'] and
            absolute(outer['argv'][5])==absolute(scope['launcher_ref']['path']) and
            absolute(outer['argv'][6])==SCOPE and outer['argv'][7]==SCOPE_SHA and len(outer['argv'])==8,
            'Actual outer invocation argv binding')
    out, export, auth = [absolute(scope[k]) for k in ['new_output_root','new_export_root','new_authorization_root']]
    require(not any(os.path.lexists(p) for p in [out/'driver.exception.json',auth/'failure.origin.json',
                                                out/'inputs.after_failure.json']), 'Success seal refuses failed run')
    original_trees = [(p,snapshot_tree(p)) for p in [out,auth]]
    completed = doc(auth/'completed.json')
    require(completed['actual_exit']==0 and completed['status']=='ROOT_FINITE14_EXECUTION_FINISHED_REVIEW_PENDING' and
            completed['source_acceptance'] is False and completed['formal_increment']==0, 'Launcher not completed')
    grant_ref = completed['grant_ref']
    require(absolute(grant_ref['path'])==auth/'authorization.execute.json', 'Wrong grant')
    verify(grant_ref)
    # This fixed gate has only filesystem/JSON/hash operations; never import a native helper or driver.
    gate_raw = verify(scope['authorization_gate_ref'])
    require(hashlib.sha256(gate_raw).hexdigest()==GATE_SHA, 'Pure gate code pin')
    gate = types.ModuleType('root14_sealer_pure_authorization_gate')
    gate.__file__ = str(absolute(scope['authorization_gate_ref']['path']))
    exec(compile(gate_raw,gate.__file__,'exec'),gate.__dict__)
    authorization = gate.validate_grant(SCOPE,SCOPE_SHA,absolute(grant_ref['path']),grant_ref['sha256'])
    for item in authorization['authorization_input_refs']:
        verify(item)
    for old in ['v2_actual_prelaunch_failure_ref','v2_original_launcher_failure_ref']:
        verify(scope[old])
    inner = invocation(auth/'inner.invocation.json',False)
    require(inner['argv'][1:5]==scope['python_flags'] and
            absolute(inner['argv'][5])==absolute(scope['runner_ref']['path']) and
            absolute(inner['argv'][6])==SCOPE and inner['argv'][7]==SCOPE_SHA and
            absolute(inner['argv'][8])==absolute(grant_ref['path']) and inner['argv'][9]==grant_ref['sha256'],
            'Inner actual argv/grant')
    for name in ['head','status','index']:
        invocation(auth/(name+'.invocation.json'),False)
    runtime_catalog = strict(verify(scope['runtime_resources_ref']))['files']
    runtime_index = index(runtime_catalog + [scope[k] for k in
                          ['launcher_ref','authorization_gate_ref','owned_process_helper_ref']])
    for name in ['runtime.before_git.json','runtime.before_inner.json','runtime.after_inner.json']:
        observation = doc(auth/name)
        require(observation['all_observed_inputs_pre_pinned'] is True and observation['files'], 'Launcher runtime point')
        subset(observation['files'],runtime_index)
        for item in observation['files']:
            verify(item)
    result = doc(out/'result.json')
    require(result['candidate']==scope['source_commit'] and result['independent_actor']=='codex:/root' and
            result['native_case_invocations']==result['PASS_leaves']==14 and result['SKIP']==0 and result['input_drift']==0 and
            result['SDK_worker_model_external_paid_private']==0 and result['source_acceptance'] is False and
            result['Main_integration_authorized'] is False and result['formal_increment']==0 and len(result['cases'])==14,
            'Final bounded result mismatch')
    stages = {n:doc(out/('inputs.'+n+'.json')) for n in ['before_Go_tools','after_Go_list','before_compile',
                                                        'after_compile','before_first_case','after_cases']}
    full = stages['before_first_case']
    full_index = index(full)
    require(stages['before_Go_tools']==stages['after_Go_list'] and stages['before_compile']==stages['after_compile'] and
            full==stages['after_cases'] and len(full)==result['input_count'], 'Stage input drift')
    subset(stages['before_Go_tools'],index(stages['before_compile']))
    subset(stages['before_compile'],full_index)
    subset(doc(out/'authorization-inputs.original.json'),index(stages['before_Go_tools']))
    subset(authorization['authorization_input_refs'],index(stages['before_Go_tools']))
    for item in full:
        verify(item)
    for file in out.glob('*.invocation.json'):
        invocation(file)
    exports = doc(out/'public-source-export.json')
    expected_invocations = {n+'.invocation.json' for n in ['candidate-source-delta','candidate-parent',
        'public-tree','protected-base-test','readonly-gofmt','go-version','go-list','compile','exe-buildinfo']}
    expected_invocations.update(f'git-export-{i:04d}.invocation.json' for i in range(1,len(exports)+1))
    expected_invocations.update(f'case-{i:02d}.invocation.json' for i in range(1,15))
    require({p.name for p in out.glob('*.invocation.json')}==expected_invocations, 'Invocation roster is incomplete or expanded')
    for item in exports:
        require(absolute(item['path'])==export/item['relative_path'], 'Export destination mismatch')
        raw = verify(item)
        require(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==item['git_blob'], 'Git blob differs')
    subset(exports,full_index)
    export_names = {x['relative_path'] for x in exports}
    catalog = strict(verify(scope['public_compiler_catalog_ref']))
    require(len(catalog['git_resources'])==518 and all(x['path'] in export_names for x in catalog['git_resources']),
            'Known public compiler catalog omitted')
    for path, pin in scope['individually_approved_public_Go_resources'].items():
        require(path in export_names and hashlib.sha256(read(export/path)).hexdigest()==pin['sha256'],
                'Named public compiler resource mismatch')
    for path, digest in scope['source_paths_sha256'].items():
        require(hashlib.sha256(read(export/path)).hexdigest()==digest, 'Exact source pin')
    old = read(out/'protected-base-test.stdout.raw')
    marker = b'// Only the host binding port'
    protected = old[old.index(marker):]
    require(len(protected)==scope['protected_body_bytes'] and
            hashlib.sha256(protected).hexdigest()==scope['protected_body_sha256'] and
            read(export/'internal/api/v2_sessions_test.go').split(marker,1)[1].startswith(protected[len(marker):]),
            'Original protected test body changed')
    require(read(out/'candidate-parent.stdout.raw').decode('ascii').strip()==scope['actual_candidate_parent_expected'] and
            read(out/'candidate-source-delta.stdout.raw').decode('utf-8').splitlines()==scope['actual_source_delta_paths'],
            'Source delta/parent evidence')
    require(read(out/'readonly-gofmt.stdout.raw')==b'', 'Readonly gofmt output')
    work = absolute(result['whole_compiler_WORK_path'])
    require(work.is_relative_to(export/'.local/gotmp'), 'WORK not fresh export')
    work_rows = doc(out/'compiled_WORK_vector.json')
    require(index(snapshot_tree(work))==index(work_rows), 'All WORK contents differ')
    subset(work_rows,full_index)
    for item in doc(out/'actual-importcfg-packagefile-refs.json'):
        require(key(item['importcfg']) in index(work_rows), 'Importcfg not in WORK')
        parsed = []
        for line in read(item['importcfg']).decode('utf-8',errors='strict').splitlines():
            if line.startswith('packagefile '):
                package, archive = line[len('packagefile '):].split('=',1)
                parsed.append((package,key(archive.replace('$WORK',str(work)))))
        require((item['package'],key(item['archive']['path'])) in parsed, 'Exact package/archive not in actual importcfg')
        verify(item['archive'])
        subset([item['archive']],full_index)
    mains = list((out/'generated').rglob('_testmain.go'))
    require(len(mains)==1 and b'TestSessionListHTTPOriginalContextIdentity' in read(mains[0]), 'Generated test entry missing')
    for p in (out/'generated').rglob('*'):
        if p.is_file():
            require(read(p)==read(work/p.relative_to(out/'generated')), 'Generated copy differs from actual WORK')
    exe = out/'session-list-api.test.exe'
    require(absolute(result['new_executable']['path'])==exe, 'New executable path')
    verify(result['new_executable'])
    subset([result['new_executable']],full_index)
    require(invocation(out/'compile.invocation.json')['argv'][1:]==
            ['test','-c','-work','-x','-o',str(exe),'./internal/api'], 'Compile provenance argv')
    require(invocation(out/'go-list.invocation.json')['argv'][1:]==
            ['list','-deps','-test','-compiled','-json','./internal/api'], 'Compiled graph argv')
    graph_raw = read(out/'go-list.stdout.raw').decode('utf-8',errors='strict')
    decoder, position, packages = json.JSONDecoder(), 0, []
    while position < len(graph_raw):
        while position < len(graph_raw) and graph_raw[position].isspace():
            position += 1
        if position == len(graph_raw):
            break
        package, position = decoder.raw_decode(graph_raw,position)
        require(not package.get('Error') and not package.get('DepsErrors'), 'Actual compiled graph error')
        packages.append(package)
    require(packages and any(str(p.get('ImportPath','')).endswith('/internal/api.test') for p in packages),
            'Generated test variant absent from graph')
    advertised = doc(out/'generated-advertised.json')['paths']
    before_compile_index = index(stages['before_compile'])
    fields = ['GoFiles','CgoFiles','CompiledGoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles',
              'SFiles','SwigFiles','SwigCXXFiles','SysoFiles','EmbedFiles','TestGoFiles','XTestGoFiles',
              'TestEmbedFiles','XTestEmbedFiles']
    for package in packages:
        for field in fields:
            for value in package.get(field,[]):
                p = Path(value)
                if not p.is_absolute():
                    p = Path(package['Dir'])/p
                if key(p) in before_compile_index:
                    continue
                require(field=='CompiledGoFiles' and str(p.resolve()) in advertised and
                        p.resolve().is_relative_to(export/'.local'), 'Graph input not frozen/advertised: '+str(p))
        mod = package.get('Module',{}).get('GoMod')
        if mod:
            require(key(mod) in before_compile_index, 'Module graph input absent')
    require(invocation(out/'exe-buildinfo.invocation.json')['argv'][1:]==['version','-m',str(exe)], 'Exe buildinfo argv')
    require(read(out/'exe-buildinfo.stdout.raw'), 'Buildinfo raw empty')
    total = sum(check_case(out,n,i,full,result['cases'][i-1],exe) for i,n in enumerate(NAMES,1))
    require(total==result['actual_HTTP_calls_including_setup'] and total<=224, 'Total HTTP count')
    for directory, before in original_trees:
        require(snapshot_tree(directory)==before, 'Original evidence tree changed during seal')
    for item in list(READS.values()):
        verify(item)
    audit = {'schema':'researchos.root14-readonly-evidence-seal.v1','actor':'codex:/root',
             'status':'BOUNDED_FINITE14_EVIDENCE_HASH_VERIFIED_PENDING_INDEPENDENT_REVIEW',
             'scope_ref':ref(SCOPE),'outer_completion_ref':ref(args.outer_receipt),'grant_ref':grant_ref,
             'actual_native_case_invocations':14,'PASS_leaves':14,'SKIP':0,'HTTP_calls_including_setup':total,
             'current_frozen_input_count':len(full),'input_drift':0,'SQL_reexecution':0,'product_processes_started':0,
             'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,
             'limits':['Sealer consumes saved SQL comparisons; it does not re-run SQLite.',
                       'Implicit rowid not independently exported; same-user path TOCTOU remains.',
                       'Python/module inventories are point observations, not whole-lifetime loading proof.',
                       'Root outer tool evidence is supplied and signed by Root; no native exit inferred from outer exit.'],
             'old_failure_refs':[scope[k] for k in ['v2_actual_prelaunch_failure_ref','v2_original_launcher_failure_ref']]}
    audit_ref = save(destination,'audit.json',audit)
    save(destination,'handoff.json',{'audit_ref':audit_ref,'source_acceptance':False,'formal_increment':0,
                                  'original_evidence_modified':False,'status':audit['status']})


def main():
    require(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize,
            'Use pinned Python -I -S -X utf8 without optimization')
    parser = argparse.ArgumentParser()
    parser.add_argument('--outer-receipt',required=True)
    parser.add_argument('--outer-sha256',required=True)
    parser.add_argument('--seal-directory',required=True)
    args = parser.parse_args()
    destination = absolute(args.seal_directory)
    require(destination.is_relative_to(ROOT/'execution/v2.4/receipts/W05/W05-99/root14_evidence_sealed_codex') and
            destination.parent.is_dir() and not os.path.lexists(destination), 'Fresh dedicated seal directory required')
    destination.mkdir()
    error = None
    try:
        ref(__file__)
        seal(args,destination)
    except BaseException as exc:
        error = exc
        save(destination,'failure.origin.json',{'error':repr(exc),'traceback':traceback.format_exc(),
             'actual_product_native_exit':None,'sealer_exit':1,'automatic_retry':False,'counter_reset':False,
             'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    finally:
        # All consumed originals, full original OUT/AUTH trees, closed DBs and new seal files.
        # Exclude only this manifest itself; never delete or rewrite any evidence.
        for p in destination.iterdir():
            if p.is_file():
                ref(p)
        entries = sorted(READS.values(),key=lambda x:x['path'])
        save(destination,'manifest.json',{'schema':'researchos.readonly-evidence-manifest.v1',
             'count':len(entries),'entries':entries,'excluded_only':str(destination/'manifest.json'),
             'originals_retained_in_place':True,'seal_success':error is None})
    if error is not None:
        raise error


if __name__=='__main__':
    main()
