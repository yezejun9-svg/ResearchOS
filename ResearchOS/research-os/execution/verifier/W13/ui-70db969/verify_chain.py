from scenarios import login


def verify_chain(page, base, project_path, token, report, out):
    expected = report['notification_contract']
    page.set_viewport_size({'width':1440,'height':1000})
    login(page, base, project_path, token)
    rail = page.locator('.rail-release[href="' + project_path + '/releases/' + expected['release_id'] + '"]')
    rail.wait_for()
    rail.click()
    page.get_by_role('heading', name='C17 offline release', exact=True).wait_for()
    assert page.url == base + project_path + '/releases/' + expected['release_id']
    page.get_by_text('查看实际检查与命令', exact=True).click()
    page.locator('.raw-details pre').filter(has_text=expected['acceptance_id']).wait_for()
    assert expected['artifact_ref']['content_hash'] in page.locator('.artifact-preview').inner_text()
    page.get_by_role('button', name='受控预览').click()
    page.locator('.preview-text').get_by_text('"C18": 0', exact=False).wait_for()
    page.screenshot(path=str(out / 'reviewer-sidebar-exact-chain.png'), full_page=True)
    report['screenshots'].append('reviewer-sidebar-exact-chain.png')
    report['reviewer_sidebar_chain'] = {'release_id':expected['release_id'],'artifact_ref':expected['artifact_ref'],'acceptance_id':expected['acceptance_id'],'clicked_actual_sidebar_link':True,'expanded_full_receipt':True,'hash_checked_content_rendered':True}
    report['checks'].append('Independent reviewer clicks actual sidebar release and verifies same full release ID, exact artifact ref/hash, full acceptance ID and content as offline notification deep link')
