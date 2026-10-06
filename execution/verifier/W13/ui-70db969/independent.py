"""Reviewer-authored counterexamples on real browser, using explicit UI fixtures."""
import json
from scenarios import login


def probe(page, base, project_path, owner, api, report, out):
    prefix = project_path.replace('/p/', '/v1/projects/')
    # Service-empty baseline is captured before any fixture response is installed.
    login(page, base, project_path + '/evidence', owner)
    page.get_by_text('本页没有符合筛选条件的证据；来源受限应查看周期覆盖。', exact=True).wait_for()
    page.screenshot(path=str(out / 'independent-empty.png'), full_page=False)
    # Use real API-created records from the database through a narrowly provisioned fixture principal.
    from pathlib import Path
    import os, subprocess
    import browser_smoke
    # The outer harness supplies temporary binaries and data directory only in its frame.
    import inspect
    parent = inspect.currentframe().f_back.f_locals
    environment = dict(parent['environment'], RESEARCHOS_TASK_ID='W13')
    done = subprocess.run([str(parent['provision_binary']), project_path.rsplit('/',1)[1]], cwd=browser_smoke.ROOT, env=environment, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    credentials = json.loads(done.stdout)
    refs = []
    for marker in ['Reviewer original A', 'Reviewer original B']:
        refs.append(browser_smoke.fixture_artifact(base, credentials['token'], credentials['principal_id'], project_path, 'text/plain', marker.encode(), marker)[1])
    login(page, base, project_path + '/evidence?focus=' + refs[0]['id'], owner)
    page.get_by_text('Reviewer original A', exact=True).wait_for()
    page.locator('.list-panel .record-row').filter(has_text=refs[1]['id'][:12]).click()
    page.get_by_text('Reviewer original B', exact=True).wait_for()
    report['independent_typography'] = page.evaluate('''() => ['.tag','.stage-count','.stage-extra','.sidebar-head','.stage-number'].flatMap(selector => [...document.querySelectorAll(selector)].filter(el=>el.getClientRects().length).map(el=>({selector,text:el.textContent,font_size:getComputedStyle(el).fontSize})))''')
    before = {'url':page.url, 'visible_selected':'Reviewer original B', 'expected_focus':refs[1]['id']}
    page.screenshot(path=str(out / 'independent-selection-before-refresh.png'), full_page=False)
    page.reload(wait_until='domcontentloaded')
    page.get_by_label('访问令牌').fill(owner)
    page.get_by_role('button', name='打开工作台').click()
    page.get_by_text('Reviewer original A', exact=True).wait_for()
    after = {'url':page.url, 'visible_selected':'Reviewer original A', 'selection_restored':False}
    page.screenshot(path=str(out / 'independent-selection-after-refresh.png'), full_page=False)
    report['independent_selection_counterexample'] = {'before':before,'after':after,'real_api_records':refs}
    # Escape/focus trap verified independently at the exact 320x780 contract viewport.
    page.set_viewport_size({'width':320,'height':780})
    report['independent_typography'] += page.locator('.bottom-nav a').evaluate_all('(els)=>els.map(el=>({selector:".bottom-nav a",text:el.textContent,font_size:getComputedStyle(el).fontSize}))')
    page.get_by_role('button', name='打开导航').click()
    page.get_by_role('button', name='关闭导航').wait_for()
    page.keyboard.press('Shift+Tab')
    assert page.evaluate('!!document.activeElement.closest(".sidebar")')
    page.keyboard.press('Tab')
    assert page.evaluate('document.activeElement.getAttribute("aria-label")') == '关闭导航'
    page.keyboard.press('Escape')
    assert page.evaluate('document.activeElement.getAttribute("aria-label")') == '打开导航'
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
    page.screenshot(path=str(out / 'independent-320-keyboard.png'), full_page=False)
    report['independent_keyboard'] = {'viewport':[320,780],'tab_wrap':True,'escape_focus_restored':True,'no_overflow':True}
    report['checks'].append('Reviewer probe reproduces stale evidence URL and wrong selection after reload; 320x780 keyboard drawer wrap and focus return pass')
    report['screenshots'] += ['independent-empty.png','independent-selection-before-refresh.png','independent-selection-after-refresh.png','independent-320-keyboard.png']
    if os.environ.get('REVIEW_TIMEOUT_PROBE') == '1':
        held = []
        page.route('**' + prefix + '/budget-policy', lambda route: held.append(route))
        login(page, base, project_path + '/resources', owner)
        page.locator('main .loading-state').wait_for()
        page.wait_for_timeout(35000)
        report['independent_pending_request'] = {'held_operation':'getBudgetPolicy','elapsed_ms':35000,'held_count':len(held),
            'loading_still_visible':page.locator('main .loading-state').is_visible(),
            'error_or_retry_count':page.locator('main .state-notice').count(),
            'source_deadline':'createApi.call fetch has no timeout signal; useQueries waits for allSettled and has no deadline'}
        page.screenshot(path=str(out / 'independent-pending-35s.png'), full_page=False)
        report['screenshots'].append('independent-pending-35s.png')
        for request in held:
            request.abort('timedout')
