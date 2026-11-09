"""Populated content UI, using real sealed bytes and explicitly labelled metadata fixtures."""
import hashlib
import json
import subprocess
import uuid
import jsonschema

from scenarios import login, ref, responsive_screen
from workflow import contract, now


def content_cases(page, base, project_path, owner, credentials, api, fixture_artifact, binary, environment, root, report, out):
    project_id = project_path.rsplit('/', 1)[1]
    prefix = project_path.replace('/p/', '/v1/projects/')
    schema = json.loads((root / 'spec/v2.0/contracts/domain.schema.json').read_text(encoding='utf-8'))
    def validate(kind, value):
        jsonschema.validate(value, {'$ref':'#/$defs/' + kind, '$defs':schema['$defs']})
    def get(path):
        return api(base, owner, 'GET', prefix + path)
    def seal(media, content, title):
        return fixture_artifact(base, credentials['token'], credentials['principal_id'], project_path, media, content, title)
    def metadata(items):
        done = subprocess.run([str(binary), project_id, 'artifact-metadata'], input=json.dumps(items), cwd=root,
                              env=environment, text=True, capture_output=True, timeout=30)
        assert done.returncode == 0, done.stderr
    def object_base():
        return {'id':uuid.uuid4().hex,'project_id':project_id,'revision':1,'created_at':now(),'updated_at':now()}
    baseline, baseline_evidence = seal('application/json', b'{"fixture":"baseline"}', 'C23 baseline')
    candidate, candidate_evidence = seal('text/plain', b'{"fixture":"candidate"}', 'C23 candidate')
    frozen = contract('{"expected_case_ids":["case1","case2"]}')
    frozen['checks'][0]['command_key'] = 'experiments.paired-mean-v1'
    del frozen['contract_hash']
    frozen['contract_hash'] = 'sha256:' + hashlib.sha256(json.dumps(frozen, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    state, profile = get('/state'), get('/profile')
    experiment = api(base, credentials['editor_token'], 'POST', prefix + '/experiments', {
        'cycle_id':None,'scope':'PROJECT','hypothesis':'C23 compare frozen baseline and candidate',
        'candidate_ref':ref(candidate, 'Artifact'),'baseline_refs':[ref(baseline,'Artifact')],'input_refs':[ref(baseline,'Artifact')],
        'metrics':[{'metric_id':'quality','description':'Fixed metric definition','unit':'score','operator':'GTE','target':'1','upper_target':None,'mandatory':True}],
        'acceptance_contract':frozen,'stop_policy':{'wall_time_seconds':60,'max_attempts':1,'max_parallel_runs':1,'stop_conditions':['fixture limit']},
        'budget_policy_id':profile['budget_policy_id'],'measurement_mode':'FIXTURE'}, f'"r{state["revision"]}"')
    summary = {'schema_version':'2.0.0','project_id':project_id,'experiment_id':experiment['id'],'run_id':uuid.uuid4().hex,
        'report_artifact_ref':ref(baseline,'Artifact'),'dataset_split':'DEVELOPMENT',
        'counts':{'expected_count':10,'observed_count':9,'pass_count':5,'fail_count':1,'error_count':1,'abstain_count':2,'missing_count':1,'duplicate_count':0},
        'dataset_hash':baseline['content_hash'],'candidate_hash':candidate['content_hash'],'baseline_hash':baseline['content_hash'],
        'rubric_hash':frozen['contract_hash'],'integrity_status':'INCOMPLETE','duration_ms':1234,'cost':None,
        'limitations':['W13 rendering fixture; not a provider evaluation or independent verdict'],'created_at':now()}
    validate('EvaluationSummary', summary)
    summary_artifact, summary_evidence = seal('application/json', json.dumps(summary).encode(), 'C23 aggregate evaluation summary')
    populated_experiment = dict(experiment, status='INCONCLUSIVE', outcome='INCONCLUSIVE', results=[{'metric_id':'quality','baseline':'0.5','candidate':'0.5','sample_count':9,'evidence_refs':[ref(summary_artifact,'Artifact')],'status':'INCONCLUSIVE'}])
    validate('Experiment', populated_experiment)
    def experiment_reply(route):
        route.fulfill(status=200, content_type='application/json', body=json.dumps(populated_experiment))
    page.route('**' + prefix + '/experiments/' + experiment['id'], experiment_reply)
    login(page, base, project_path + '/experiments/' + experiment['id'], owner)
    page.get_by_role('heading', name=experiment['hypothesis'], exact=True).wait_for()
    page.get_by_role('button', name='受控预览').click()
    page.get_by_role('region', name='聚合评测摘要').wait_for()
    summary_view = page.locator('.evaluation-summary')
    assert summary_view.locator('tbody td').all_text_contents() == ['10','9','5','1','1','2','1','0']
    assert 'INCOMPLETE' in summary_view.inner_text() and '未知或待结算' in summary_view.inner_text()
    assert candidate['content_hash'] in summary_view.inner_text() and baseline['content_hash'] in summary_view.inner_text()
    assert '无改善或证据不足是合法结果' in page.locator('main').inner_text()
    responsive_screen(page, 'experiment-populated', report, out)
    page.unroute('**' + prefix + '/experiments/' + experiment['id'], experiment_reply)
    report['evaluation_ui'] = {'experiment_id':experiment['id'],'summary_artifact_ref':ref(summary_artifact,'Artifact'),
        'counts':summary['counts'],'integrity_status':'INCOMPLETE','cost':None,
        'fixture_boundary':'Experiment DRAFT and sealed bytes use real APIs; INCONCLUSIVE result metadata is a schema-validated fixed HTTP fixture. No actual evaluation run or acceptance claimed.'}
    report['checks'].append('C23 EvaluationSummary displays eight separate counters, hashes, incomplete status, duration and unknown cost from hash-checked sealed JSON; populated experiment uses shared metric rows and keeps negative conclusion visible')

    login(page, base, project_path + '/evidence', owner)
    page.get_by_label('检索词', exact=True).focus()
    page.keyboard.type('candidate')
    page.wait_for_function("!document.querySelector('.filter-row button[type=submit]').disabled")
    page.get_by_role('button', name='服务端检索', exact=True).focus()
    with page.expect_response(lambda response: response.url.endswith('/search')) as search_response:
        page.keyboard.press('Enter')
    assert search_response.value.status == 200, search_response.value.text()
    report['search_response'] = search_response.value.json()
    page.get_by_text('服务端返回 1 条检索结果；范围为本页筛选后的封存快照。', exact=True).wait_for()
    page.get_by_role('button', name='定位证据', exact=True).click()
    page.get_by_text('C23 candidate', exact=True).wait_for()
    page.get_by_label('独立来源', exact=False).select_option(candidate_evidence['independence_key'])
    assert page.locator('.list-panel .record-row').count() == 1
    page.get_by_label('抓取起日（UTC）', exact=True).fill('2099-01-01')
    page.get_by_text('本页没有符合筛选条件的证据；来源受限应查看周期覆盖。', exact=True).wait_for()
    page.get_by_label('抓取起日（UTC）', exact=True).fill('')
    report['checks'].append('C23/C24 keyboard source query sends real visible snapshot IDs and renders SearchResponse.hits; evidence claim, independent-source and UTC date filters bind actual fields')

    # A malformed image still offers a controlled download of the original sealed bytes.
    bad_image, bad_evidence = seal('image/png', b'not-a-valid-png-W13', 'C25 image failure')
    login(page, base, project_path + '/evidence', owner)
    page.get_by_role('button').filter(has=page.locator('strong', has_text=bad_evidence['id'][:12])).click()
    page.get_by_role('button', name='受控预览').click()
    page.get_by_text('预览失败：图片无法渲染，可下载已封存内容', exact=True).wait_for()
    with page.expect_download() as download:
        page.get_by_role('button', name='受控下载', exact=True).click()
    from pathlib import Path
    assert Path(download.value.path()).read_bytes() == b'not-a-valid-png-W13'
    private = dict(candidate, id=uuid.uuid4().hex, content_hash='sha256:' + hashlib.sha256(b'classification-only').hexdigest(),
                   storage_key='unbound-w13-protected-metadata', access_class='VERIFIER_ONLY', byte_size=0)
    stale = dict(baseline, validity='STALE', revision=baseline['revision'] + 1, updated_at=now())
    metadata([private, stale])
    failures = {}
    for label, path in [('metadata','/artifacts/' + private['id']),('content','/artifacts/' + private['id'] + '/content'),('traversal','/artifacts/..%2F..%2FAGENTS.md/content')]:
        try:
            get(path)
            raise AssertionError(label + ' unexpectedly readable')
        except RuntimeError as error:
            failures[label] = str(error)
            assert '-> 404' in str(error) or '-> 403' in str(error) or '-> 400' in str(error), str(error)
            assert private['storage_key'] not in str(error)
    assert all(item['id'] != private['id'] for item in get('/artifacts')['items'])
    login(page, base, project_path + '/evidence', owner)
    page.get_by_role('button').filter(has=page.locator('strong', has_text=baseline_evidence['id'][:12])).click()
    page.locator('.artifact-preview').get_by_text('STALE', exact=False).wait_for()
    page.get_by_role('button', name='受控预览').click()
    page.get_by_text('预览失败：产物修订与固定引用不一致', exact=True).wait_for()
    assert private['storage_key'] not in page.locator('main').inner_text() and private['content_hash'] not in page.locator('main').inner_text()
    page.screenshot(path=str(out / 'stale-artifact-denied.png'), full_page=False)
    report['screenshots'].append('stale-artifact-denied.png')
    report['preview_security'] = {'invalid_image_artifact':bad_image['id'],'download_original_bytes':True,'private_http_denials':failures,
        'stale_artifact_ref':ref(stale,'Artifact'),'protected_boundary':'Synthetic classification metadata only; no formal holdout/protected bytes stored; actual protected storage remains W17'}
    report['checks'].append('C25 corrupted image recovers with hash-checked download; real API denies restricted metadata/content and traversal, list filtering excludes restricted record, STALE revision remains visible and frozen-reference mismatch stops preview')

    # Knowledge is a fixed UI contract fixture while W14 promotion remains outside W13.
    skill = dict(object_base(), skill_name='C23 candidate skill', version='0.1.0', status='CANDIDATE', scope='PROJECT',
        content_artifact_ref=ref(candidate,'Artifact'), source_refs=[ref(candidate_evidence,'Evidence')],
        expected_source_ids=[candidate_evidence['id'],baseline_evidence['id']], processed_source_ids=[candidate_evidence['id']],
        failed_source_ids=[baseline_evidence['id']],conflict_ids=[],license_expression='MIT',required_variables=[],allowed_capabilities=[],
        baseline_skill_id=None,experiment_id=experiment['id'],acceptance_id=None,rollback_skill_id=None)
    validate('SkillVersion', skill)
    def skills(route):
        route.fulfill(status=200, content_type='application/json', body=json.dumps({'items':[skill]}))
    def skill_detail(route):
        route.fulfill(status=200, content_type='application/json', body=json.dumps(skill))
    page.route('**' + prefix + '/skills', skills)
    page.route('**' + prefix + '/skills/' + skill['id'], skill_detail)
    login(page, base, project_path + '/knowledge', owner)
    page.get_by_role('button', name='C23 candidate skill · 0.1.0', exact=False).click()
    page.get_by_text('1 / 2 已处理', exact=True).wait_for()
    assert page.get_by_text('尚无回执', exact=True).is_visible()
    assert page.get_by_role('link', name='查看关联实验', exact=True).get_attribute('href').endswith(experiment['id'])
    assert not page.get_by_role('button', name='晋升', exact=True).count()
    responsive_screen(page, 'knowledge-populated', report, out)
    page.unroute('**' + prefix + '/skills', skills)
    page.unroute('**' + prefix + '/skills/' + skill['id'], skill_detail)
    report['checks'].append('C23 fixed SkillVersion fixture renders skill_name/version, candidate status, 1/2 source coverage, failed sources, absent acceptance/rollback and experiment link without promotion authority')

    policy = get('/budget-policy')
    entries = []
    for operation, basis, money in [('COMMIT','ACTUAL',{'amount':'1.25','currency':'USD'}),('RESERVE','UPPER_BOUND',{'amount':'2.00','currency':'USD'}),('UNKNOWN','UNKNOWN',None)]:
        entry = {k:v for k,v in object_base().items() if k != 'updated_at'}
        entry.update(receipt_hash='sha256:' + 'c' * 64,policy_id=policy['id'],run_id=uuid.uuid4().hex,operation=operation,money=money,
            provider_request_id=uuid.uuid4().hex,provider_event_id=uuid.uuid4().hex,reservation_id=None,cost_basis=basis,occurred_at=now())
        validate('BudgetLedgerEntry',entry)
        entries.append(entry)
    request = dict(object_base(),category='QUOTA',account_ref=None,reason_code='UI_FIXTURE_QUOTA',summary='C23 quota resource fixture',
        dedup_key='sha256:' + 'd' * 64,status='OPEN',blocked_task_ids=[uuid.uuid4().hex],continuable_task_ids=[],
        completed_artifact_refs=[ref(candidate,'Artifact')],requested_capability='Additional quota after recorded checkpoint',
        estimated_cost=None,cost_known=False,resume_checkpoint_ref=ref(candidate,'Artifact'),resolved_by=None)
    validate('ResourceRequest',request)
    def ledger(route):
        route.fulfill(status=200,content_type='application/json',body=json.dumps({'items':entries}))
    def requests(route):
        route.fulfill(status=200,content_type='application/json',body=json.dumps({'items':[request]}))
    page.route('**' + prefix + '/budget-ledger',ledger)
    page.route('**' + prefix + '/resource-requests',requests)
    login(page,base,project_path+'/resources',owner)
    page.get_by_text('C23 quota resource fixture',exact=True).wait_for()
    assert '已结算 1 笔 · 在途预留 1 笔 · 未知 1 笔' in page.locator('main').inner_text()
    assert '1.25 USD' in page.locator('main').inner_text() and '2.00 USD' in page.locator('main').inner_text()
    assert '受阻任务 1 · 可继续任务 0 · 已保留产物 1' in page.locator('main').inner_text()
    page.get_by_label('策略',exact=False).focus()
    page.keyboard.press('Home')
    page.keyboard.press('ArrowDown')
    page.get_by_label('金额',exact=True).focus()
    page.keyboard.type('25.00')
    assert page.get_by_label('金额',exact=True).input_value() == '25.00'
    page.get_by_role('button',name='保存上限',exact=True).focus()
    with page.expect_response(lambda response: response.url.endswith('/budget-policy') and response.request.method == 'PUT') as policy_response:
        page.keyboard.press('Enter')
    report['budget_update_response'] = {'status':policy_response.value.status,'body':policy_response.value.json()}
    assert policy_response.value.ok, policy_response.value.text()
    page.get_by_text('金额策略已由服务保存',exact=True).wait_for()
    saved_policy = get('/budget-policy')
    assert saved_policy['cap']=={'amount':'25.00','currency':'USD'}
    assert saved_policy['enforcement'] == 'STRICT' and saved_policy['unknown_cost_action'] == 'BLOCK'
    page.locator('.summary-strip').get_by_text('25.00 USD',exact=True).wait_for()
    page.get_by_label('策略',exact=False).select_option('UNLIMITED_AMOUNT')
    with page.expect_response(lambda response: response.url.endswith('/budget-policy') and response.request.method == 'PUT') as unlimited_response:
        page.get_by_role('button',name='保存上限',exact=True).click()
    assert unlimited_response.value.ok, unlimited_response.value.text()
    unlimited = get('/budget-policy')
    assert unlimited['cap'] is None and unlimited['enforcement'] == 'ACCOUNTING_ONLY' and unlimited['unknown_cost_action'] == 'ALLOW_AND_RECORD'
    page.locator('.summary-strip').get_by_text('未设上限',exact=True).wait_for()
    page.wait_for_function("!document.querySelector('button[type=submit]').disabled")
    page.get_by_label('策略',exact=False).select_option('CAPPED')
    page.get_by_label('金额',exact=True).fill('25.00')
    page.get_by_label('执行方式',exact=False).select_option('ESTIMATED')
    with page.expect_response(lambda response: response.url.endswith('/budget-policy') and response.request.method == 'PUT') as estimated_response:
        page.get_by_role('button',name='保存上限',exact=True).click()
    assert estimated_response.value.ok, estimated_response.value.text()
    estimated = get('/budget-policy')
    assert estimated['enforcement'] == 'ESTIMATED' and estimated['unknown_cost_action'] == 'ALLOW_AND_RECORD'
    report['budget_policy_roundtrip'] = [saved_policy, unlimited, estimated]
    responsive_screen(page,'resources-populated',report,out)
    page.unroute('**'+prefix+'/budget-ledger',ledger)
    page.unroute('**'+prefix+'/resource-requests',requests)
    report['checks'].append('C23 fixed ledger/resource fixtures distinguish actual charge, outstanding reservation, unknown amount and checkpoint impact; real browser cap edit persists 25.00 USD through service API')
    report['content_fixture_boundaries'] = ['Skill/ledger/resource populated metadata are schema-validated fixed UI payloads, not W14 promotion or live billing evidence',
        'Artifacts, hashes, policy mutation, access denial, stale classification and controlled bytes use the real local HTTP service',
        'Physical phone, formal holdout isolation and device pairing remain W17']
