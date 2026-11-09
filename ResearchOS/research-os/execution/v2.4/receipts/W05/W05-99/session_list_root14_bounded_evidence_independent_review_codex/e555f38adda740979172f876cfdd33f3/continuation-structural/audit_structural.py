import base64
import collections
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

R = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
N = R / 'execution/v2.4/receipts/W05/W05-99'
P = N / 'session_list_closedcopy_exact1_root_replay_codex/0b2ae4ec4e824c968553ff884c3fa132'
A = N / 'session_list_closedcopy_exact1_root_replay_authorization_codex/0b2ae4ec4e824c968553ff884c3fa132'
S = N / 'root14_evidence_sealed_codex/e1b3d1e2a8404f6997dab28af163d25c'
E = R / '.local/independent-session-list-closedcopy-root-0b2ae4ec4e824c968553ff884c3fa132'
GIT = Path('C:/Program Files/Git/cmd/git.exe')
checks = []
reads = {}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def raw(p):
    p = Path(p)
    if not p.is_absolute():
        p = R / p
    b = p.read_bytes()
    reads[str(p)] = {'path': str(p), 'sha256': digest(b), 'bytes': len(b)}
    return b

def load(p):
    return json.loads(raw(p))

def save(name, obj):
    with (HERE / name).open('xb') as f:
        f.write((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def check(name, ok, details=None):
    checks.append({'check': name, 'passed': bool(ok), 'details': details})

def key(p):
    return os.path.normcase(os.path.abspath(p))

def vmap(rows):
    out = {key(x['path']): (x['sha256'], x['bytes']) for x in rows}
    check('vector_unique_paths', len(out) == len(rows), len(rows))
    return out

def subset(a, b):
    return all(b.get(k) == v for k, v in a.items())

def verify_ref(x):
    b = raw(x['path'])
    return digest(b) == x['sha256'] and len(b) == x['bytes']

def git(label, args):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
    env.update(GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='nul')
    proc = subprocess.run([str(GIT), '-C', str(R), *args], env=env, capture_output=True)
    for suffix, b in [('stdout.raw', proc.stdout), ('stderr.raw', proc.stderr)]:
        with (HERE / (label + '.' + suffix)).open('xb') as f:
            f.write(b)
    save(label + '.invocation.json', {'argv': [str(GIT), '-C', str(R), *args], 'actual_exit': proc.returncode, 'product_execution': False})
    check('readonly_git_' + label, proc.returncode == 0)
    if proc.returncode != 0:
        raise RuntimeError('readonly Git failed; stop: ' + label)
    return proc.stdout

started = time.time()
try:
    pins = [('audit.json', '5444b4202ce69e82f4b39ad8216ed1ab849bf7a39c83b2cda4232a2c3eb31e58'), ('handoff.json', 'd9843eeccf9862a20aca62f19b08fc00acea10c5123ca20bdaf079b57ca9f4cd'), ('manifest.json', 'bbf0683877fdbdc1178b85b6808db029ea201ec2510083cc1456ed919868e9f2')]
    for name, sha in pins:
        check('root_seal_pin_' + name, digest(raw(S / name)) == sha)
    manifest = load(S / 'manifest.json')
    entries = manifest['entries']
    check('manifest_20350', manifest['count'] == len(entries) == 20350)
    mm = vmap(entries)

    def hash_entry(x):
        p = Path(x['path'])
        try:
            h = hashlib.sha256()
            size = 0
            with p.open('rb') as f:
                while b := f.read(4 * 1024 * 1024):
                    size += len(b)
                    h.update(b)
            return {'path': str(p), 'sha256': h.hexdigest(), 'bytes': size, 'match': h.hexdigest() == x['sha256'] and size == x['bytes']}
        except OSError as e:
            return {'path': str(p), 'match': False, 'error': str(e)}

    prior = HERE.parent / 'manifest.current-byte-audit.json'
    hashed = load(prior)
    check('reused_actual_completed_hash_audit_20350',len(hashed)==20350 and all(x['match'] for x in hashed))
    check('reused_hash_audit_exact_manifest',vmap(hashed)==mm)

    grant = load(A / 'authorization.execute.json')
    scope = load(P / 'scope.original.json')
    result = load(P / 'result.json')
    check('actual_grant', grant['actual_registration_completed'] is True and grant['status'] == 'ROOT_REGISTERED_EXECUTION_AUTHORIZED')
    # Preserve complete historical authority; current canonical movement is not substituted.
    def walkrefs(x):
        if isinstance(x, dict):
            if {'path', 'sha256', 'bytes'} <= x.keys():
                yield x
            for v in x.values():
                yield from walkrefs(v)
        elif isinstance(x, list):
            for v in x:
                yield from walkrefs(v)
    authority_refs = list(walkrefs(grant))
    for x in authority_refs:
        check('historical_authority_ref', verify_ref(x), x['path'])
    check('grant_hash', digest(raw(A / 'authorization.execute.json')) == 'a79c1941460cc6e3bc4460e130624d8c00b77a37571913f403710c98fbd07f7d')

    vectors = {}
    for n in ['before_Go_tools', 'after_Go_list', 'before_compile', 'after_compile', 'before_first_case', 'after_cases']:
        vectors[n] = vmap(load(P / ('inputs.' + n + '.json')))
    stages = ['before_Go_tools', 'after_Go_list', 'before_compile', 'after_compile', 'before_first_case', 'after_cases']
    for a, b in zip(stages, stages[1:]):
        check('append_only_input_extension_' + a + '_' + b, subset(vectors[a], vectors[b]))
    frozen = vectors['before_first_case']
    check('frozen_18202_after_exact', len(frozen) == 18202 and frozen == vectors['after_cases'])
    check('frozen_covered_by_manifest', subset(frozen, mm))
    work = vmap(load(P / 'compiled_WORK_vector.json'))
    check('whole_WORK_frozen', len(work) == 1866 and subset(work, frozen))
    importcfg = load(P / 'actual-importcfg-packagefile-refs.json')
    for x in importcfg:
        ar = x['archive']
        check('importcfg_actual_archive_frozen', key(x['importcfg']) in frozen and frozen.get(key(ar['path'])) == (ar['sha256'], ar['bytes']))

    names = ['NullContext','OwnedContext','ContextNotResultFilter','ExactReplayAfterCommit','ChangedPayloadConflict','ChangedSIDConflict','CrossProjectContext','ForeignPrincipalContext','ForeignPrincipalNullList','UnknownContext','ProjectGrantDenied','CrossProjectCursor','CrossPrincipalCursor','MalformedRequest']
    check('result_roster', [x['leaf'] for x in result['cases']] == names)
    summaries = []
    for i, name in enumerate(names, 1):
        stem = f'case-{i:02d}'
        inv = load(P / (stem + '.invocation.json'))
        obs = inv['process_observation']; cleanup = obs['job_cleanup']
        check(stem + '_actual_owned_success', inv['actual_exit'] == 0 and inv['wrapper_error'] is None and obs['actual_exit'] == 0 and obs['error'] is None and not obs['timed_out'] and obs['resumed'] is True and inv['automatic_retry'] is False)
        check(stem + '_all_job_guards', all(cleanup.get(x) is True for x in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and cleanup['errors'] == [] and cleanup['active_processes_last_observed'] == 0)
        check(stem + '_exact_selector_exe', inv['argv'][0] == str(P / 'session-list-api.test.exe') and inv['argv'][1:3] == ['-test.run', '^TestSessionListHTTPOriginalContextIdentity$/^' + name + '$'])
        stdout = raw(P / (stem + '.stdout.raw')).decode('utf-8')
        check(stem + '_actual_leaf_PASS_no_SKIP_FAIL', '--- PASS: TestSessionListHTTPOriginalContextIdentity/' + name + ' ' in stdout and '\nPASS\n' in stdout.replace('\r\n', '\n') and '--- SKIP:' not in stdout and '--- FAIL:' not in stdout)
        runtimes = []
        for stage in ['before_native','after_native','after_fixture_proofs']:
            check(stem + '_' + stage + '_full_vector', vmap(load(P / (stem + '.' + stage + '.inputs.json'))) == frozen)
            rt = vmap(load(P / (stem + '.' + stage + '.runtime.json')))
            check(stem + '_' + stage + '_runtime_frozen', subset(rt, frozen))
            runtimes.append(rt)
        check(stem + '_runtime_stages_identical', runtimes[0] == runtimes[1] == runtimes[2])
        proof = load(P / (stem + '.independent-proof.json'))
        check(stem + '_result_is_original_case_proof', result['cases'][i-1] == proof)
        C = P / ('cases/TestSessionListHTTPOriginalContextIdentity__' + name)
        cp = load(C / 'closed-proof.json'); ass = load(C / 'assertions.json')
        closed = load(C / 'closed.rows.json'); opened = load(C / 'post-open.rows.json')
        check(stem + '_saved_full_typed_multisets', closed == opened and set(closed['tables']) == set(closed['columns']) and proof['database_check']['table_counts'] == {k:len(v) for k,v in closed['tables'].items()})
        check(stem + '_closed_proofs', cp['all_table_schema_multisets_equal'] is True and cp['closed_copy_bytes_unchanged_by_read'] is True and cp['closed_copy_sidecars_absent'] is True and cp['case_failed'] is False and cp['SDK_worker_model_external_paid'] == 0 and cp['closed_copy_sha256'] == digest(raw(C / 'closed.sqlite')))
        sidecars = ['closed-original.sidecars.json','closed-copy.before.sidecars.json','closed-copy.after.sidecars.json','independent-python.before_read.sidecars.json','independent-python.after_connection_close.sidecars.json']
        for n in sidecars:
            x = load(C / n)
            check(stem + '_' + n, set(x) == {'-wal','-shm'} and all(v == {'exists':False,'error':None} for v in x.values()))
        check(stem + '_sidecars_remain_absent', not (C/'closed.sqlite-wal').exists() and not (C/'closed.sqlite-shm').exists())
        before = load(C / 'target.before.rows.json'); after = load(C / 'target.after.rows.json')
        check(stem + '_schema_unchanged', before['schema'] == after['schema'] and before['columns'] == after['columns'] and set(before['tables']) == set(after['tables']))
        added = name not in ['ProjectGrantDenied','MalformedRequest']
        for table, rows in before['tables'].items():
            left, right = collections.Counter(rows), collections.Counter(after['tables'][table])
            expected_add = added and table in ['idempotency','client_command_identities']
            check(stem + '_table_delta_' + table, (not (left-right) and sum((right-left).values()) == 1) if expected_add else left == right)
        metas = sorted(C.glob('http-*.request.json'))
        for m in metas:
            h = m.name.removesuffix('.request.json')
            for kind in ['request','response']:
                meta = load(C / (h+'.'+kind+'.json')); b = raw(C / (h+'.'+kind+'.raw'))
                check(stem + '_' + h + '_' + kind + '_raw', meta['bytes'] == len(b) and meta['sha256'] == digest(b))
        journals = sorted(C.glob('journal-*.json'))
        check(stem + '_journal_count', len(journals) == int(added))
        for jpath in journals:
            j = load(jpath); num = int(jpath.stem.split('-')[1]); h = f'http-{num:02d}'
            reqraw = raw(C/(h+'.request.raw')); req=json.loads(reqraw); resraw=raw(C/(h+'.response.raw')); res=json.loads(resraw)
            header=json.loads(j['headers']); stored=json.loads(j['body'])
            check(stem+'_private_original_request', header['schema']=='researchos.private-command-envelope.v1' and header['encoding']=='base64' and base64.b64decode(header['raw_envelope_base64'],validate=True)==reqraw)
            check(stem+'_journal_response_identity', stored==res and stored['session_id']==req['session_id'] and stored['revision'] is None and j['command_id']==req['command_id']==stored['command_id'] and j['project']==req['project_id'] and j['method']==req['method']==stored['method']=='session.list')
        if name in ['ExactReplayAfterCommit','ChangedPayloadConflict','ChangedSIDConflict']:
            check(stem+'_replay_all_rows_unchanged', load(C/'replay.after.rows.json')==after)
            originals=[m for m in metas if json.loads(raw(C/m.name.replace('.request.json','.request.raw'))).get('command_id')=='list-original']
            check(stem+'_original_and_replay_two_requests', len(originals)==2)
            h1=originals[0].name.removesuffix('.request.json');h2=originals[1].name.removesuffix('.request.json')
            if name=='ExactReplayAfterCommit':
                check(stem+'_wire_replay_byte_exact',raw(C/(h1+'.request.raw'))==raw(C/(h2+'.request.raw')) and raw(C/(h1+'.response.raw'))==raw(C/(h2+'.response.raw')))
            else:
                response=load(C/(h2+'.response.json')); body=json.loads(raw(C/(h2+'.response.raw')))
                check(stem+'_changed_request_409',raw(C/(h1+'.request.raw'))!=raw(C/(h2+'.request.raw')) and response['status']==409 and body['error']['code']=='COMMAND_ID_CONFLICT')
        count=len(metas)
        check(stem+'_HTTP_count_cap',0<count<=16 and count==cp['HTTP_calls_including_setup']==ass['HTTP_calls_including_setup']==proof['wire_check']['HTTP_calls_including_setup'])
        summaries.append({'id':f'L{i:02d}','name':name,'native_exit':0,'http_calls':count,'closed_database_sha256':cp['closed_copy_sha256'],'pid':obs['owned_child_pid'],'creation_time_100ns':obs['creation_time_100ns']})
    check('aggregate_exact14_78', len(summaries)==14 and sum(x['http_calls'] for x in summaries)==78 and result['PASS_leaves']==14 and result['SKIP']==0)
    save('case-summary.json',summaries)

    outer=load(N/'integration_codex/root14-outer-completion-a294f6-1cd304/outer-completion.json')
    check('outer_separate_nullable_native',outer['actual_outer_exit']==0 and outer['actual_native_launcher_exit'] is None)
    for ref in load(S/'audit.json')['old_failure_refs']:
        check('old_failure_retained',verify_ref(ref) and key(ref['path']) in mm,ref['path'])

    # Source-only Git chain and actual exported blobs; no checkout mutation.
    base='2cdb0d43d5a600eef13c8f1735946a9adf52d079';handler='22752a6a41732c8c158d7d7e1b8932ec958f8cb8';fix='534857db99fa5e694987f877af74c322eaa2a0b3';candidate='a5d6d16ffaf129de0361470c3a1570228bd259a2'
    deltas=[]
    for label,parent,child in [('handler',base,handler),('list',handler,fix),('closedcopy',fix,candidate)]:
        actualparent=git(label+'-parent',['rev-parse',child+'^']).decode().strip()
        delta=git(label+'-delta',['diff-tree','--no-commit-id','--name-only','-r',child]).decode().splitlines()
        check(label+'_exact_parent',actualparent==parent)
        deltas.append(delta)
    check('38_2_1_unique38',list(map(len,deltas))==[38,2,1] and set(deltas[1])<=set(deltas[0]) and set(deltas[2])<=set(deltas[1]) and len(set().union(*map(set,deltas)))==38)
    export=load(P/'public-source-export.json')
    # ls-tree supplies immutable path/blob binding; blob Git hashes independently match actual bytes.
    tree=git('candidate-tree',['ls-tree','-r',candidate]).decode().splitlines()
    treemap={line.split('\t',1)[1]:line.split('\t',1)[0].split()[2] for line in tree}
    for x in export:
        b=raw(x['path']); blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        check('export_Git_blob_'+x['relative_path'],blob==x['git_blob']==treemap.get(x['relative_path']) and digest(b)==x['sha256'] and len(b)==x['bytes'])
    check('export_count',len(export)==713)
    old=raw(P/'protected-base-test.stdout.raw');marker=b'// Only the host binding port';body=old[old.index(marker):]
    new=raw(E/'internal/api/v2_sessions_test.go')
    check('protected_original_14633',len(body)==14633 and digest(body)=='c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1' and new.split(marker,1)[1].startswith(body[len(marker):]))
    prior=git('list-test-original',['show',fix+':internal/api/v2_sessions_test.go']);suffix=b'func TestSessionListHTTPOriginalContextIdentity(t *testing.T) {'
    check('original14_suffix_unchanged',prior[prior.index(suffix):]==new[new.index(suffix):])
    save('source-chain.json',{'commits':[base,handler,fix,candidate],'deltas':deltas,'unique_source_paths':sorted(set().union(*map(set,deltas)))})
    save('source38-current-map.json',[x for x in export if x['relative_path'] in deltas[0]])
except Exception as e:
    save('audit.exception.json',{'type':type(e).__name__,'message':str(e),'product_executions':0,'SQL_connections':0})
    raise
finally:
    save('read-refs.json',list(reads.values()))
    save('checks.json',checks)
    save('audit-summary.json',{'checks':len(checks),'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],'elapsed_seconds':time.time()-started,'product_executions':0,'SQL_connections':0,'imports_of_reviewed_code':0})
print(json.dumps({'checks':len(checks),'failed':[x for x in checks if not x['passed']]},ensure_ascii=False))
