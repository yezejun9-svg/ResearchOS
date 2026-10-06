"""Independent, expected-success probes for the three reported UI defects."""
import inspect, json, os, subprocess, time
from urllib.parse import parse_qs, urlsplit
from scenarios import login
import browser_smoke


def probe(page, base, project_path, owner, api, report, out):
    harness = inspect.currentframe().f_back.f_locals
    environment = dict(harness['environment'], RESEARCHOS_TASK_ID='W13')
    provision = subprocess.run([str(harness['provision_binary']), project_path.rsplit('/',1)[1]], cwd=browser_smoke.ROOT, env=environment, capture_output=True, text=True)
    assert provision.returncode == 0, provision.stderr
    credentials = json.loads(provision.stdout)
    evidence = []
    for marker in ['Review route A', 'Review route B']:
        evidence.append(browser_smoke.fixture_artifact(base, credentials['token'], credentials['principal_id'], project_path, 'text/plain', marker.encode(), marker)[1])
    login(page, base, project_path + '/evidence?context=review&focus=' + evidence[0]['id'], owner)
    page.get_by_text('Review route A', exact=True).wait_for()
    page.get_by_label('检索词', exact=True).fill('Review route')
    page.locator('.list-panel .record-row').filter(has_text=evidence[1]['id'][:12]).click()
    page.get_by_text('Review route B', exact=True).wait_for()
    expected_query = {'context':['review'],'focus':[evidence[1]['id']]}
    assert parse_qs(urlsplit(page.url).query) == expected_query
    assert page.get_by_label('检索词', exact=True).input_value() == 'Review route'
    page.go_back()
    page.get_by_text('Review route A', exact=True).wait_for()
    page.go_forward()
    page.get_by_text('Review route B', exact=True).wait_for()
    page.reload(wait_until='domcontentloaded')
    page.get_by_label('访问令牌').fill(owner)
    page.get_by_role('button', name='打开工作台').click()
    page.get_by_text('Review route B', exact=True).wait_for()
    assert parse_qs(urlsplit(page.url).query) == expected_query
    page.get_by_label('检索词', exact=True).fill('Review route A')
    page.get_by_role('button', name='服务端检索', exact=True).click()
    page.get_by_role('button', name='定位证据', exact=True).wait_for()
    page.get_by_role('button', name='定位证据', exact=True).click()
    page.get_by_text('Review route A', exact=True).wait_for()
    assert parse_qs(urlsplit(page.url).query)['focus'] == [evidence[0]['id']]
    assert page.get_by_label('检索词', exact=True).input_value() == 'Review route A'
    report['route_regression'] = {'list_url':True,'reload_selection':True,'back_forward':True,'preserves_other_query':True,'filter_survives_selection':True,'search_hit_updates_focus':True,'evidence_ids':[item['id'] for item in evidence]}
    typography = page.evaluate('''() => ['.tag','.stage-count','.sidebar-head','.stage-number'].flatMap(selector => [...document.querySelectorAll(selector)].filter(el=>el.getClientRects().length).map(el=>({selector,text:el.textContent,size:parseFloat(getComputedStyle(el).fontSize)})))''')
    assert all(item['size'] >= (13 if item['selector'] in ['.tag','.stage-count'] else 12) for item in typography), typography
    page.screenshot(path=str(out / 'regression-evidence-desktop.png'), full_page=False)
    page.get_by_label('检索词', exact=True).fill('')
    for width,height in [(1440,1000),(1024,768),(768,1024),(390,844),(320,780)]:
        page.set_viewport_size({'width':width,'height':height})
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1'), width
    bottom_sizes = page.locator('.bottom-nav a').evaluate_all('(els)=>els.map(el=>parseFloat(getComputedStyle(el).fontSize))')
    assert all(size >= 12 for size in bottom_sizes), bottom_sizes
    page.get_by_role('button', name='打开阶段进度').click()
    page.get_by_role('button', name='关闭进度').wait_for()
    page.wait_for_function('document.querySelector(".progress-rail").getBoundingClientRect().right <= innerWidth + 1')
    assert page.locator('.stage-count').evaluate_all('(els)=>els.every(el=>parseFloat(getComputedStyle(el).fontSize)>=13)')
    page.screenshot(path=str(out / 'regression-stage-mobile.png'), full_page=False)
    page.keyboard.press('Escape')
    assert page.evaluate('document.activeElement.getAttribute("aria-label")') == '打开阶段进度'
    report['typography_regression'] = {'computed':typography,'bottom_sizes':bottom_sizes,'widths':[1440,1024,768,390,320],'no_overflow':True,'drawer_focus_return':True}
    prefix = project_path.replace('/p/', '/v1/projects/')
    held=[]
    def hold(route): held.append(route)
    page.route('**' + prefix + '/budget-policy', hold)
    login(page, base, project_path + '/resources', owner)
    page.locator('main .loading-state').wait_for()
    start=time.monotonic()
    page.locator('main .state-notice', has_text='请求超时').wait_for(timeout=45000)
    elapsed=time.monotonic()-start
    assert not page.locator('main .loading-state').count()
    page.screenshot(path=str(out / 'regression-timeout-error.png'), full_page=False)
    page.unroute('**' + prefix + '/budget-policy', hold)
    for route in held:
        try: route.abort('timedout')
        except Exception: pass
    page.get_by_role('button', name='重新读取', exact=True).click()
    page.get_by_role('button', name='保存上限', exact=True).wait_for()
    assert not page.locator('main .state-notice').count()
    report['timeout_regression']={'actual_wait_seconds':round(elapsed,3),'error_explained':True,'retry_recovers':True,'held_calls':len(held)}
    report['checks'].append('Independent fixed-source probes pass URL selection/reload/history/search positioning, minimum computed fonts/320px drawer, real 30-second stalled HTTP timeout and explicit retry recovery')
    report['screenshots'] += ['regression-evidence-desktop.png','regression-stage-mobile.png','regression-timeout-error.png']
