"""One narrow C06 browser delta over real Service.Handler and synthetic source captures."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,tempfile,time,traceback
from playwright.sync_api import sync_playwright

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
locked=json.loads((ROOT/'execution/toolchains/locked.json').read_text('utf-8'))
go=Path(locked['tools']['go']['path']);node=Path(locked['tools']['node']['path'])
sources={p.relative_to(ROOT).as_posix():sha(p) for pattern in ['internal/**/*.go','adapters/**/*.go','migrations/sqlite/*.sql','spec/v2.0/contracts/*.json','spec/v2.0/ui/*.json','apps/web/src/*','apps/web/package*.json','apps/web/index.html','go.mod','go.sum'] for p in ROOT.glob(pattern) if p.is_file()}
before={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'started_at':now(),'source_hashes':sources,'go_sha256':sha(go),'node_sha256':sha(node),'probe_go_sha256':sha(OUT/'probe_test.go'),'probe_python_sha256':sha(__file__),'scope':'C06-02_FIXTURE_ONLY','provider_calls':0}
save('before.json',before)
commands=[];checks=[];api_events=[];errors=[];proc=None
def command(name,argv,cwd,env=None):
    start=now();r=subprocess.run([str(x) for x in argv],cwd=cwd,env=env,capture_output=True,timeout=180)
    (OUT/(name+'.stdout.txt')).write_bytes(r.stdout);(OUT/(name+'.stderr.txt')).write_bytes(r.stderr)
    commands.append({'name':name,'argv':[str(x) for x in argv],'cwd':str(cwd),'started_at':start,'ended_at':now(),'exit_code':r.returncode});save('commands.json',commands)
    assert r.returncode==0,f'{name} failed; preserved stdout/stderr'
def check(id,want,got,refs):
    status='PASS' if want==got else 'FAIL';checks.append({'id':id,'expected':want,'actual':got,'status':status,'evidence_refs':refs})
    assert status=='PASS',id
def response_log(response):
    if '/v1/' not in response.url or '/events/stream' in response.url:return
    try:
        body=response.body()
        try:decoded=json.loads(body)
        except Exception:decoded=body.decode('utf-8','replace')
        api_events.append({'url':response.url,'method':response.request.method,'status':response.status,'body_sha256':sha_bytes(body),'body':decoded,'at':now()})
    except Exception as e:errors.append({'response_read_error':str(e),'url':response.url})
def sha_bytes(b):return hashlib.sha256(b).hexdigest()

report={'scope':'REAL_WINDOWS_BROWSER_AND_SQLITE_WITH_SYNTHETIC_SOURCE_CAPTURE','status':'FAIL','C06_complete_signed':False,'provider_calls':0,'product_modified':False,'started_at':now()}
try:
 with tempfile.TemporaryDirectory(prefix='researchos-c06-ui-') as temp:
    temp=Path(temp).resolve();assert temp.name.startswith('researchos-c06-ui-')
    web=temp/'web';control=temp/'control';control.mkdir()
    command('web-build',[node,ROOT/'apps/web/node_modules/vite/bin/vite.js','build','--outDir',web],ROOT/'apps/web')
    report['web_build_hashes']={p.relative_to(web).as_posix():sha(p) for p in web.rglob('*') if p.is_file()}
    overlay=temp/'overlay.json';overlay.write_text(json.dumps({'Replace':{str(ROOT/'internal/domain/c06_ui_overlay_test.go'):str(OUT/'probe_test.go')}}),encoding='utf-8')
    save('overlay.json',json.loads(overlay.read_text()))
    executable=temp/'c06-ui.test.exe'
    env=dict(os.environ,GOTOOLCHAIN='local',GOENV='off',C06_EVIDENCE=str(OUT),C06_WEB=str(web),C06_CONTROL=str(control))
    command('probe-build',[go,'test','-c','-overlay',overlay,'-o',executable,'.'],ROOT/'internal/domain',env)
    report['test_binary_sha256']=sha(executable)
    argv=[str(executable),'-test.run','^TestC06IndependentUIFixture$','-test.v','-test.timeout','300s']
    proc=subprocess.Popen(argv,cwd=ROOT/'internal/domain',env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    report['parent_observed_child_pid']=proc.pid
    start=time.monotonic()
    while not (control/'ready.json').exists():
        if proc.poll() is not None:raise RuntimeError('fixture process exited before readiness')
        if time.monotonic()-start>45:raise RuntimeError('fixture readiness timeout')
        time.sleep(.1)
    ready=json.loads((control/'ready.json').read_text('utf-8'))
    check('CHILD-PID-BINDING',proc.pid,ready['pid'],['commands.json'])
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=False)
        report['browser_version']=browser.version
        try:
            for case in ready['cases']:
                fault=case['fault'];stem=fault.lower();seed=json.loads((OUT/(stem+'-seed.json')).read_text('utf-8'))
                check(fault+'-EXACT-SOURCE-SET',{'GITHUB':'COMPLETE','PAPER':'COMPLETE','X':fault},seed['coverage_statuses'],[stem+'-seed.json'])
                check(fault+'-CYCLE-PARTIAL','PARTIAL',seed['cycle']['status'],[stem+'-seed.json'])
                check(fault+'-FALSE-COMPLETE-DENIED',422,seed['complete_attempt']['status'],[stem+'-seed-api.json'])
                if fault=='RATE_LIMITED':
                    check('RETRY-AFTER-NO-ADDITIONAL-FETCH',0,seed['additional_adapter_fetches'],[stem+'-seed.json'])
                    check('RETRY-AFTER-WITHIN-WAIT',True,seed['repeat_attempt_at']<seed['retry_after'],[stem+'-seed.json'])
                    check('RESEARCH-RETRIGGER-COALESCED',True,seed['repeat_trigger_coalesced'],[stem+'-seed.json'])
                context=browser.new_context(viewport={'width':1440,'height':1100},locale='zh-CN',timezone_id='Asia/Shanghai')
                page=context.new_page();page.on('response',response_log);page.on('pageerror',lambda e:errors.append({'pageerror':str(e)}))
                base=case['url'];project='/p/'+case['project']
                page.goto(base+project,wait_until='domcontentloaded')
                page.get_by_label('访问令牌').fill(case['token']);page.get_by_role('button',name='打开工作台',exact=True).click()
                for kind,suffix in [('dashboard',''),('detail','/cycles/'+case['cycle'])]:
                    if kind=='detail':
                        page.goto(base+project+suffix,wait_until='domcontentloaded')
                        page.get_by_label('访问令牌').fill(case['token']);page.get_by_role('button',name='打开工作台',exact=True).click()
                    page.get_by_text(fault,exact=True).first.wait_for(timeout=20000)
                    coverage=page.locator('.coverage-row' if kind=='dashboard' else '.coverage-card')
                    expected={value[:12]:fault if source=='X' else 'COMPLETE' for source,value in case['source_ids'].items()}
                    visible={}
                    for row in coverage.all():
                        text=row.inner_text()
                        for source,value in case['source_ids'].items():
                            if value[:12] in text:
                                visible[value[:12]]=row.locator('.tag').inner_text()
                                gap=next(x['gap_reason'] for x in seed['cycle']['source_coverage'] if x['source_id']==value)
                                if source=='X':check(fault+'-'+kind+'-GAP-VISIBLE',True,gap in text,[stem+'-seed.json',stem+'-'+kind+'.png'])
                    check(fault+'-'+kind+'-COVERAGE',expected,visible,[stem+'-'+kind+'.png'])
                    cycle_status=page.locator('.summary-strip > div').nth(2).locator('strong').inner_text() if kind=='dashboard' else page.locator('.page-heading > .tag').inner_text()
                    check(fault+'-'+kind+'-CYCLE-STATUS','PARTIAL',cycle_status,[stem+'-'+kind+'.png'])
                    if kind=='detail':check(fault+'-NO-FULL-SCAN-INFERENCE',True,page.get_by_text('本轮范围 · 非全面扫描推断',exact=True).is_visible(),[stem+'-detail.png'])
                    visible_text=page.locator('main').inner_text()
                    check(fault+'-'+kind+'-NO-FULL-SCAN-CLAIM',False,any(phrase in visible_text for phrase in ['已全面扫描','全面扫描完成','全部来源已完成','本轮全面完成']),[stem+'-'+kind+'.txt'])
                    (OUT/(stem+'-'+kind+'.txt')).write_text(visible_text,encoding='utf-8')
                    page.screenshot(path=str(OUT/(stem+'-'+kind+'.png')),full_page=True)
                context.close()
        finally:
            browser.close()
            (control/'stop').write_text('stop',encoding='utf-8')
            stdout,stderr=proc.communicate(timeout=15)
            (OUT/'probe.stdout.txt').write_bytes(stdout);(OUT/'probe.stderr.txt').write_bytes(stderr)
            check('PROBE-CLEAN-EXIT',0,proc.returncode,['probe.stdout.txt','probe.stderr.txt'])
            proc=None
    drift=[name for name,h in sources.items() if sha(ROOT/name)!=h]
    check('SOURCE-HASH-CONTINUITY',[],drift,['before.json'])
    check('BROWSER-PAGE-ERRORS',[],[e for e in errors if 'pageerror' in e],['browser-errors.json'])
    report['status']='PASS'
 report['temporary_directory_removed']=not temp.exists()
except Exception:
 report['error']=traceback.format_exc()
finally:
 if proc is not None:
    proc.terminate()
    try:stdout,stderr=proc.communicate(timeout=10)
    except subprocess.TimeoutExpired:proc.kill();stdout,stderr=proc.communicate()
    (OUT/'probe.stdout.txt').write_bytes(stdout);(OUT/'probe.stderr.txt').write_bytes(stderr)
 save('browser-api.json',api_events);save('browser-errors.json',errors);save('checks.json',checks)
 report.update(finished_at=now(),assertion_count=len(checks),passed=sum(x['status']=='PASS' for x in checks),screenshots=[p.name for p in sorted(OUT.glob('*.png'))],source_revision=before['head'],browser_api_response_count=len(api_events))
 save('report.json',report)
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(0 if report['status']=='PASS' else 1)
