"""Bounded C26 regressions; transport injection is explicit, never OS sleep evidence."""
import time
import uuid
from scenarios import login, event_recovery


IDLE = 'C26 real idle SSE heartbeats keep one connection for 47 seconds without queries or business progress changes'
STALE = 'C26 silent online SSE expires within 47 seconds, shows stale last-sync, cancels reader and reconciles actual server watermark'
RESUME = 'C26 browser lifecycle freeze resumes through a new snapshot and rejects late bytes from the aborted old connection'


def recovery_cases(page, base, project_path, owner, api, report, out, freshness_only=False):
    other = api(base, owner, 'POST', '/v1/projects', {
        'name': 'C26 isolated project', 'intent': 'Isolated recovery project', 'facts': [],
        'accepted_scope': ['Local C26 fixture'], 'constraints': [], 'source_document_refs': [],
        'read_snapshot_ids': [], 'source_configs': []})
    if not freshness_only:
        event_recovery(page, base, project_path, owner, api, report, out,
                       other['project_id'], 'C26 isolated project', None)
    prefix = project_path.replace('/p/', '/v1/projects/')
    # Real server stream is the default. Only the next requested stream can be
    # replaced with an explicitly stalled browser ReadableStream.
    page.add_init_script("""(() => {
      const evidence = window.recoveryEvidence = {opens:0, queries:0, heartbeats:0,
        stallNext:false, stalled:0, aborted:0, lateBytes:0};
      const originalFetch = window.fetch;
      const getReader = ReadableStream.prototype.getReader;
      ReadableStream.prototype.getReader = function(...args) {
        const reader = getReader.apply(this, args), read = reader.read.bind(reader);
        reader.read = async (...a) => { const result = await read(...a);
          if (result.value && new TextDecoder().decode(result.value).includes(': heartbeat')) evidence.heartbeats++;
          return result; };
        return reader;
      };
      window.fetch = async (url, options={}) => {
        const path = new URL(url, location.origin).pathname;
        if (path.startsWith('/v1/') && !path.endsWith('/events/stream') && (!options.method || options.method === 'GET')) evidence.queries++;
        if (path.endsWith('/events/stream')) {
          evidence.opens++;
          if (evidence.stallNext) {
            evidence.stallNext=false; evidence.stalled++; evidence.started=Date.now();
            let controller;
            const body = new ReadableStream({start(c){controller=c;
              c.enqueue(new TextEncoder().encode(': explicit stalled stream fixture\\n\\n'));
            }});
            options.signal.addEventListener('abort', () => {
              evidence.aborted++; evidence.abortedAt=Date.now();
              // Deliberately deliver bytes after abort to exercise the consumer
              // fence independently of the normal fetch cancellation guarantee.
              controller.enqueue(new TextEncoder().encode('data: '+JSON.stringify(evidence.lateEvent)+'\\n\\n'));
              evidence.lateBytes++; controller.close();
            }, {once:true});
            return new Response(body, {status:200, headers:{'Content-Type':'text/event-stream'}});
          }
        }
        return originalFetch(url, options);
      };
    })();""")
    page.set_viewport_size({'width': 1440, 'height': 1000})
    login(page, base, project_path, owner)
    page.locator('.connection-banner').wait_for(state='hidden')
    page.wait_for_timeout(1500)
    before = page.locator('.progress-rail').inner_text()
    start = page.evaluate('({...recoveryEvidence, at:Date.now()})')
    idle = start
    if not freshness_only:
        page.wait_for_timeout(47000)
        idle = page.evaluate('({...recoveryEvidence, at:Date.now()})')
        assert idle['opens'] == start['opens'] and idle['queries'] == start['queries'], (start, idle)
        assert idle['heartbeats'] - start['heartbeats'] >= 3, (start, idle)
        assert before == page.locator('.progress-rail').inner_text()
        assert not page.locator('.connection-banner').count()
        report['idle_heartbeat'] = {'before': start, 'after': idle, 'business_progress_unchanged': True}
        report['checks'].append(IDLE)
    baseline = api(base, owner, 'GET', prefix + '/progress')
    # Give late bytes a valid next sequence: absence of a fence would accept it.
    late = {'id': 'late-aborted-fixture', 'project_id': other['project_id'],
            'sequence': baseline['as_of_event_sequence'] + 1}
    page.evaluate('(event) => {recoveryEvidence.lateEvent=event; recoveryEvidence.stallNext=true; dispatchEvent(new PageTransitionEvent("pageshow", {persisted:true}))}', late)
    page.wait_for_function('recoveryEvidence.stalled === 1')
    page.locator('.connection-banner').wait_for(state='hidden')
    state = api(base, owner, 'GET', prefix + '/state')
    api(base, owner, 'POST', prefix + '/requirements', {
        'requirement_key': 'C26-silent-' + uuid.uuid4().hex, 'text': 'Change during silent SSE fixture',
        'basis': 'USER_STATED', 'source_refs': [], 'rationale': 'C26 silent recovery',
        'supersedes_id': None, 'acceptance_check_ids': []}, f'"r{state["revision"]}"')
    expected = api(base, owner, 'GET', prefix + '/progress')
    page.locator('.connection-banner').wait_for(timeout=50000)
    banner = page.locator('.connection-banner').inner_text()
    assert '最后同步' in banner and '可能过期' in banner and page.evaluate('navigator.onLine')
    last_sync_age = page.evaluate('Date.now() - new Date(document.querySelector(".connection-banner").textContent.split("最后同步 " )[1].slice(0,-1)).getTime()')
    assert last_sync_age >= 44000, last_sync_age
    page.screenshot(path=str(out / 'silent-stream-stale.png'), full_page=False)
    report['screenshots'].append('silent-stream-stale.png')
    page.locator('.connection-banner').wait_for(state='hidden', timeout=15000)
    page.wait_for_function('(n) => document.querySelector(".progress-rail").textContent.includes("事件水位 " + n)', arg=expected['as_of_event_sequence'])
    silent = page.evaluate('({...recoveryEvidence})')
    assert 45000 <= silent['abortedAt'] - silent['started'] <= 47000, silent
    assert silent['aborted'] == 1 and silent['lateBytes'] == 1
    assert silent['queries'] > idle['queries'] and silent['opens'] >= idle['opens'] + 2
    report['silent_stream'] = {'transport': 'One explicitly injected silent ReadableStream; browser stays online',
        'before_watermark': baseline['as_of_event_sequence'], 'after_watermark': expected['as_of_event_sequence'],
        'banner': banner, 'last_sync_age_ms': last_sync_age, 'reader_evidence': silent}
    report['checks'].append(STALE)

    # This time use a same-project stale event; abort must fence it before it can
    # raise the sequence, clear the warning, or force a query from the old stream.
    late.update(project_id=project_path.rsplit('/', 1)[1], sequence=expected['as_of_event_sequence'] + 100)
    page.evaluate('(event) => {recoveryEvidence.lateEvent=event; recoveryEvidence.stallNext=true; dispatchEvent(new PageTransitionEvent("pageshow", {persisted:true}))}', late)
    page.wait_for_function('recoveryEvidence.stalled === 2')
    page.locator('.connection-banner').wait_for(state='hidden')
    frozen_before = page.evaluate('({...recoveryEvidence})')
    session = page.context.new_cdp_session(page)
    session.send('Page.setWebLifecycleState', {'state': 'frozen'})
    # Actual browser timers stop, while the separate loopback server stays up.
    time.sleep(22)
    state = api(base, owner, 'GET', prefix + '/state')
    api(base, owner, 'POST', prefix + '/requirements', {
        'requirement_key': 'C26-resume-' + uuid.uuid4().hex, 'text': 'Change during frozen browser fixture',
        'basis': 'USER_STATED', 'source_refs': [], 'rationale': 'C26 lifecycle recovery',
        'supersedes_id': None, 'acceptance_check_ids': []}, f'"r{state["revision"]}"')
    expected = api(base, owner, 'GET', prefix + '/progress')
    session.send('Page.setWebLifecycleState', {'state': 'active'})
    page.wait_for_function('recoveryEvidence.aborted === 2', timeout=15000)
    page.locator('.connection-banner').wait_for(state='hidden', timeout=15000)
    page.wait_for_function('(n) => document.querySelector(".progress-rail").textContent.includes("事件水位 " + n)', arg=expected['as_of_event_sequence'])
    resumed = page.evaluate('({...recoveryEvidence})')
    assert resumed['opens'] > frozen_before['opens'] and resumed['queries'] > frozen_before['queries']
    assert resumed['lateBytes'] == 2
    page.screenshot(path=str(out / 'browser-resume-snapshot.png'), full_page=False)
    report['screenshots'].append('browser-resume-snapshot.png')
    report['resume_freshness'] = {'before': frozen_before, 'after': resumed,
        'watermark': expected['as_of_event_sequence'], 'actual_browser_freeze_seconds': 22, 'physical_os_sleep': False}
    report['checks'].append(RESUME)
    session.detach()
