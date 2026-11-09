"""PREPARATION ONLY. No authority module/resource/scope/grant is presently bound.

Future interface: Python -I -S -X utf8 THIS scope scopeSHA grant grantSHA.
The separate Root authority verifier is a mandatory reviewed input, not actor-text trust.
"""
import hashlib,json,os,re,sys,time,traceback,types
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
SOURCE='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def strict(raw):
    def pairs(rows):
        result={}
        for k,v in rows:
            need(k not in result,'Duplicate JSON key');result[k]=v
        return result
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verify(r):
    need(isinstance(r,dict) and set(r)=={'path','sha256','bytes'},'Exact ref required')
    p=Path(r['path']);need(p.is_absolute() and str(p.resolve())==str(p),'Canonical absolute ref')
    b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes'],'Pin mismatch '+str(p));return b
def module(r,name):
    raw=verify(r);m=types.ModuleType(name);m.__file__=r['path'];sys.modules[name]=m
    exec(compile(raw,r['path'],'exec'),m.__dict__);return m
def save(p,value):
    with Path(p).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
def safe(p,base,absent=False):
    p=Path(p);base=Path(base)
    need(p.is_absolute() and p!=base and p.is_relative_to(base) and '..' not in p.parts,'Output outside own root')
    need(str(p.resolve(strict=False))==str(p),'Output alias')
    cur=p
    while cur!=cur.parent:
        if os.path.lexists(cur):need(not cur.is_symlink() and not(getattr(os.lstat(cur),'st_file_attributes',0)&0x400),'Reparse ancestor')
        cur=cur.parent
    if absent:need(not os.path.lexists(p),'Output already exists')
    return p
def inventory(base,junction=None,target=None):
    result=[]
    for root,dirs,files in os.walk(base,followlinks=False):
        for n in list(dirs):
            p=Path(root)/n
            if p.is_symlink() or getattr(os.lstat(p),'st_file_attributes',0)&0x400:
                need(junction is not None and p==junction and p.resolve()==target,'Unexpected artifact reparse')
                dirs.remove(n)
        for n in files:
            p=Path(root)/n;need(not p.is_symlink() and not(getattr(os.lstat(p),'st_file_attributes',0)&0x400),'Artifact file alias');result.append(p)
    return sorted(result)
def main():
    need(sys.flags.isolated and sys.flags.no_site and len(sys.argv)==5,'Pinned isolated Python/explicit scope and grant')
    sys.dont_write_bytecode=True
    sp=Path(sys.argv[1]);raw=sp.read_bytes();need(hashlib.sha256(raw).hexdigest()==sys.argv[2],'Scope SHA')
    scope=strict(raw)
    need(scope.get('preparation_only') is False and scope.get('execution_authorized') is True,'PREPARATION_ONLY')
    # The future Root verifier must implement actual CAS4/manifest/review/lease/grant semantics.
    # It is deliberately unbound in this preparation: no generic authorized:true fallback.
    gate=module(scope['authorization_verifier_ref'],'desktop58_root_authority')
    authorized=gate.validate_grant(*sys.argv[1:])
    need(authorized['scope']==scope and authorized['source_commit']==SOURCE and
         authorized['fresh_current58_CLI2_qualified'] is True and authorized['original_CLI2_case_count']==2,
         'Actual same-head fresh CLI2 prerequisite missing')
    need(authorized['registered_Root_scope_and_grant_verified'] is True and authorized['authorization_input_refs'], 'Root authority chain missing')
    need(scope['source_commit']==SOURCE and scope['node_cases']==169 and scope['Go_top_cases']==3 and
         scope['loopback_HTTP_max']==390 and scope['offscreen_Electron_controls']==2 and
         scope['installed_visible_GUI_calls']==0 and scope['SDK_model_external_paid_calls']==0,'Finite scope')
    need(scope['first_unexpected_stop'] is True and scope['automatic_retry'] is False,'Stop/retry')
    util=module(scope['utility_ref'],'desktop58_pinned_IO_utility')
    resources=strict(verify(scope['resource_catalog_ref']))
    code_keys=['controller_ref','launcher_ref','authorization_verifier_ref','utility_ref','owned_helper_ref','debug_helper_ref',
        'network_observer_ref','fixture_evaluator_ref','roster_ref','alias_roster_ref','alias_edits_ref','instrumented_test_ref','source_catalog_ref','builder_source_ref']
    allowed=resources['files']+[scope[k] for k in code_keys]
    need(resources['complete_public_roots_frozen'] is True, 'Actual complete public input closure required')
    for r in allowed+authorized['authorization_input_refs']:verify(r)
    normal=module(scope['owned_helper_ref'],'desktop58_owned_job')
    debug=module(scope['debug_helper_ref'],'desktop58_debug_job')
    out=None;first=None;secondary=[];ledger=None;last=None;stage='ALLOCATE';native=0;rows=[];allcases=[];current_case=None;http_total=0
    need(scope['native_top_command_cap']==176 and scope['process_cap']<=2048, 'Exact declared top-level operation bound')
    start=time.monotonic();deadline=start+scope['inner_seconds']
    need(type(scope['inner_seconds']) is int and scope['inner_seconds']>0 and scope['cleanup_seconds']==5,'Explicit finite allocation')
    try:
        out=safe(scope['output_root'],ROOT/'execution/v2.4/receipts/W13/W13-03',True);out.mkdir()
        export=safe(scope['export_root'],ROOT/'.local',True);export.mkdir()
        ledger=util.Ledger(out);ledger.add('authority-resource-code',[r['path'] for r in allowed+authorized['authorization_input_refs']])
        ledger.check('initial');save(out/'runtime.before.json',util.module_observation(allowed,normal))
        roster=strict(verify(scope['roster_ref']));need(len(roster['leaves'])==162 and len(roster['regressions'])==7 and len(roster['go_units'])==3,'Original finite roster')
        aliases=strict(verify(scope['alias_roster_ref']))['rows'];need(len(aliases)==20,'Exact20 alias allocation')
        allcases=[{'lane':'go3','name':'pure-Go-exact3','state':'NOT_STARTED','native_exit':None,'qualified':False}]+[
          {'lane':'node','name':x['name'],'state':'NOT_STARTED','native_exit':None,'qualified':False} for x in roster['leaves']+roster['regressions']]
        images=resources['images'];need(len(images)<=60,'Static images leave four fresh artifact slots')
        for x in images:verify(x)
        env=dict(scope['public_environment']);need(set(env)<=set(['SystemRoot','WINDIR','ComSpec','PATH','PATHEXT']),'Public environment only')
        tmp=export/'.desktop-controller-tmp';tmp.mkdir()
        env.update({'TEMP':str(tmp),'TMP':str(tmp),'GOTOOLCHAIN':'local','GOENV':'off','GOWORK':'off','GOPROXY':'off','GOSUMDB':'off',
            'GOOS':'windows','GOARCH':'amd64','GOAMD64':'v1','CGO_ENABLED':'0','GOEXPERIMENT':'','GODEBUG':'',
            'GOFLAGS':'-p=1 -buildvcs=false -mod=readonly','PYTHONDONTWRITEBYTECODE':'1'})
        def run(label,argv,cwd,seconds,expected_images,ee=None,stdin=None,futures=None,context=None):
            nonlocal stage,native,last
            stage=label;remaining=deadline-time.monotonic()-5
            need(remaining>0 and native<scope['native_top_command_cap'],'Native/time allocation exhausted')
            native+=1;timeout=min(seconds,remaining)
            req={'argv':argv,'cwd':str(cwd),'environment':ee or env,'requested_timeout':seconds,'effective_timeout':timeout,
                 'remaining_before_start':remaining,'future_images':futures,'future_context':context,'sequence':native}
            save(out/(label+'.request.json'),req);r=None;error=None
            try:
                with (out/(label+'.stdout.raw')).open('xb') as so,(out/(label+'.stderr.raw')).open('xb') as se:
                    r=debug.run_owned(argv,str(cwd),ee or env,so,se,timeout,expected_image={k:pin(argv[0])[k] for k in ['sha256','bytes']},
                       allowed_images=expected_images,allowed_module_files=list(ledger.members.values()),process_cap=scope['process_cap'],stdin=stdin,
                       future_images=futures,future_context=context)
                    last=r
                    if current_case is not None:
                        current_case['native_exit']=r.get('actual_exit')
                        current_case['state']='NATIVE_EXIT_OBSERVED' if r.get('actual_exit') is not None else 'STARTED_EXIT_UNKNOWN'
                        current_case['owned_child_pid']=r.get('owned_child_pid')
                        current_case['creation_time_100ns']=r.get('creation_time_100ns')
            except BaseException as exc:error=exc
            finally:
                save(out/(label+'.invocation.json'),{'request':req,'result':r,'actual_native_exit':r.get('actual_exit') if r else None,'exception':repr(error) if error else None})
                for label2,fn in [('vector',lambda:ledger.check(label+'-native-after')),('runtime',lambda:save(out/(label+'.runtime.after.json'),util.module_observation(allowed,normal)))]:
                    try:fn()
                    except BaseException as exc:
                        if error is None:error=exc
                        else:secondary.append({'stage':label+'-'+label2,'error':repr(exc),'actual_native_exit':None})
            if error:raise error
            util.job_ok(r,True)
            return (out/(label+'.stdout.raw')).read_bytes(),r
        tools=resources['tools'];git=tools['git']['path'];go=tools['go']['path'];node=tools['node']['path'];python=tools['python']['path']
        head,_=run('git-head',[git,'rev-parse','HEAD'],ROOT,30,images);need(head.decode('ascii').strip()==SOURCE,'Current head changed')
        catalog=strict(verify(scope['source_catalog_ref']));need(catalog['commit']==SOURCE and catalog['files'],'New source catalogue')
        for item in catalog['files']:
            p=safe(ROOT/item['path'],ROOT);need(pin(p)['sha256']==item['sha256'] and pin(p)['bytes']==item['bytes'],'Original current source pin')
        ledger.add('original-current-source',[ROOT/x['path'] for x in catalog['files']])
        batch=''.join(x['git_blob']+'\n' for x in catalog['files']).encode();(out/'export.stdin.raw').open('xb').write(batch)
        with (out/'export.stdin.raw').open('rb') as stream:raw,_=run('export-blobs',[git,'cat-file','--batch'],ROOT,90,images,stdin=stream)
        pos=0
        for row in catalog['files']:
            end=raw.index(b'\n',pos);sha,kind,size=raw[pos:end].decode().split();pos=end+1;body=raw[pos:pos+int(size)];pos+=int(size)
            need(kind=='blob' and sha==row['git_blob'] and hashlib.sha256(body).hexdigest()==row['sha256'] and len(body)==row['bytes'] and raw[pos:pos+1]==b'\n','Export blob mismatch');pos+=1
            p=safe(export/row['path'],export,True);p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write(body)
        need(pos==len(raw),'Extra Git batch bytes')
        # Instrument only test setup allocation; original mkdir/wx/copy and every original assertion remain.
        plan=strict(verify(scope['alias_edits_ref']));testfile=export/'tests/ui/desktop/http-wire-boundary.test.mjs';base=testfile.read_bytes()
        instrumented=verify(scope['instrumented_test_ref']);reverse=instrumented.decode()
        for e in reversed(plan):need(reverse.count(e['new'])==1,'Alias reverse ambiguous');reverse=reverse.replace(e['new'],e['old'],1)
        need(reverse.encode()==base,'Alias original full byte inverse');testfile.write_bytes(instrumented)
        ledger.add('export',[p for p in inventory(export) if not p.is_relative_to(tmp)]);ledger.check('before-build')
        build=safe(export/'.desktop58-build',export,True);receipts=safe(export/'.desktop58-build-receipts',export,True)
        builder=export/'apps/desktop/build-validator.py';need(pin(builder)['sha256']==scope['builder_source_ref']['sha256'],'Current builder pin')
        argv=[python,'-I','-S','-X','utf8',str(builder),'--go',go,'--node',node,'--electron',tools['electron']['path'],
          '--module-cache',resources['GOMODCACHE'],'--web-modules',resources['web_modules'],'--output',str(build),'--receipts',str(receipts)]
        run('build-current58',argv,export,scope['builder_seconds'],images)
        result=strict((receipts/'result.json').read_bytes());need(result['status']=='BUILT_NOT_TESTED' and result['drift']==[],'Builder closed failure/drift')
        expected_nested=['go-version','node-version','go-list','go-list-negative-fixture','go-build','negative-child-build','go-test-build','web-module-junction','react-build']
        need([x['stdout'] for x in result['invocations']]==[x+'.stdout' for x in expected_nested],'Exact existing builder operation graph')
        for row in result['invocations']:need(row['exit']==0,'Nested builder reported failure; timeout124 is not an observed OS native exit')
        descriptor=Path(result['descriptor']);need(descriptor==build/'apps/desktop/resources/client-wire/descriptor.json','Descriptor location')
        desc=strict(descriptor.read_bytes());need(desc['schema']=='researchos.desktop.client-wire-release/1' and desc['build_input_digest']==result['build_input_digest'],'Descriptor binding')
        before=strict((receipts/'inputs.before.json').read_bytes())
        need(hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':')).encode()).hexdigest()==desc['build_input_digest'],'buildInputDigest')
        for row in before:
            actual=pin(row['path']);need(actual==row,'Builder source drift')
            need(row['path'] in ledger.members or Path(row['path']).is_relative_to(build),'Uncatalogued actual builder input')
        work=strict((receipts/'compiler-work-archive.json').read_bytes())
        need(work['WORK'] and work['archives'] and any(Path(x['path']).name=='_testmain.go' for x in work['WORK']),'Generated WORK/testmain/archives missing')
        for row in work['WORK']+work['archives']:verify(row)
        packages=[];decoder=json.JSONDecoder()
        for label in ['go-list','go-list-negative-fixture']:
            text=(receipts/(label+'.stdout')).read_text(encoding='utf-8',errors='strict');pos=0
            while pos<len(text):
                if text[pos].isspace():pos+=1;continue
                package,pos=decoder.raw_decode(text,pos);packages.append(package)
        graph_files=[]
        for package in packages:
            need(not package.get('Error') and not package.get('DepsErrors'),'Actual package graph error')
            directory=Path(package.get('Dir',''))
            for key in ['GoFiles','CgoFiles','CompiledGoFiles','IgnoredGoFiles','IgnoredOtherFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles']:
                for name in package.get(key,[]):
                    p=Path(name) if Path(name).is_absolute() else directory/name
                    need(p.is_file(),'Missing actual graph member');need(str(p) in ledger.members or p.is_relative_to(build),'Unfrozen actual graph input');graph_files.append(pin(p))
            if package.get('Module',{}).get('GoMod'):
                p=Path(package['Module']['GoMod']);need(p.is_file() and str(p) in ledger.members,'Unfrozen actual module GoMod');graph_files.append(pin(p))
        save(out/'actual-package-graph.json',{'packages':packages,'input_refs':graph_files})
        validator=build/'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe';negative=Path(desc['qualification_fixture_binary']['path']);testexe=build/'validator.test.exe'
        need(pin(validator)['sha256']==desc['binary_sha256'] and pin(negative)['sha256']==desc['qualification_fixture_binary']['sha256'],'Fresh executable descriptor')
        junction=build/'apps/web/node_modules';target=Path(resources['web_modules']).resolve()
        ledger.add('fresh-build-graph-artifacts',inventory(build,junction,target)+inventory(receipts)+[Path(x['path']) for x in work['WORK']+work['archives']])
        buildimages=images+[pin(validator),pin(negative),pin(testexe)]
        for name,p in [('validator',validator),('negative',negative),('test',testexe)]:run('buildinfo-'+name,[go,'version','-m',str(p)],export,30,images)
        ledger.check('before-first-case');save(out/'fresh-release.json',{'descriptor':pin(descriptor),'validator':pin(validator),'negative':pin(negative),'testexe':pin(testexe),'WORK':work,'source':SOURCE})
        ee=dict(env);ee.update(RESEARCHOS_DESKTOP_WIRE_ROOT=str(build/'apps/desktop'),RESEARCHOS_DESKTOP_ELECTRON=tools['electron']['path'])
        for index,state in enumerate(allcases):
            stage='case-'+str(index).zfill(3);case=out/stage;case.mkdir();evidence=case/'evidence';caseenv=dict(ee);caseenv['RESEARCHOS_DESKTOP_CASE_RECEIPT']=str(evidence)
            current_case=state;state['state']='STARTED';save(case/'started.json',state);ledger.check(stage+'-before')
            futures=[];context={'root':str(export/'.local/desktop-wire-negative'),'run_uuid':scope['run_uuid'],'case_name':state['name'],'scope_sha256':sys.argv[2]}
            if index==0:argv=[str(testexe),'-test.run','^('+'|'.join(roster['go_units'])+')$','-test.v','-test.count=1','-test.failfast','-test.timeout=120s']
            else:
                leaf=(roster['leaves']+roster['regressions'])[index-1]
                if index<=162:argv=[node,'--require',scope['network_observer_ref']['path'],'--test','--test-reporter=tap','--test-name-pattern','^'+re.escape(leaf['name'])+'$','tests/ui/desktop/http-wire-boundary.test.mjs']
                else:argv=[node,'--require',scope['network_observer_ref']['path'],*leaf['argv'][1:]]
                selected=[a for a in aliases if a['name']==state['name']]
                if selected:
                    a=selected[0];root=Path(context['root'])/(scope['run_uuid']+'-'+str(a['allocation_ordinal']).zfill(2))
                    need(not root.exists(),'Fresh alias root already exists')
                    ap=case/'negative-alias-plan.json';save(ap,{'schema':'researchos.desktop-negative-alias-plan/1','case_name':a['name'],'mode':a['mode'],'rows':[{'run_uuid':scope['run_uuid'],'ordinal':a['allocation_ordinal'],'root':str(root)}]})
                    caseenv.update(RESEARCHOS_DESKTOP_NEGATIVE_ALIAS_PLAN=str(ap),RESEARCHOS_DESKTOP_NEGATIVE_ALIAS_SHA256=pin(ap)['sha256'],RESEARCHOS_DESKTOP_CASE_NAME=a['name'])
                    if a['expected_image_creates']:
                        futures=[{'path':str(root/'resources/client-wire/researchos-client-wire-validator.exe'),'sha256':pin(negative)['sha256'],'bytes':pin(negative)['bytes'],
                          'origin_ref':pin(negative),'scope_sha256':sys.argv[2],'run_uuid':scope['run_uuid'],'case_name':a['name'],
                          'allocation_ordinal':a['allocation_ordinal'],'max_creates':a['expected_image_creates']}]
            raw,job=run(stage,argv,export,150,buildimages,caseenv,futures=futures,context=context)
            state.update(state='NATIVE_EXIT_OBSERVED',native_exit=job['actual_exit'])
            text=raw.decode('utf-8',errors='strict')
            if index==0:
                need(all(re.search(r'^--- PASS: '+re.escape(x)+r' \(',text,re.M) for x in roster['go_units']) and '\nPASS\n' in text.replace('\r\n','\n') and '--- FAIL:' not in text and '--- SKIP:' not in text,'Go3 exact raw proof')
            elif index<=162 or leaf.get('count_kind')=='existing exact node:test leaf':
                need(re.search(r'^# pass 1$',text,re.M) and re.search(r'^# fail 0$',text,re.M) and re.search(r'^# skipped 0$',text,re.M),'Node exact leaf TAP proof')
            else:need(any(strict(line).get('status')=='PASS' for line in raw.splitlines() if line.startswith(b'{')),'Legacy program explicit PASS missing')
            # Evaluator is a separately pinned source contract; it must inspect raw fixture/transport/renderer records.
            evaluation=module(scope['fixture_evaluator_ref'],'desktop58_fixture_evaluator').validate_case(state,leaf if index else None,case,export,job,scope)
            need(evaluation['qualified'] is True and evaluation['source_assertions_preserved'] is True,'Fixture evidence incomplete')
            http_total+=evaluation['HTTP'];need(http_total<=390,'Original aggregate observed HTTP cap')
            save(case/'fixture-verdict.json',evaluation);state.update(state='QUALIFIED',qualified=True);rows.append(dict(state))
            current_case=None
            ledger.check(stage+'-fixture-after');save(case/'result.json',state)
        need(len(rows)==170 and all(x['qualified'] for x in rows),'Finite lanes incomplete')
        save(out/'completed.json',{'node_controls':169,'Go_top_cases':3,'rows':rows,'actual_native_top_commands':native,'source_acceptance':False,'formal_increment':0})
    except BaseException as exc:first={'stage':stage,'error':repr(exc),'traceback':traceback.format_exc(),'actual_native_exit':None}
    finally:
        if out is not None:
            for tag,fn in [('vector',lambda:ledger.check('final') if ledger else None),('runtime',lambda:save(out/'runtime.after.json',util.module_observation(allowed,normal)))]:
                try:fn()
                except BaseException as exc:
                    item={'stage':'final-'+tag,'error':repr(exc),'actual_native_exit':None}
                    if first is None:first=item
                    else:secondary.append(item)
            if time.monotonic()>deadline and first is None:first={'stage':'final-deadline','error':'Root inner deadline exceeded','actual_native_exit':None}
            save(out/'result.json',{'first_error':first,'secondary_errors':secondary,'last_child_result':last,'rows':rows,'all_case_states':allcases,'actual_observed_HTTP_total':http_total,'actual_native_top_commands':native,'source_acceptance':False})
            if time.monotonic()>deadline:
                save(out/'tail-deadline.failure.json',{'first_error':first,'error':'Root inner deadline exceeded after final evidence IO','actual_native_exit':None})
                return 1
    return 1 if first else 0
if __name__=='__main__':
    try:code=main()
    except BaseException:
        traceback.print_exc();code=1
    raise SystemExit(code)
