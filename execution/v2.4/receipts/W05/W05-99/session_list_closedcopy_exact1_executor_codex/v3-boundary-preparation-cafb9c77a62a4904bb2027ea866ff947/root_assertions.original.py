def typed_cells(values):
    cells = []
    for typ, value in zip(values[::2], values[1::2]):
        if typ == 'null':
            payload = ''
        elif typ == 'integer':
            payload = str(value)
        elif typ == 'real':
            payload = float(value).hex()
        elif typ == 'text':
            payload = base64.b64encode(value.encode('utf-8')).decode()
        elif typ == 'blob':
            payload = base64.b64encode(value).decode()
        else:
            raise RuntimeError('Unknown SQLite storage class')
        cells.append((typ, payload))
    return tuple(cells)


def canonical_saved_cells(serialized):
    pairs = json.loads(serialized)
    return tuple((typ, float(payload).hex() if typ == 'real' else payload) for typ, payload in pairs)


def check_closed(directory):
    database = directory / 'closed.sqlite'
    before = row(database)
    assert not Path(str(database) + '-wal').exists() and not Path(str(database) + '-shm').exists()
    recorded = load(directory / 'closed.rows.json')
    assert recorded == load(directory / 'post-open.rows.json')
    connection = sqlite3.connect(database.as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        connection.execute('PRAGMA query_only=ON')
        schema = [list(item) for item in connection.execute('SELECT type,name,tbl_name,rootpage,sql FROM sqlite_schema ORDER BY type,name')]
        assert Counter(tuple(item) for item in schema) == Counter(tuple(json.loads(item)) for item in recorded['schema'])
        tables = [item[0] for item in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name")]
        assert set(tables) == set(recorded['tables']) == set(recorded['columns'])
        table_counts = {}
        for name in tables:
            quoted = '"' + name.replace('"', '""') + '"'
            columns = [list(item) for item in connection.execute('PRAGMA table_xinfo(' + quoted + ')')]
            assert Counter(tuple(item) for item in columns) == Counter(tuple(json.loads(item)) for item in recorded['columns'][name])
            names = ['"' + item[1].replace('"', '""') + '"' for item in columns]
            expressions = ','.join(value for name in names for value in ['typeof(' + name + ')', name])
            actual = Counter(typed_cells(values) for values in connection.execute('SELECT ' + expressions + ' FROM ' + quoted))
            expected = Counter(canonical_saved_cells(item) for item in recorded['tables'][name])
            assert actual == expected
            table_counts[name] = sum(actual.values())
    finally:
        connection.close()
    assert row(database) == before
    proof = load(directory / 'closed-proof.json')
    assert proof['closed_copy_sha256'] == before['sha256']
    assert proof['all_table_schema_multisets_equal'] is True and proof['closed_copy_bytes_unchanged_by_read'] is True
    assert proof['case_failed'] is False and proof['SDK_worker_model_external_paid'] == 0
    return {'database': before, 'independent_python_sqlite_version': sqlite3.sqlite_version,
        'schema_all_columns_all_typed_row_multisets_equal': True, 'table_counts': table_counts,
        'readonly_bytes_unchanged': True, 'rowid_not_separately_exported': True}


def check_wire(directory, name):
    count = 0
    for request_meta in sorted(directory.glob('http-*.request.json')):
        stem = request_meta.name.removesuffix('.request.json')
        request = load(request_meta)
        response = load(directory / (stem + '.response.json'))
        for kind, meta in [('request', request), ('response', response)]:
            raw = (directory / (stem + '.' + kind + '.raw')).read_bytes()
            assert meta['bytes'] == len(raw) and meta['sha256'] == hashlib.sha256(raw).hexdigest()
        count += 1
    assertions = load(directory / 'assertions.json')
    assert assertions['case'] == name and assertions['all_assertions_reached'] is True
    proof = load(directory / 'closed-proof.json')
    assert 0 < count == assertions['HTTP_calls_including_setup'] == proof['HTTP_calls_including_setup'] <= 16
    journals = sorted(directory.glob('journal-*.json'))
    for journal_path in journals:
        journal = load(journal_path)
        number = int(journal_path.stem.split('-')[1])
        raw = (directory / f'http-{number:02d}.request.raw').read_bytes()
        response_raw = (directory / f'http-{number:02d}.response.raw').read_bytes()
        envelope = json.loads(raw)
        stored = json.loads(journal['body'])
        header = json.loads(journal['headers'])
        assert base64.b64decode(header['raw_envelope_base64'], validate=True) == raw
        assert stored == json.loads(response_raw)
        assert journal['command_id'] == envelope['command_id'] == stored['command_id']
        assert journal['project'] == envelope['project_id'] and journal['method'] == envelope['method'] == stored['method'] == 'session.list'
        assert stored['session_id'] == envelope['session_id']
        assert stored['protocol_version'] == envelope['protocol_version'] == 'researchos-client/2'
        assert stored['revision'] is None
    if name in ['ProjectGrantDenied', 'MalformedRequest']:
        assert len(journals) == 0
    else:
        assert len(journals) == 1
    return {'HTTP_calls_including_setup': count, 'actual_raw_wire_hashes_checked': True,
        'original_committed_identity_and_replay_journal_checked': True,
        'full_public_Go_schema_and_domain_hash_validation': 'unchanged native assertions, not reimplemented by Python'}

