"""Receipt-only finite G2 runner. Requires a separately registered Root grant.
This file is prepared/AST checked only until such authorization is supplied.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import traceback
import types

HERE = Path('D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\provider_g2_finite_replay_preparation_codex\\3ed3a3da52c3471d9ddc524897100842')

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def ref(path):
    p = Path(path).absolute()
    return {'path': str(p), 'resolved': str(p.resolve(strict=True)), 'sha256': digest(p), 'bytes': p.stat().st_size}

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def verify(item):
    actual = ref(item['path'])
    require(actual['sha256'] == item['sha256'], 'SHA mismatch: ' + item['path'])
    if 'bytes' in item:
        require(actual['bytes'] == item['bytes'], 'Size mismatch: ' + item['path'])
    if 'resolved' in item:
        require(os.path.normcase(actual['resolved']) == os.path.normcase(item['resolved']), 'Physical path mismatch: ' + item['path'])
    return actual

def vector(paths):
    return [ref(p) for p in sorted(set(Path(p).absolute() for p in paths), key=lambda p:str(p).casefold())]

def check_vector(expected, output):
    actual, errors = [], []
    for item in expected:
        try:
            row = ref(item['path'])
            actual.append(row)
            if any(row[k] != item[k] for k in ['sha256', 'bytes', 'resolved']):
                errors.append({'expected': item, 'actual': row})
        except Exception as e:
            errors.append({'expected': item, 'error': repr(e)})
    save(output, {'at':now(), 'observed':actual, 'errors':errors})
    require(not errors, 'Protected input drift: ' + str(output))

def json_stream(text):
    decoder = json.JSONDecoder()
    out = []
    while text.strip():
        text = text.lstrip()
        value, end = decoder.raw_decode(text)
        out.append(value)
        text = text[end:]
    return out

def function_bytes(source, name):
    text = source.decode('utf-8')
    match = re.search(r'^func '+re.escape(name)+r'\(', text, re.M)
    require(match is not None, 'Missing protected function: ' + name)
    start = match.start(); i = text.index('{', match.end()); depth = 0; state = 'code'
    while i < len(text):
        c = text[i]; pair = text[i:i+2]
        if state == 'line':
            if c == '\n': state = 'code'
        elif state == 'block':
            if pair == '*/': state = 'code'; i += 1
        elif state in ('string','rune'):
            if c == '\\': i += 1
            elif c == ('"' if state == 'string' else "'"): state = 'code'
        elif state == 'raw':
            if c == '`': state = 'code'
        elif pair == '//': state = 'line'; i += 1
        elif pair == '/*': state = 'block'; i += 1
        elif c == '"': state = 'string'
        elif c == "'": state = 'rune'
        elif c == '`': state = 'raw'
        elif c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return text[start:i+1].encode('utf-8')
        i += 1
    raise RuntimeError('Unclosed protected function: ' + name)

class Replay:
    def __init__(self, spec, grant, phase, helper):
        self.s = spec; self.grant = grant; self.phase = phase; self.helper = helper
        self.work = Path(spec['work_root']); self.out = Path(spec['output_root'])
        self.source = self.work / 'source'; self.phaseout = self.out / phase
        self.go = Path(spec['tools']['go']['path']); self.node = Path(spec['tools']['node']['path'])
        self.git = Path(spec['git']['path']); self.bundle = Path(spec['bundle']['path'])
        self.exe = self.work / 'domain.g2.independent.test.exe'
        self.env = {k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'}}
        self.env.update({'PATH':str(self.node.parent)+';C:/Windows/System32;C:/Windows', 'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(self.go.parent.parent),
            'GOPATH':str(Path(spec['repo'])/'.local/gopath'),'GOCACHE':str(self.work/'cache'),'GOTMPDIR':str(self.work/'gotmp'),
            'TEMP':str(self.work/'temp'),'TMP':str(self.work/'temp'),'GOPROXY':'off','GOSUMDB':'off',
            'RESEARCHOS_MU_BUNDLE':str(self.bundle),'RESEARCHOS_GO':str(self.go),
            'CGO_ENABLED':'0','GOOS':'windows','GOARCH':'amd64','GOAMD64':'v1','GOEXPERIMENT':'','GODEBUG':'','GOWORK':'off',
            'GOFLAGS':'-buildvcs=false','GOMODCACHE':str(Path(spec['repo'])/'.local/gopath/pkg/mod'),
            'GIT_NO_REPLACE_OBJECTS':'1','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull})
        self.guarded = []; self.results = []; self.callnumber = 0; self.controller_paths = set()

    def run(self, name, argv, cwd, timeout, env=None, stdin_path=None):
        d = self.phaseout / ('process-%03d-%s' % (self.callnumber,name)); self.callnumber += 1; d.mkdir()
        invocation = {'argv':[str(a) for a in argv], 'cwd':str(cwd),'environment':env or self.env,'started_at':now(),'stdin':ref(stdin_path) if stdin_path else None}
        result = None
        try:
            with (d/'stdout.raw').open('xb') as stdout, (d/'stderr.raw').open('xb') as stderr:
                if stdin_path:
                    with Path(stdin_path).open('rb') as inp:
                        result = self.helper.run_owned(invocation['argv'],str(cwd),env or self.env,stdout,stderr,timeout,stdin=inp)
                else:
                    result = self.helper.run_owned(invocation['argv'],str(cwd),env or self.env,stdout,stderr,timeout)
        finally:
            invocation.update({'ended_at':now(),'result':result, 'actual_exit':result.get('actual_exit') if result else None})
            save(d/'invocation.json',invocation)
        require(result is not None, 'Owned process did not return observable result')
        require(result['error'] is None and not result['timed_out'] and result['actual_exit'] == 0,
                'Process failed: '+name+' '+repr(result))
        cleanup=result.get('job_cleanup') or {}
        require(result.get('resumed') is True and all(cleanup.get(key) is True for key in
            ['kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed'])
            and cleanup.get('errors')==[], 'Full ownedJob cleanup not confirmed')
        return d

    def runtime_paths(self, label):
        # pathlib URI conversion lazily imports modules. Prime it before inventory.
        uris={key:path.resolve().as_uri() for key,path in [('work',self.work),('source',self.source),('output',self.out)]}
        dlls=self.helper.runtime_resource_paths()
        paths=set(); modules=[]
        for name,module in sorted(list(sys.modules.items())):
            row={'module':name}
            for attr in ['__file__','__cached__']:
                value=getattr(module,attr,None)
                if isinstance(value,str):
                    p=Path(value).absolute();exists=p.is_file()
                    row[attr]={'path':str(p),'exists':exists}
                    if exists:paths.add(p)
            modules.append(row)
        for item in dlls:paths.add(Path(item if isinstance(item,str) else item['path']))
        save(self.phaseout/(label+'.json'),{'URIs_primed_before_freeze':uris,'loaded_modules':modules,'loaded_DLL_paths':dlls,
             'dont_write_bytecode':'Only inhibits writes. Existing actually referenced __cached__ files are separately frozen.'})
        return paths

    def resource_paths(self):
        paths = {Path(__file__), HERE/'execution_spec.json', HERE/'case_expectations.json', HERE/'preparation_manifest.json',
                 Path(self.grant['_path']),self.go,self.go.parent/'gofmt.exe',self.git,self.node,Path(sys.executable),self.bundle,Path(str(self.bundle)+'.build.json'),Path(self.s['helper']['path'])}
        for item in load(HERE/'preparation_manifest.json')['entries']:
            verify(item); paths.add(Path(item['path']))
        self.controller_paths={Path(__file__),HERE/'execution_spec.json',HERE/'finite_roster.json',HERE/'case_expectations.json',
             HERE/'preparation_manifest.json',Path(self.grant['_path']),Path(self.s['helper']['path'])}
        for item in self.grant['scope_refs']+self.grant['controller_refs']:
            verify(item);self.controller_paths.add(Path(item['path']))
        runtime=self.runtime_paths('python-os-runtime.before')
        self.controller_paths.update(runtime);paths.update(self.controller_paths)
        for name in ['old_build_input_inventory','protected_functions','static_review','future_scope']:
            verify(self.s[name]); paths.add(Path(self.s[name]['path']))
        for expected in load(HERE/'case_expectations.json').values():
            verify(expected['original_evidence_ref']); paths.add(Path(expected['original_evidence_ref']['path']))
        sdkdirs=set()
        for row in load(self.s['old_build_input_inventory']['path']):
            normalized = row['path'].replace('\\','/').lower()
            if any(x in normalized for x in ['/node_modules/','/third_party/','/adapters/runtime/mu/']):
                verify(row); paths.add(Path(row['path'])); sdkdirs.add(Path(row['path']).parent)
        for directory in sdkdirs:
            paths.update(p for p in directory.iterdir() if p.is_file())
        pythonroot = Path(sys.base_prefix)
        for p in pythonroot.rglob('*'):
            if not p.is_file(): continue
            rel = p.relative_to(pythonroot)
            if any(x.casefold() in {'site-packages','__pycache__','scripts'} for x in rel.parts):continue
            if p.suffix.lower() in {'.py','.pyd','.dll','.exe','.zip'}:paths.add(p)
        paths.update(p for p in (self.go.parent.parent/'pkg/tool').rglob('*') if p.is_file())
        return paths

    def export(self):
        check = self.run('source-delta',[self.git,'diff-tree','--no-commit-id','--name-only','-r',self.s['candidate']],Path(self.s['repo']),60)
        require(sorted((check/'stdout.raw').read_text(encoding='utf-8').splitlines()) == sorted(self.s['source_paths']), 'Candidate delta is not exact2')
        parent = self.run('source-parent',[self.git,'rev-parse',self.s['candidate']+'^'],Path(self.s['repo']),60)
        require((parent/'stdout.raw').read_text().strip()==self.s['base'],'Wrong candidate parent')
        tree = self.run('git-tree',[self.git,'ls-tree','-r','-z','--full-tree',self.s['candidate']],Path(self.s['repo']),60)
        chosen=[]
        for raw in (tree/'stdout.raw').read_bytes().split(b'\0'):
            if not raw:continue
            left,path = raw.split(b'\t',1); mode,kind,oid = left.decode('ascii').split(); path=path.decode('utf-8')
            if path not in self.s['export_exact'] and not any(path.startswith(p) for p in self.s['export_prefixes']):continue
            pp=PurePosixPath(path)
            require(not pp.is_absolute() and '..' not in pp.parts and ':' not in path and '\\' not in path,'Unsafe export path')
            require(kind=='blob' and mode in {'100644','100755'},'Unsupported public export object: '+path)
            chosen.append({'path':path,'oid':oid,'mode':mode})
        require(chosen and len({x['path'].casefold() for x in chosen})==len(chosen),'Empty/colliding export')
        batch=self.phaseout/'git-batch.stdin.raw'; batch.write_bytes(''.join(x['oid']+'\n' for x in chosen).encode('ascii'))
        result=self.run('git-blobs',[self.git,'cat-file','--batch'],Path(self.s['repo']),180,stdin_path=batch)
        self.source.mkdir()
        with (result/'stdout.raw').open('rb') as f:
            for row in chosen:
                header=f.readline().decode('ascii').rstrip('\n').split()
                require(len(header)==3 and header[:2]==[row['oid'],'blob'],'Wrong Git blob header')
                body=f.read(int(header[2])); require(len(body)==int(header[2]) and f.read(1)==b'\n','Incomplete Git blob')
                require(hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==row['oid'],'Git blob integrity mismatch')
                dst=self.source/row['path']; dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(body); row['exported']=ref(dst)
            require(not f.read(1),'Trailing cat-file output')
        save(self.phaseout/'export.json',chosen)
        rows=[]
        for x in load(self.s['protected_functions']['path'])['rows']:
            actual=hashlib.sha256(function_bytes((self.source/x['path']).read_bytes(),x['function'])).hexdigest()
            rows.append(dict(x,actual_sha256=actual)); require(actual==x['sha256'],'Protected function changed '+x['function'])
        save(self.phaseout/'protected-functions.json',rows)

    def prepare(self):
        resources=self.resource_paths(); resource_baseline=vector(resources); self.guarded=resource_baseline; save(self.phaseout/'resources.before.json',resource_baseline)
        self.export()
        fmt=self.run('gofmt-check',[self.go.parent/'gofmt.exe','-l']+[self.source/p for p in self.s['source_paths']],self.source,60)
        require(not (fmt/'stdout.raw').read_bytes().strip(),'Unformatted frozen source; no edit allowed')
        self.run('go-version',[self.go,'version'],self.source,60)
        graph=self.run('go-list',[self.go,'list','-deps','-test','-compiled','-json','./internal/domain'],self.source,600)
        packages=json_stream((graph/'stdout.raw').read_text(encoding='utf-8'))
        paths=set(resources)|{p for p in self.source.rglob('*') if p.is_file()}
        for item in packages:
            require(not item.get('Error') and not item.get('DepsErrors'),'Incomplete actual Go dependency graph')
            if not item.get('Dir'):continue
            d=Path(item['Dir'])
            paths.update(p for p in d.iterdir() if p.is_file() and p.suffix.lower() in {'.go','.s','.h','.c','.cc','.cpp','.syso'})
            for key in ['GoFiles','CgoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles']:
                for rel in item.get(key,[]):
                    p=Path(rel) if Path(rel).is_absolute() else d/rel
                    if not p.is_file() and key=='CompiledGoFiles':
                        require(p.resolve().is_relative_to(self.work.resolve()),'Generated compiler input outside own work/cache')
                        continue
                    require(p.is_file(),'Missing actual graph input '+str(p)); paths.add(p)
            if item.get('Module',{}).get('GoMod'):paths.add(Path(item['Module']['GoMod']))
        # Preserve the original resource cohort across export and dependency discovery.
        check_vector(resource_baseline,self.phaseout/'resources.after-export-and-graph.json')
        self.guarded=vector(paths); save(self.phaseout/'inputs.before-build.json',self.guarded)
        build=self.run('go-compile',[self.go,'test','-c','-work','-x','-o',self.exe,'./internal/domain'],self.source,600)
        self.run('buildinfo',[self.go,'version','-m',self.exe],self.source,60)
        raw=(build/'stderr.raw').read_text(encoding='utf-8'); works=re.findall(r'^WORK=(.+)$',raw,re.M)
        require(len(works)==1,'Expected actual unique WORK path'); work=Path(works[0].strip())
        require(work.resolve().is_relative_to((self.work/'gotmp').resolve()),'WORK escaped own gotmp')
        generated=[]; archives=set(); testmains=[]
        for p in work.rglob('*'):
            if not p.is_file() or not (p.suffix=='.go' or p.name.startswith('importcfg')):continue
            dst=self.phaseout/'compiler-generated'/p.relative_to(work); dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(p.read_bytes())
            generated.append({'original':ref(p),'copy':ref(dst)}); paths.update([p,dst])
            if p.name=='_testmain.go':testmains.append(p.read_text(encoding='utf-8'))
            if p.name.startswith('importcfg'):
                for line in p.read_text(encoding='utf-8').splitlines():
                    if line.startswith('packagefile '):archives.add(Path(line.split('=',1)[1].replace('$WORK',str(work))))
        require(testmains,'No generated testmain')
        for row in self.s['roster']:
            require(row['leaf'].split('/')[0] in '\n'.join(testmains),'Missing planned symbol')
        actual_WORK={p for p in work.rglob('*') if p.is_file()}
        save(self.phaseout/'actual_WORK.allfiles.json',vector(actual_WORK))
        paths.update(actual_WORK)
        save(self.phaseout/'generated.json',generated);save(self.phaseout/'archives.json',vector(archives))
        check_vector(resource_baseline,self.phaseout/'resources.after-build.json')
        check_vector(self.guarded,self.phaseout/'inputs.after-build.json')
        paths.update(archives);paths.add(self.exe);self.guarded=vector(paths)
        late_runtime=self.runtime_paths('python-os-runtime.after')
        require(late_runtime.issubset(paths),'New unbound Python/OS runtime input after prepare')
        save(self.out/'prepared.json',{'status':'COMPILED_NOT_EXECUTED','spec':ref(HERE/'execution_spec.json'),'runner':ref(Path(__file__)),
             'actual_WORK':str(work),'exe':ref(self.exe),'inputs':self.guarded,'generated_count':len(generated),'archive_count':len(archives),'source_commit':self.s['candidate']})

    def snapshot_audit(self, case):
        reports=[]
        for p in sorted(case.rglob('*.sqlite')):
            require(not Path(str(p)+'-wal').exists(),'Snapshot has WAL; not a closed immutable image')
            before=ref(p); uri=p.resolve().as_uri()+'?mode=ro&immutable=1'
            db=sqlite3.connect(uri,uri=True)
            try:
                db.execute('PRAGMA query_only=ON')
                integrity=db.execute('PRAGMA integrity_check').fetchall(); require(integrity==[('ok',)],'Snapshot integrity failure')
                schema=db.execute('SELECT type,name,tbl_name,rootpage,sql FROM sqlite_schema ORDER BY type,name').fetchall()
                tables={}
                for name, in db.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name"):
                    q='"'+name.replace('"','""')+'"'; cols=db.execute('PRAGMA table_info('+q+')').fetchall()
                    names=[x[1] for x in cols]; projection=','.join('typeof("'+c.replace('"','""')+'")' for c in names)
                    data=[]
                    for row in db.execute('SELECT *, '+projection+' FROM '+q):
                        values=row[:len(names)]; storage=row[len(names):]
                        data.append([{'type':t,'value':v.hex() if isinstance(v,bytes) else v} for v,t in zip(values,storage)])
                    data.sort(key=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=True))
                    tables[name]={'columns':cols,'rows_multiset':data}
                reports.append({'snapshot':before,'method':'author fixture VACUUM INTO','source_original_file_retained':False,'integrity':integrity,'schema':schema,'tables':tables,'implicit_rowid_checked':False})
            finally:db.close()
            require(ref(p)==before,'Read-only snapshot bytes changed')
        save(case/'snapshot-audit.json',reports)
        return len(reports)

    def execute(self):
        require(load(self.out/'prepare/completed.json')['status']=='COMPLETED_NOT_ACCEPTED','Prepare phase did not complete')
        require(self.grant.get('prepared_sha256')==digest(self.out/'prepared.json'),'Execute grant must bind actual prepared bytes')
        prep=load(self.out/'prepared.json'); verify(prep['spec']);verify(prep['runner']);verify(prep['exe'])
        # The execute grant may be a new Root scope/controller, outside the prepared directory.
        # Freeze its actual files and this phase's real Python .py/.pyc/DLL inputs as well.
        phase_resources=self.resource_paths()
        self.guarded=vector({Path(x['path']) for x in prep['inputs']}|phase_resources|{self.out/'prepared.json'})
        for expected in prep['inputs']: verify(expected)
        check_vector(self.guarded,self.phaseout/'inputs.before-first.json')
        save(self.phaseout/'uri-conversion.json', {'work_file_uri':self.work.resolve().as_uri(), 'source_file_uri':self.source.resolve().as_uri(),
             'snapshot_rule':'Resolved absolute path.as_uri() + ?mode=ro&immutable=1; no handwritten file URI'})
        critical={self.exe,self.bundle}|{self.source/p for p in self.s['source_paths']}|self.controller_paths
        baseline={os.path.normcase(str(Path(x['path']).absolute())):x for x in self.guarded}
        critical_baseline=[baseline[os.path.normcase(str(p.absolute()))] for p in sorted(critical,key=str)]
        expectations=load(HERE/'case_expectations.json'); total=0; snapshots=0
        for i,row in enumerate(self.s['roster']):
            if i==18:check_vector(self.guarded,self.phaseout/'component-after-native-before.json')
            case=self.phaseout/('%02d-'%i+row['leaf'].replace('/','_'));case.mkdir(); evidence=case/'evidence';evidence.mkdir()
            env=dict(self.env,RESEARCHOS_PROVIDER_EVIDENCE_DIR=str(evidence))
            check_vector(critical_baseline,case/'critical.before.json')
            check_vector(self.guarded,case/'all-inputs.before.json')
            proc=self.run('case-%02d'%i,[self.exe,'-test.v','-test.count=1','-test.timeout=150s','-test.failfast','-test.run='+row['selector']],self.source/'internal/domain',180,env=env)
            raw=(proc/'stdout.raw').read_text(encoding='utf-8',errors='strict')
            passes=re.findall(r'^\s*--- PASS: (\S+)',raw,re.M)
            require([x for x in passes if '/' in x]==[row['leaf']],'Wrong exact PASS leaf')
            require(not re.search(r'^\s*--- (FAIL|SKIP):',raw,re.M),'Failure/skip event')
            counts=list(evidence.rglob('provider-http-counts.json')); calls=len(list(evidence.rglob('http-*.json')))
            require(calls==row['MODEL_calls'],'Unexpected MODEL count');total+=calls;require(total<=4,'MODEL bound exceeded')
            for p in counts:
                c=load(p);require(c['model_requests']==calls and c['external_paid_requests']==0,'Provider counter mismatch')
            if i>=18:
                facts=list(evidence.rglob('native-stages-and-fault.json'));require(len(facts)==1,'Missing native facts')
                fact=load(facts[0]); expected=expectations[str(i)]
                require({k:fact['actual_fault'][k] for k in ['Status','Code','Message']}==expected['fault'],'Wrong native Fault cause')
                require(fact['stage_counts']==expected['stage_counts'],'Wrong native stages')
                require(len(list(evidence.rglob('original-dispatch.json')))==1,'Missing original dispatch')
                if i>=25:require(len(list(evidence.rglob('original-model-cause.json')))==1,'Missing original MODEL UNKNOWN chain')
            if i in (8,9):
                before=list(evidence.rglob('rows-before.json'));after=list(evidence.rglob('rows-after.json'))
                require(len(before)==len(after)==1 and load(before[0])==load(after[0]),'Rollback row multiset changed')
                require(len(list(evidence.rglob('before-task-budget.json')))==1,'Missing pre-Task Goal budget proof')
            check_vector(self.guarded,case/'all-inputs.after-native.json')
            snapshots+=self.snapshot_audit(case)
            check_vector(self.guarded,case/'all-inputs.after-fixtures.json')
            check_vector(critical_baseline,case/'critical.after.json')
            case_runtime=self.runtime_paths('python-os-runtime.case-%02d-after'%i)
            require({os.path.normcase(str(p.absolute())) for p in case_runtime}.issubset(baseline),'New unbound Python/OS runtime input in case')
            result={'index':i,'selector':row['selector'],'status':'PASS_LOCAL_FIXTURE_NOT_ACCEPTED','process':ref(proc/'invocation.json'), 'MODEL':calls,
                'evidence':[ref(p) for p in evidence.rglob('*') if p.is_file()],'snapshot_audit':ref(case/'snapshot-audit.json')}
            save(case/'result.json',result);self.results.append(result)
        require(total==4 and snapshots==13,'Final MODEL/snapshot counts differ')
        late_runtime=self.runtime_paths('python-os-runtime.after')
        require({os.path.normcase(str(p.absolute())) for p in late_runtime}.issubset(baseline),'New unbound Python/OS runtime input after cases')
        check_vector(self.guarded,self.phaseout/'inputs.after-all.json')
        save(self.phaseout/'result.json',{'status':'FINITE29_EXECUTION_REPORTED_NOT_ACCEPTED','results':self.results,'MODEL_loopback':total,'snapshots':snapshots,'bootstrap_HTTP':'UNKNOWN_NOT_INSTRUMENTED','source_ready':False})

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['prepare','execute'],required=True);ap.add_argument('--authorization',required=True);ap.add_argument('--authorization-sha256',required=True);args=ap.parse_args()
    require(sys.flags.optimize==0,'Optimized Python unsupported')
    spec=load(HERE/'execution_spec.json');grantpath=Path(args.authorization).resolve();require(digest(grantpath)==args.authorization_sha256,'Grant hash differs')
    grant=load(grantpath)
    require(grant['status']=='ROOT_REGISTERED_EXECUTION_AUTHORIZED' and grant['actual_registration_completed'] is True,'No completed Root authorization')
    require(grant['executor'] in {'codex:/root','codex:/root/w05_merge_review'},'Executor identity not registered nonauthor')
    require(grant['candidate']==spec['candidate'] and grant['spec_sha256']==digest(HERE/'execution_spec.json') and grant['runner_sha256']==digest(Path(__file__)),'Grant inputs differ')
    require(grant['output_root']==spec['output_root'] and grant['work_root']==spec['work_root'] and grant['roster']==[x['selector'] for x in spec['roster']],'Grant layout/finite roster differs')
    require(args.phase in grant['phases'],'Phase not granted');grant['_path']=str(grantpath)
    for group in ['scope_refs','controller_refs']:
        require(isinstance(grant.get(group),list) and len(grant[group])>0,'Missing actual Root '+group)
        for item in grant[group]:
            require(isinstance(item,dict) and isinstance(item.get('path'),str),'Malformed Root reference')
            verify(item)
    for row in load(HERE/'preparation_manifest.json')['entries']:verify(row)
    verify(spec['helper']);verify(spec['bundle']);verify(spec['git'])
    for tool in spec['tools'].values():verify(tool)
    require(Path(sys.executable).resolve()==Path(spec['tools']['python']['path']).resolve(),'Wrong Python executable')
    out=Path(spec['output_root']);work=Path(spec['work_root'])
    require(out.is_absolute() and work.is_absolute() and not out.is_relative_to(Path(spec['author_worktree'])) and not work.is_relative_to(Path(spec['author_worktree'])),'Output aliases author tree')
    if args.phase=='prepare':
        require(not out.exists() and not work.exists(),'Output/work already exists: no retry')
        out.mkdir(parents=True);work.mkdir(parents=True)
        for d in ['cache','gotmp','temp']:(work/d).mkdir()
    else:require((out/'prepared.json').is_file(),'No prepared candidate')
    phaseout=out/args.phase;phaseout.mkdir() # existing phase refuses before entering failure-write region
    save(phaseout/'started.json',{'at':now(),'authorization':ref(grantpath),'phase':args.phase})
    runner=None
    try:
        module=types.ModuleType('frozen_windows_owned_process');module.__file__=spec['helper']['path']
        exec(compile(Path(spec['helper']['path']).read_bytes(),spec['helper']['path'],'exec'),module.__dict__)
        runner=Replay(spec,grant,args.phase,module)
        if args.phase=='prepare':runner.prepare()
        else:runner.execute()
        save(phaseout/'completed.json',{'at':now(),'status':'COMPLETED_NOT_ACCEPTED'})
        return 0
    except BaseException as exc:
        save(phaseout/'failure.json',{'at':now(),'error':repr(exc),'traceback':traceback.format_exc(),'phase':args.phase,'product_actual_exit':'See original process invocation; not inferred from harness exit','not_run':[x for x in spec['roster'] if runner is None or x['index'] not in [r['index'] for r in runner.results]],'retry':False})
        if runner is not None and runner.guarded:
            try:check_vector(runner.guarded,phaseout/'inputs.after-failure.json')
            except BaseException as checkerr:save(phaseout/'post-failure-check-error.json',{'actual_error':repr(checkerr)})
        save(phaseout/'available-public-files.json',[ref(p) for p in phaseout.rglob('*') if p.is_file()])
        return 1

if __name__=='__main__':
    raise SystemExit(main())
