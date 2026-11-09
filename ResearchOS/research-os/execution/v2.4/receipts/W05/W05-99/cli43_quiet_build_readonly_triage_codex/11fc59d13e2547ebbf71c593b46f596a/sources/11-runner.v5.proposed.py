"""PREPARATION ONLY. Root scope/grant/resources are deliberately NULL in the proposal.

Future execution: Python -I -S -X utf8 THIS scope scopeSHA grant grantSHA.
No SQLite Python reader. All SQL observations belong to explicitly instrumented tests.
"""
import base64
import hashlib
import json
import os
import re
import sys
import time
import traceback
import types
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = 'a510dbef4a7e08fb5c428df44c39b133f3ffa856'
LEAVES = ['real-existing-open-readonly', 'real-existing-self-send']


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def strict(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            need(k not in out, 'Duplicate JSON key')
            out[k] = v
        return out
    return json.loads(raw.decode('utf-8', errors='strict'), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def pin(path):
    p = Path(path).absolute()
    h = hashlib.sha256()
    size = 0
    with p.open('rb') as f:
        while b := f.read(1048576):
            size += len(b)
            h.update(b)
    return {'path': str(p), 'sha256': h.hexdigest(), 'bytes': size}


def verify(ref):
    need(isinstance(ref, dict) and set(ref) == {'path', 'sha256', 'bytes'}, 'Immutable input ref shape')
    need(isinstance(ref['path'], str) and type(ref['bytes']) is int and ref['bytes'] >= 0
         and isinstance(ref['sha256'], str) and len(ref['sha256']) == 64
         and all(c in '0123456789abcdef' for c in ref['sha256']), 'Immutable input ref fields')
    p = Path(ref['path']).absolute()
    need(str(p) == ref['path'], 'Immutable input absolute path spelling')
    raw = p.read_bytes()
    need(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'Immutable input mismatch')
    return raw


def save(path, value):
    with Path(path).open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def safe(path, root, absent=False):
    p, root = Path(path).absolute(), Path(root).absolute()
    need('..' not in p.parts and p != root and p.is_relative_to(root), 'Owned path boundary')
    need(p.resolve(strict=False) == p, 'Path alias')
    for q in [p] + list(p.parents):
        if os.path.lexists(q):
            st = q.lstat()
            need(not q.is_symlink() and not getattr(st, 'st_file_attributes', 0) & 0x400, 'Reparse path')
    if absent:
        need(not os.path.lexists(p), 'Fresh path already exists')
    return p


def files(root):
    root = Path(root)
    out = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            p = Path(directory) / name
            need(not p.is_symlink() and not getattr(p.lstat(), 'st_file_attributes', 0) & 0x400, 'Inventory reparse')
        out.extend(Path(directory) / name for name in names)
    return sorted(out, key=lambda p: str(p).casefold())


def raw_module(ref, name):
    m = types.ModuleType(name)
    m.__file__ = ref['path']
    exec(compile(verify(ref), ref['path'], 'exec'), m.__dict__)
    return m


class Ledger:
    def __init__(self, out):
        self.out, self.members, self.revision = out, {}, 0

    def add(self, label, paths):
        added = []
        for p in sorted(set(str(Path(x).absolute()) for x in paths)):
            row = pin(p)
            if p in self.members:
                need(row == self.members[p], 'Input changed while extending ledger: ' + p)
            else:
                self.members[p] = row
                added.append(row)
        self.revision += 1  # Empty addition still has an exact prefix revision.
        save(self.out / f'ledger-add-{self.revision:03d}.json',
             {'revision': self.revision, 'label': label, 'added': added,
              'full_members': [self.members[p] for p in sorted(self.members)]})

    def check(self, label):
        observed, drift = [], []
        for p, old in sorted(self.members.items()):
            try:
                new = pin(p)
                observed.append(new)
                if new != old:
                    drift.append({'expected': old, 'actual': new})
            except BaseException as e:
                drift.append({'expected': old, 'read_error': repr(e)})
        result = {'revision': self.revision, 'expected_members': [self.members[p] for p in sorted(self.members)],
                  'observed_members': observed, 'file_count': len(self.members), 'drift': drift}
        save(self.out / (label + '.vector.json'), result)
        need(not drift and len(observed) == len(self.members), 'Input vector drift: ' + label)


def job_ok(r, debug=False):
    c = r['job_cleanup']
    need(r['actual_exit'] == 0 and r['error'] is None and not r['timed_out'] and r['resumed'] is True,
         'Owned process failed')
    need(all(c.get(k) is True for k in ['unnamed_exclusive_job', 'assigned_before_resume',
         'kill_on_job_close_configured', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed'])
         and c['active_processes_last_observed'] == 0 and not c['errors'],
         'Owned process cleanup incomplete')
    if debug:
        need(c['explicit_owned_handles_remaining'] == 0, 'Retained debug handles not closed')
        d = r['debug_capture']
        need(d['mode'] == 'CREATE_OWN_JOB_DEBUG_PROCESS_TREE' and d['complete'] is True
             and d['actual_loaded_file_handles_only'] is True and d['modules'], 'Debug tree incomplete')
        need(len(d['process_generations']) == d['create_process_count'] == d['exit_process_count']
             == d['total_processes_last_observed'], 'Process tree event accounting')
        need(all(x['before'] == x['after'] for x in d['modules']), 'Actual retained DLL changed')
        need(all(x['job_membership_observed'] and x['exit_continued'] and
                 x['exit_event_code'] == x['independent_exit'] for x in d['process_generations']), 'Exit facts')


def module_observation(allowed, helper):
    paths = {str(Path(sys.executable).absolute()), str(Path(__file__).absolute())}
    paths.update(str(Path(p).absolute()) for p in helper.runtime_resource_paths())
    for m in tuple(sys.modules.values()):
        for key in ['__file__', '__cached__']:
            p = getattr(m, key, None)
            if p and Path(p).is_file():
                paths.add(str(Path(p).absolute()))
    # This helper discovers actually loaded OS modules only at the observation point.
    rows = []
    bypath = {os.path.normcase(x['path']): x for x in allowed}
    for p in sorted(paths):
        row = pin(p)
        need(bypath.get(os.path.normcase(p)) == row, 'Unpinned observed Python/OS resource: ' + p)
        rows.append(row)
    return {'files': rows, 'point_in_time_only': True, 'Python_lifecycle_proof': False}


def validate_http_evidence(directory, summary):
    def raw_bytes(value):
        b=b'' if value['raw_base64'] is None and value['bytes']==0 else base64.b64decode(value['raw_base64'],validate=True)
        need(len(b)==value['bytes'] and hashlib.sha256(b).hexdigest()==value['sha256'],'Actual body bytes/SHA')
        return b
    need(summary['first_overflow'] is None and summary['stopped'] is False and not summary['pending'],
         'HTTP overflow/unfinished pending reservation')
    need(summary['setup_included_in_upstream'] is True and summary['unobserved_client_outbound_attempts'] is None,
         'HTTP boundary claim changed')
    up,proxy=summary['upstream'],summary['proxy'];records=summary['records']
    for layer,c in [('upstream',up),('proxy',proxy)]:
        need(all(type(v) is int and v>=0 for v in c.values()),'Counter type')
        need(c['attempt']==c['admitted']+c['rejected']==c['completed'] and c['outstanding']==0 and
             c['rejected']==0 and 0<c['admitted']<=32,'HTTP reservation/completion counters')
        need(sum(x['layer']==layer for x in records.values())==c['attempt'],'Counters vs preserved attempts')
    need(up['dispatched']==up['admitted']==up['responses']==up['body_closed']==up['received']==summary['upstream_received'],
         'Upstream dispatch/response/body close/server ingress mismatch')
    need(proxy['received']==proxy['attempt'] and summary['actual_received_HTTP_legs']==up['received']+proxy['received']<=64,
         'Actual observed ingress qualification cap')
    need(sorted(int(x) for x in records)==list(range(1,len(records)+1)),'Admission sequence continuity')
    forwards={}
    for key,row in records.items():
        seq=int(key);need(row['sequence']==seq and row['completed'] is True and row['admitted'] is True,'HTTP record status')
        original=strict((directory/f'http-attempt-{seq:04d}.json').read_bytes())
        completed=strict((directory/f'http-completed-{seq:04d}.json').read_bytes())
        need(completed==row and original['request']==row['request'] and original['request_key']==row['request_key'],
             'Immutable raw attempt/completion pair')
        raw_bytes(row['request'])
        if row['layer']=='upstream':
            need(row['dispatched'] is True and row['response_observed'] is True and
                 row['read_EOF_observed'] is True and row['response_close_error'] is None and
                 type(row['status']) is int and isinstance(row['response_headers'],dict),'Upstream received boundary')
            need(all(x['error'] in (None,'EOF') for x in row['read_calls']),'Upstream response reader error')
            raw_bytes(row['response'])
            parent=row['proxy_sequence']
            if parent is not None:
                need(type(parent) is int and str(parent) in records and records[str(parent)]['layer']=='proxy' and
                     records[str(parent)]['request_key']==row['request_key'] and parent<seq,'Exact proxy-forward pairing')
                need(parent not in forwards,'Proxy forwarded more than once')
                forwards[parent]=row
        else:
            need(row['CLI_facing_handler_boundary'] is True and row['request_read_error'] is None and
                 row['request_close_error'] is None and row['actual_client_received_headers'] is None and
                 row['actual_client_received_body'] is None and row['automatic_transport_headers'] is None,
                 'Proxy boundary promoted to unobserved socket/client fields')
            accepted=[]
            for w in row['write_calls']:
                requested=raw_bytes(w['requested']);part=raw_bytes(w['accepted'])
                need(type(w['actual_n']) is int and 0<=w['actual_n']<=len(requested) and
                     part==requested[:w['actual_n']],'Actual accepted write subset')
                need(w['error'] is None and w['actual_n']==len(requested),'Partial/error write: execution remains unqualified')
                accepted.append(part)
            need(b''.join(accepted)==raw_bytes(row['accepted_body']),'Actual writer body aggregation')
    for key,row in records.items():
        if row['layer']=='proxy':
            need(int(key) in forwards,'Proxy with no original upstream forward')
            upstream=forwards[int(key)]
            need(row['status']==upstream['status'] and raw_bytes(row['accepted_body'])==raw_bytes(upstream['response']),
                 'Upstream received and proxy accepted bytes/status differ')
    ingress=[]
    for p in sorted(directory.glob('upstream-received-*.json')):
        r=strict(p.read_bytes());need(r['read_error'] is None and r['close_error'] is None,'Upstream request reader error')
        seq=r['dispatch_sequence'];need(type(seq) is int and str(seq) in records and records[str(seq)]['layer']=='upstream','Unpaired real ingress')
        need(r['request']==records[str(seq)]['request'],'Real ingress vs original dispatched raw')
        f=strict((directory/f"upstream-handler-{r['received_sequence']:04d}.json").read_bytes())
        need(f['dispatch_sequence']==seq and f['request_key']==records[str(seq)]['request_key'],'Handler pairing')
        need(f['actual_client_received_headers'] is None and f['automatic_transport_headers'] is None,'Handler automatic headers unknown')
        accepted=[]
        for w in f['write_calls']:
            requested=raw_bytes(w['requested']);part=raw_bytes(w['accepted'])
            need(type(w['actual_n']) is int and w['actual_n']==len(requested) and w['error'] is None and
                 part==requested,'Upstream actual writer incomplete/error')
            accepted.append(part)
        need(b''.join(accepted)==raw_bytes(f['accepted_body'])==raw_bytes(records[str(seq)]['response']) and
             f['status']==records[str(seq)]['status'],'Upstream handler accepted bytes vs actual fixture transport received')
        ingress.append(seq)
    need(len(ingress)==len(set(ingress))==up['received'],'Every ingress preserved once')
    return {'upstream_dispatches':up['dispatched'],'proxy_admissions':proxy['admitted'],
            'actual_received_HTTP_legs':summary['actual_received_HTTP_legs'],
            'unobserved_client_outbound_attempts':None,'cap_is_observation_qualification':True}


def main():
    need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
    sys.dont_write_bytecode = True
    need(len(sys.argv) == 5, 'scope scopeSHA grant grantSHA required')
    scope_path, scope_sha, grant_path, grant_sha = sys.argv[1:]
    raw = Path(scope_path).read_bytes()
    need(hashlib.sha256(raw).hexdigest() == scope_sha, 'Scope hash')
    scope = strict(raw)
    need(scope.get('preparation_only') is False and scope.get('execution_authorized') is True,
         'PREPARATION_ONLY: no actual scope/grant')
    gate = raw_module(scope['authorization_gate_ref'], 'cli43_authorization')
    authorized = gate.validate_grant(scope_path, scope_sha, grant_path, grant_sha)
    need(scope == authorized['scope'] and scope['source_commit'] == SOURCE and scope['ordered_cases'] == LEAVES,
         'Finite source/roster binding')
    out = None
    stage, first, secondary, last_result = 'CREATE_OWNED_OUTPUT', None, [], None
    ledger = None
    stages, case_results, native_calls = [], [], 0
    case_roster = [{'leaf':leaf,'state':'NOT_STARTED','launch_attempted':False,'resumed':None,
                    'owned_child_pid':None,'creation_time_100ns':None,'actual_native_exit':None,
                    'requested':False,'test_leaf_started':None,'fixture_observation':'NOT_STARTED',
                    'qualified':False,'failure':None} for leaf in LEAVES]
    current_case = None
    started = time.monotonic()
    normal = debug = None
    try:
        candidate = safe(scope['new_output_root'], ROOT / 'execution/v2.4/receipts/W05/W05-99', True)
        need(candidate.parent.is_dir(), 'Root must prepare bounded parent before launch')
        candidate.mkdir()
        out = candidate
        save(out / 'scope.actual.json', scope)
        export = safe(scope['new_export_root'], ROOT / '.local', True)
        export.mkdir()
        build = export / '.cli43-build'
        build.mkdir()
        for name in ['gocache', 'gotmp', 'work', 'tmp', 'case-evidence']:
            (build / name).mkdir()
        runtime = strict(verify(scope['runtime_resources_ref']))
        compiler = strict(verify(scope['compiler_resources_ref']))
        need(runtime['files'] and compiler['files'] and compiler['complete_public_roots'], 'Fresh resource inventories missing')
        resources = runtime['files'] + compiler['files']
        for row in resources:
            verify(row)
        for r in compiler['complete_public_roots']:
            actual = [pin(p) for p in files(r['path'])]
            need(actual == r['files'], 'Immutable compiler root membership changed')
        controls = [scope[k] for k in ['runner_ref', 'launcher_ref', 'authorization_gate_ref',
                    'owned_process_helper_ref', 'debug_tree_helper_ref']]
        allowed = resources + controls
        # Imports happen after raw source pins, with Python/OS preapproved; no site or pyc writes.
        normal = raw_module(scope['owned_process_helper_ref'], 'owned_process')
        debug = raw_module(scope['debug_tree_helper_ref'], 'debug_process_tree')
        ledger = Ledger(out)
        authorization_refs=[]
        for row in authorized['authorization_input_refs']:
            p=Path(row['path']);p=p if p.is_absolute() else ROOT/p
            expected={**row,'path':str(p.absolute())};verify(expected);authorization_refs.append(expected)
        ledger.add('authorization-runtime-and-compiler', authorized['authorization_paths'] +
                   [x['path'] for x in resources + controls])
        need(all(ledger.members[x['path']]==x for x in authorization_refs),'Authorization changed before initial freeze')
        ledger.check('initial')
        save(out / 'python-os.before.json', module_observation(allowed, normal))
        tools = strict(Path(scope['toolchain_lock_path']).read_bytes())['tools']
        for name in ['python', 'git', 'go']:
            need(pin(tools[name]['path'])['sha256'] == tools[name]['sha256'], 'Pinned tool mismatch')
        need(Path(sys.executable).resolve() == Path(tools['python']['path']).resolve(), 'Actual Python mismatch')
        go, git = tools['go']['path'], tools['git']['path']
        env = dict(scope['public_environment'])
        need(set(env).issubset({'SystemRoot','WINDIR','ComSpec','PATH','PATHEXT'}), 'Nonpublic inherited environment')
        env.update({'GOTOOLCHAIN':'local','GOENV':'off','GOWORK':'off','GOPROXY':'off','GOSUMDB':'off',
                    'GOOS':'windows','GOARCH':'amd64','GOAMD64':'v1','CGO_ENABLED':'0','GOEXPERIMENT':'',
                    'GODEBUG':'','GOFLAGS':'','GOROOT':compiler['GOROOT'],'GOPATH':compiler['GOPATH'],
                    'GOMODCACHE':compiler['GOMODCACHE'],'GOCACHE':str(build/'gocache'),
                    'GOTMPDIR':str(build/'gotmp'),'TEMP':str(build/'tmp'),'TMP':str(build/'tmp'),
                    'GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1','GIT_CONFIG_NOSYSTEM':'1',
                    'GIT_CONFIG_GLOBAL':os.devnull})

        def run(label, argv, cwd, timeout, tree=False, images=None, process_cap=1, case_env=None, stdin=None):
            nonlocal stage, native_calls, last_result
            stage = label
            need(time.monotonic() - started < 3300 and native_calls < 16, 'Controller time/call cap')
            native_calls += 1
            if current_case is not None:
                current_case['state']='STARTED';current_case['requested']=True
                save(out/(label+'.case-started.json'),dict(current_case))
            request = {'argv':argv,'cwd':str(cwd),'environment':case_env or env,'timeout_seconds':timeout,
                       'sequence':native_calls,'debug_tree':tree,'process_cap':process_cap}
            save(out/(label+'.request.json'), request)
            r = None; invocation_error=None
            try:
                with (out/(label+'.stdout.raw')).open('xb') as stdout, (out/(label+'.stderr.raw')).open('xb') as stderr:
                    if current_case is not None: current_case['launch_attempted']=True
                    if tree:
                        r = debug.run_owned(argv,str(cwd),case_env or env,stdout,stderr,timeout,
                              expected_image={k:pin(argv[0])[k] for k in ['sha256','bytes']},
                              allowed_images=images,allowed_module_files=list(ledger.members.values()),
                              process_cap=process_cap,stdin=stdin)
                    else:
                        r = normal.run_owned(argv,str(cwd),case_env or env,stdout,stderr,timeout,stdin=stdin)
                last_result = r
            except BaseException as e:
                invocation_error=e
            finally:
                save(out/(label+'.invocation.json'), {'request':request,'result':r,
                    'actual_exit':r['actual_exit'] if r else None, 'automatic_retry':False,'counter_reset':False})
                if current_case is not None:
                    current_case.update(resumed=r.get('resumed') if r else None,
                        owned_child_pid=r.get('owned_child_pid') if r else None,
                        creation_time_100ns=r.get('creation_time_100ns') if r else None,
                        actual_native_exit=r.get('actual_exit') if r else None)
                    if r and r.get('resumed'): current_case['state']='RESUMED'
                    if r and r.get('actual_exit') is not None: current_case['state']='NATIVE_EXIT_OBSERVED'
                    save(out/(label+'.case-native-observation.json'),dict(current_case))
            primary_error=invocation_error
            if primary_error is None:
                try: job_ok(r, tree)
                except BaseException as e: primary_error=e
            native_observation_errors=[]
            if current_case is not None:
                try:
                    case_events=[strict(line) for line in (out/(label+'.stdout.raw')).read_bytes().splitlines() if line.strip()]
                    expected_leaf='TestCLIProtocolInteractiveAuthority/'+current_case['leaf']
                    entered=any(x.get('Action')=='run' and x.get('Test')==expected_leaf for x in case_events)
                    current_case['test_leaf_started']=True if entered else (False if r and r.get('actual_exit') is not None else None)
                    save(out/(label+'.test-events.observed.json'),{'events':case_events,
                        'test_leaf_started':current_case['test_leaf_started'],'qualification_claim':False})
                except BaseException as e:
                    native_observation_errors.append({'stage':label+'-partial-test-events','error':repr(e)})
            try: ledger.check(label+'-native-after')
            except BaseException as e: native_observation_errors.append({'stage':label+'-native-after-vector','error':repr(e)})
            try: save(out/(label+'.python-os.native-after.json'),module_observation(allowed,normal))
            except BaseException as e: native_observation_errors.append({'stage':label+'-native-after-runtime','error':repr(e)})
            if primary_error is not None:
                secondary.extend(native_observation_errors)
                raise primary_error
            if native_observation_errors:
                secondary.extend(native_observation_errors[1:])
                raise RuntimeError(native_observation_errors[0])
            stages.append({'label':label,'result_ref':pin(out/(label+'.invocation.json'))})
            return (out/(label+'.stdout.raw')).read_bytes(), r

        head, _ = run('git-head', [git,'rev-parse','HEAD'], ROOT,30)
        need(head.decode('ascii').strip() == SOURCE, 'Current Main source changed')
        catalog = strict(verify(scope['catalog_ref']))
        need(catalog['commit'] == SOURCE and catalog['files'], 'Fresh Git catalogue')
        main_inputs=[]
        for row in catalog['files']:
            p=ROOT/row['path'];actual=pin(p)
            need(actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'],'Main public source changed')
            main_inputs.append(p)
        ledger.add('current-Main43-public-source',main_inputs)
        batch = ''.join(x['git_blob']+'\n' for x in catalog['files']).encode('ascii')
        (out/'git-batch.stdin.raw').open('xb').write(batch)
        with (out/'git-batch.stdin.raw').open('rb') as stdin:
            blobs,_ = run('git-public-blobs',[git,'cat-file','--batch'],ROOT,90,stdin=stdin)
        pos = 0
        for row in catalog['files']:
            end=blobs.index(b'\n',pos); sha,kind,size=blobs[pos:end].decode('ascii').split();pos=end+1
            size=int(size);body=blobs[pos:pos+size];pos+=size
            need(sha==row['git_blob'] and kind=='blob' and len(body)==row['bytes'] and
                 hashlib.sha256(body).hexdigest()==row['sha256'] and blobs[pos:pos+1]==b'\n','Git blob mismatch')
            pos+=1
            target=safe(export/row['path'],export,True);target.parent.mkdir(parents=True,exist_ok=True)
            target.open('xb').write(body)
        need(pos==len(blobs),'Extra batch bytes')
        original=export/'apps/cli/cli_sessions_test.go'
        plan=strict(verify(scope['instrumentation_ref']))
        need(pin(original)['sha256']==plan['original_sha256'],'Test original SHA')
        instrumented=verify(scope['instrumented_source_ref'])
        need(hashlib.sha256(instrumented).hexdigest()==plan['instrumented_sha256'],'Instrumented SHA')
        reverse=instrumented.decode('utf-8')
        for c in reversed(plan['changes']):
            need(reverse.count(c['new'])==1,'Nonunique instrumentation replacement')
            reverse=reverse.replace(c['new'],c['old'],1)
        need(reverse.encode('utf-8')==original.read_bytes(),'Instrumentation removes original bytes')
        (out/'cli_sessions_test.original.go.txt').open('xb').write(original.read_bytes())
        original.write_bytes(instrumented)  # The sole explicitly authorized EXPORT-ONLY replacement.
        helper=export/'apps/cli/cli43_receipt_instrumentation_test.go'
        helper.open('xb').write(verify(scope['instrumentation_helper_ref']))
        save(out/'instrumentation.actual.json',{'original':plan['original_sha256'],'export_test':pin(original),
                                              'helper':pin(helper),'unmodified_Main_testexe':False})
        ledger.add('fresh-export-and-instrumentation',[p for p in files(export) if not p.is_relative_to(build)])
        ledger.check('before-any-go')
        images=compiler['compiler_images']
        need(images and len(images)<=62,'Finite compiler image list must leave two slots for the new test and CLI')
        for row in images: verify(row)
        run('go-version',[go,'version'],export,30,True,images,4)
        run('go-env',[go,'env','-json','GOROOT','GOPATH','GOMODCACHE','GOCACHE','GOTMPDIR','GOOS','GOARCH','GOAMD64',
             'CGO_ENABLED','GOTOOLCHAIN','GOENV','GOWORK','GOEXPERIMENT','GODEBUG'],export,30,True,images,4)
        graph,_=run('go-list',[go,'list','-buildvcs=false','-mod=readonly','-compiled','-deps','-test','-json','-work','-x','./apps/cli'],export,240,True,images,2048)
        decoder=json.JSONDecoder();text=graph.decode('utf-8',errors='strict');idx=0;packages=[]
        while idx<len(text):
            if text[idx].isspace(): idx+=1;continue
            obj,idx=decoder.raw_decode(text,idx);packages.append(obj)
        need(packages and all(not p.get('Error') and not p.get('DepsErrors') for p in packages),'Go dependency errors')
        graph_files=[]
        fields=['GoFiles','CgoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','IgnoredGoFiles','IgnoredOtherFiles',
                'CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles',
                'EmbedFiles','TestEmbedFiles','XTestEmbedFiles']
        for p in packages:
            for field in fields:
                for name in p.get(field,[]):
                    q=Path(name) if Path(name).is_absolute() else Path(p['Dir'])/name
                    need(q.is_file(),'Missing actual graph file: '+str(q))
                    need(str(q.absolute()) in ledger.members or q.is_relative_to(build),'Uncatalogued Go input: '+str(q))
                    graph_files.append(q)
            for field in ['GoMod']:
                name=p.get('Module',{}).get(field)
                if name:
                    need(str(Path(name).absolute()) in ledger.members,'Uncatalogued module metadata')
                    graph_files.append(Path(name))
        save(out/'go-graph.actual.json',{'packages':packages,'all_referenced_files':[pin(p) for p in sorted(set(graph_files))]})
        cli=build/'researchos-cli.exe';test=build/'cli.test.exe'
        run('build-cli',[go,'build','-mod=readonly','-buildvcs=false','-work','-x','-o',str(cli),'./apps/cli'],export,600,True,images,2048)
        run('build-test',[go,'test','-c','-mod=readonly','-buildvcs=false','-work','-x','-o',str(test),'./apps/cli'],export,600,True,images,2048)
        allwork=files(build/'gotmp');allcache=files(build/'gocache')
        need(any(p.name=='_testmain.go' for p in allwork),'No generated test main captured')
        importcfg=[];archives=[]
        for p in allwork:
            if p.name in ['importcfg','importcfg.link']:
                importcfg.append(pin(p))
                for line in p.read_text(encoding='utf-8',errors='strict').splitlines():
                    if line.startswith('packagefile '):
                        q=Path(line.split('=',1)[1]);need(q.is_file(),'Missing compiler archive')
                        need(q.is_relative_to(build) or str(q.absolute()) in ledger.members,'Uncatalogued archive')
                        archives.append(q)
        need(importcfg and archives,'No importcfg/archive evidence')
        ledger.add('allWORK-cache-archives-newexecutables',allwork+allcache+archives+[cli,test])
        save(out/'compiled-closure.json',{'WORK':[pin(p) for p in allwork],'cache':[pin(p) for p in allcache],
             'importcfg':importcfg,'archives':[pin(p) for p in sorted(set(archives))],
             'cli':pin(cli),'testexe':pin(test),'same_round':True,'Main_test_instrumented':True})
        run('buildinfo-cli',[go,'version','-m',str(cli)],export,30,True,images,4)
        run('buildinfo-test',[go,'version','-m',str(test)],export,30,True,images,4)
        ledger.check('compiled-before-first-case')
        for i,leaf in enumerate(LEAVES):
            current_case=case_roster[i]
            label=f'case-{i:02d}';case=build/'case-evidence'/label;case.mkdir()
            for r in compiler['complete_public_roots']:
                need([pin(p) for p in files(r['path'])]==r['files'],'Compiler root membership drift before case')
            ledger.check(label+'-before')
            ee=dict(env);ee.update({'RESEARCHOS_CLI_PROTOCOL_BINARY':str(cli),
                                    'RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR':str(case)})
            selector='^TestCLIProtocolInteractiveAuthority$/^'+leaf+'$'
            argv=[go,'tool','test2json','-t','-p','researchos.local/research-os/apps/cli',str(test),
                  '-test.v','-test.count=1','-test.timeout=480s','-test.failfast','-test.run',selector]
            stdout,r=run(label,argv,export/'apps/cli',510,True,images+[pin(cli),pin(test)],16,ee)
            current_case['fixture_observation']='STARTED'
            events=[strict(line) for line in stdout.splitlines() if line.strip()]
            expected={'TestCLIProtocolInteractiveAuthority','TestCLIProtocolInteractiveAuthority/'+leaf}
            need({x.get('Test') for x in events if x['Action']=='run'}==expected,'Unexpected test roster')
            need({x.get('Test') for x in events if x['Action']=='pass' and x.get('Test')}==expected and
                 not any(x['Action'] in ['fail','skip'] for x in events),'Test event failure/skip')
            gens=r['debug_capture']['process_generations']
            cli_gens=[x for x in gens if x['image']['before']=={k:pin(cli)[k] for k in ['sha256','bytes']}]
            need(len(cli_gens)==1 and cli_gens[0]['independent_exit']==(0 if i==0 else 3),'Actual CLI generation/exit')
            evidence=case/('TestCLIProtocolInteractiveAuthority_'+leaf)
            proof=strict((evidence/'closed-proof.json').read_bytes())
            need(proof['closed_bytes_equal'] and proof['all_schema_column_typed_row_multisets_equal'] and
                 proof['original_and_copy_WAL_SHM_absent'] and not proof['original_reopened'] and not proof['case_failed'],
                 'Closed-copy proof incomplete')
            for name in ['session.sqlite','closed-copy.sqlite']:
                need(pin(evidence/name)['sha256']==proof['original_after_close_sha256'],'Actual closed bytes')
                need(not os.path.lexists(str(evidence/name)+'-wal') and not os.path.lexists(str(evidence/name)+'-shm'),'Sidecar exists')
            before=strict((evidence/'db-post-open.rows.json').read_bytes());after=strict((evidence/'db-closed-copy.rows.json').read_bytes())
            need(before==after,'Actual schema/typed row mismatch')
            summary=strict((evidence/'http-summary.json').read_bytes())
            counts=validate_http_evidence(evidence,summary)
            business=strict((evidence/'business-counts.json').read_bytes())
            need(business=={'sends':i,'tasks':i,'send_journal':i,'read_only_attach':1,'cli_exit':0 if i==0 else 3},'Original business assertions')
            ident=strict((evidence/'identity-proof.json').read_bytes())
            need(ident['before_sid']==ident['after_sid']==ident['db_sid'] and ident['epoch']==1,'Original SID')
            current_case['fixture_observation']='OBSERVED'
            ledger.check(label+'-fixture-after')
            save(out/(label+'.python-os.fixture-after.json'),module_observation(allowed,normal))
            for rr in compiler['complete_public_roots']:
                need([pin(p) for p in files(rr['path'])]==rr['files'],'Compiler root membership drift after case')
            case_results.append({'leaf':leaf,'status':'PASS','HTTP':counts,'proof_ref':pin(evidence/'closed-proof.json')})
            current_case['qualified']=True;current_case['state']='QUALIFIED'
            save(out/(label+'.verified.json'),case_results[-1])
            current_case=None
        ledger.check('final')
        need(len(case_results)==2,'Incomplete finite run')
    except BaseException as e:
        first={'stage':stage,'error':repr(e),'traceback':traceback.format_exc(),
               'actual_stage_native_exit':None,'last_child_result':last_result,
               'automatic_retry':False,'counter_reset':False}
        if current_case is not None:
            current_case['failure']=first
            if current_case['resumed'] is True:
                current_case['state']='EXECUTED_FAILED' if current_case['actual_native_exit'] not in (None,0) else 'EXECUTED_UNQUALIFIED'
            elif current_case['launch_attempted']:
                current_case['state']='LAUNCH_ATTEMPT_FAILED_OR_UNCONFIRMED'
            else:
                current_case['state']='PRELAUNCH_BLOCKED'
        if out is None:
            sys.stderr.write(json.dumps(first,ensure_ascii=False)+'\n')
    finally:
        if out is not None:
            if 'build' in locals():
                try: save(out/'build-artifacts.finally.json',{'files':[pin(p) for p in files(build)],'partial_if_failed':first is not None})
                except BaseException as e: secondary.append({'stage':'partial-artifact-inventory','error':repr(e)})
            if ledger:
                try: ledger.check('after-finally')
                except BaseException as e: secondary.append({'stage':'final-vector','error':repr(e)})
            if normal:
                try: save(out/'python-os.after.json',module_observation(allowed,normal))
                except BaseException as e: secondary.append({'stage':'runtime-after','error':repr(e)})
            if first is None and secondary:
                first={'stage':'EVIDENCE_FINALIZATION','error':secondary[0], 'actual_stage_native_exit':None}
            try:
                if first is not None: save(out/'failure.origin.json',first)
                save(out/'result.json',{'status':'BOUNDED_DEVELOPMENT_EVIDENCE_REPORTED' if first is None else 'STOPPED',
                     'first_cause':first,'secondary':secondary,'stages':stages,'cases':case_results,
                     'case_roster':case_roster,'NOT_RUN':[x['leaf'] for x in case_roster if not x['launch_attempted']],
                     'not_started_definition':'No launch call entered; never derived from qualified/pass counts','native_calls':native_calls,
                     'product_acceptance':False,'formal_increment':0,'SDK_MODEL_external_paid':0})
                manifest=[pin(p) for p in files(out)]
                save(out/'manifest.json',{'files':manifest,'count':len(manifest),'excluded_only_self':True})
            except BaseException as e:
                secondary.append({'stage':'FINAL_RECEIPT_WRITE','error':repr(e)})
                first=first or {'stage':'FINAL_RECEIPT_WRITE','error':repr(e),'actual_stage_native_exit':None}
                sys.stderr.write(json.dumps({'first_cause':first,'secondary':secondary,'case_roster':case_roster,
                    'partial_inner_manifest_not_success':True,'actual_stage_native_exit':None},ensure_ascii=False)+'\n')
    return 0 if first is None else 1


if __name__ == '__main__':
    try:
        code=main()
    except BaseException as exc:
        # No safe owned leaf may exist: actual Root outer saves these original stderr bytes.
        sys.stderr.write(json.dumps({'stage':'ENTRY_OR_UNHANDLED_FINALIZE','error':repr(exc),
            'traceback':traceback.format_exc(),'actual_native_exit':None,'local_origin_available':False,
            'outer_raw_stderr_is_authority':True,'automatic_retry':False,'counter_reset':False},ensure_ascii=False)+'\n')
        code=1
    raise SystemExit(code)
