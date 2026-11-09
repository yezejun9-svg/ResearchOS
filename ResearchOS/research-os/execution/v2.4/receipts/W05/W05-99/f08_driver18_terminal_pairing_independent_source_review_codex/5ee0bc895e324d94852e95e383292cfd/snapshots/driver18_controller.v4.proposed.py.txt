"""PREPARATION ONLY. Future Root: -I -S -X utf8 THIS phase scope sha grant sha.
No authorization is implemented here: a separately reviewed Root gate is required.
No proposed/fixture module is loaded during static preparation.
"""
import ast
import hashlib
import json
import os
import re
import sys
import time
import traceback
import types
from pathlib import Path

ROOT=Path('D:/作品集/ResearchOS/research-os')
IDS=[f'I{i:02d}' for i in range(1,19)]
CAPS={'native_calls':32,'compiler_seconds':600,'test_seconds':750,
      'inner_seconds':3300,'outer_seconds':3600,'cleanup_seconds':5,
      'images':64,'compiler_processes':2048,'job_active_processes':16,
      'fixture_HTTP':0,'SDK_Node_model_external_paid':0}
class PreparedComplete(Exception):
    """Internal phase completion; still passes through evidence finalization."""
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def strict(raw):
    def pairs(rows):
        d={}
        for k,v in rows:
            need(k not in d,'DUPLICATE_KEY');d[k]=v
        return d
    return json.loads(raw.decode('utf8'),object_pairs_hook=pairs,
                      parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
def verify(ref):
    need(isinstance(ref,dict) and set(ref)=={'path','sha256','bytes'},'EXACT_REF_REQUIRED')
    p=Path(ref['path']);need(p.is_absolute() and p.resolve()==p,'NONCANONICAL_INPUT_PATH')
    for q in [p,*p.parents]:
        if q.exists():need(not q.is_symlink() and not getattr(q.lstat(),'st_file_attributes',0)&0x400,'REPARSE_INPUT')
    raw=p.read_bytes();need(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'INPUT_PIN')
    return raw
def doc(ref):return strict(verify(ref))
def pin(p):
    p=Path(p).absolute();raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(p,v):
    with Path(p).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def module(ref,name):
    raw=verify(ref);m=types.ModuleType(name);m.__file__=ref['path'];sys.modules[name]=m
    exec(compile(raw,ref['path'],'exec'),m.__dict__);return m
def rel(text):
    p=Path(text);need(not p.is_absolute() and '..' not in p.parts and str(p) not in ('','.'),'RELATIVE_PATH')
    return p
def copy_one(ref,dst):
    raw=verify(ref);dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open('xb') as f:f.write(raw)
    need(pin(dst)['sha256']==ref['sha256'],'COPY_PIN')
def no_sidecars(p):
    need(p.is_file(),'I16_DB_MISSING')
    need(not any(os.path.lexists(str(p)+x) for x in ('-wal','-shm','-journal')),'I16_SIDECAR_PRESENT')
def main():
    need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,'USE_I_S_UTF8')
    sys.dont_write_bytecode=True
    need(len(sys.argv)==6,'phase scope scopeSHA grant grantSHA')
    phase,sp,sh,gp,gh=sys.argv[1:];need(phase in ('prepare','execute'),'PHASE')
    raw=Path(sp).read_bytes();need(hashlib.sha256(raw).hexdigest()==sh,'SCOPE_SHA');s=strict(raw)
    need(s['preparation_only'] is False and s['caps']==CAPS,'UNBOUND_PREPARATION_OR_CAPS')
    need(s['authority_validator_ref'] is not None,'OPEN_ACTUAL_ROOT_AUTHORITY_VALIDATOR')
    gate=module(s['authority_validator_ref'],'driver18_root_authority')
    authority=gate.validate_grant(sp,sh,gp,gh)
    need(authority['scope']==s and authority['phase']==phase and authority['actor']=='codex:/root','ROOT_PHASE_AUTHORITY')
    # Gate must authenticate actual sealed CAS/review/canonical copies before any helper/native call.
    refs=authority['authorization_input_refs']
    need(refs and authority['actual_registration_completed'] is True,'SEALED_ROOT_REGISTRATION_REQUIRED')
    for r in refs:verify(r)
    u=module(s['utility_ref'],'driver18_fixed_utilities')
    out=None;work=None;ledger=None;normal=None;first=None;secondary=[];stage='CREATE_OWN_OUTPUT'
    roster=[{'id':i,'status':'NOT_STARTED','actual_exit':None,'qualified':False} for i in IDS]
    active=None;last=None;calls=0;started=time.monotonic();inner_deadline=started+CAPS['inner_seconds']
    try:
        out=u.safe(s[phase+'_output_root'],ROOT/'execution/v2.4/receipts/W05/W05-99',True)
        out.mkdir();save(out/'authority.json',authority)
        b=doc(s['fixed_inputs_ref']);res=doc(s['resource_catalog_ref'])
        allowed=res['files']+[s[k] for k in ('controller_ref','launcher_ref','authority_validator_ref','utility_ref','owned_helper_ref','debug_helper_ref')]
        for r in allowed:verify(r)
        need(pin(sys.executable)==res['python'],'ACTUAL_PYTHON_PIN')
        normal=module(s['owned_helper_ref'],'driver18_owned_helper')
        debug=module(s['debug_helper_ref'],'driver18_debug_helper')
        ledger=u.Ledger(out);ledger.add('authority-resources-controls',[r['path'] for r in refs+allowed]+[sp,gp,s['fixed_inputs_ref']['path'],s['resource_catalog_ref']['path']])
        fixed_refs=[v for v in b.values() if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}]
        for r in fixed_refs:verify(r)
        ledger.add('fixed-source-contracts-locks-and-tests',[r['path'] for r in fixed_refs])
        ledger.check('initial');save(out/'python-os.before.json',u.module_observation(allowed,normal))
        if phase=='prepare':
            work=u.safe(s['work_root'],ROOT/'.local',True);work.mkdir()
            for d in ('fork','consumer/cmd/i16fixture','old-probe','modcache','build','data'):(work/d).mkdir(parents=True,exist_ok=True)
            lock=doc(b['fork_lock_ref']);old=doc(b['original_lock_ref'])
            need(len(lock['files'])==len(old['files'])==1899,'FULL_MODULE_MEMBERSHIP')
            ledger.add('original-and-fork-full-source-prefix',[r['path'] for r in lock['files']+old['files']])
            for label,rows,destination in [('fork',lock['files'],work/'fork'),('original',old['files'],work/'modcache/modernc.org/sqlite@v1.60.1')]:
                seen=set()
                for row in rows:
                    rp=rel(row['relative_path']);need(str(rp).casefold() not in seen,'MODULE_DUPLICATE')
                    seen.add(str(rp).casefold());copy_one({k:row[k] for k in ('path','sha256','bytes')},destination/rp)
                need(len(u.files(destination))==1899,'MODULE_COPY_MEMBERSHIP')
            # Root supplies a finite offline dependency/cache-metadata set; cannot overwrite pristine sqlite.
            for row in res['offline_modcache_copies']:
                need(row['ref'] in res['files'],'OFFLINE_DEPENDENCY_NOT_IN_PRE_PINNED_CATALOG')
                dst=work/'modcache'/rel(row['relative_path'])
                copy_one(row['ref'],dst)
            # Re-inventory the actual pristine module AFTER all offline copies.
            pristine=work/'modcache/modernc.org/sqlite@v1.60.1'
            expected_pristine={str(rel(row['relative_path'])).casefold():row for row in old['files']}
            actual_pristine={}
            for p in u.files(pristine):
                rp=str(p.relative_to(pristine)).casefold()
                need(rp not in actual_pristine,'PRISTINE_POST_COPY_DUPLICATE')
                actual_pristine[rp]=pin(p)
            need(len(expected_pristine)==1899 and set(actual_pristine)==set(expected_pristine),'PRISTINE_POST_COPY_MEMBERSHIP')
            for rp,row in expected_pristine.items():
                actual=actual_pristine[rp]
                need(actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'],'PRISTINE_POST_COPY_BYTES')
                verify(actual)
            mappings=[('test_source_ref','fork/driver18_innocuous_test.go'),('surface_ref','consumer/surface.go'),
                      ('producer_ref','consumer/cmd/i16fixture/main.go'),('probe_ref','old-probe/main.go'),
                      ('consumer_mod_ref','consumer/go.mod'),('sum_ref','consumer/go.sum'),
                      ('old_mod_ref','old-probe/go.mod'),('sum_ref','old-probe/go.sum')]
            for key,dst in mappings:copy_one(b[key],work/dst)
            need(pin(work/'fork/func_test.go')['sha256']==b['original_regression_ref']['sha256'],'ORIGINAL_I18_BODY_PIN')
            need(b'replace modernc.org/sqlite v1.60.1 => ../fork' in (work/'consumer/go.mod').read_bytes(),'QUALIFIED_FORK_REPLACE')
            need(b'replace ' not in (work/'old-probe/go.mod').read_bytes(),'OLD_PROBE_MUST_NOT_REPLACE')
            source=[pin(p) for p in u.files(work)]
            ledger.add('fresh-isolated-source-and-offline-dependencies',[r['path'] for r in source]);ledger.check('prepared')
            save(out/'prepared.json',{'work_root':str(work),'files':source,'fixed_inputs_ref':s['fixed_inputs_ref'],
                 'resource_catalog_ref':s['resource_catalog_ref'],'root_preparation_grant_ref':pin(gp),
                 'source_overlays':mappings,'actual_Go_calls':0,'I17':'FATAL_OPEN','all18':'NOT_RUN'})
            raise PreparedComplete()
        prepared=doc(s['prepared_ref']);work=Path(prepared['work_root'])
        need(str(work)==s['work_root'] and prepared['fixed_inputs_ref']==s['fixed_inputs_ref'] and prepared['resource_catalog_ref']==s['resource_catalog_ref'],'PREPARED_BINDING')
        for r in prepared['files']:verify(r)
        ledger.add('prepared-source',[r['path'] for r in prepared['files']]+[s['prepared_ref']['path']])
        need(s['mode']=='PARTIAL_17_EXPLICIT' and s['ordered_cases']==[i for i in IDS if i!='I17'],
             'I17_FATAL_OPEN_NO_ACTUAL_CALLBACKS: only separately reviewed explicit partial17 scope is currently executable')
        roster[16]['status']='OPEN_NOT_AUTHORIZED';mode_cases=s['ordered_cases']
        build=work/'build';need(not u.files(build),'FRESH_BUILD_REQUIRED')
        for name in ('cache','tmp','gotmp','bin'):(build/name).mkdir()
        go=res['go']['path'];verify(res['go']);images=res['compiler_images']
        need(images and len(images)<=61,'FINITE_COMPILER_IMAGES_WITH_THREE_NEW_EXES')
        for r in images:verify(r)
        env=dict(s['public_environment']);need(set(env)<=set(['SystemRoot','WINDIR','ComSpec','PATH','PATHEXT']),'PUBLIC_ENV_ONLY')
        env.update({'GOTOOLCHAIN':'local','GOENV':'off','GOWORK':'off','GOPROXY':'off','GOSUMDB':'off','GOFLAGS':'',
                    'GOOS':'windows','GOARCH':'amd64','GOAMD64':'v1','CGO_ENABLED':'0','GOEXPERIMENT':'','GODEBUG':'',
                    'GOROOT':res['GOROOT'],'GOPATH':str(work/'gopath'),'GOMODCACHE':str(work/'modcache'),
                    'GOCACHE':str(build/'cache'),'GOTMPDIR':str(build/'gotmp'),'TEMP':str(build/'tmp'),'TMP':str(build/'tmp')})
        def run(label,argv,cwd,seconds,extra=None):
            nonlocal stage,calls,last
            stage=label;remaining_seconds=inner_deadline-time.monotonic()
            need(remaining_seconds>CAPS['cleanup_seconds'] and calls<32,'FINITE_DEADLINE_OR_CALLCAP')
            effective_seconds=min(seconds,remaining_seconds-CAPS['cleanup_seconds'])
            calls+=1;ee=dict(env);ee.update(extra or {})
            if active is not None:active['status']='STARTED'
            save(out/(label+'.request.json'),{'argv':argv,'cwd':str(cwd),'env':ee,'timeout':effective_seconds,'requested_timeout':seconds,'effective_timeout':effective_seconds,
                'remaining_inner_seconds':remaining_seconds,'cleanup_reserve_seconds':CAPS['cleanup_seconds'],'call':calls})
            error=None;result=None
            try:
                with (out/(label+'.stdout.raw')).open('xb') as so,(out/(label+'.stderr.raw')).open('xb') as se:
                    result=debug.run_owned(argv,str(cwd),ee,so,se,effective_seconds,
                        {k:pin(argv[0])[k] for k in ('sha256','bytes')},images,list(ledger.members.values()),2048)
                last=result
                if active is not None:active.update(status='NATIVE_EXIT_OBSERVED',actual_exit=result.get('actual_exit'))
                u.job_ok(result,True)
            except BaseException as e:error=e
            finally:
                save(out/(label+'.invocation.json'),{'result':result,'error':repr(error) if error else None})
                try:ledger.check(label+'-native-after');save(out/(label+'.python-os.after.json'),u.module_observation(allowed,normal))
                except BaseException as e:
                    if error is None:error=e
                    else:secondary.append({'stage':label+'-closure','error':repr(e)})
            if error:raise error
            return (out/(label+'.stdout.raw')).read_bytes()
        run('go-version',[go,'version'],work,600)
        fields=['GoFiles','CgoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','IgnoredGoFiles','IgnoredOtherFiles',
                'CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles']
        for label,cwd,pattern,expect in [('fork',work/'fork','.',work/'fork'),('consumer',work/'consumer','./...',work/'fork'),('old',work/'old-probe','.',work/'modcache/modernc.org/sqlite@v1.60.1')]:
            raw=run('graph-'+label,[go,'list','-buildvcs=false','-mod=readonly','-compiled','-deps','-test','-json','-work','-x',pattern],cwd,600)
            text=raw.decode('utf8');decoder=json.JSONDecoder();idx=0;pkgs=[];actual=[]
            while idx<len(text):
                if text[idx].isspace():idx+=1;continue
                v,idx=decoder.raw_decode(text,idx);pkgs.append(v)
            need(pkgs and not any(p.get('Error') or p.get('DepsErrors') for p in pkgs),'GRAPH_ERROR')
            chosen=[p for p in pkgs if p.get('ImportPath')=='modernc.org/sqlite']
            need(len(chosen)==1 and Path(chosen[0]['Dir']).resolve()==expect.resolve(),'ACTUAL_DRIVER_DIR')
            selected=chosen[0].get('Module',{})
            if label=='old':need(selected.get('Version')=='v1.60.1' and not selected.get('Replace'),'OLD_DRIVER_REPLACED')
            if label=='consumer':need(selected.get('Version')=='v1.60.1' and Path(selected['Replace']['Dir']).resolve()==(work/'fork').resolve(),'FORK_REPLACE_SELECTION')
            for p in pkgs:
                for field in fields:
                    for name in p.get(field,[]):
                        q=(Path(name) if Path(name).is_absolute() else Path(p['Dir'])/name).absolute()
                        need(q.is_file() and (str(q) in ledger.members or q.is_relative_to(build)),'UNCATALOGUED_GRAPH_INPUT '+str(q));actual.append(q)
                for m in [p.get('Module') or {},(p.get('Module') or {}).get('Replace') or {}]:
                    if m.get('GoMod'):
                        q=Path(m['GoMod']).absolute();need(str(q) in ledger.members,'UNCATALOGUED_MOD');actual.append(q)
            save(out/('graph-'+label+'.json'),{'packages':pkgs,'actual_source_inputs':[pin(p) for p in sorted(set(actual))]})
        test=build/'bin/driver18.test.exe';producer=build/'bin/i16-producer.exe';oldexe=build/'bin/i16-old.exe';surface=build/'bin/consumer.a'
        for label,cwd,args in [('fork-test',work/'fork',['test','-c','-o',str(test),'.']),
            ('consumer-surface',work/'consumer',['build','-o',str(surface),'.']),
            ('i16-producer',work/'consumer',['build','-o',str(producer),'./cmd/i16fixture']),
            ('i16-old',work/'old-probe',['build','-o',str(oldexe),'.'])]:
            run('build-'+label,[go,args[0],'-p=1','-mod=readonly','-buildvcs=false','-work','-x',*args[1:]],cwd,600)
        artifacts=u.files(build);archives=[]
        for p in artifacts:
            if p.name in ('importcfg','importcfg.link'):
                for line in p.read_text(encoding='utf8',errors='strict').splitlines():
                    if line.startswith('packagefile '):
                        q=Path(line.split('=',1)[1]).absolute();need(q.is_file() and (q.is_relative_to(build) or str(q) in ledger.members),'ARCHIVE_BOUNDARY');archives.append(q)
        need(archives and any(p.name=='_testmain.go' for p in artifacts),'COMPILED_CLOSURE_MISSING')
        ledger.add('actual-WORK-cache-archives-and-executables',artifacts+archives)
        save(out/'compiled-closure.json',{'all_BUILD':[pin(p) for p in artifacts],'archives':[pin(p) for p in sorted(set(archives))],
             'testexe':pin(test),'producer':pin(producer),'oldexe':pin(oldexe),'surface_archive':pin(surface)})
        images=images+[pin(test),pin(producer),pin(oldexe)]
        for label,exe in [('test',test),('producer',producer),('old',oldexe)]:run('buildinfo-'+label,[go,'version','-m',str(exe)],work,600)
        ledger.check('before-first-case')
        for ident in mode_cases:
            active=roster[IDS.index(ident)];extra={}
            ledger.check(ident+'-before')
            if ident=='I16':
                case=work/'data/I16';case.mkdir();db=case/'fixture.sqlite';report=case/'old-result.json'
                setup=strict(run('I16-produce',[str(producer),str(db)],work,750))
                need(setup=={'schema':'researchos.driver18.fixture-prepared.v1','database':str(db),'closed':True,'phase_only_not_case_pass':True},'I16_PRODUCER_REPORT')
                no_sidecars(db);before=pin(db);copy_one(before,case/'before-old.closed-copy.sqlite')
                raw=run('I16-old-probe',[str(oldexe),str(db),str(report)],work,750)
                need(strict(raw)==strict(report.read_bytes()),'I16_REPORT_NOT_ACTUAL_STDOUT')
                no_sidecars(db);after=pin(db);need(before==after,'I16_OLD_PHASE_DB_BYTES_CHANGED')
                copy_one(after,case/'after-old.closed-copy.sqlite')
                save(out/'I16-preconditions.json',{'before':before,'after':after,'bytes_equal':True,
                     'schema_rows_unchanged_by_identical_closed_bytes':True,'separate_SQL_full_inventory_executed':False,
                     'old_report':pin(report),'producer':pin(producer),'oldexe':pin(oldexe),'phase_only_not_case_pass':True})
                ledger.add('I16-old-result-and-immutable-closed-copies',[report,case/'before-old.closed-copy.sqlite',case/'after-old.closed-copy.sqlite'])
                extra={'DRIVER18_I16_DB':str(db),'DRIVER18_I16_OLD_RESULT':str(report)}
            raw=run('case-'+ident,[str(test),'-test.v','-test.count=1','-test.failfast','-test.timeout=750s','-test.run','^TestDriver'+ident+'$'],work/'fork',750,extra)
            text=raw.decode('utf8',errors='strict')
            need(re.search(r'^--- PASS: TestDriver'+ident+r' \(',text,re.M) and re.search(r'^PASS\r?$',text,re.M)
                 and not re.search(r'^\s*--- (FAIL|SKIP):',text,re.M),'CASE_NOT_QUALIFIED')
            if ident=='I16':
                no_sidecars(db);copy_one(pin(db),case/'after-fork.closed-copy.sqlite')
                save(out/'I16-third-stage.json',{'closed_db':pin(db),'test_assertions':'Original x=7, count=1, real insert9, count=2','actual_native_exit':active['actual_exit']})
            ledger.check(ident+'-fixture-after');need(time.monotonic()<inner_deadline,'INNER_DEADLINE_EXPIRED');active.update(status='QUALIFIED',qualified=True);save(out/(ident+'.result.json'),active);active=None
        need(calls==30,'PARTIAL17_COMPLETE_NATIVE_ROSTER')
        ledger.check('final');need(time.monotonic()<inner_deadline,'INNER_DEADLINE_EXPIRED');save(out/'qualified-partial17.json',{'partial17':True,'I17':'OPEN_NOT_AUTHORIZED','all18_pass':False,'source_acceptance':False})
    except PreparedComplete:
        pass
    except BaseException as e:
        first={'stage':stage,'error':repr(e),'traceback':traceback.format_exc(),'actual_stage_native_exit':None,'last_child_result':last,'retry':False}
        if active is not None:active['status']='STARTED_UNQUALIFIED';active['failure']=first
        if out is None:sys.stderr.write(json.dumps(first,ensure_ascii=False)+'\n')
    finally:
        if out is not None:
            for label,fn in [('input-final',lambda:ledger.check('after-finally') if ledger else None),
                             ('runtime-final',lambda:save(out/'python-os.after.json',u.module_observation(allowed,normal)) if normal else None),
                             ('artifacts-final',lambda:save(out/'artifacts.final.json',{'files':[pin(p) for p in u.files(work/'build')]} ) if work and (work/'build').exists() else None)]:
                try:fn()
                except BaseException as e:secondary.append({'stage':label,'error':repr(e)})
            if time.monotonic()>=inner_deadline:secondary.append({'stage':'EVIDENCE_FINALIZATION','error':'INNER_DEADLINE_EXPIRED','actual_stage_native_exit':None})
            if first is None and secondary:first={'stage':'EVIDENCE_FINALIZATION','error':secondary[0],'actual_stage_native_exit':None}
            try:
                if first:save(out/'failure.origin.json',first)
                save(out/'result.json',{'phase':phase,'first_cause':first,'secondary':secondary,'roster':roster,'native_calls':calls,'all18_pass':False,'source_acceptance':False,'counter_reset':False})
                save(out/'manifest.json',{'files':[pin(p) for p in u.files(out)],'excluded_only_self':True})
            except BaseException as e:
                sys.stderr.write(json.dumps({'first_cause':first,'finalize_error':repr(e),'native_exit':None})+'\n');first=first or {'error':repr(e)}
    if time.monotonic()>=inner_deadline:
        sys.stderr.write(json.dumps({'stage':'FINAL_RETURN','error':'INNER_DEADLINE_EXPIRED','first_cause':first,'actual_native_exit':None,'outer_raw_authority':True})+'\n')
        return 1
    return 1 if first else 0
if __name__=='__main__':
    try:exit_code=main()
    except BaseException as e:
        sys.stderr.write(json.dumps({'stage':'ENTRY','error':repr(e),'traceback':traceback.format_exc(),'actual_native_exit':None,'outer_raw_authority':True})+'\n');exit_code=1
    sys.exit(exit_code)
