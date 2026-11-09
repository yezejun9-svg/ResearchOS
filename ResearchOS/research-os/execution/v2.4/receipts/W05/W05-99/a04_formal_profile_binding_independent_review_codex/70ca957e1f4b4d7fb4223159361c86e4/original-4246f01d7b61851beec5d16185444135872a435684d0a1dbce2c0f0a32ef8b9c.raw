# This ABI is a SOURCE proposal. Root must implement and independently review its
# real capture producer; this module never produces those observations.
ASSERTION_LANES = dict(zip(IDS, ('success', 'pending_queue_cancel',
                                'executor_crash', 'H08', 'P01', 'U02')))


def _integer(value, label):
    if type(value) is not int or value < 0:
        raise ValueError('OPEN_TYPED_INTEGER:' + label)
    return value


def _nonempty(value, label, kind=str):
    if type(value) is not kind or not value:
        raise ValueError('OPEN_REQUIRED_ORIGINAL:' + label)
    return value


def _json_original(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('OPEN_DUPLICATE_ORIGINAL_KEY')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(
                          ValueError('OPEN_NONFINITE_ORIGINAL')))


def _original(doc, raw, reference):
    if type(reference) is not dict or set(reference) != {'path', 'sha256'}:
        raise ValueError('OPEN_WHOLE_ORIGINAL_REQUIRED')
    return doc(reference), raw(reference)


def _root_pair(document, scope):
    if type(document) is not dict or document.get('schema') != 'researchos.w05.original-tool-pair.v2':
        raise ValueError('OPEN_ORIGINAL_ROOT_TOOL_PAIR')
    initial, terminal = document.get('initial'), document.get('terminal')
    for pair in (initial, terminal):
        if type(pair) is not dict or set(pair) != {'tool', 'input', 'result'} or type(pair['input']) is not dict or type(pair['result']) is not dict:
            raise ValueError('OPEN_ORIGINAL_TOOL_INPUT_RESULT')
    if initial['tool'] != 'exec_command' or initial['input'] != scope['initial_tool_input']:
        raise ValueError('OPEN_ROOT_INITIAL_INPUT')
    first = initial['result']
    if type(first.get('session_id')) is int:
        if terminal['tool'] != 'write_stdin' or terminal['input'].get('session_id') != first['session_id'] or terminal['input'].get('chars', '') != '':
            raise ValueError('OPEN_ROOT_TERMINAL_SESSION')
    elif terminal != initial:
        raise ValueError('OPEN_ROOT_SYNCHRONOUS_PAIR')
    _integer(terminal['result'].get('exit_code'), 'actual outer exit')
    output = _nonempty(terminal['result'].get('output'), 'original terminal output')
    lines = output.splitlines()
    summaries = [_json_original(line) for line in lines if line.startswith('{')]
    closed = [row for row in summaries if type(row) is dict and 'actual_launcher_native_exit' in row]
    if len(closed) != 1:
        raise ValueError('OPEN_ACTUAL_NATIVE_BRIDGE')
    _integer(closed[0]['actual_launcher_native_exit'], 'actual launcher native exit')
    return closed[0]


def _database(raw, identity):
    # In-memory deserialization prevents mutation or WAL omission of a live path.
    # Only a Root-materialized complete, quiescent SQLite snapshot is supported.
    if type(raw) is not bytes or not raw.startswith(b'SQLite format 3\\x00'):
        raise ValueError('OPEN_COMPLETE_SQLITE_ORIGINAL')
    import sqlite3
    db = sqlite3.connect(':memory:')
    try:
        db.deserialize(raw)
        db.execute('PRAGMA query_only=ON')
        result = {}
        for kind, key in (('Task', 'task_id'), ('TaskRun', 'run_id')):
            rows = db.execute('SELECT revision,content_hash,body FROM domain_objects WHERE project=? AND kind=? AND id=?',
                              (identity['project_id'], kind, identity[key])).fetchall()
            if len(rows) != 1:
                raise ValueError('OPEN_DATABASE_CURRENT_IDENTITY')
            revision, digest, body = rows[0]
            _integer(revision, 'database revision')
            if revision < 1 or type(digest) is not str or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError('OPEN_DATABASE_REF')
            value = _json_original(body)
            if value.get('id') != identity[key] or value.get('revision') != revision:
                raise ValueError('OPEN_DATABASE_BODY')
            result[kind] = value
        if result['TaskRun'].get('task_id') != identity['task_id']:
            raise ValueError('OPEN_DATABASE_TASK_RUN')
        result['acceptance_count'] = db.execute(
            "SELECT count(*) FROM domain_objects WHERE project=? AND kind='AcceptanceReceipt' AND json_extract(body,'$.task_id')=?",
            (identity['project_id'], identity['task_id'])).fetchone()[0]
        return result
    finally:
        db.close()


def _jsonl(raw, identity):
    lines = raw.decode('utf-8').splitlines()
    if not lines or any(not line.strip() for line in lines):
        raise ValueError('OPEN_COMPLETE_JSONL')
    frames = [_json_original(line) for line in lines]
    events, finals = [], []
    for ordinal, frame in enumerate(frames):
        if type(frame) is not dict:
            raise ValueError('OPEN_JSONL_OBJECT')
        if frame.get('type') == 'session.event':
            if finals:
                raise ValueError('OPEN_EVENT_AFTER_FINAL')
            event = frame.get('event')
            if type(event) is not dict or event.get('session_id') != identity['session_id'] or event.get('protocol_version') != 'researchos-client/2' or event.get('core_build_id') != identity['core_build_id']:
                raise ValueError('OPEN_EVENT_IDENTITY')
            _integer(event.get('sequence'), 'event sequence')
            if events and event['sequence'] != events[-1]['sequence'] + 1:
                raise ValueError('OPEN_EVENT_GAP')
            if event.get('run_id') not in (None, identity['run_id']):
                raise ValueError('OPEN_FOREIGN_RUN_EVENT')
            events.append(event)
        elif frame.get('type') == 'session.snapshot':
            raise ValueError('OPEN_EVENT_RESYNC_OR_SNAPSHOT')
        else:
            if ordinal != len(frames)-1 or finals or type(frame.get('execution')) is not dict:
                raise ValueError('OPEN_SINGLE_FINAL_REQUIRED')
            finals.append(frame['execution'])
    if not events or len(finals) != 1:
        raise ValueError('OPEN_ORIGINAL_EVENT_STREAM')
    final = finals[0]
    for key in ('project_id', 'session_id', 'goal_id', 'task_id', 'run_id'):
        if final.get(key) != identity[key]:
            raise ValueError('OPEN_FINAL_IDENTITY')
    if final.get('event_sequence') != events[-1]['sequence'] or final.get('independent_acceptance') != 'NOT_EVALUATED':
        raise ValueError('OPEN_FINAL_CURSOR_ACCEPTANCE')
    _integer(final.get('exit_code'), 'actual CLI exit')
    return events, final


def verify_live_originals(doc, raw, context, row, invocation, scope):
    identity = row.get('product_identity')
    keys = {'project_id', 'session_id', 'goal_id', 'task_id', 'run_id', 'core_build_id'}
    if type(identity) is not dict or set(identity) != keys or not all(type(value) is str and value for value in identity.values()):
        raise ValueError('OPEN_ACTUAL_PRODUCT_IDENTITIES')
    if row['lane'] != ASSERTION_LANES[row['id']]:
        raise ValueError('OPEN_FROZEN_ASSERTION_LANE')
    original, _ = _original(doc, raw, row.get('original_witness_ref'))
    if original.get('schema') != 'researchos.w05.a04-whole-originals.v2' or original.get('run_id') != context['run_id'] or original.get('lane') != row['lane'] or original.get('product_identity') != identity:
        raise ValueError('OPEN_WHOLE_ORIGINAL_IDENTITY')
    for key in ('argv', 'cwd', 'env_names', 'initial_tool_input', 'producer_ref'):
        if key not in scope or scope[key] != invocation.get(key):
            raise ValueError('OPEN_COMPLETE_SCOPE_ABI')
    _nonempty(invocation.get('argv'), 'actual argv', list)
    _nonempty(invocation.get('cwd'), 'actual cwd')
    if type(invocation.get('env_names')) is not list or any(type(v) is not str or not v for v in invocation['env_names']):
        raise ValueError('OPEN_ACTUAL_ENV_NAMES')
    _integer(invocation.get('native_exit'), 'actual invocation exit')
    capture, _ = _original(doc, raw, original.get('root_tool_pair_ref'))
    closed = _root_pair(capture, scope)
    if closed['actual_launcher_native_exit'] != invocation['native_exit']:
        raise ValueError('OPEN_NATIVE_RESULT_CONFLICT')
    job, _ = _original(doc, raw, original.get('windows_job_ref'))
    if job.get('schema') != 'researchos.w05.windows-job-original.v2' or job.get('run_id') != context['run_id'] or job.get('lane') != row['lane'] or job.get('root_tool_pair_ref') != original['root_tool_pair_ref'] or job.get('producer_ref') != scope['producer_ref'] or job.get('native_exit') != invocation['native_exit']:
        raise ValueError('OPEN_WINDOWS_JOB_BINDING')
    for key in ('owned_processes_before', 'owned_processes_after', 'pending_requests_after', 'launch_events'):
        if type(job.get(key)) is not list:
            raise ValueError('OPEN_COMPLETE_WINDOWS_JOB_EVENTS')
    if job.get('job_closed') is not True or job.get('cleanup_complete') is not True:
        raise ValueError('OPEN_WINDOWS_JOB_NOT_CLOSED')
    objects = _database(raw(original['database_ref']), identity)
    events, final = _jsonl(raw(original['jsonl_ref']), identity)
    if final['exit_code'] != invocation['native_exit']:
        raise ValueError('OPEN_JSONL_NATIVE_CONFLICT')
    task, run = objects['Task'], objects['TaskRun']
    states = [ev.get('payload') for ev in events if ev.get('kind') == 'RUN_STATE' and ev.get('run_id') == identity['run_id']]
    if not states or type(states[-1]) is not dict:
        raise ValueError('OPEN_RUN_STATE_ORIGINAL')
    state = states[-1]
    _integer(state.get('revision'), 'RUN_STATE revision')
    if state.get('revision') != run.get('revision') or state.get('status') != run.get('status') or run.get('children_stopped') is not True or run.get('queue_empty') is not True:
        raise ValueError('OPEN_RUN_DATABASE_EVENT_BINDING')
    if row['id'] == 'A04-01':
        if task.get('status') != 'EXECUTION_REPORTED' or run.get('status') != 'SETTLED' or objects['acceptance_count'] != 0 or final.get('status') != 'EXECUTION_REPORTED':
            raise ValueError('OPEN_EXECUTION_REPORTED_NOT_ACCEPTED')
        if not run.get('result_artifact_ids') or state.get('settled_at') != run.get('runtime_settled_at'):
            raise ValueError('OPEN_SETTLED_RECEIPTS')
    elif row['id'] == 'A04-02':
        if run.get('status') != 'CANCELLED' or not run.get('cancel_confirmed_at') or state.get('cancel_confirmed_at') != run['cancel_confirmed_at'] or job['owned_processes_after'] or job['pending_requests_after']:
            raise ValueError('OPEN_CANCEL_SETTLEMENT')
        for event in job['launch_events']:
            if type(event) is not dict or event.get('task_id') != identity['task_id'] or type(event.get('after_cancel')) is not bool or event['after_cancel']:
                raise ValueError('OPEN_CANCEL_LATE_OR_FOREIGN_LAUNCH')
    # Recovery/nested SDK/installed interaction/Issue actions require actual
    # producer formats not yet frozen or implemented. Do not let booleans or
    # an arbitrary "facts" export stand in for those missing semantic decoders.
    else:
        for key in ('sdk_jsonl_ref', 'action_jsonl_ref', 'recovery_ref'):
            _original(doc, raw, original.get(key))
        raise ValueError('OPEN_A04_' + row['id'] + '_ACTUAL_PRODUCER_SEMANTIC_DECODER_REQUIRED')
    return original


def verify_refusal(doc, raw, context, row):
    for reference in _nonempty(row.get('refusal_evidence_refs'), 'actual refusal refs', list):
        refusal, _ = _original(doc, raw, reference)
        if refusal.get('schema') != 'researchos.w05.actual-refusal.v2' or refusal.get('assertion_id') != row['id'] or refusal.get('run_id') != context['run_id'] or refusal.get('lane') != row['lane'] or refusal.get('task_id') != row['product_identity']['task_id'] or refusal.get('rejected') is not True:
            raise ValueError('OPEN_ACTUAL_REFUSAL_IDENTITY')
        if type(refusal.get('negative_condition')) is not str or not refusal['negative_condition'] or refusal.get('invocation_ref') != row['negative_invocation_ref']:
            raise ValueError('OPEN_FROZEN_NEGATIVE_BINDING')
        invocation, _ = _original(doc, raw, refusal['invocation_ref'])
        _integer(invocation.get('native_exit'), 'refusal native exit')
        pair, _ = _original(doc, raw, invocation['root_tool_pair_ref'])
        closed = _root_pair(pair, invocation['scope'])
        if closed['actual_launcher_native_exit'] != invocation['native_exit'] or invocation['native_exit'] == 0:
            raise ValueError('OPEN_REFUSAL_ACTUAL_NONZERO')
        response, _ = _original(doc, raw, refusal['original_response_ref'])
        if response.get('status') not in ('REJECTED', 'BLOCKED', 'DENIED') or response.get('task_id') != row['product_identity']['task_id']:
            raise ValueError('OPEN_ORIGINAL_REFUSAL_RESPONSE')

